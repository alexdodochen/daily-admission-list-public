"""Process batch EMR data and write C/D/F/G to affected sheets (4/20-4/23)."""
import json, re, time
from gsheet_utils import get_worksheet, get_spreadsheet, add_note

LOG = open('_process_emr_batch.log', 'w', encoding='utf-8')
def log(msg):
    LOG.write(msg + '\n'); LOG.flush()

DIAG_RULES = [
    (['STEMI', 'ST elevation myocardial'], 'STEMI'),
    (['NSTEMI', 'non-ST elevation', 'non ST elevation'], 'Others:NSTEMI'),
    (['unstable angina'], 'Unstable'),
    (['severe AS', 'aortic stenosis'], 'AS'),
    (['severe AR', 'aortic regurgitation'], 'AR'),
    (['severe MR', 'mitral regurgitation', 'MVRepair', 'MVR'], 'MR'),
    (['severe TR', 'tricuspid regurgitation'], 'Others:Severe TR'),
    (['generator replacement', 'PPM generator', 'ICD generator'], 'Generator replacement'),
    (['paroxysmal Af', 'paroxysmal atrial fibrillation',
      'Long persistent atrial fibrillation', 'persistent Af',
      'persistent atrial fibrillation', 'pAf'], 'pAf'),
    (['supraventricular tachycardia', 'PSVT'], 'PSVT'),
    (['WPW'], 'WPW syndrome'),
    (['atrial flutter', 'Aflutter'], 'Atrial flutter'),
    (['ventricular premature', 'VPC'], 'VPC'),
    (['sick sinus', 'sinus nodal dysfunction', 'sinus pause', 'tachy-brady', 'SSS'], 'Sinus nodal dysfunction'),
    (['complete AV block', 'AV nodal dysfunction', 'CAVB', 'AV block'], 'AV nodal dysfunction'),
    (['PAOD', 'peripheral arterial occlusive', 'peripheral arterial disease'], 'PAOD'),
    (['carotid stenting', 'carotid stenosis'], 'Carotid stenting'),
    (['HFrEF', 'HFpEF', 'heart failure', 'CHF', 'congestive heart failure'], 'CHF'),
    (['dilated cardiomyopathy', 'DCM'], 'DCM'),
    (['hypertrophic cardiomyopathy', 'HCM'], 'HCM'),
    (['pulmonary hypertension', 'pulmonary HTN'], 'Pulmonary HTN'),
    (['syncope'], 'Syncope'),
    (['angina pectoris', 'angina'], 'Angina pectoris'),
    (['CAD', 'coronary artery disease',
      'chest pain', 'chest tightness', 'chest tigthness',
      'ACS', 'acute coronary syndrome',
      'I259', 'I250', 'I251',
      'TET (+)', 'TMT (+)', 'THL (+)', 'TET+', 'TMT+', 'THL+'], 'CAD'),
]
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
    (['cath study', 'catheterization', 'Cath study', 'Cath on', 'cath on', 'CAG', 'LHC'], 'Left heart cath.'),
]
F_TO_G_DEFAULT = {
    'CAD': 'Left heart cath.', 'Angina pectoris': 'Left heart cath.',
    'Unstable': 'Left heart cath.', 'CHF': 'Left heart cath.',
    'STEMI': 'PCI', 'Others:NSTEMI': 'PCI',
    's/p PCI': 'Left heart cath.', 'PAOD': 'PTA',
    'pAf': 'RF ablation', 'PSVT': 'RF ablation',
    'WPW syndrome': 'RF ablation', 'Atrial flutter': 'RF ablation', 'VPC': 'RF ablation',
    'Sinus nodal dysfunction': 'PPM', 'AV nodal dysfunction': 'PPM',
    'Generator replacement': 'PPM',
    'AS': 'Both-sided cath.', 'AR': 'Both-sided cath.', 'MR': 'Both-sided cath.',
    'Others:Severe TR': 'Both-sided cath.',
    'DCM': 'Right heart cath.', 'HCM': 'Left heart cath.',
    'Pulmonary HTN': 'Right heart cath.',
    'Carotid stenting': 'Carotid angiography + stenting',
    'Syncope': 'EP study',
}

def extract_dx_section(emr_text):
    parts = re.split(r'\[(Diagnosis|Subjective|Objective|Assessment & Plan)\]', emr_text)
    diag_text = ''
    for i, part in enumerate(parts):
        if part == 'Diagnosis' and i + 1 < len(parts):
            diag_text = parts[i + 1]; break
    if not diag_text: return ''
    out = []
    for line in diag_text.split('\n'):
        s = line.strip()
        if not s or s.startswith('Description'): continue
        s = re.sub(r'^\*?\s*\(Dx\)\s*', '', s)
        out.append(s)
    return '\n'.join(out)

ICD10_FALLBACK = [
    ((r'I25[019]',), 'CAD'), ((r'I21[0-9]',), 'STEMI'),
    ((r'I50[0-9]',), 'CHF'), ((r'I48[0-9]',), 'pAf'),
    ((r'I47[0-9]',), 'PSVT'), ((r'I49[5]',), 'Sinus nodal dysfunction'),
    ((r'I44[12]',), 'AV nodal dysfunction'),
    ((r'I35[0]',), 'AS'), ((r'I35[1]',), 'AR'), ((r'I34[0]',), 'MR'),
    ((r'I70[2]',), 'PAOD'),
]

def detect_via_icd(dx_text):
    icd_codes = re.findall(r'ICD[\-\u2010-\u2015]?10[^A-Z]{0,3}([A-Z]\d{2,4})', dx_text)
    if not icd_codes: return ''
    joined = ' '.join(icd_codes)
    for patterns, value in ICD10_FALLBACK:
        for p in patterns:
            if re.search(p, joined): return value
    return ''

def clean_past_tense_pci(text):
    patterns = [r's/p\s+PCI[^\n]*', r'post[\-\s]+PCI[^\n]*',
                r'status\s+post[^\n]*PCI[^\n]*',
                r'PCI\s+on\s+\d{4}[/\-]?\d{0,2}[/\-]?\d{0,2}',
                r'PCI\s+done[^\n]*', r'previous\s+PCI[^\n]*',
                r'history\s+of\s+PCI[^\n]*', r'old\s+PCI[^\n]*']
    for p in patterns:
        text = re.sub(p, ' ', text, flags=re.IGNORECASE)
    return text

def match_rules(text, rules):
    tl = text.lower()
    for kws, val in rules:
        for kw in kws:
            kwl = kw.lower()
            if len(kw) <= 4:
                if re.search(r'(?<![a-zA-Z])' + re.escape(kwl) + r'(?![a-zA-Z])', tl):
                    return val
            else:
                if kwl in tl:
                    return val
    return ''

def detect_diag(dx_text):
    if not dx_text: return ''
    text_no_icd = '\n'.join([l for l in dx_text.split('\n') if not l.strip().startswith('* (ICD')])
    items = re.findall(r'(?:^|\n)\s*\d+\s*[\.\)]\s*([^\n]+)', text_no_icd)
    if items:
        for item in items:
            m = match_rules(item, DIAG_RULES)
            if m: return m
    m = match_rules(text_no_icd, DIAG_RULES)
    if m: return m
    return detect_via_icd(dx_text)

def detect_fg(emr_text):
    dx = extract_dx_section(emr_text)
    f_diag = detect_diag(dx) if dx else match_rules(emr_text, DIAG_RULES)
    if '[Assessment & Plan]' in emr_text:
        plan_sec = emr_text.split('[Assessment & Plan]')[1][:1500]
    else:
        plan_sec = emr_text
    pl = plan_sec.lower()
    if 'generator replacement' in pl or 'ppm replacement' in pl \
            or 'icd replacement' in pl or 'crt replacement' in pl \
            or 'change generator' in pl:
        f_diag = 'Generator replacement'
    g_cath = match_rules(clean_past_tense_pci(plan_sec), CATH_RULES)
    if not g_cath and f_diag:
        g_cath = F_TO_G_DEFAULT.get(f_diag, '')
    return f_diag, g_cath

def short_label(visit_label):
    if not visit_label:
        return ''
    m = re.match(r'\(\u9580\u8a3a\)(\d{4}/\d{2}/\d{2})\s*(.+?)\s+(.+)', visit_label.replace('\xa0', ' '))
    if m:
        date, doctor, dept = m.group(1), m.group(2).strip(), m.group(3).strip()
        return f'\u9580\u8a3a, {doctor}, {dept}, {date}'
    return visit_label.replace('\xa0', ' ')

def generate_summary(emr_text, age='', gender=''):
    sec = {'diag': '', 'subj': '', 'obj': '', 'plan': ''}
    parts = re.split(r'\[(Diagnosis|Subjective|Objective|Assessment & Plan)\]', emr_text)
    for i, part in enumerate(parts):
        if part == 'Diagnosis' and i+1 < len(parts): sec['diag'] = parts[i+1].strip()
        elif part == 'Subjective' and i+1 < len(parts): sec['subj'] = parts[i+1].strip()
        elif part == 'Objective' and i+1 < len(parts): sec['obj'] = parts[i+1].strip()
        elif part == 'Assessment & Plan' and i+1 < len(parts): sec['plan'] = parts[i+1].strip()
    diag = '\n'.join([l for l in sec['diag'].split('\n') if l.strip() and not l.strip().startswith('* (ICD')])
    subj_lines = [l.strip() for l in sec['subj'].split('\n')
                  if l.strip() and not l.strip().startswith(('No ', 'Family history', 'Current medication'))]
    subj = '\n'.join(subj_lines[:15])
    obj = '\n'.join([l.strip() for l in sec['obj'].split('\n')
                     if l.strip() and '[Plan' not in l and '[Medicine' not in l][:20])
    plan_lines = []
    for l in sec['plan'].split('\n'):
        l = l.strip()
        cut = len(l)
        for tag in ('[Medicine]', '[Medication]', '------'):
            idx = l.find(tag)
            if idx != -1 and idx < cut:
                cut = idx
        if cut < len(l):
            prefix = l[:cut].strip()
            if prefix: plan_lines.append(prefix)
            break
        if l: plan_lines.append(l)
    plan = '\n'.join(plan_lines[:10])
    header = f'{age} y/o {gender}' if age else ''
    return f"""{header}
\u4e00\u3001\u5fc3\u81df\u79d1\u76f8\u95dc\u8a3a\u65b7\uff1a
{diag[:500]}

\u4e8c\u3001\u75c5\u53f2\uff1a
{subj[:500]}

\u4e09\u3001\u5ba2\u89c0\u6aa2\u67e5\uff1a
{obj[:500]}

\u56db\u3001\u672c\u6b21\u4f4f\u9662\u8a08\u756b\uff1a
{plan[:500]}""".strip()

def one_line_diag(summary):
    lines = summary.split('\n')
    for i, l in enumerate(lines):
        if '\u4e00\u3001\u5fc3\u81df\u79d1\u76f8\u95dc\u8a3a\u65b7' in l:
            for j in range(i+1, len(lines)):
                if lines[j].strip():
                    return lines[j].strip()
    return ''

# Load EMR data
with open('emr_data_batch.json', 'r', encoding='utf-8') as f:
    emr_data = json.load(f)

# Group by sheet
by_sheet = {}
for chart, info in emr_data.items():
    s = info['sheet']
    if s not in by_sheet:
        by_sheet[s] = {}
    by_sheet[s][chart] = info

log(f'Sheets to update: {list(by_sheet.keys())}')

for sheet_name, patients in sorted(by_sheet.items()):
    log(f'\n=== {sheet_name} ({len(patients)} patients) ===')
    ws = get_worksheet(sheet_name)
    sheet_id = ws.id
    all_vals = ws.get_all_values()

    main_end = 1
    for i in range(1, len(all_vals)):
        if all_vals[i] and re.match(r'^\d{4}-\d{2}-\d{2}$', (all_vals[i][0] or '').strip()):
            main_end = i + 1
        else:
            break

    chart_to_row = {}
    for i in range(main_end, len(all_vals)):
        row = all_vals[i]
        if len(row) >= 2:
            chart = (row[1] or '').strip().lstrip("'")
            name = (row[0] or '').strip()
            if chart and len(chart) == 8 and chart.isdigit() and name not in ('\u59d3\u540d', ''):
                chart_to_row[chart] = i + 1
    log(f'  chart_to_row: {chart_to_row}')

    updates_values = []
    updates_notes = []

    for chart, info in patients.items():
        if chart not in chart_to_row:
            log(f'  SKIP {chart} {info["name"]} - not in sub-table')
            continue
        row = chart_to_row[chart]
        status = info['status']
        emr_text = info.get('emr', '')
        age = info.get('age', '')
        gender = info.get('gender', '')
        current_row = all_vals[row - 1] if row - 1 < len(all_vals) else []
        current_c = (current_row[2] if len(current_row) > 2 else '').strip()

        if status in ('ok', 'ok_fallback') and emr_text:
            visit = info.get('visit', '')
            label = short_label(visit)
            summary = generate_summary(emr_text, age, gender)
            diag_line = one_line_diag(summary) or (f'{age} y/o {gender}' if age else '')
            plan_sec = emr_text.split('[Assessment & Plan]')[1][:1500] if '[Assessment & Plan]' in emr_text else ''
            f_diag = match_rules(emr_text, DIAG_RULES)
            g_cath = match_rules(plan_sec if plan_sec else emr_text, CATH_RULES)

            updates_values.append((row, 3, label))
            updates_notes.append((row, 3, emr_text))
            updates_values.append((row, 4, diag_line))
            updates_notes.append((row, 4, summary))

            current_f = (current_row[5] if len(current_row) > 5 else '').strip()
            current_g = (current_row[6] if len(current_row) > 6 else '').strip()
            if f_diag and not current_f:
                updates_values.append((row, 6, f_diag))
            if g_cath and not current_g:
                updates_values.append((row, 7, g_cath))

            log(f'  {chart} {info["name"]} row={row}: OK label="{label}" F={f_diag or current_f} G={g_cath or current_g}')
        else:
            if not current_c:
                updates_values.append((row, 3, '\u7121\u672c\u9662\u4e00\u5e74\u5167\u4e3b\u6cbb\u91ab\u5e2b\u9580\u8a3a\u7d00\u9304'))
                updates_notes.append((row, 3, ''))
                updates_values.append((row, 4, f'{age} y/o {gender}' if age else ''))
                updates_notes.append((row, 4, ''))
                log(f'  {chart} {info["name"]} row={row}: {status} -> writing no-record')
            else:
                log(f'  {chart} {info["name"]} row={row}: {status} but C has data, preserving')

    if not updates_values:
        log(f'  No updates for {sheet_name}')
        continue

    cells = []
    for r, c, v in updates_values:
        cell = ws.cell(r, c)
        cell.value = v
        cells.append(cell)
    ws.update_cells(cells, value_input_option='USER_ENTERED')
    log(f'  Wrote {len(cells)} cell values')
    time.sleep(1)

    for r, c, note in updates_notes:
        add_note(ws, r, c, note)
        time.sleep(0.15)
    log(f'  Wrote {len(updates_notes)} notes')
    time.sleep(1)

log('\n=== DONE ===')
LOG.close()
