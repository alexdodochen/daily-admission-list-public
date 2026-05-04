============================================
  交班文件 — Last Updated: 2026-05-04 12:12
============================================

【本次 session 做了什麼】
  1. **5/5/5/6/5/7 三張 sheet 截圖 diff-update**：使用者貼 3 張 HIS 截圖，新增 14 位（5/5 +10、5/6 +3、5/7 +1）+ 既有病人 K 入院提示更新 + 5/5 13675145(吳昆山) E 主診斷 41400→4010。寫了 `_diff_update_week.py`（unmerge → clear → batch_update RAW + 8-col SUB_HEADER）一次處理。
  2. **EMR 抽取 16 位待抽**（5/5×12 + 5/6×3 + 5/7×1）：因 sub-table 是 8-col 而 process_emr.py 已 migrate 成 7-col 寫入會錯欄，自寫 `_run_emr_8col.py` 用 process_emr 的 detect_fg/parse_* helper + 自訂 8-col 寫入（C/F/G）。Playwright 一個 session 抓完 16 人；姓名校正 2 個（吳莉雄→吳菊雄 / 宋香光→宋哲光）；3 位 fallback / 無門診（方文忠/張連財/胡川陵）。
  3. 修 sheet 寫入兩個踩過的坑：
     - **merged sub-table title row 會吃掉新 main data 寫入** → `_diff_update_week.py` 先 unmergeCells A2:V80 再寫
     - **gspread USER_ENTERED 會把 leading-zero chart no parse 成 number 掉 0** → 用 `value_input_option='RAW'` 寫 main data + sub-table 內容
  4. memory 更新：`feedback_no_emr_summary.md` 加「5/5-5/7 例外」段（5/4 下午 diff-update 過的 3 張也維持 8-col）、`feedback_no_auto_lottery.md` 已被外部更新成「圖→sheet→sub-table→EMR 自動跑 / lottery+ordering+cathlab 等命令」分兩段的清晰版

【當前狀態】
  - Branch: main, working tree (除 HANDOFF + memory) clean
  - 最新遠端 commit: af37e43 (上 session)
  - 本 session 待 commit: feedback_no_emr_summary.md（加例外段）+ HANDOFF.md + scratch cleanup
  - 5/5/5/6/5/7 三張 sheet：主資料 + sub-table + EMR 都已寫入完成；leading-zero chart 已驗證保留

【下一步該做什麼】
  - 等使用者命令進下一階段（**抽籤 / 排住院序 / 導管排程**）— 不要主動接（feedback_no_auto_lottery.md）
  - 使用者需人工確認的點：
    1. **F=Unstable** 兩位（5/5 歐黃江 15806757 / 楊三益 15862766）detect_fg 截斷，要看 EMR 確認 Unstable angina vs 其他；楊三益 F=Unstable + G=PPM 組合不合理
    2. **3 位無門診** F/G 空白（方文忠 00182573 / 張連財 11750894 / 胡川陵 00317709）需依 indication 手填
    3. 5/5 吳菊雄(改名)用蔡惟全 fallback，F/G 不一定準
  - 「memory 全英化 batch」（上 session 留下的）仍待開新 task 做

【已知問題 / 卡關】
  - **8-col 例外清單**（不對齊 7-col canonical）：5/5/5/6/5/7 + 5/10-5/14 + 所有 5/3 之前 sheet。對這些 sheet 跑 ordering / verify / cathlab 時要當「舊 layout」處理（sub-table E=手動序、F=術前、G=預計、H=註記）。5/15 起新建 sheet 才用 7-col。
  - process_emr.py / generate_ordering.py / verify_cathlab.py 都是 7-col 假設 — 對 8-col sheet 直接跑會錯欄；要嘛複製 _run_emr_8col.py 模式手寫，要嘛幫這些 script 加 layout-detect fallback
  - public mirror sheet `1u2FZE6...` 5/3 真實病人 PHI 仍未清（從 5/1 留下）

【不要重蹈覆轍】
  - **diff-update 用 raw=True**（write_range / ws.batch_update value_input_option='RAW'）保住 chart 前導 0；USER_ENTERED 會壞
  - **diff-update 前先 unmerge A2:V80**：原 sheet sub-table title row 是 merge A:H，沒拆會把寫到那 row 的 main data 主要欄位吃掉
  - **8-col sheet 的 EMR 抽取不能跑 process_emr.main / refresh_emr.py**（會寫 E=diag/F=cath，但 8-col 那是 E=手動序/F=術前 → 整個錯位）。看到 8-col 例外日期就走 _run_emr_8col.py 模式
  - 圖→Sheet→sub-table→EMR 一條龍自動跑；lottery / ordering / cathlab 等命令（feedback_no_auto_lottery.md）

【相關檔案】
  - scratch（已清/將清）：`_diff_update_week.py`, `_diff_update_20260505.py`, `_run_emr_8col.py`, `_emr_combined.json`, `_emr_result_2026050[5-7].txt`, `_diff_*.log`, `_emr_run.log`
  - 永久（沒動）：`gsheet_utils.py`, `fetch_emr.py`, `process_emr.py`（仍是 7-col canonical，不要為了今天的 8-col 例外去 patch）
  - memory：`feedback_no_emr_summary.md` 加例外段；`feedback_no_auto_lottery.md`（外部已更新）

【重要 memory 檔（本 session 動到）】
  - feedback_no_emr_summary.md（更新：加 5/5-5/7 例外段，跟 5/10-5/14 平行）
