"""Process EMR JSON, auto-detect F/G, write to Sheet.

Usage: python process_emr.py <date8>   e.g. 20260419

Reads emr_data_<date>.json, reads sub-tables from Sheet <date>, writes:
- C col: full EMR text (raw)
- F col: auto-detected 術前診斷
- G col: auto-detected 預計心導管
- A col (name): auto-corrected from EMR name

Sub-table layout (8 cols, canonical): A=姓名 | B=病歷號 | C=EMR | D=EMR摘要
                                      E=手動設定入院序 | F=術前診斷 | G=預計心導管 | H=註記

D=EMR摘要 is a placeholder column — this script does NOT auto-generate or write
summary content. User triggers Gemini summary on demand to fill D when needed.

Also updates main data F col (姓名) if EMR-corrected name differs.
"""
import sys, json, re, time
sys.path.insert(0, '.')
import gsheet_utils as gu

# Order matters: 急/specific > arrhythmias > vascular > CHF > CAD-family (broadest, last).
# Diag matching is constrained to the (Dx) section by extract_dx_section() so
# comorbidity entries like `* (ICD-10:I495)` (sick sinus) don't bleed into primary Dx.
DIAG_RULES = [
    # Acute / time-critical
    # NSTEMI checked BEFORE STEMI — 'non ST elevation' contains 'ST elevation' substring
    # so STEMI rule would mis-fire if STEMI were checked first. Same reason 'ST elevation'
    # has been dropped from STEMI keywords; rely on the 'STEMI' abbrev itself.
    (['NSTEMI', 'non-ST elevation', 'non ST elevation'], 'Others:NSTEMI'),
    (['STEMI'], 'STEMI'),
    # Unstable angina rule moved DOWN below CAD — when a single Dx item lists both
    # ("Unstable angina, ... CAD - 2VD ...", "CAD with unstable angina", etc.) human
    # consistently picks CAD. Keep Unstable only for pure "unstable angina" cases
    # without CAD co-mention. See _fg_learning_report.md (5/15).
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
    # CAD family — moved UP above soft comorbidities. Per 5/15 learning analysis,
    # when CAD keyword appears in a Dx item, human picks CAD regardless of co-mentioned
    # Unstable / Angina / CHF / Syncope / VPC.
    (['CAD', 'coronary artery disease',
      'chest pain', 'chest tightness', 'chest tigthness',
      'ACS', 'acute coronary syndrome',
      'I259', 'I250', 'I251',
      'TET (+)', 'TMT (+)', 'THL (+)', 'TET+', 'TMT+', 'THL+'], 'CAD'),
    # Soft comorbidities — only fire when CAD is absent from this Dx item.
    (['unstable angina'], 'Unstable'),
    (['angina pectoris', 'angina'], 'Angina pectoris'),
    # Symptom-driven (after CAD per learning)
    (['syncope'], 'Syncope'),
]

# CATH matching runs against [Assessment & Plan] section after past-tense PCI is stripped.
# CRT is more specific than PPM so it goes first. PCI keywords avoid bare 's/p PCI'.
CATH_RULES = [
    (['CRT-D', 'CRT-P', 'CRT upgrade', 'cardiac resynchronization'], 'CRT'),
    (['TAVI', 'transcatheter aortic valve'], 'TAVI'),
    # PCI rule — only forward-looking triggers. Bare 'PCI' / 'intervention' kept
    # firing on `s/p percutaneous coronary intervention (PCI)` historical mentions
    # even after clean_past_tense_pci, because `intervention` appears outside the
    # `s/p ...` clause. Human consistently picks Left heart cath. when this admission
    # is for re-cath, not a planned PCI. See _fg_learning_report.md (5/15).
    (['plan PCI', 'plan for PCI', 'arrange PCI', 'PCI for admission',
      'primary PCI', '→PCI', '→ PCI', 'POBA', 'rotablation'], 'PCI'),
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
    """Return primary diagnosis lines from the Dx block.

    Supports two EMR formats:
      A. `[Diagnosis] ... [Subjective]` section-marker form (older)
      B. `* (Dx)1. ... \n * (ICD-10：...)` numbered form (current Web EMR)

    Strips `* (Dx)` prefix so numbered items become parseable.
    """
    diag_text = ''

    # Format B (current Web EMR): `* (Dx)` numbered items until `* (ICD-10` block,
    # PLUS the `* (ICD-10` block itself (so detect_via_icd has codes to scan).
    # Boundary: free-text Dx ends where `* (ICD` block starts; ICD block ends where
    # `[Subjective]` or end-of-text starts.
    m_dx = re.search(r'\*\s*\(Dx\)(.*?)(?=\n\s*\*\s*\(ICD|\Z)', emr_text, flags=re.DOTALL)
    m_icd_block = re.search(r'((?:\n\s*\*\s*\(ICD[^\n]*\n?)+)', emr_text)
    if m_dx:
        diag_text = m_dx.group(1)
        if m_icd_block:
            diag_text = diag_text + '\n' + m_icd_block.group(1)

    # Format A fallback (legacy)
    if not diag_text:
        parts = re.split(r'\[(Diagnosis|Subjective|Objective|Assessment & Plan)\]', emr_text)
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
    """Strip historical PCI mentions so CATH PCI doesn't fire on `s/p PCI on 2020`.

    Note (5/15 learning): patterns must allow many words between `s/p` and `PCI`
    because real EMR Dx text expands the acronym, e.g. `s/p percutaneous coronary
    intervention (PCI)` — the original literal-adjacent pattern missed this
    completely, letting 22 cases mis-fire the PCI rule.
    """
    patterns = [
        # `s/p ... PCI ... <end-of-line>` — allow expansion like `percutaneous coronary intervention (PCI)`
        r's/p[^\n]{0,200}?PCI[^\n]*',
        r'post[\-\s][^\n]{0,200}?PCI[^\n]*',
        r'status\s+post[^\n]{0,200}?PCI[^\n]*',
        r'PCI\s+(?:on|in)\s+\d{4}[/\-]?\d{0,2}[/\-]?\d{0,2}',
        r'PCI\s+done[^\n]*',
        r'previous\s+PCI[^\n]*',
        r'history\s+of\s+PCI[^\n]*',
        r'old\s+PCI[^\n]*',
        # Past-tense PCI by year-suffix even without s/p prefix: `PCI ... 2020`, `PCI ... [2024/4/5]`
        r'PCI[^\n]{0,80}\[?\d{4}[/\-]\d{1,2}[/\-]?\d{0,2}\]?',
        # Past-tense ablation — `s/p AFL ablation`, `post ablation 2024`, etc.
        r's/p[^\n]{0,200}?ablation[^\n]*',
        r'post[\-\s][^\n]{0,200}?ablation[^\n]*',
        r'status\s+post[^\n]{0,200}?ablation[^\n]*',
        r'previous\s+ablation[^\n]*',
        r'history\s+of\s+ablation[^\n]*',
        r'ablation[^\n]{0,40}\[?\d{4}[/\-]\d{1,2}[/\-]?\d{0,2}\]?',
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


_SOFT_COMORBID_F = {'Unstable', 'Angina pectoris', 'Syncope', 'VPC', 'CHF'}
_CAD_HINT_RE = re.compile(
    r'\b(CAD|coronary\s+artery\s+disease)\b|\bI25[019]\b',
    re.IGNORECASE,
)


def _cad_anywhere(text):
    return bool(_CAD_HINT_RE.search(text))


def detect_diag(dx_text):
    """Apply DIAG_RULES with numbered-item priority + soft-comorbidity CAD override.

    Numbered Dx (`2.CAD ... 4.pAf`) means item 2 is more important than item 4,
    so iterate items in order and take the first that matches a rule.

    Soft-comorbidity override (5/15 learning): when first-matching F is
    Unstable / Angina pectoris / Syncope / VPC, but CAD keyword appears
    ANYWHERE in dx_text, return 'CAD' instead. Cath-lab admission bias —
    these comorbidities co-mentioned with CAD always indicate CAD admission.
    Not applied to CHF or pAf — data shows both directions (sometimes CHF/pAf
    is the primary F).

    Strip ICD-10 lines BEFORE keyword matching so comorbidity codes don't pollute,
    but keep them available for the ICD fallback at the end.
    """
    if not dx_text:
        return ''
    text_no_icd = '\n'.join([l for l in dx_text.split('\n') if not l.strip().startswith('* (ICD')])
    cad_present = _cad_anywhere(dx_text)  # check full text including ICD codes

    items = re.findall(r'(?:^|\n)\s*\d+\s*[\.\)]\s*([^\n]+)', text_no_icd)
    if items:
        for item in items:
            m = match_rules(item, DIAG_RULES)
            if m:
                if m in _SOFT_COMORBID_F and cad_present:
                    return 'CAD'
                return m
    m = match_rules(text_no_icd, DIAG_RULES)
    if m:
        if m in _SOFT_COMORBID_F and cad_present:
            return 'CAD'
        return m
    # Last resort: cardiac ICD-10 codes
    return detect_via_icd(dx_text)


# Plan-section rules (5/15 learning): attending writes admission reason +
# procedure in the bottom of EMR. These are the highest-signal cues:
# `5/11 ADMISSION / 5/12 AF ablation(Vari-pulse)`, `Adm for LAAO`,
# `Arrange admission for right cath`, `5/12 TRA PCI for LAD`, `Admission on
# 5/10. Cath study on 5/11.`, `5/17 adm / EVICD on 5/18pm`, etc.

PLAN_F_RULES = [
    # Arrhythmia ablation → specific F (more specific than Dx mention)
    (['AFL ablation', 'atrial flutter ablation', 'typical flutter ablation', 'atypical flutter ablation'], 'Atrial flutter'),
    (['AF ablation', 'Af ablation', 'Afib ablation', 'AFFERA', 'PVI', 'pulmonary vein isolation', 'varipulse', 'vari-pulse'], 'pAf'),
    (['VPC ablation', 'PVC ablation'], 'VPC'),
    (['PSVT ablation', 'SVT ablation'], 'PSVT'),
    # Valve interventions → valve F
    (['TAVI', 'transcatheter aortic valve'], 'AS'),
    (['M-TEER', 'MTEER', 'MitraClip', 'mitral TEER'], 'MR'),
    # Generator replacement
    (['generator replacement', 'ppm replacement', 'icd replacement',
      'crt replacement', 'change generator'], 'Generator replacement'),
]

PLAN_G_RULES = [
    # KEY 5/15 INSIGHT: G is the cath-lab BOOKING slot, not the procedure outcome.
    # Even when plan says "TRA PCI" / "PCI for LAD", the cath lab books as
    # "Left heart cath." (PCI is the intervention performed AFTER staging angio).
    # The only G values that override Left heart cath. are special bookings:
    # TAVI, CRT, EVICD/ICD, M-TEER, LAAO Occluder, RF ablation, Myocardial biopsy,
    # PTA, PPM, Right heart cath., Both-sided cath., Carotid stenting,
    # EP study, primary PCI (STEMI only — rare).
    #
    # Plan PCI / TRA PCI / arrange PCI are all booked as Left heart cath.
    # See _fg_learning_report.md (5/15): 23 PCI-prediction cases all human-chose LHC.
    (['EVICD', 'EVCID', 'AICD', 'ICD implant', 'ICD implantation'], 'ICD'),
    (['CRT-D', 'CRT-P', 'CRT upgrade', 'cardiac resynchronization', 'CRT implant'], 'CRT'),
    (['TAVI', 'transcatheter aortic valve'], 'TAVI'),
    (['M-TEER', 'MTEER', 'MitraClip', 'mitral TEER'], 'M-TEER'),
    (['LAAO', 'left atrial appendage occlusion', 'Watchman'], 'LAAO Occluder'),
    (['AFL ablation', 'AF ablation', 'Af ablation', 'Afib ablation',
      'VPC ablation', 'PVC ablation', 'PSVT ablation', 'SVT ablation',
      'VT ablation', 'PVI', 'pulmonary vein isolation',
      'varipulse', 'vari-pulse', 'AFFERA',
      'RF ablation', 'RFA', 'ablation'], 'RF ablation'),
    (['EP study'], 'EP study'),
    # Primary PCI for STEMI — only true PCI booking. Everything else falls through to LHC.
    (['primary PCI'], 'PCI'),
    (['PPM implant', 'permanent pacemaker', 'pacemaker implant', 'PPM'], 'PPM'),
    (['both-sided cath', 'BHC'], 'Both-sided cath.'),
    (['right cath', 'right heart cath', 'RHC'], 'Right heart cath.'),
    # 'biopsy' alone is too broad (matches `[Pre-PCI medication] biopsy ...` etc).
    # Require explicit `myocardial biopsy` / `EMB` to fire.
    (['myocardial biopsy', 'EMB'], 'Myocardial biopsy'),
    (['PTA'], 'PTA'),
    (['carotid stenting', 'carotid angiography'], 'Carotid angiography + stenting'),
    # Generic cath — also catches "TRA PCI" / "PCI for ..." / "POBA" / "stenting"
    # by falling through here (PCI plan-keywords removed above to force this default).
    (['cath study', 'catheterization', 'CAG', 'LHC', 'left heart cath',
      'cath on', 'cath via', 'PCI for', 'PCI on', 'TRA PCI', 'TFA PCI',
      'POBA', 'rotablation', 'stenting', 'plan PCI', 'arrange PCI'], 'Left heart cath.'),
]

# When plan yields G but no F, derive F from G when unambiguous
PLAN_G_TO_F = {
    'PCI': 'STEMI',          # primary PCI → STEMI admission
    'Left heart cath.': 'CAD',
    'PTA': 'PAOD',
    'TAVI': 'AS',
    'M-TEER': 'MR',
    'LAAO Occluder': 'pAf',
    'CRT': 'CHF',
    'Carotid angiography + stenting': 'Carotid stenting',
}

_PROCEDURE_KEYWORDS_RE = re.compile(
    r'\b(?:PCI|POBA|stenting|rotablation|ablation|biopsy|EVICD|EVCID|AICD|ICD|PPM|'
    r'CRT|TAVI|LAAO|Watchman|M-TEER|MTEER|MitraClip|cath|CAG|LHC|RHC|PTA|'
    r'TEE|EMB|PVI|AFFERA|ANS|varipulse|vari-pulse|admission|adm)\b',
    re.IGNORECASE,
)
_ADMISSION_CUE_RE = re.compile(
    r'(?:\b(?:adm(?:ission)?|arrange|plan)\b'
    r'|^\s*\d{1,2}[/-]\d{1,2}\s)',
    re.IGNORECASE | re.MULTILINE,
)


def extract_plan_signal(emr_text):
    """Return the admission-plan lines that carry the attending's intent.

    Strategy: scan the bottom 60 lines of the EMR for any line containing
    a procedure keyword OR an admission/arrange cue. Concatenate kept lines.
    Empty result means the EMR has no recognisable plan section — fall back to
    Dx-based detection.
    """
    if not emr_text:
        return ''
    lines = emr_text.split('\n')
    tail = lines[-60:] if len(lines) > 60 else lines
    kept = []
    for line in tail:
        s = line.strip()
        if not s:
            continue
        if _PROCEDURE_KEYWORDS_RE.search(s) or _ADMISSION_CUE_RE.search(s):
            kept.append(s)
    return '\n'.join(kept)


def detect_fg(emr_text):
    """Detect (F, G) using PLAN section as primary signal (5/15 learning).

    Priority order:
      1. Plan section (bottom of EMR) — attending's stated admission reason + procedure
      2. Dx section (numbered items) — fallback when plan is missing/unclear

    Cleans past-tense PCI mentions before matching so historical s/p PCI doesn't
    fire the PCI rule.
    """
    plan_signal = extract_plan_signal(emr_text)
    plan_clean = clean_past_tense_pci(plan_signal) if plan_signal else ''

    # G from plan
    g_cath = match_rules(plan_clean, PLAN_G_RULES) if plan_clean else ''

    # F from plan (specific arrhythmia / valve / generator overrides)
    f_diag = match_rules(plan_clean, PLAN_F_RULES) if plan_clean else ''

    # If plan gave G but not F → derive
    if g_cath and not f_diag:
        f_diag = PLAN_G_TO_F.get(g_cath, '')

    # Fallback: Dx-based F if plan signal didn't classify F
    if not f_diag:
        dx = extract_dx_section(emr_text)
        f_diag = detect_diag(dx) if dx else match_rules(emr_text, DIAG_RULES)

    # Fallback: G from F default if plan signal didn't classify G
    if not g_cath and f_diag:
        g_cath = F_TO_G_DEFAULT.get(f_diag, '')

    return f_diag, g_cath

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
                # Prepend age/gender so user sees demographics first line
                age_prefix = ''
                if info.get('name'):
                    raw_name = info['name']
                    birth = parse_birth_from_raw(raw_name)
                    gender = parse_gender_from_raw(raw_name)
                    if birth and gender:
                        age = compute_age(birth, mi.get('admission_date', ''))
                        if age is not None:
                            age_prefix = f'{age} y/o {gender}\n'
                emr_full = age_prefix + visit_header + emr_text

                f_diag, g_cath = detect_fg(emr_text)

                # Read current F/G — preserve human-vetted values
                # (5/15 rule: never overwrite human F/G during re-run; auto-detect
                # rules may be wrong, human judgment is authoritative).
                cur_f = (row[5].strip() if len(row) > 5 else '')
                cur_g = (row[6].strip() if len(row) > 6 else '')

                # 8-col layout: F=術前診斷, G=預計心導管. D=EMR摘要 left empty.
                updates.append((f'C{pr}', emr_full))
                if f_diag and not cur_f:
                    updates.append((f'F{pr}', f_diag))
                if g_cath and not cur_g:
                    updates.append((f'G{pr}', g_cath))

                prefill.append({
                    'chart': chart, 'name': name, 'doctor': doc_name,
                    'f': f_diag, 'g': g_cath, 'row': pr,
                    'matched': matched, 'visit': visit,
                })
            elif info and info.get('status') in ('no_visit', 'empty'):
                updates.append((f'C{pr}', '無本院一年內主治醫師門診紀錄'))
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
