---
name: Main table → first sub-table = 2 blank rows gap
description: Date sheet layout requires exactly 2 blank rows between the main A-L data block and the first sub-table title row. Single-blank-row gap (current default of rebuild_date_sheet / write_doctor_table) is wrong.
type: feedback
---

Layout rule: between the last main-data row (col A = `YYYY-MM-DD`) and the first sub-table title row (col A = `醫師（N人）`), there must be **exactly 2 blank rows**.

**Why:** User instruction (5/8): «你5/10 還是沒有變成我喜歡的格式ㄟ 就是subtable要跟table空兩行». Visual breathing room separates the canonical patient roster from the per-doctor work surface. With only 1 blank row, the two blocks read as continuous, and the user's eye can't anchor on which is which.

**How to apply:**
- After writing/rebuilding any date sheet, verify `first_sub_title_row - main_end_row == 3` (i.e. 2 blank rows in between).
- Easy fix on existing sheet: `ws.insert_rows([[]]*2, row=main_end+1)` then `enforce_sheet_format(date)`.
- For new sheets: `write_doctor_table` / `rebuild_date_sheet.py` should leave 2 blank rows after main_end before placing the first title. Pre-5/8 they were leaving only 1 — should be patched.
- This applies only to the main→first-sub gap. Inter-sub-table gap rule (between two sub-table blocks) is separately defined as 2 blank rows in `write_doctor_table` (return `end_row + 3`), but the 5/8 audit found existing sheets often have just 1 — that's a separate bug, fix when it bites.

**Don't:**
- Don't insert random blank rows just to add visual padding elsewhere — the 2-row gap is specifically between main and first sub-table.
- Don't use `enforce_sheet_format` to fix this — it formats existing rows but doesn't shift sub-tables. You need `insert_rows` first.
