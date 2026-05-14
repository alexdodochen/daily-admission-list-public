============================================
  HANDOFF — Last Updated: 2026-05-14 (Thu)
============================================

[What this session did]
  1. Root-caused «林佳淩 EMR 兩週都抓不到» — EMR system uses 林佳淩 (淩, 氵), our sheets/cathlab_keyin/schedule/工作流程.txt all use 林佳凌 (凌, 冫). JS `t.includes('林佳凌')` failed on `'林佳淩'` link text → fallback whitelist (doesn't include either) → no_visit for every patient of hers.
  2. Fixed in fetch_emr.py: NAME_ALIASES dict + variants loop in `_click_visit`. Validated by re-fetching 5/13 chart 08473654 (董相路) → matched `(門診)2026/04/24 林佳淩 心臟血管科07診`, returned 883-char EMR.
  3. Widened F/G columns to 160 px in `enforce_sheet_format` (gsheet_utils.py) per user request «讓 FG 欄寬益點 不然都看不到術前診斷還有預計心導管». Applied retroactively to 10 date sheets (5/11–5/22).
  4. Memory + index updated; CLAUDE.md fetch_emr.py entry mentions NAME_ALIASES.

[Current state]
  - Branch: main, in sync with origin/main pre-session
  - Local mods staged: fetch_emr.py (NAME_ALIASES), gsheet_utils.py (F/G width), CLAUDE.md (Key Files note), memory/MEMORY.md (+2), memory/feedback_doctor_name_variant_lin_jialing.md (new), memory/feedback_fg_column_width.md (new), memory/HANDOFF.md (this)
  - Date sheets touched: 20260511,12,13,14,17,18,19,20,21,22 — F/G now 160 px

[Next steps]
  - Optional: re-run `process_emr.py 20260513` to backfill 董相路 sub-table C with the proper EMR cell (currently has «無本院一年內主治醫師門診紀錄»). User didn't request — skip unless asked.
  - Watch for similar silent failures on other doctors; if one shows 0 visits across multiple JSONs, dump EMR link list for one of their charts and check for char variants → add to NAME_ALIASES (don't rewrite sheets/code).

[Known issues / blockers]
  - 無

[Don't repeat these mistakes]
  - DO NOT assume EMR uses the same Han character variant as the sheet. JS `.includes()` is byte-exact; 凌/淩, 鈞/鈞, 諭/諭, 翔/翔 are different code points. When EMR fetch returns 0 visits across multiple sessions for the same doctor → suspect char variant first, not «doctor has no recent OPD».
  - DO NOT rewrite all systems (cathlab_keyin / schedule / 工作流程.txt) to match EMR. The fix surface is `fetch_emr.py` NAME_ALIASES — one place, doesn't disturb user-facing materials.
  - DO NOT skip running `enforce_sheet_format(date)` after sheet edits — it now also enforces F/G widths.

[Relevant files]
  - fetch_emr.py (NAME_ALIASES added)
  - gsheet_utils.py (F/G col width in enforce_sheet_format)
  - CLAUDE.md (Key Files entry updated)

[Important memory files]
  - feedback_doctor_name_variant_lin_jialing.md (new — char variant SOP)
  - feedback_fg_column_width.md (new — F/G 160 px rule)
