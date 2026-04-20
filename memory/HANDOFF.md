============================================
  交班文件 — Last Updated: 2026-04-20 23:55
============================================

【本次 session 做了什麼】
  1. 20260421 入院序重抽（用 4/22 週三 cathlab schedule）— 最終籤池 8 支：詹*2/林/陳/張*2/黃/廖
  2. 訂正 主治醫師抽籤表：週四 柯呈諭+柯呈諭 → 柯呈諭*2（保留週一 黃鼎鈞）
  3. 抽籤表 G 欄加上使用規則說明 + A1 cell note
  4. 釐清 主治醫師抽籤表（抽籤用）vs 主治醫師導管時段表（cathlab key-in 用）分工
  5. 新增 memory：`feedback_lottery_read_full_column.md`、`feedback_two_doctor_sheets.md`
  6. CLAUDE.md 補上兩表分工說明

【當前狀態】
  - Branch / Worktree: claude/sharp-mendel-f118cc (clean 尚未推)
  - 部署/執行狀態: 20260421 N-V 已寫回 Sheet（最新抽籤：張獻元→陳儒逸→詹世鴻→廖瑀→黃睦翔）
  - 最新 commit: ca8e368 docs: 4/21 入院序 + LINE monthly quota memory

【下一步該做什麼】
  - 4/22 cathlab keyin 時用 `主治醫師導管時段表` 對照房間/時段（H1/H2/C1/C2 × AM/PM）
  - 若 user 授權，更新 admission-lottery SKILL.md：
    1. 去除 xlsx 與「續等清單」舊敘述（續等已於 2026-04-19 下線）
    2. 明示「直接讀 Google Sheet 主治醫師抽籤表工作表」
    3. 加上 duplicate-row 籤數規則與「先 dump 籤池讓 user 確認再抽」步驟

【已知問題 / 卡關】
  - 主治醫師抽籤表 週一 黃鼎鈞 在導管時段表圖上沒對應時段，是 user 額外加入；
    日後若別人對照會困惑，但這是 user 明確保留，不動。

【不要重蹈覆轍】
  - 抽籤絕不可靠使用者訊息重建籤池；一律 gspread 直讀 `主治醫師抽籤表` 該欄
  - `*2` 字面 = 2 支籤；同名重複列 = 累加（不是 dedupe）
  - 不要把導管時段表（H1/H2/C1/C2）當抽籤表來源
  - 本 session 連續三次抽錯都是因為沒去讀 sheet 而腦補

【相關檔案】
  - `.claude/worktrees/sharp-mendel-f118cc/CLAUDE.md`（新增兩表分工）
  - 工作表（遠端）：`主治醫師抽籤表` D7=柯呈諭*2, D10=空, G2:G13=規則說明

【重要 memory 檔】
  - `feedback_lottery_read_full_column.md`（新規則版）
  - `feedback_two_doctor_sheets.md`（新）
  - `MEMORY.md` 索引已更新
