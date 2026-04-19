"""Process EMR JSON, generate summaries + auto-detect F/G, write to Sheet.

Usage: python process_emr.py <date8>   e.g. 20260419

Reads emr_data_<date>.json, reads sub-tables from Sheet <date>, writes:
- C col: full EMR text
- D col: 4-section summary
- F col: auto-detected 術前診斷
- G col: auto-detected 預計心導管
- A col (name): auto-corrected from EMR name

Also updates main data G col and N-V P col if patient exists there.
"""
import sys, json, re, time
sys.path.insert(0, '.')
import gsheet_utils as gu

# Order matters: 急/specific > arrhythmias > vascular > CHF > CAD-family (broadest, last).
# Diag matching is constrained to the (Dx) section by extract_dx_section() so
# comorbidity entries like `* (ICD-10:I495)` (sick sinus) don't bleed into primary Dx.
DIAG_RULES = [
    # Acute / time-critical
    (['STEMI', 'ST elevation myocardial'], 'STEMI'),
    (['NSTEMI', 'non-ST elevation', 'non ST elevation'], 'Others:NSTEMI'),
    (['unstable angina'], 'Unstable'),
    # Specific structural valves
    (['severe AS', 'aortic stenosis'], 'AS'),
    (['severe AR', 'aortic regurgitation'], 'AR'),
    (['severe MR', 'mitral regurgitation', 'MVRepair', 'MVR'], 'MR'),
    (['severe TR', 'tricuspid regurgitation'], 'Others:Severe TR'),
    # Devices
    (['generator replacement', 'PPM generator', 'ICD generator'], 'Generator replacement'),
    # Arrhythmias
    (['paroxysmal Af', 'paroxysmal atrial fibrillation',
      'Long persistent atrial fibrillation', 'persistent Af',
      'persistent atrial fibrillation', 'pAf'], 'pAf'),
    (['supraventricular tachycardia', 'PSVT'], 'PSVT'),
    (['WPW'], 'WPW syndrome'),
    (['atrial flutter', 'Aflutter'], 'Atrial flutter'),
    (['ventricular premature', 'VPC'], 'VPC'),
    (['sick sinus', 'sinus nodal dysfunction', 'sinus pause', 'tachy-brady', 'SSS'], 'Sinus nodal dysfunction'),
    (['complete AV block', 'AV nodal dysfunction', 'CAVB', 'AV block'], 'AV nodal dysfunction'),
    # Vascular
    (['PAOD', 'peripheral arterial occlusive', 'peripheral arterial disease'], 'PAOD'),
    (['carotid stenting', 'carotid stenosis'], 'Carotid stenting'),
    # CHF / cardiomyopathy
    (['HFrEF', 'HFpEF', 'heart failure', 'CHF', 'congestive heart failure'], 'CHF'),
    (['dilated cardiomyopathy', 'DCM'], 'DCM'),
    (['hypertrophic cardiomyopathy', 'HCM'], 'HCM'),
    (['pulmonary hypertension', 'pulmonary HTN'], 'Pulmonary HTN'),
    # Symptom-driven
    (['syncope'], 'Syncope'),
    # (Removed ISR / in-stent restenosis — too aggressive; CAD rule below catches these correctly.)
    # CAD family — broadest, last. Trigger words expanded per learning analysis.
    (['angina pectoris', 'angina'], 'Angina pectoris'),
    (['CAD', 'coronary artery disease',
      'chest pain', 'chest tightness', 'chest tigthness',
      'ACS', 'acute coronary syndrome',
      'I259', 'I250', 'I251',
      'TET (+)', 'TMT (+)', 'THL (+)', 'TET+', 'TMT+', 'THL+'], 'CAD'),
]

# CATH matching runs against [Assessment & Plan] section after past-tense PCI is stripped.
# CRT is more specific than PPM so it goes first. PCI keywords avoid bare 's/p PCI'.
CATH_RULES = [
    (['CRT-D', 'CRT-P', 'CRT upgrade', 'cardiac resynchronization'], 'CRT'),
    (['TAVI', 'transcatheter aortic valve'], 'TAVI'),
    (['plan PCI', 'plan for PCI', 'arrange PCI', 'PCI for', 'primary PCI', '→PCI', '→ PCI', 'PCI ', 'intervention'], 'PCI'),
    (['RF ablation', 'RFA', 'ablation'], 'RF ablation'),
    (['PPM', 'pacemaker implant'], 'PPM'),
    (['EP study'], 'EP study'),
    (['PTA'], 'PTA'),
    (['carotid angiography', 'carotid stenting'], 'Carotid angiography + stenting'),
    (['both-sided cath', 'BHC'], 'Both-sided cath.'),
    (['right heart cath', 'RHC'], 'Right heart cath.'),
    (['myocardial biopsy', 'EMB'], 'Myocardial biopsy'),
    (['cath study', 'catheterization', 'Cath on', 'cath on', 'CAG', 'LHC'], 'Left heart cath.'),
]

# When CATH_RULES finds nothing in plan, fall back to the F → G typical mapping.
# Valve diseases (AS/AR/MR/TR) intentionally omitted — user usually leaves G blank
# for these so surgical-vs-percutaneous route can be discussed at the meeting.
F_TO_G_DEFAULT = {
    'CAD': 'Left heart cath.',
    'Angina pectoris': 'Left heart cath.',
    'Unstable': 'Left heart cath.',
    'CHF': 'Left heart cath.',
    'STEMI': 'PCI',
    'Others:NSTEMI': 'PCI',
    's/p PCI': 'Left heart cath.',
    'PAOD': 'PTA',
    'pAf': 'RF ablation',
    'PSVT': 'RF ablation',
    'WPW syndrome': 'RF ablation',
    'Atrial flutter': 'RF ablation',
    'VPC': 'RF ablation',
    'Sinus nodal dysfunction': 'PPM',
    'AV nodal dysfunction': 'PPM',
    'Generator replacement': 'PPM',
    # Valves default to Both-sided cath. (the typical eval procedure). User may
    # blank for surgical-vs-percutaneous discussion.
    'AS': 'Both-sided cath.', 'AR': 'Both-sided cath.', 'MR': 'Both-sided cath.',
    'Others:Severe TR': 'Both-sided cath.',
    'DCM': 'Right heart cath.',
    'HCM': 'Left heart cath.',
    'Pulmonary HTN': 'Right heart cath.',
    'Carotid stenting': 'Carotid angiography + stenting',
    'Syncope': 'EP study',
}


def extract_dx_section(emr_text):
    """Return primary diagnosis lines + ICD-10 codes from [Diagnosis] section.
    - Strips `* (Dx)` and `* (Dx)N.` prefixes so numbered items become parseable
    - Keeps ICD-10 codes on their own lines (cardiac codes I250/I259 are useful
      fallback when free-text Dx doesn't mention CAD)
    - Drops `Description :` header rows."""
    parts = re.split(r'\[(Diagnosis|Subjective|Objective|Assessment & Plan)\]', emr_text)
    diag_text = ''
    for i, part in enumerate(parts):
        if part == 'Diagnosis' and i + 1 < len(parts):
            diag_text = parts[i + 1]
            break
    if not diag_text:
        return ''
    out = []
    for line in diag_text.split('\n'):
        s = line.strip()
        if not s or s.startswith('Description'):
            continue
        # Normalise the "* (Dx)" / "* (Dx)1." prefix off
        s = re.sub(r'^\*?\s*\(Dx\)\s*', '', s)
        out.append(s)
    return '\n'.join(out)


# ICD-10 codes worth matching as a fallback when free-text Dx is silent on cardiac issues
ICD10_FALLBACK = [
    ((r'I25[019]',), 'CAD'),         # I250 / I251 / I259 chronic ischemic heart disease
    ((r'I21[0-9]',), 'STEMI'),       # I21x acute MI
    ((r'I50[0-9]',), 'CHF'),         # I50x heart failure
    ((r'I48[0-9]',), 'pAf'),         # I48x atrial fibrillation
    ((r'I47[0-9]',), 'PSVT'),        # I47x supraventricular tachycardia
    ((r'I49[5]',), 'Sinus nodal dysfunction'),  # I495 sick sinus
    ((r'I44[12]',), 'AV nodal dysfunction'),    # I441/I442 AV block
    ((r'I35[0]',), 'AS'),
    ((r'I35[1]',), 'AR'),
    ((r'I34[0]',), 'MR'),
    ((r'I70[2]',), 'PAOD'),
]


def detect_via_icd(dx_text):
    """Fallback: scan ICD-10 codes in Dx section."""
    icd_codes = re.findall(r'ICD[\-\u2010-\u2015]?10[^A-Z]{0,3}([A-Z]\d{2,4})', dx_text)
    if not icd_codes:
        return ''
    joined = ' '.join(icd_codes)
    for patterns, value in ICD10_FALLBACK:
        for p in patterns:
            if re.search(p, joined):
                return value
    return ''


def clean_past_tense_pci(text):
    """Strip historical PCI mentions so CATH PCI doesn't fire on `s/p PCI on 2020`."""
    patterns = [
        r's/p\s+PCI[^\n]*',
        r'post[\-\s]+PCI[^\n]*',
        r'status\s+post[^\n]*PCI[^\n]*',
        r'PCI\s+on\s+\d{4}[/\-]?\d{0,2}[/\-]?\d{0,2}',
        r'PCI\s+done[^\n]*',
        r'previous\s+PCI[^\n]*',
        r'history\s+of\s+PCI[^\n]*',
        r'old\s+PCI[^\n]*',
    ]
    for p in patterns:
        text = re.sub(p, ' ', text, flags=re.IGNORECASE)
    return text


def match_rules(text, rules):
    t = text.lower()
    for keywords, value in rules:
        for kw in keywords:
            kl = kw.lower()
            if len(kw) <= 4:
                if re.search(r'(?<![a-zA-Z])' + re.escape(kl) + r'(?![a-zA-Z])', t):
                    return value
            else:
                if kl in t:
                    return value
    return ''


def detect_diag(dx_text):
    """Apply DIAG_RULES with numbered-item priority.
    Numbered Dx (`2.CAD ... 4.pAf`) means item 2 is more important than item 4,
    so iterate items in order and take the first that matches a rule.
    Strip ICD-10 lines BEFORE keyword matching so comorbidity codes don't pollute,
    but keep them available for the ICD fallback at the end."""
    if not dx_text:
        return ''
    text_no_icd = '\n'.join([l for l in dx_text.split('\n') if not l.strip().startswith('* (ICD')])
    items = re.findall(r'(?:^|\n)\s*\d+\s*[\.\)]\s*([^\n]+)', text_no_icd)
    if items:
        for item in items:
            m = match_rules(item, DIAG_RULES)
            if m:
                return m
    m = match_rules(text_no_icd, DIAG_RULES)
    if m:
        return m
    # Last resort: cardiac ICD-10 codes
    return detect_via_icd(dx_text)


def detect_fg(emr_text):
    """Detect (F, G) using Dx-only matching for F and plan-cleaned matching for G,
    with F→G default fallback."""
    dx = extract_dx_section(emr_text)
    f_diag = detect_diag(dx) if dx else match_rules(emr_text, DIAG_RULES)

    if '[Assessment & Plan]' in emr_text:
        plan_sec = emr_text.split('[Assessment & Plan]')[1][:1500]
    else:
        plan_sec = emr_text

    # Plan-driven F overrides for procedure-defined diagnoses
    pl = plan_sec.lower()
    if 'generator replacement' in pl or 'ppm replacement' in pl \
            or 'icd replacement' in pl or 'crt replacement' in pl \
            or 'change generator' in pl:
        f_diag = 'Generator replacement'

    g_cath = match_rules(clean_past_tense_pci(plan_sec), CATH_RULES)
    if not g_cath and f_diag:
        g_cath = F_TO_G_DEFAULT.get(f_diag, '')
    return f_diag, g_cath

def generate_summary(emr_text, age='', gender=''):
    sections = {'diag': '', 'subj': '', 'obj': '', 'plan': ''}
    parts = re.split(r'\[(Diagnosis|Subjective|Objective|Assessment & Plan)\]', emr_text)
    for i, part in enumerate(parts):
        if part == 'Diagnosis' and i+1 < len(parts):
            sections['diag'] = parts[i+1].strip()
        elif part == 'Subjective' and i+1 < len(parts):
            sections['subj'] = parts[i+1].strip()
        elif part == 'Objective' and i+1 < len(parts):
            sections['obj'] = parts[i+1].strip()
        elif part == 'Assessment & Plan' and i+1 < len(parts):
            sections['plan'] = parts[i+1].strip()

    # If no structured sections found, dump whole text into "病史" so user sees something
    all_raw = emr_text.strip()
    if not any(sections.values()):
        sections['subj'] = all_raw[:1500]

    diag_lines = [l for l in sections['diag'].split('\n')
                  if l.strip() and not l.strip().startswith('* (ICD')]
    diag_clean = '\n'.join(diag_lines) if diag_lines else ''

    subj_lines = []
    for l in sections['subj'].split('\n'):
        l = l.strip()
        if l and not l.startswith('No ') and not l.startswith('Family history') and not l.startswith('Current medication'):
            subj_lines.append(l)
    subj_clean = '\n'.join(subj_lines[:15])

    obj_lines = [l.strip() for l in sections['obj'].split('\n')
                 if l.strip() and '[Plan' not in l and '[Medicine' not in l]
    obj_clean = '\n'.join(obj_lines[:20])

    plan_lines = []
    for l in sections['plan'].split('\n'):
        l = l.strip()
        cut = len(l)
        for tag in ('[Medicine]', '[Medication]', '------'):
            idx = l.find(tag)
            if idx != -1 and idx < cut:
                cut = idx
        if cut < len(l):
            prefix = l[:cut].strip()
            if prefix:
                plan_lines.append(prefix)
            break
        if l:
            plan_lines.append(l)
    plan_clean = '\n'.join(plan_lines[:10])

    header = f'{age} y/o {gender}' if age else ''
    return f"""{header}
一、心臟科相關診斷：
{diag_clean[:500]}

二、病史：
{subj_clean[:500]}

三、客觀檢查：
{obj_clean[:500]}

四、本次住院計畫：
{plan_clean[:500]}""".strip()


def parse_name_from_raw(raw):
    # raw like "姓名 : 謝秀嬌 , 生日 : 1955/02/20 , 性別 : 女 ..."
    m = re.search(r'姓名\s*[：:]\s*([^\s,，]+)', raw)
    if m:
        return m.group(1).strip()
    return ''


def parse_birth_from_raw(raw):
    m = re.search(r'生日\s*[：:]\s*(\d{4})/(\d{1,2})/(\d{1,2})', raw)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None


def parse_gender_from_raw(raw):
    m = re.search(r'性別\s*[：:]\s*([男女])', raw)
    return m.group(1) if m else ''


def compute_age(birth, admission_date):
    # admission_date like '2026-04-24'
    try:
        ay, am, ad = (int(x) for x in admission_date.split('-'))
    except Exception:
        return None
    by, bm, bd = birth
    age = ay - by
    if (am, ad) < (bm, bd):
        age -= 1
    return age


def main(date8):
    with open(f'emr_data_{date8}.json', encoding='utf-8') as f:
        emr = json.load(f)

    ws = gu.get_worksheet(date8)
    if ws is None:
        print(f'ERROR: sheet {date8} not found')
        return

    # Read main data A-L to build chart -> {age, gender} map and row idx
    all_vals = ws.get_all_values()
    main_info = {}  # chart -> {age, gender, row, name}
    for ri, row in enumerate(all_vals[1:], 2):  # skip header
        if not row or not row[0] or row[0] == '':
            continue
        if not row[0].startswith('2026'):
            break  # reached sub-table region
        if len(row) < 9:
            continue
        chart = row[8].strip() if len(row) > 8 else ''
        if not chart:
            continue
        # Strip leading '
        chart = chart.lstrip("'")
        main_info[chart] = {
            'age': row[7].strip() if len(row) > 7 else '',
            'gender': row[6].strip() if len(row) > 6 else '',
            'name': row[5].strip() if len(row) > 5 else '',
            'admission_date': row[0].strip() if len(row) > 0 else '',
            'row': ri,
        }

    # Find sub-tables: rows like "X人）" merged headers
    # Record {row_of_title: doctor_name} so we know which doctor a patient row belongs to
    import re as _re
    subtable_rows = []  # list of (doctor_name, title_row)
    for ri, row in enumerate(all_vals, 1):
        if row and row[0] and '人）' in row[0]:
            m = _re.match(r'^([^（(]+)', row[0].strip())
            doc_name = m.group(1).strip() if m else ''
            subtable_rows.append((doc_name, ri))

    # For each sub-table, patient rows are start+2, start+3, ...
    updates = []  # (range, value) list
    name_corrections = {}  # chart -> corrected_name
    prefill = []  # list of dicts for preview
    mismatches = []  # safety log

    for doc_name, sr in subtable_rows:
        # Sub-header is sr+1, patients start at sr+2
        pr = sr + 2
        while pr <= len(all_vals):
            row = all_vals[pr - 1]
            if not row or not row[0]:
                break
            name = row[0].strip()
            chart_raw = row[1].strip() if len(row) > 1 else ''
            chart = chart_raw.lstrip("'")
            if not chart or not chart.isdigit():
                break

            # SAFETY: verify sub-table A name == main data F name (by chart)
            mi = main_info.get(chart)
            if mi is None:
                mismatches.append(f'row{pr} [{doc_name}] chart {chart} ({name}) — 不在主資料，skip')
                pr += 1
                continue
            if name != mi['name']:
                # Trust main data; log and fix A cell but proceed with write
                mismatches.append(f'row{pr} [{doc_name}] chart {chart}: sub A="{name}" vs main F="{mi["name"]}" — 以主資料為準')
                updates.append((f'A{pr}', mi['name']))
                name = mi['name']

            info = emr.get(chart)

            # Apply name/age/gender corrections from EMR #divUserSpec whenever available,
            # regardless of whether EMR visit text was found.
            if info and info.get('name'):
                raw_name = info.get('name', '')
                emr_name = parse_name_from_raw(raw_name)
                if emr_name and emr_name != name:
                    name_corrections[chart] = (name, emr_name)
                    updates.append((f'A{pr}', emr_name))
                    name = emr_name
                birth = parse_birth_from_raw(raw_name)
                if birth:
                    new_age = compute_age(birth, mi.get('admission_date', ''))
                    if new_age is not None:
                        cur_age = str(mi.get('age', '')).strip()
                        if cur_age != str(new_age):
                            updates.append((f'H{mi["row"]}', new_age))
                emr_gender = parse_gender_from_raw(raw_name)
                if emr_gender and emr_gender != mi.get('gender', '').strip():
                    updates.append((f'G{mi["row"]}', emr_gender))

            if info and info.get('status') == 'ok':
                emr_text = info.get('emr', '')
                visit = info.get('visit', '')
                matched = info.get('matched_doctor', True)

                # Prepend visit source header so user sees origin at a glance
                src_tag = '' if matched else '(非本醫師門診)'
                visit_header = f'【EMR來源門診：{visit}】{src_tag}\n' if visit else ''
                emr_full = visit_header + emr_text

                summary = generate_summary(emr_text, mi.get('age', ''), mi.get('gender', ''))
                f_diag, g_cath = detect_fg(emr_text)

                updates.append((f'C{pr}', emr_full))
                updates.append((f'D{pr}', summary))
                if f_diag:
                    updates.append((f'F{pr}', f_diag))
                if g_cath:
                    updates.append((f'G{pr}', g_cath))

                prefill.append({
                    'chart': chart, 'name': name, 'doctor': doc_name,
                    'f': f_diag, 'g': g_cath, 'row': pr,
                    'matched': matched, 'visit': visit,
                })
            elif info and info.get('status') in ('no_visit', 'empty'):
                updates.append((f'C{pr}', '無本院一年內主治醫師門診紀錄'))
                updates.append((f'D{pr}', '(無門診紀錄)'))
                prefill.append({
                    'chart': chart, 'name': name, 'doctor': doc_name,
                    'f': '', 'g': '', 'row': pr, 'matched': False, 'visit': '(無)',
                })
            pr += 1

    # Also write EMR-corrected names back to main data F column
    for chart, (old, new) in name_corrections.items():
        mi = main_info.get(chart)
        if mi:
            updates.append((f'F{mi["row"]}', new))

    # Apply all updates as batch
    body = [{'range': r, 'values': [[v]]} for r, v in updates]
    if body:
        ws.batch_update(body, value_input_option='USER_ENTERED')
    print(f'Applied {len(updates)} cell updates')

    # Post-write verification: re-read and check chart→row alignment
    time.sleep(1)
    verify_vals = ws.get('A1:D80')
    align_errors = []
    for p in prefill:
        r = verify_vals[p['row'] - 1] if p['row'] - 1 < len(verify_vals) else []
        va = (r[0] if len(r) > 0 else '').strip()
        vb = (r[1] if len(r) > 1 else '').strip().lstrip("'")
        if vb != p['chart']:
            align_errors.append(f'  row{p["row"]}: expected chart {p["chart"]} got {vb}')
        elif va != p['name']:
            align_errors.append(f'  row{p["row"]}: chart {p["chart"]} name {va} != {p["name"]}')

    # Report
    out_lines = [f'=== {date8} EMR 處理結果 ===']
    if mismatches:
        out_lines.append('\n【A 姓名 vs 主資料不符】')
        for m in mismatches:
            out_lines.append(f'  {m}')
    if name_corrections:
        out_lines.append('\n【EMR 姓名校正】')
        for chart, (old, new) in name_corrections.items():
            out_lines.append(f'  {chart}: {old} → {new}')
    out_lines.append('\n【F/G 預填 / EMR 來源】')
    for p in prefill:
        tag = '' if p['matched'] else ' ⚠非本醫師門診'
        out_lines.append(f'  [{p["chart"]}] {p["doctor"]}/{p["name"]}: F={p["f"] or "(空)"} G={p["g"] or "(空)"} | {p["visit"]}{tag}')
    out_lines.append('\n【寫入後對齊驗證】')
    if align_errors:
        out_lines.append('  ⚠ 發現錯位：')
        out_lines.extend(align_errors)
    else:
        out_lines.append(f'  OK — {len(prefill)} 筆全部對齊')
    with open(f'_emr_result_{date8}.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))
    print(f'[{date8}] done, {len(updates)} updates, {len(align_errors)} align errors, {len(mismatches)} A-name mismatches')


if __name__ == '__main__':
    main(sys.argv[1])
