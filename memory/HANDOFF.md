============================================
  交班文件 — Last Updated: 2026-04-26 evening
============================================

【本次 session 做了什麼】
  1. 修兩個 skill (admission-lottery / admission-ordering)：補 reference_lottery_by_weekday.md
     引用 + 警告不要查 schedule_readable.txt（commit bcb9ca0）
  2. 補建 4/24 HANDOFF 漏建的 memory：reference_lottery_by_weekday.md（各日時段醫師 snapshot）
  3. 4/27 入院清單 diff-update：
     - 主資料 4 人：鄭/徐/李 補床號+年齡+1；row 5 黃秋煌(01433685) 整列換成 陳爽(04668242)
     - 黃睦翔 sub-table row 9: 黃秋煌 → 陳爽 CAD/Left heart cath.
     - 陳爽 EMR 院內無門診（fallback 也空）→ 使用者手動給 CAD/LHC
  4. 4/27 入院序 N-V 7 人 round-robin（陳儒逸 1, 黃睦翔 2, 張獻元 3 — 使用者語音指定順序，
     張獻元 sub-table 8人標題中目前實 3 人也加入）
  5. 4/28 cathlab keyin 陳爽 — WEBCVIS 已 pre-keyed → SKIP ADD + UPT 補 F/G
  6. **3 件 token/速度優化**（commit b2ccee2）：
     - cathlab_keyin.py 通用 driver（吃 cathlab_patients_*.json）取代每天 200 行手刻 keyin
     - gsheet_utils.batch_write_cells(updates) 一次 batch 多 cell write
     - .claude/skills/admission-diff-update.md 新 skill 封裝今天的 diff 流程
     預估同類 session token -75% / wall-time -60%
  7. 修 admission-cathlab-keyin skill：原本 body 是「404: Not Found」(stub 壞掉至少 2 週)，
     重寫接到新 cathlab_keyin.py 通用版
  8. CLAUDE.md / 每日入院清單工作流程.txt 同步更新

【當前狀態】
  - Branch: main, clean (即將 commit workflow-docs 變更)
  - 20260427 sheet 完整：主資料 4 人 + 5 子表格 + N-V 7 人 + V 改期 2 筆
  - 20260428 WEBCVIS: 9 charts (4 = 4/27 admit + 黃秋煌 V轉 + 3 張獻元 batch + 1 unknown)
  - 最新 commit: b2ccee2 feat: generic cathlab_keyin + batch_write_cells helper +
    admission-diff-update skill

【下一步該做什麼】
  - 4/28 黃秋煌 TTEER (使用者已手動 keyed)、4/29 王陳玉英 (張獻元 Wed PM C2 or H2，使用者手動)
  - 下次有截圖更新已存在 sheet → /admission-diff-update + 貼 image + EMR session URL，
    一條龍跑完
  - 下次 cathlab keyin → 寫 cathlab_patients_YYYYMMDD.json + python cathlab_keyin.py <json>，
    不要再複製舊 per-date keyin 腳本

【已知問題 / 卡關】
  - 張獻元 sub-table title 寫「8人」實 3 人，差 5 個 placeholder。本 session 入院序按實 3 人排，
    若使用者後續補進 5 人需重排 N-V

【不要重蹈覆轍】
  - **Lottery 時段醫師查 主治醫師抽籤表 / reference_lottery_by_weekday.md，不要看
    schedule_readable.txt（房間表，不同用途）**
  - **cathlab keyin 的 PDI/PHC ID 一律從 cathlab_id_maps.json 載**，硬編會猜錯
    （我踩過：SSS 寫成 PDI20090908120038 應為 PDI20090908120026；
    PTA 寫成 PHC20090907120010 應為 PHC20090907120007）
  - HANDOFF.md 寫「已建某 memory」務必驗證該檔真的存在（4/24 HANDOFF 寫了沒建）
  - 圖片病人姓名可能截斷顯示（徐黃素 vs 徐黃素燕）→ **病歷號才是 PK**
  - 圖片中的病人和 sheet row 5 醫師相同（都黃睦翔）但病歷號不同 = 不同病人，不要當成更新

【相關檔案（本 session 產出 / 修改）】
  - cathlab_keyin.py（新，通用 driver）
  - gsheet_utils.py（加 batch_write_cells）
  - .claude/skills/admission-diff-update.md（新）
  - .claude/skills/admission-cathlab-keyin.md（重寫，原本壞掉）
  - .claude/skills/admission-lottery.md / admission-ordering.md（加 reference 引用）
  - CLAUDE.md / 每日入院清單工作流程.txt（同步）

【重要 memory 檔（本 session 新增/更新）】
  - reference_lottery_by_weekday.md（4/24 漏建，補上）
  - feedback_cathlab_id_maps_only.md（新；ID 一律從 JSON 載）
  - project_session_optimizations_0426.md（新；3 件優化記錄）
  - MEMORY.md（更新索引）
