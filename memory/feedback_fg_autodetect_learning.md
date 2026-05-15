---
name: F/G auto-detect rules — learnings from 248-row 2026 corpus
description: process_emr.py DIAG_RULES / CATH_RULES / extract_dx_section refinements based on comparing rule output vs human-vetted F/G across all 2026 sheets
type: feedback
---

User asked (5/15): «重新讀取所有工作表的EMR 然後自己生成FG存好 再跟先有工作表的FG相比對 線有工作表都是人工判讀出來的FG 以人工判讀的FG為準 請你學習EMR跟人工判讀的FG的關聯，改進你以後自動生成FG的能力».

Analysis script: `_fg_learning_analysis.py` (gitignored — ephemeral). Output: `_fg_learning_report.md`.

## Initial 5/15 corpus
- 248 sub-table patient rows across all 2026* date sheets
- Baseline disagreement rate: F=58% (144/248), G=25% (62/248)

## Top patterns (rule → human)

| Rule said | Human said | Count | Root cause |
|---|---|---|---|
| Syncope | CAD | 24 | EMR mentioned syncope in history; current admission is CAD f/u |
| Unstable | CAD | 21 | Dx item says "Unstable angina, ... CAD - 2VD ..." or "CAD with unstable angina" — co-mention means CAD admission |
| STEMI | CAD | 11 | `'ST elevation myocardial'` substring fired on `'non-ST elevation myocardial'` (NSTEMI text) |
| pAf | CAD | 10 | Patient has Af history but admission is for CAD |
| CHF | CAD | 7 | CHF history, admission CAD f/u |
| (G) PCI | Left heart cath. | 22 | `'intervention'` / `'PCI '` substring fired on `s/p percutaneous coronary intervention (PCI)` historical mentions |
| (G) EP study | Left heart cath. | 5 | Syncope misclassified as F → F→G default mapped EP study |

## Root causes
1. **`extract_dx_section` only recognised `[Diagnosis]` literal**, not the actual `* (Dx)` format used by Web EMR → all rules ran on whole-EMR substring match → lost numbered-item priority
2. **STEMI rule checked before NSTEMI** + substring match → `'ST elevation'` in `'non-ST elevation'` triggered STEMI
3. **CATH_RULES PCI rule too broad** (`'PCI '`, `'intervention'`) → matched historical PCI mentions outside `s/p ...` clauses that `clean_past_tense_pci` strips
4. **DIAG_RULES order had Unstable BEFORE CAD** → co-mention items always picked Unstable
5. **No past-tense cleaning for F** (mirror of CATH's `clean_past_tense_pci`) → `s/p NSTEMI`, `s/p Af`, etc. still fired

## Fixes applied (5/15)
1. `extract_dx_section`: parse `* (Dx)...* (ICD-10` numbered form. Keep ICD-10 block in extracted text so `detect_via_icd` fallback still works.
2. STEMI rule keywords narrowed to `['STEMI']` only (drop `'ST elevation myocardial'`). NSTEMI rule already ordered before, but reorder confirmed.
3. CATH_RULES PCI keywords tightened: drop `'PCI '` (bare), `'intervention'`. Keep `plan PCI`, `plan for PCI`, `arrange PCI`, `PCI for admission`, `primary PCI`, `→PCI`, `→ PCI`, `POBA`, `rotablation`.
4. DIAG_RULES: move `unstable angina` to END (after CAD). Co-mention always means CAD admission per corpus.

## Measured impact (after all 5/15 fixes — final)
- F disagreements: **144 → 64 (-56%)**
- G disagreements: **62 → 40 (-35%)**

Fixes 5-9 added after Plan-section pivot (user direction: «看 plan 段落 主治醫師會寫住院原因跟手術»):
5. `extract_dx_section`: keep `* (ICD-10` block in extracted text so `detect_via_icd` fallback works (F under-detection CAD: 18 → 2).
6. `detect_diag` soft-comorbid CAD override: when first-matching F is `Unstable` / `Angina pectoris` / `Syncope` / `VPC` / `CHF` AND CAD keyword appears anywhere in dx_text → return `CAD`. Cath-lab admission bias: these comorbidities co-mentioned with CAD always indicate CAD admission. Not applied to `pAf` or specific procedure indications (RFA / PPM / PTA / valve) — data shows those are often the primary F.
7. `clean_past_tense_pci`: regex broadened from literal `r's/p\s+PCI'` to `r's/p[^\n]{0,200}?PCI[^\n]*'` (allow expansion like `s/p percutaneous coronary intervention (PCI)`). Added `'PCI ... \[?YYYY/MM/DD\]?'` pattern. Same broadening applied to `ablation` past-tense.
8. **Plan-section primary signal (`extract_plan_signal` + `PLAN_F_RULES` + `PLAN_G_RULES`)**: take bottom 60 lines of EMR, keep lines with procedure keywords or admission cues, apply F/G rules to those. Plan signal is primary; Dx-based detection is fallback only.
9. **Key G-mapping insight (5/15)**: G is the cath-lab BOOKING slot, not the procedure outcome. Even when plan says `TRA PCI` / `PCI for LAD` / `5/12 PCI` → human books as `Left heart cath.` (PCI is the intervention performed AFTER staging angio). Only special bookings override LHC: `TAVI`, `CRT`, `EVICD/ICD`, `M-TEER`, `LAAO Occluder`, `RF ablation`, `Myocardial biopsy`, `PTA`, `PPM`, `Right heart cath.`, `Both-sided cath.`, `Carotid stenting`, `EP study`, `primary PCI` (STEMI only). All other PCI plan-keywords flow to LHC.

## Plan signal extraction
`extract_plan_signal(emr_text)`:
- Bottom 60 lines of EMR
- Keep lines matching procedure keywords (`PCI|POBA|ablation|biopsy|EVICD|ICD|PPM|CRT|TAVI|LAAO|M-TEER|cath|CAG|LHC|RHC|PTA|TEE|EMB|PVI|AFFERA|varipulse|admission|adm`) OR admission cues (`adm|arrange|plan|^MM/DD `)
- Output is concatenated lines, fed to `clean_past_tense_pci` then `PLAN_G_RULES` / `PLAN_F_RULES`

Real plan examples:
- `5/14 admission / 5/15 TRA PCI` → G=Left heart cath., F=CAD (via PLAN_G_TO_F)
- `Adm for LAAO / Adm on 5/11pm, LAAO on 5/12pm` → G=LAAO Occluder, F=pAf
- `5/11 ADMISSION / 5/12 AF ablation(Vari-pulse)` → G=RF ablation, F=pAf
- `5/17 adm / EVICD on 5/18pm` → G=ICD, F unchanged
- `Arrange admission for right cath` → G=Right heart cath.
- `Admission for Long-standing persistent Afib ablation (AFFERA)` → G=RF ablation, F=pAf

## Outstanding patterns worth future investigation
- **F under-detection CAD (18 cases)**: Dx item lacks `CAD`/`coronary` keyword but I259/I250 ICD codes present — fix #1 should now route these through `detect_via_icd`. Validate post-deploy.
- **CHF → CAD (7)**: CHF often co-mentioned with CAD; same co-mention rule as Unstable should apply. Consider moving CHF below CAD too.
- **VPC → CAD (3)** + **PSVT → CAD (1)**: minor arrhythmia mentions in CAD admissions.
- **G PCI → Left heart cath. (8 remaining)**: residual false PCI predictions — likely OPD plan text mentions "PCI" forward-looking even when the admission is staging angio. Need plan-section anchoring to "plan/arrange" verbs.

## How to apply
- Run `python _fg_learning_analysis.py` after rule changes to measure delta.
- Sample size 248 is sufficient for top patterns; tail patterns (1-2 occurrences) are too noisy to chase.
- Never modify rules to fit a single case — require ≥3 corpus instances.
- `_fg_learning_report.md` is gitignored ephemeral; re-generate as the corpus grows.

Related: [[diff-update sub-table 只動 ADD/DELETE 不要重寫]] (don't wipe vetted F/G), [[deferred patients — pull EMR from original date sheet first]] (preserves prior human F/G).
