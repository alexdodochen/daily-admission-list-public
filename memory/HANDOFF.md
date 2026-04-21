============================================
  交班文件 — Last Updated: 2026-04-21 (session end)
============================================

【本次 session 做了什麼】
  1. 4/23 新清單匯入 + EMR 萃取（14 人，diff-update：1 刪 / 4 新 / 10 留）
  2. 4/22 重抽：廖瑀 當 黃鼎鈞*2 籤進主 round-robin（N-V 已重寫 9 列，S 欄 TEXT）
  3. 發現並修 write_doctor_table 白底跑掉根因（5 根因 postmortem）
  4. 4/22 驗證：張獻元 週三入院兩人原已在 4/22 PM CATH2 同日時段
  5. verify_cathlab.py 加「張獻元 週三入院 → 同日」規則；工作流程 txt 同步更新

【當前狀態】
  - Branch: main（3 檔 modified + 1 檔 untracked，尚未 commit）
  - 部署/執行狀態: 4/22 N-V 已定案、4/23 入院清單已匯入＋EMR 完成（F/G 待使用者審）
  - 最新 commit: ca8e368 docs: 4/21 入院序 + LINE monthly quota memory

【下一步該做什麼】
  - 使用者審 4/23 F/G → Claude 做 4/23 抽籤 + N-V 定案 + cathlab keyin（4/24 排程）
  - 若要繼續本 session 未完的 4/23 主 round-robin：星期五 pool = 劉嚴文/陳柏偉/陳儒逸/詹世鴻/李文煌/柯呈諭/鄭朝允/陳則瑋（各 1 籤）

【已知問題 / 卡關】
  - 4/22 邱鵬勳（備註檢查 CCTA）雖依規則 SKIP，但實際 WEBCVIS 有排 — 使用者自行決定是否手動刪

【不要重蹈覆轍】
  - S 欄（病歷號）寫入要用 updateCells + userEnteredValue.stringValue + numberFormat TEXT，不要用 ws.update() 配 USER_ENTERED（前導 0 會被吃）
  - 子表格 patient row 要顯式刷 WHITE bg + 2 列 gap + 空列清框（duplicateSheet 殘留會透）
  - 張獻元 週三入院病人 cathlab = 同日 PM，不要走 N+1（週四無時段）
  - 工作流跑完整條龍，不用每 phase 問使用者要不要繼續

【相關檔案】
  - gsheet_utils.py (write_doctor_table 白底+2列gap 修)
  - verify_cathlab.py (張獻元週三規則)
  - 每日入院清單工作流程.txt (張獻元週三病人規則)
  - memory/feedback_zhang_xianyuan_wed_same_day.md (新增)

【重要 memory 檔】
  - memory/feedback_zhang_xianyuan_wed_same_day.md
