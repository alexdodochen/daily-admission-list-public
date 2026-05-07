---
name: rebuild_date_sheet.py writes sub-table to A:G but data has 8 cols (A:H)
description: Known bug in rebuild_date_sheet.py — writes the 8-col sub-table to A:G range, causing APIError 400 'tried writing to column [H]'. Use inline 8-col write instead.
type: reference
---

`rebuild_date_sheet.py` line 248:
```python
ws.update(values=sub_rows_write, range_name=f'A{sub_start}:G{sub_end}', ...)
```

But `SUB_HEADERS` has 8 entries (A-H) and each data row has 8 cols ending with 註記 column. Calling rebuild_one() with the 8-col layout fails:
```
APIError: [400]: Requested writing within range ['{date}'!A6:G14], but tried writing to column [H]
```

**Workaround (until fixed):**
- Don't import `rebuild_one` directly. Inline the same logic in your script with `range_name=f'A{sub_start}:H{sub_end}'`.
- Reference inline implementation in `_reschedule_build.py` (2026-05-07 reschedule run).

**Fix to apply later:**
Change `A{sub_start}:G{sub_end}` → `A{sub_start}:H{sub_end}` in rebuild_date_sheet.py. Verify with one date sheet that has ≥1 doctor block.

Also consider auditing other places: `rebuild_one` is the canonical builder; an inline copy in `_reschedule_build.py` should be deleted once the upstream is fixed.
