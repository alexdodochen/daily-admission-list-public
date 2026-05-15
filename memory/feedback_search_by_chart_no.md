---
name: cross-sheet patient search — by chart no only
description: ALL locate/move/modify operations on patient data must locate by 病歷號 first — never by name, position, or any other attribute
type: feedback
---

**For every patient operation — search, move, modify, copy, diff, verify — locate by 病歷號 first.** Never by 姓名, never by row position, never by date+name combo.

**Why (5/15):** chart no is the unique stable key; name has variants:
- Han character variants (淩/凌, 鉛/鈞, 諭/論, 翔/翔) — `feedback_doctor_name_variant_lin_jialing.md` proved EMR vs sheet use different code points
- OCR corrections — sheet may have OCR-corrected name, EMR may have system canonical
- Name updates — Sheet A col may be EMR-corrected, image OCR may not be

User's instructions (cumulative):
- 5/15: «查找就只要用病歷號查找 最有效率»
- 5/15 (reinforcement): «你要有一個習慣 需要查找病人資料的時候 一律去對病歷號即可 不用整組EMR FG甚麼的全部對 只有要移動資料的時候才需要整列搬移»
- 5/15 (generalized): «所有要移動 定位 更改 都先以病歷號定位 幫助你省token 省時間» — now the universal rule, not just cross-sheet search

**How to apply (universal):**
- Diff-update: compare sheet's main I col vs image's chart col → ADD/DEL set (no name/age/diagnosis comparison)
- Move/reschedule: find source row by chart no, find target slot by chart no, copy/insert
- Manual edit: «改 X 的 F 欄» → ask «病歷號是？» if not given, never guess by name
- Cross-sheet lookup: iterate sheets, scan rows, match `r[1] == target_chart` (sub-table B) or `r[8] == target_chart` (main I)
- Skip sub-table title rows (`row[0].endswith('人）')`) and header rows
- Validate by `len(r[2]) > 50` if you want an EMR-bearing row (skip blank chart-only matches)

**Anti-pattern:**
```python
# DON'T: name-based match (fragile to variants)
if r[0] == '林佳凌':  # may be '林佳淩' in EMR
    ...

# DO: chart-no match (stable)
if r[1] == '08473654':
    ...
```

**Also minimal-fields rule (5/15 reinforcement):**
> 你要有一個習慣 需要查找病人資料的時候 一律去對病歷號即可
> 不用整組EMR FG甚麼的全部對 只有要移動資料的時候才需要整列搬移

When *locating* a patient, only match by chart no — don't pull EMR/F/G/H text into comparison. Full-row read is only justified when the result will be *written* somewhere (e.g. row migration, EMR copy from origin date sheet). Saves cells read + cells compared + cognitive load.

Related: [[Doctor name char variant: 林佳淩 (EMR) vs 林佳凌 (sheets)]], [[deferred patients — pull EMR from original date sheet first]]
