---
name: name-conflict-refetch-emr
description: When OCR (image) name disagrees with sheet name, re-fetch EMR divUserSpec to resolve — never ask user to visually confirm
metadata:
  type: feedback
---

**Rule**: When an admission-list image OCR name disagrees with the sheet's existing name (both are non-EMR sources), the first action is to re-fetch the EMR for that chart using `fetch_emr.py` and read divUserSpec. **Never** ask the user to visually confirm.

**Why**: divUserSpec is canonical for names ([[feedback_emr_auto_name_fix.md]] / [[feedback_emr_name_location.md]]). It's populated by chart-no entry, BEFORE any visit click — so it works even when EMR returns `no_visit` for that chart. So there is always a way to get the authoritative name programmatically. Asking the user to OCR-judge an unusual character (鉻 vs 路) on a low-res image is exactly the kind of thing automation already solves.

**How to apply**:
- When diff-update finds a name discrepancy between OCR and sheet, treat it as "OCR vs unknown" — don't pick a side, just re-fetch EMR
- `fetch_emr.py SESSION_URL out.json CHART_NO DOCTOR` returns a line containing `姓名 : <name>` from divUserSpec regardless of visit status
- Apply the divUserSpec name to both main F col and sub-table A col (process_emr.py does this automatically when run after fetch)
- Only flag to user if EMR somehow returns no divUserSpec data (rare; chart not in HIS system)

**Concrete miss (5/12)**: 5/13 diff-update found image OCR = 董相鉻, sheet = 董相路, chart 08473654. EMR divUserSpec immediately returned 「姓名 : 董相路」when re-queried. I had hedged with "請目視確認" instead. User pushed back: 「名字都是以EMR divUserSpec 為準阿 有甚麼問題?!」
