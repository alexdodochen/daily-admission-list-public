---
name: fg-column-width
description: Date-sheet F/G/H columns must be wider (160px) so sub-table 術前診斷/預計心導管/註記 are visible without click-to-expand
metadata:
  type: feedback
---

User asked (5/14): «讓 FG 欄寬益點 不然都看不到術前診斷還有預計心導管»; extended (5/15): «H 欄也要 routine 拉寬 我才有空間看備註».

`enforce_sheet_format` now sets F (col 6), G (col 7), H (col 8) to **pixelSize 160** on every run. Idempotent — re-running widens repeatedly to the same value, no drift.

**Why:** All three columns are dual-purpose between main row + sub-table:
- F: main `姓名` (3-5 chars, default fine) + sub-table `術前診斷` (e.g. `AS s/p TAVI`, `Acute pericarditis r/o`, often >12 chars)
- G: main `性別` (1 char, default wastes space) + sub-table `預計心導管` (e.g. `Myocardial biopsy`, `EP study + RFA`, >10 chars)
- H: main `年齡` (2-3 chars) + sub-table `註記` (e.g. `劉秉彥`, `全麻 Affera`, `cardioversion 不用排導管`, `N` for newly-added — variable length, can grow with annotations)

Default ~100 px truncates sub-table content; user couldn't read F/G/H in the dashboard view.

**How to apply:** Already wired into `enforce_sheet_format` (gsheet_utils.py). Every sheet write triggers the post-format hook → F/G/H stay wide automatically. For one-off legacy sheets without recent writes, manually call `enforce_sheet_format(YYYYMMDD)`.
