============================================
  交班文件 — Last Updated: 2026-04-23 evening
============================================

【本次 session 做了什麼】
  1. 20260424（週五）入院序列 3 人（李文煌/林裕興、詹世鴻/劉清和、詹世鴻/郭慶彰）
     - 子表格 E 欄填好、N-V ordering 寫好、header V 改「改期」、S 欄 TEXT 格式
  2. verify_cathlab.py 20260424 跑 → 3/3 ALL CLEAR（cathlab keyin 由使用者手動完成）
  3. 釐清詹世鴻週五入院 = 非時段醫師 → 標準 H1 2100+（不是他 AM C2）
  4. 更新 feedback_no_reconfirm_workflow.md：已有成文規則時不要多問

【當前狀態】
  - Branch: main（剛 pull 過 origin/main，clean）
  - 部署/執行狀態: 20260424 入院序 N-V 已寫、cathlab 已 key（使用者手動）、verify 通過
  - 最新 commit (pre-sync): acfccc3 docs: 4/22 — 4/23 入院序排定 + 4/24 cathlab 驗證

【下一步該做什麼】
  - 若 user 授權，修 2 個過時 SKILL.md（HANDOFF 4/20 也提過）：
    1. admission-lottery — xlsx/openpyxl 整份改 gspread、續等清單已下線（2026-04-19）、定案 workflow 廢棄、加 *2 直讀 sheet、加詹週五非時段、加 五→五 規則
    2. admission-ordering — N-S 6 col → N-V 9 col、續等段落刪、補詹週五非時段 + 五→五
  - 4/27（一）或之後若有新入院清單 → 走標準流程

【已知問題 / 卡關】
  - 20260424 sheet 的 N-V header 舊版「每日續等清單」本次改為「改期」；其他未來 sheet 若由 rebuild_date_sheet.py 建好應已正確，遇到再改

【不要重蹈覆轍】
  - 不要把 "排 X 週五 PM 導管時間" 讀成「用他 AM C2 時段」→ 週五詹是非時段 = H1 2100+ note="本日無時段"
  - 非時段醫師 cathlab 一律 routine H1 2100+，不要反覆問「要排哪間」（CLAUDE.md rule #7）
  - 規則衝突（CLAUDE.md vs Sheet）才要請 user 裁決，其他照既定規則直接做

【相關檔案】
  - 20260424 sheet（Google Sheets 遠端）
  - memory/feedback_no_reconfirm_workflow.md（更新）

【重要 memory 檔】
  - memory/feedback_no_reconfirm_workflow.md（補充「已成文規則不要多問」）
