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
            'row': ri,
        }

    # Find sub-tables: rows like "X人）" merged headers
    subtable_rows = []  # list of (doctor, start_row_of_sub_header, patient_rows_list)
    for ri, row in enumerate(all_vals, 1):
        if row and row[0] and '人）' in row[0]:
            subtable_rows.append(ri)

    # For each sub-table, patient rows are start+2, start+3, ...
    updates = []  # (range, value) list
    name_corrections = {}  # chart -> corrected_name
    prefill = []  # list of dicts for preview

    for sr in subtable_rows:
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
            info = emr.get(chart)
            if info and info.get('status') == 'ok':
                emr_text = info.get('emr', '')
                raw_name = info.get('name', '')
                corrected = parse_name_from_raw(raw_name)
                if corrected and corrected != name:
                    name_corrections[chart] = (name, corrected)
                    # Update sub-table A col
                    updates.append((f'A{pr}', corrected))

                # Generate summary
                mi = main_info.get(chart, {})
                summary = generate_summary(emr_text, mi.get('age', ''), mi.get('gender', ''))

                # Auto-detect F/G
                plan_section = ''
                if '[Assessment & Plan]' in emr_text:
                    plan_section = emr_text.split('[Assessment & Plan]')[1][:1500]
                f_diag = match_rules(emr_text, DIAG_RULES)
                g_cath = match_rules(plan_section if plan_section else emr_text, CATH_RULES)

                # Write C (EMR), D (summary), F (diag), G (cath) on sub-table row
                updates.append((f'C{pr}', emr_text))
                updates.append((f'D{pr}', summary))
                if f_diag:
                    updates.append((f'F{pr}', f_diag))
                if g_cath:
                    updates.append((f'G{pr}', g_cath))

                prefill.append({
                    'chart': chart, 'name': corrected or name,
                    'f': f_diag, 'g': g_cath, 'row': pr,
                })
            pr += 1

    # Apply name corrections in main data too
    for chart, (old, new) in name_corrections.items():
        mi = main_info.get(chart)
        if mi:
            updates.append((f'F{mi["row"]}', new))

    # Apply all updates as batch
    body = [{'range': r, 'values': [[v]]} for r, v in updates]
    if body:
        ws.batch_update(body, value_input_option='USER_ENTERED')
    print(f'Applied {len(updates)} cell updates')

    # Report
    out_lines = [f'=== {date8} EMR 處理結果 ===']
    if name_corrections:
        out_lines.append('\n【姓名校正】')
        for chart, (old, new) in name_corrections.items():
            out_lines.append(f'  {chart}: {old} → {new}')
    out_lines.append('\n【F/G 預填】')
    for p in prefill:
        out_lines.append(f'  [{p["chart"]}] {p["name"]}: F={p["f"] or "(空)"} G={p["g"] or "(空)"}')
    with open(f'_emr_result_{date8}.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))
    print('\n'.join(out_lines))


if __name__ == '__main__':
    main(sys.argv[1])
