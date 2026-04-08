"""Process EMR data for 20260414: generate summaries, auto-detect F/G, write to Sheet"""
import json, os, sys, time, re
os.chdir(r'D:\心臟內科 總醫師\行政總醫師\每日入院名單\.claude\worktrees\determined-curie')
sys.path.insert(0, '.')

with open('emr_data_0414.json', 'r', encoding='utf-8') as f:
    emr_data = json.load(f)

# ===== Auto-diagnosis matching rules =====
DIAG_RULES = [
    (['STEMI', 'ST elevation myocardial'], 'STEMI'),
    (['NSTEMI', 'non-ST elevation'], 'Others:NSTEMI'),
    (['pAf', 'paroxysmal Af', 'paroxysmal atrial fibrillation'], 'pAf'),
    (['PSVT', 'supraventricular tachycardia'], 'PSVT'),
    (['WPW'], 'WPW syndrome'),
    (['atrial flutter'], 'Atrial flutter'),
    (['VPC', 'ventricular premature'], 'VPC'),
    (['sinus nodal dysfunction', 'sick sinus', 'SSS', 'sinus pause', 'tachy-brady'], 'Sinus nodal dysfunction'),
    (['AV nodal dysfunction', 'AV block'], 'AV nodal dysfunction'),
    (['syncope'], 'Syncope'),
    (['generator replacement'], 'Generator replacement'),
    (['aortic stenosis', 'severe AS'], 'AS'),
    (['mitral regurgitation', 'severe MR'], 'MR'),
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
    (['RF ablation', 'RFA', 'ablation'], 'RF ablation'),
    (['PPM', 'pacemaker implant'], 'PPM'),
    (['TAVI', 'transcatheter aortic valve'], 'TAVI'),
    (['EP study'], 'EP study'),
    (['PTA'], 'PTA'),
    (['carotid angiography', 'carotid stenting'], 'Carotid angiography + stenting'),
    (['both-sided cath'], 'Both-sided cath.'),
    (['right heart cath'], 'Right heart cath.'),
    (['myocardial biopsy'], 'Myocardial biopsy'),
    (['cath study', 'catheterization', 'Cath study', 'Cath on', 'cath on'], 'Left heart cath.'),
]

def match_rules(text, rules):
    for keywords, value in rules:
        for kw in keywords:
            if kw.lower() in text.lower():
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

    diag_lines = [l for l in sections['diag'].split('\n')
                  if l.strip() and not l.strip().startswith('* (ICD')]
    diag_clean = '\n'.join(diag_lines)

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


PATIENTS = [
    {'chart': '04282190', 'age': '75', 'gender': '女性'},
    {'chart': '01052465', 'age': '63', 'gender': '女性'},
    {'chart': '13815785', 'age': '85', 'gender': '女性'},
    {'chart': '01884136', 'age': '85', 'gender': '女性'},
    {'chart': '23297685', 'age': '69', 'gender': '男性'},
    {'chart': '04697942', 'age': '51', 'gender': '男性'},
    {'chart': '01526382', 'age': '69', 'gender': '女性'},
    {'chart': '00163449', 'age': '94', 'gender': '女性'},
    {'chart': '11784057', 'age': '67', 'gender': '男性'},
    {'chart': '21285839', 'age': '30', 'gender': '女性'},
]

results = []
out = open('_emr_final.txt', 'w', encoding='utf-8')

for pt in PATIENTS:
    chart = pt['chart']
    info = emr_data.get(chart, {})
    status = info.get('status', 'missing')
    emr_name = info.get('name', chart)

    if status == 'ok':
        emr_text = info.get('emr', '')
        summary = generate_summary(emr_text, pt['age'], pt['gender'])
        plan_section = ''
        if '[Assessment & Plan]' in emr_text:
            plan_section = emr_text.split('[Assessment & Plan]')[1][:1500]
        f_diag = match_rules(emr_text, DIAG_RULES)
        g_cath = match_rules(plan_section if plan_section else emr_text, CATH_RULES)

        results.append({
            'chart': chart, 'emr_name': emr_name, 'emr': emr_text,
            'summary': summary, 'f_diag': f_diag, 'g_cath': g_cath, 'no_data': False
        })
        out.write(f'OK: {emr_name} ({chart}): F={f_diag}, G={g_cath}\n')
    else:
        results.append({
            'chart': chart, 'emr_name': emr_name,
            'emr': '', 'summary': '', 'f_diag': '', 'g_cath': '', 'no_data': True
        })
        out.write(f'NO DATA: {emr_name} ({chart})\n')

out.close()

with open('_write_data_0414.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Print summary
with open('_emr_final.txt', 'r', encoding='utf-8') as f:
    print(f.read())
