============================================
  交班文件 — Last Updated: 2026-05-04 18:02
============================================

【本次 session 做了什麼】（5/4 整天，超長 session）
  1. 5/5/5/6/5/7 三張 sheet 截圖 diff-update（+14 病人 + K/E 欄更新）
  2. EMR 抽取 16 位（含 2 名校正：吳莉雄→吳菊雄、宋香光→宋哲光）
  3. **8-col canonical revert (commit d55ae66)**：撤回 5/4 上午的 7-col migration（保留 D=EMR摘要 placeholder，process_emr 不主動寫，使用者要時 call Gemini 填）。動到 7 個 .py + 4 skill md + CLAUDE.md + 工作流程 txt + 4 個 memory 檔
  4. 5/5 lottery + ordering 寫 N-V 18 人；cathlab keyin 5 missing (歐黃江/蕭秀雲/楊三益/吳菊雄/許慶山) + verify 0 missing
  5. 5/6/5/7 cathlab verify → 4 ADD: 黃翠娟/陳秀里/宋哲光 + 胡川陵 5/7 LHC; 加 5/13 TAVI（推薦醫師=林佳凌）
  6. cathlab_keyin.py 補 ROOM_CODES「外科開刀房25房」→「xa-外科開刀房25房」(TAVI 用)

【當前狀態】
  - Branch: main, working tree dirty (3 個檔等 commit: cathlab_keyin.py + cathlab_patients_20260505.json + 即將寫的 HANDOFF.md)
  - 最新 commit (待推): d55ae66 (8-col revert)
  - WEBCVIS 排程已 keyin: 5/6 (24)、5/7 (14)、5/8 (9)、5/13 (1) — 全週 5/4-5/14 都 OK
  - 5 張 sheet 5/4-5/8 主資料 + 子表格 + EMR + N-V + cathlab 全部完成

【下一步該做什麼】
  - 等下一週 5/11+ 的入院清單截圖
  - 「memory 全英化 batch」（從 5/4 上午留下）仍待開新 task 做
  - public mirror sheet `1u2FZE6...` 5/3 真實病人 PHI 仍未清（從 5/1 留下）

【已知問題 / 卡關】
  - 5/4 上午 8→7 col migration 留下「過渡期文字」散在多份 memory（`feedback_admission_hint_to_subtable_note.md` 之類提到「G 欄」「左移」），等將來做 memory 英化 batch 時順便清掉
  - 5/13 TAVI 預設 attendingdoctor=柯呈諭（胡川陵主治）。若 TAVI 該由 結構/瓣膜 team 其他醫師主刀，使用者要 DEL/ADD 改

【不要重蹈覆轍】
  - **Sub-table 8-col canonical**（A=姓名 B=病歷號 C=EMR D=EMR摘要 E=手動序 F=術前 G=預計 H=註記）。所有 code/skills/docs 都對齊。看到 7-col 假設（r[:7] / A:G / D=手動序）的字串 = 5/4 上午過渡死碼，立刻改回
  - **D=EMR摘要 placeholder 不主動寫** — process_emr 寫 C/F/G。使用者「我以後需要的時候會呼叫 gemini 幫我做摘要」→ 一次一格 user 自己 call
  - **diff-update sub-table 只動 ADD/DELETE row**（既有 row 完全不碰）— `feedback_diff_update_subtable_minimal.md`。5/4 整塊 clear+rewrite 連 EMR 都洗掉是反面教材
  - **gspread RAW**（不是 USER_ENTERED）寫 chart_no 保前導 0
  - **diff-update 前先 unmerge A2:V80** 再 clear（merged sub-table title 會吃寫入）
  - **verify_cathlab.py 不能盲信** — 對 8-col sheet 的 NG 結果要套 SKIP_KEYWORDS + 張獻元規則手動重判，原 verify 用 `r[:7]` 切掉 H 那 bug 已修但若再有 layout 偏移要重新檢查
  - **cathlab ADD 前必跑 week-scan**（CLAUDE.md rule #19）— Mon-Fri 5 天查 chart 有無重複，已存在 → STOP 不自動 ADD
  - 圖→Sheet→sub-table→EMR auto；lottery / ordering / cathlab 等命令（feedback_no_auto_lottery.md）

【相關檔案】
  - 程式碼：cathlab_keyin.py (ROOM_CODES 加「外科開刀房25房」)、其他 5 .py + 1 .js 都已在 d55ae66 反轉
  - JSON：cathlab_patients_20260505.json (重寫成 5 missing 那版)
  - scratch（將清）：`_diff_update_week.py`, `_run_emr_8col.py`, `_ordering_20260505.py`, `_week_scan_*.py`, `_cathlab_more_keyin.json`, `_cathlab_tavi_keyin.json`, `_*.log`, `_verify_cathlab_2026050[4-7].txt`

【重要 memory 檔（本 session 新增/更新/刪除）】
  - feedback_no_emr_summary.md（重寫：8-col canonical + D placeholder + 反轉 7-col migration history）
  - feedback_subtable_H_to_R_ordering.md（G→H 退回原 H）
  - feedback_diff_update_subtable_minimal.md（新：diff-update minimal 規則）
  - feedback_verify_cathlab_8col_broken.md（刪：obsolete after revert）
  - MEMORY.md（索引同步反轉）
