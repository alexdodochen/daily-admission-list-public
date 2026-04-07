"""Update 20260409 sub-tables with new EMR data"""
import sys, time
sys.path.insert(0, '.')
from gsheet_utils import (get_worksheet, read_all_values, clear_range, write_doctor_table)

ws = get_worksheet('20260409')
data = read_all_values(ws)

# Collect existing EMR data from sub-tables
emr_db = {}
for row in data:
    if len(row) > 1 and row[1] and len(row[1]) >= 7 and row[1].isdigit():
        emr_db[row[1]] = {
            'name': row[0], 'chart': row[1],
            'emr': row[2] if len(row) > 2 else '',
            'emr_summary': row[3] if len(row) > 3 else '',
            'order': row[4] if len(row) > 4 else '',
            'diagnosis': row[5] if len(row) > 5 else '',
            'cathlab': row[6] if len(row) > 6 else '',
            'note': row[7] if len(row) > 7 else '',
        }

# New EMR: 陳雪紅
emr_db['06779181'] = {
    'name': '陳雪紅', 'chart': '06779181',
    'emr': (
        "門診 , 詹世鴻 , 一般內科07 診 (0011) , 2026/04/07\n"
        "[Diagnosis]\n"
        "* (Dx)1. Non-ST elevation myocardial infarction, Killip III / coronary artery disease, "
        "2-vessel-disease, left anterior descending coronary artery + right coronary artery, "
        "status post ROTA and DES* 2 for left anterior descending coronary artery (LAD)\n"
        "2. Acute pulmonary edema\n3. Diabetes mellitus\n4. Hypertension\n5. Dyslipidemia\n\n"
        "* (ICD-10 : I214) : Non-ST elevation (NSTEMI) myocardial infarction\n"
        "* (ICD-10 : I259) : Chronic ischemic heart disease, unspecified\n\n"
        "[Subjective]\n"
        "(2026/04/07) She had frequently chest pain on effort and at rest, relieved by NTG."
        "The last episode developed last night.\n\n"
        "[Objective]\nBP: 107/56 mmHg\nPR: 72 bpm\nConjuntiva: not anemia\nSclera: not icteric\n"
        "Chest: clear BS, no crackles, no wheezing\nHeart: RHB, no murmur\nExtremity: no pitting edema\n\n"
        "[Assessment & Plan]\nUnstable angina was impressed.\n==>Admission as soon as possible.\n"
        "Admission on 4/9.\nCath study on 4/10."
    ),
    'emr_summary': (
        "65 y/o 女性\n"
        "一、心臟科相關診斷：\n"
        "1. NSTEMI, Killip III / CAD, 2VD (LAD+RCA), s/p ROTA and DES*2 for LAD\n"
        "2. Acute pulmonary edema\n3. DM\n4. HTN\n5. Dyslipidemia\n\n"
        "二、病史：\n"
        "(2026/04/07) Frequently chest pain on effort and at rest, relieved by NTG. Last episode last night.\n\n"
        "三、客觀檢查：\nBP: 107/56 mmHg\nPR: 72 bpm\nChest: clear BS\nHeart: RHB, no murmur\n"
        "Extremity: no pitting edema\n\n"
        "四、本次住院計畫：\nUnstable angina. Admission ASAP.\nCath study on 4/10."
    ),
    'order': '', 'diagnosis': '', 'cathlab': '', 'note': '',
}

# New EMR: 郭榮財
emr_db['20926474'] = {
    'name': '郭榮財', 'chart': '20926474',
    'emr': (
        "門診 , 詹世鴻 , 心臟血管科01 診 (0002) , 2026/04/02\n"
        "[Diagnosis]\n* (Dx)Old MI\nCAD(3VD)\n\n"
        "* (ICD-10 : I252) : Old myocardial infarction\n"
        "* (ICD-10 : I259) : Chronic ischemic heart disease, unspecified\n\n"
        "[Subjective]\nCC: In around 8 years ago, he had AMI.\n"
        "==> CAG: PCI for RCA with BMS.\n"
        "==> He had exertional dyspnea for 2 months. Palpitatin was noticed.\n"
        "==> Coronary CTA: ISR in RCA, > 70% at pLAD\n"
        "No HTN\nNo DM\nExertional dyspnea (2026/04/02)\n\n"
        "[Objective]\nBP: 130/94 mmHg\nPR: 60 bpm\nConjuntiva: not anemia\nSclera: not icteric\n"
        "Chest: clear BS, no crackles, no wheezing\nHeart: RHB, no murmur\nExtremity: no pitting edema\n\n"
        "[Assessment & Plan]\nAdmission on 4/9.\nCath study on 4/10."
    ),
    'emr_summary': (
        "55 y/o 男性\n"
        "一、心臟科相關診斷：\nOld MI\nCAD(3VD)\n\n"
        "二、病史：\n8 years ago AMI, PCI for RCA with BMS.\n"
        "Exertional dyspnea 2 months. Coronary CTA: ISR in RCA, >70% at pLAD\n\n"
        "三、客觀檢查：\nBP: 130/94 mmHg\nPR: 60 bpm\nChest: clear BS\nHeart: RHB, no murmur\n"
        "Extremity: no pitting edema\n\n"
        "四、本次住院計畫：\nAdmission 4/9, Cath study 4/10."
    ),
    'order': '', 'diagnosis': '', 'cathlab': '', 'note': '',
}

# New EMR: 莊再發
emr_db['02177819'] = {
    'name': '莊再發', 'chart': '02177819',
    'emr': (
        "門診 , 柯呈諭 , 心臟血管科02 診 (0009) , 2026/04/07\n"
        "[Diagnosis]\n"
        "* (Dx)1. CAD, LM + 3-vessel-disease, SYNTAX 40. (2025/11/19), "
        "s/p DES*1+DCB*1 for p-dLAD, cutting balloon+DES*1 for LM-LAD, DCB*1 for pLCX (2026/01/22); "
        "s/p 2*DEB dRCA-PDA, 1*DES p-mRCA on 2026/03/05\n"
        "2. Infrarenal abdominal aortic aneurysm (AAA) 3.6~4 cm, stationary\n"
        "3. Diabetes mellitus (DM)\n4. Dyslipidemia\n5. Hypertension (HTN)\n"
        "6. Mild to moderate fatty liver\n7. BPH\n8. Colonic polyp s/p biopsy removal\n"
        "9. Gastric ulcers\n\n"
        "* (ICD-10 : I10) : Essential (primary) hypertension\n"
        "* (ICD-10 : E785) : Hyperlipidemia, unspecified\n"
        "* (ICD-10 : I259) : Chronic ischemic heart disease, unspecified\n\n"
        "[Subjective]\nfrom GI for evaluation of feasibility of EGD/colon\nno chest pain\n"
        "smoking (-) alcohol (quit)\n"
        "chronic diseases (HT, DM, HL) with medications from VGH\n"
        "PH: no stroke; BPH\n"
        "20260126 focal chest pain since 1/24 afternoon\n"
        "20260313 recent admission for PCI\n"
        "20260330 still complained of chest pain, better after 普拿疼加強錠\n"
        "20260407 cold sweat after dinner sometimes\n\n"
        "[Objective]\nBP:129/68mmHg, P:53 times/min\nLDL 70\nCr 0.94\nALT: 14\nA1c 6.7\n"
        "Echo: LA dilatation, LVEF=68%, Impaired myocardial relaxation, E/e'=11.7\n"
        "No pulmonary hypertension, PA systolic pressure=31mmHg\n"
        "Valves: Mild MR, Mild AR, Mild TR\nTMT: positive\n\n"
        "[Assessment & Plan]\ntarget LDL-C < 100 mg/dL (2026-03-06 LDL-C: 67 mg/dL)\n"
        "Imp:\n1. Infrarenal aortic aneurysm, 36mm, stationary\n"
        "2. Atherosclerotic aorta with calcification and ulcerated mural atheromas\n"
        "- Please pay attention on Shaggy syndrome\n"
        "may follow up CAG > 4/9 AM admission, PM CAG\n"
        "若無床 順延至 4/12 admission, 4/13 CAG"
    ),
    'emr_summary': (
        "80 y/o 男性\n"
        "一、心臟科相關診斷：\n"
        "1. CAD, LM+3VD, SYNTAX 40, s/p multiple PCI (DES/DCB for LAD, LM-LAD, LCX, RCA)\n"
        "2. Infrarenal AAA 3.6~4 cm, stationary\n3. DM\n4. Dyslipidemia\n5. HTN\n\n"
        "二、病史：\n20260126 focal chest pain\n20260313 recent admission for PCI\n"
        "20260330 still chest pain, better after 普拿疼加強錠\n"
        "20260407 cold sweat after dinner sometimes\n\n"
        "三、客觀檢查：\nBP:129/68mmHg, P:53\nLDL 70, Cr 0.94, A1c 6.7\n"
        "Echo: LVEF=68%, LA dilatation, Mild MR/AR/TR\nTMT: positive\n\n"
        "四、本次住院計畫：\nmay follow up CAG > 4/9 AM admission, PM CAG\n"
        "若無床 順延至 4/12 admission, 4/13 CAG"
    ),
    'order': '', 'diagnosis': '', 'cathlab': '', 'note': '',
}

# 朱素蘭 (no EMR per user request)
if '10335834' not in emr_db:
    emr_db['10335834'] = {
        'name': '朱素蘭', 'chart': '10335834',
        'emr': '', 'emr_summary': '', 'order': '', 'diagnosis': '', 'cathlab': '', 'note': '4/7改期',
    }

# Doctor groupings
doctor_patients = {
    '詹世鴻': ['02407466', '10335834', '06779181', '04762762', '22718712', '07472739', '20926474'],
    '鄭朝允': ['16160484', '21971011', '13183765'],
    '陳儒逸': ['13404922', '00790747'],
    '柯呈諭': ['02177819'],
}

# Clear old sub-tables
clear_range(ws, 'A15:H60')
time.sleep(1)

# Write new sub-tables
current_row = 15
for doctor, charts in doctor_patients.items():
    patients = []
    for chart in charts:
        d = emr_db.get(chart, {})
        patients.append({
            'name': d.get('name', ''),
            'chart_no': chart,
            'emr': d.get('emr', ''),
            'emr_summary': d.get('emr_summary', ''),
            'order': d.get('order', ''),
            'diagnosis': d.get('diagnosis', ''),
            'cathlab': d.get('cathlab', ''),
            'note': d.get('note', ''),
        })
    current_row = write_doctor_table(ws, current_row, doctor, patients)
    time.sleep(1)

# Write result
with open('_subtable_result.txt', 'w', encoding='utf-8') as f:
    for doctor, charts in doctor_patients.items():
        f.write(f"{doctor} ({len(charts)} patients):\n")
        for chart in charts:
            d = emr_db.get(chart, {})
            has_emr = 'YES' if d.get('emr') and len(d.get('emr', '')) > 20 else 'NO'
            f.write(f"  {d.get('name','')} ({chart}) EMR={has_emr}\n")
        f.write("\n")

print("Done!")
