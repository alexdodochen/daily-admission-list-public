---
name: 5/15 post-mortem — why I didn't use minimal-diff + hook enforcement installed
description: Self-reflection on the 5/18 diff-update where I batch_clear'd existing sub-tables (wiping vetted F/G/H) instead of row-level INSERT/DELETE. PreToolUse hook now blocks it.
type: feedback
---

## What I did wrong (5/15)
On 5/18 admission list diff-update (3 ADD + 1 DELETE + K/L cell updates), I ran:
```python
ws.batch_clear(['A2:V50'])  # WIPES ALL EXISTING SUB-TABLE EMR
sh.batch_update(unmergeCells full range)
write_range(new_main A-L)
for each doctor: write_doctor_table(...)  # rebuild every block
```

The first script attempt errored on a `write_doctor_table` kwarg issue AFTER the clear had succeeded — leaving the sub-table area wiped. The second attempt tried to recover via `emr_cache = ws.get_all_values()` BEFORE clear, but in fact ran against the ALREADY-CLEARED sheet → cache was empty for existing patients → only 宋哲光 (pulled from 5/12) got EMR.

Result: 6 patients' EMR / F / G / H were wiped. Manual H notes lost («全麻 Affera», «劉秉彥»). Recovery required re-running `process_emr.py 20260518` (auto-detect F/G — different from the human-vetted values) + fetching new patients via fresh `fetch_emr.py`, + manually re-typing H notes from memory.

## Why I didn't apply minimal-diff
1. Treated the task as «structural change» (new patient order, doctor blocks reorganized: 黃鼎鈞 gains a patient, 張獻元 is a new block) instead of «row-level diff» (3 inserts, 1 delete, 3 cell updates).
2. Chose the lazy mental shortcut: «I have all the data in memory, clear+rewrite is simpler».
3. Didn't pause to read `memory/feedback_diff_update_subtable_minimal.md` BEFORE acting — that rule was written 5/4 for exactly this scenario.
4. The skill `admission-image-to-excel`'s template shows a write-from-scratch flow (legitimate for new sheets) — easy to copy that pattern for diff-update too, but wrong.

User quote (5/15, sharp):
> 那你要檢討為何沒有使用minimal diff!!!! 把minimal diff設定成hook 要更新時都要使用 或是用甚麼方法強制你minimal diff節省時間

## Enforcement installed
**Hook: `scripts/pre_minimal_diff_guard.py`** — PreToolUse on Bash. Exits 2 with explanation if command contains BOTH a `20YYMMDD` token AND a full-wipe pattern (`batch_clear(['A`, `.clear()`, `clear_area(`, `clear_range(`).

Sanctioned bypasses:
- `rebuild_date_sheet.py` (the legitimate clean-slate driver, used by `admission-sheet-rebuild` skill when a sheet is genuinely broken)
- `refresh_emr.py` (internal mutations only)
- Prefix `ALLOW_FULL_SHEET_WIPE=1` (forced override; must justify in chat)

Wired in `.claude/settings.json` PreToolUse.Bash.

## How to apply minimal-diff (the rule the hook protects)
For each doctor block:
1. `existing_charts` = set of chart no's already in sub-table
2. `new_charts` = set of chart no's from new admission image
3. `to_add` = new - existing → use sheets API `insertRange` + `batch_write_cells` for A=name, B=chart only (EMR/F/G/H stay blank for fetch_emr to fill)
4. `to_remove` = existing - new → use sheets API `deleteRange`
5. `to_keep` = intersection → **DO NOT TOUCH** (no read-then-rewrite either — that's still a write)
6. Update doctor title `（N人）` count via `batch_write_cells`
7. Whole doctor block empty → delete title+header+gap together
8. `enforce_sheet_format(date)` at the end

For 延期 patients (K col contains `(YYYY/MM/DD ...延期)` or `(N/N無床延期)`):
- Search by 病歷號 in origin date sheet first (see [[deferred patients — pull EMR from original date sheet first]])
- If found → pull C/F/G/H, write to new sheet's sub-table row directly (still minimal — just the new INSERT row, not a sheet-wide rebuild)

## How to apply (search efficiency)
Per [[Cross-sheet patient search by 病歷號 only — never name]] + 5/15 reinforcement:
> 你要有一個習慣 需要查找病人資料的時候 一律去對病歷號即可 不用整組EMR FG甚麼的全部對 只有要移動資料的時候才需要整列搬移

Match by chart no only when *locating*. Pull full row only when *moving/copying* the row.

Related: [[diff-update sub-table 只動 ADD/DELETE 不要重寫]], [[deferred patients — pull EMR from original date sheet first]], [[Cross-sheet patient search by 病歷號 only — never name]]
