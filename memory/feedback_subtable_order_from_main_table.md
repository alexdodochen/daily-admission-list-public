---
name: Sub-table doctor block order = main-table D col first-appearance order
description: Sub-table doctor blocks follow the order doctors appear in main A-L (col D), NOT weighted_doctor_shuffle from 主治醫師抽籤表. Lottery randomization retired for sub-table layout.
type: feedback
---

When building sub-tables (子表格) under a date sheet, the doctor block order is determined by the **first-appearance order in main data col D (主治醫師)**, NOT by `lottery_utils.weighted_doctor_shuffle()` or any random draw.

**Why:** 2026-05-11 user explicit instruction: «以後子表格就依照主表順序生成 不用特別抽籤». The lottery-based sub-table ordering (weighted *N tickets → shuffle → dedup) is no longer used for layout.

**How to apply:**
- `admission-lottery` skill / any batch sub-table builder must read main D col, iterate top-to-bottom, build `seen` dict to preserve first-appearance order:
  ```python
  doctor_order = []
  seen = set()
  for row in data[1:]:
      d = row[3].strip()
      if d and d not in seen:
          seen.add(d)
          doctor_order.append(d)
  ```
- Do **not** call `weighted_doctor_shuffle()` for sub-table block layout.
- 主治醫師抽籤表 still exists as reference data; current rule does NOT delete or modify it. Just don't use it for sub-table doctor order.
- This rule covers sub-table generation only. Per-doctor patient order within a block, N-V round-robin ordering, and any future ordering logic are NOT affected by this rule unless the user says so.
- Non-slot doctor logic (詹世鴻 Fri 例外, 張獻元 Wed-admit etc.) is unaffected — those concern cathlab scheduling and N-V grouping, not sub-table block order.

**Cross-repo audit:** This rule is project-specific (admission-list daily workflow). Other 4 alexdodochen repos do not have sub-tables — no propagation needed.
