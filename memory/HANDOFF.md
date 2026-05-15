============================================
  HANDOFF — Last Updated: 2026-05-15 (Fri)
============================================

[What this session did]
  1. 5/18 diff-update — added 李全福 (05696379, 黃鼎鈞) as the only new patient vs existing sheet. Main row 6 insert + 黃鼎鈞 sub-table 王瑞香 後新增 row 28 + 標題 (2人)→(3人). Existing 9 patients (with EMR + manual order + F/G) untouched.
  2. Fetched + wrote 李全福 EMR (3602 chars, visit 2026/05/15 黃鼎鈞), F=AF / G=RF ablation (clinical judgment: AF s/p ablation 2019 + recurrent now Afib + LVEF 43.9% + Mon EP doctor).
  3. New rule absorbed: diff-update 新 patient → sub-table H="N" 標記. Applied to 李全福 H28=N.
  4. New rule absorbed: H column 加入 enforce_sheet_format 寬度規則 (160px). Re-applied to 10 sheets (5/11–5/22).
  5. Generalized rule: all locate/move/modify ops 一律先以病歷號定位 (was cross-sheet-only rule, now universal).

[Current state]
  - Branch: main, up-to-date with origin pre-session
  - Local modifications staged for commit: gsheet_utils.py (H col width), CLAUDE.md (diff-update note), memory/MEMORY.md (3 entries), memory/feedback_fg_column_width.md (F/G→F/G/H), memory/feedback_search_by_chart_no.md (universal), memory/feedback_diff_update_new_patient_N_marker.md (NEW), memory/feedback_fg_just_fill_user_will_check.md (NEW)
  - Sheets touched: 20260518 (李全福 add + EMR write), 20260511-20260522 (H col re-widened)

[Next steps]
  - 5/18 lottery + ordering (user trigger): «排住院序» when ready. 李全福 已備好 N 標記, F=AF, G=RF ablation.
  - 5/18 cathlab keyin: after ordering, «排導管». Mon+EP rule → 洪晨惠 second for any EP procedure.
  - Optional: F/G 李全福 是 Claude 判斷的, user 會 review — 若覺得不對請改子表格 F28/G28.

[Known issues / blockers]
  - 無

[Don't repeat these mistakes]
  - DO NOT compare full A-L row when diffing — chart no only (per session rule «比對病歷號就好»). Pulling EMR/F/G text into comparison wastes tokens.
  - DO NOT ask «要不要把 F/G 改成 X» for clinical judgment calls — just write best read, user re-checks before lottery (per feedback_fg_just_fill_user_will_check.md).
  - DO NOT forget H="N" on diff-inserted new patients — user scans H col for new ones during the week.
  - DO NOT use ws.batch_clear + rewrite for sub-table changes (PreToolUse hook blocks it) — use ws.insert_row for row-level INSERT, batch_write_cells for value updates.

[Relevant files]
  - gsheet_utils.py (col 8 added to F/G width rule)
  - CLAUDE.md (diff-update note → N marker)
  - emr_data_20260518.json (merged 10 charts now, includes 李全福)

[Important memory files]
  - feedback_diff_update_new_patient_N_marker.md (NEW)
  - feedback_fg_just_fill_user_will_check.md (NEW)
  - feedback_search_by_chart_no.md (broadened to universal rule)
  - feedback_fg_column_width.md (F/G → F/G/H)
