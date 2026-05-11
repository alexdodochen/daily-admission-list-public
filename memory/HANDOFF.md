============================================
  HANDOFF — Last Updated: 2026-05-11 (5/11 reschedule session)
============================================

[What this session did]
  1. 5/11 王玉珍 (17222056) 改 5/14 住院 + 5/15 cathlab：V mark 5/11 N=9, append 5/14 main row 4 + 陳儒逸 sub-table 第3人, cathlab ADD 5/15 C1 1100 (second=蘇奕嘉), cathlab DEL 5/12 0930
  2. User feedback: 改期流程太慢/太耗 token — 印整段 EMR (C 4339 chars + D 549 chars) 是純浪費；多次 update_cell 應合併
  3. 新 memory: feedback_reschedule_lean_mode.md — 單病人 reschedule 預設精簡模式

[Current state]
  - Branch: main, in sync with origin/main (尚未 push 本次變更)
  - 5/11 sheet: 王玉珍 row 10 V=20260514 (改期標記)
  - 5/14 sheet: 陳儒逸 sub-table 3 人 (林森政/陳謝秀英/王玉珍), main A-L 3 列
  - 5/15 WEBCVIS: xa-CATH1 0800 林森政, 0930 陳謝秀英, 1100 王玉珍 (新增)
  - 5/12 WEBCVIS: 王玉珍 0930 已 DEL
  - Format check (PostToolUse hook) passed on 5/11 + 5/14

[Next steps]
  - 5/12 cathlab keyin (Tue admission 5/11 → cath 5/12) 仍待跑 — 8 患者 (扣除 reschedule 出去的 王玉珍)
  - 留意 5/14 sheet 的 main+sub gap 是否需要插入 2 列空行（per feedback_main_to_subtable_two_blank_rows.md）；當前 main rows 2-4, sub-table title row 5（無 gap）→ 視 enforce_sheet_format 是否已補

[Known issues / blockers]
  - 無

[Don't repeat these mistakes]
  - 改期單病人不要印 sub-table C/D 整段 EMR/summary（>4000 字元純廢 token）。capture 進變數但不 print，只印長度。
  - 多個 update_cell 寫入應合併成單一 batch_write_cells（V mark + main row + sub-title + sub-row 一次寫入）
  - 工作前先確認 DNS / 網路：本 session 第一次 sheet 讀取 DNS fail，重試即通

[Relevant files]
  - 5/11 sheet (V mark row 10), 5/14 sheet (main row 4 + sub-table row 5/9), 5/15 WEBCVIS
  - memory/feedback_reschedule_lean_mode.md (新)
  - memory/MEMORY.md (索引更新)

[Important memory files]
  - feedback_reschedule_lean_mode.md (5/11 new — 單病人 reschedule 精簡模式)
