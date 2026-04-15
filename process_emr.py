"""Process EMR JSON, generate summaries + auto-detect F/G, write to Sheet.

Usage: python process_emr.py <date8>   e.g. 20260419

Reads emr_data_<date>.json, reads sub-tables from Sheet <date>, writes:
- C col: full EMR text
- D col: 4-section summary
- F col: auto-detected 術前診斷
- G col: auto-detected 預計心導管
- A col (name): auto-corrected from EMR name

Also updates main data G col and N-W P col if patient exists there.
"""
import sys, json, re, time
sys.path.insert(0, '.')
import gsheet_utils as gu

DIAG_RULES = [
    (['STEMI', 'ST elevation myocardial'], 'STEMI'),
    (['NSTEMI', 'non-ST elevation'], 'Others:NSTEMI'),
    (['pAf', 'paroxysmal Af', 'paroxysmal atrial fibrillation', 'Long persistent atrial fibrillation', 'persistent Af'], 'pAf'),
    (['PSVT', 'supraventricular tachycardia'], 'PSVT'),
    (['WPW'], 'WPW syndrome'),
    (['atrial flutter'], 'Atrial flutter'),
    (['VPC', 'ventricular premature'], 'VPC'),
    (['sinus nodal dysfunction', 'sick sinus', 'SSS', 'sinus pause', 'tachy-brady'], 'Sinus nodal dysfunction'),
    (['AV nodal dysfunction', 'AV block'], 'AV nodal dysfunction'),
    (['syncope'], 'Syncope'),
    (['generator replacement'], 'Generator replacement'),
    (['aortic stenosis', 'severe AS'], 'AS'),
    (['mitral regurgitation', 'severe MR', 'MVRepair', 'MVR'], 'MR'),
    (['severe TR'], 'Others:Severe TR'),
    (['PAOD', 'peripheral arterial occlusive'], 'PAOD'),
    (['carotid stenting', 'carotid stenosis'], 'Carotid stenting'),
    (['CHF', 'heart failure', 'HFrEF', 'HFpEF'], 'CHF'),
    (['DCM', 'dilated cardiomyopathy'], 'DCM'),
    (['HCM', 'hypertrophic cardiomyopathy'], 'HCM'),
    (['pulmonary HTN', 'pulmonary hypertension'], 'Pulmonary HTN'),
    (['s/p PCI', 'ISR', 'in-stent restenosis', 'post PCI'], 's/p PCI'),
    (['unstable angina'], 'Unstable'),
    (['angina'], 'Angina pectoris'),
    (['CAD', 'coronary artery disease'], 'CAD'),
]

CATH_RULES = [
    (['PCI on', 'PCI ', 'intervention'], 'PCI'),
    (['ablation', 'RF ablation', 'RFA'], 'RF ablation'),
    (['PPM', 'pacemaker implant'], 'PPM'),
    (['TAVI', 'transcatheter aortic valve'], 'TAVI'),
    (['EP study'], 'EP study'),
    (['PTA'], 'PTA'),
    (['carotid angiography', 'carotid stenting'], 'Carotid angiography + stenting'),
    (['both-sided cath'], 'Both-sided cath.'),
    (['right heart cath'], 'Right heart cath.'),
    (['myocardial biopsy'], 'Myocardial biopsy'),
    (['cath study', 'catheterization', 'Cath on', 'cath on', 'CAG'], 'Left heart cath.'),
]

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
        if '[Medicine]' in l or '[Medication]' in l or '------' in l:
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
                plan_section = ''
                if '[Assessment & Plan]' in emr_text:
                    plan_section = emr_text.split('[Assessment & Plan]')[1][:1500]
                f_diag = match_rules(emr_text, DIAG_RULES)
                g_cath = match_rules(plan_section if plan_section else emr_text, CATH_RULES)

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
