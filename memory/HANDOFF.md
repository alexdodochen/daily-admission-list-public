============================================
  交班文件 — Last Updated: 2026-04-24 evening
============================================

【本次 session 做了什麼】
  1. 20260426 入院清單 diff 更新（5 人，+3 新增 -1 取消 -2 保留）
     - 取消: 梁百煜（詹世鴻）
     - 保留（含 EMR/F/G）: 鄭沈盈（劉）、黃彭玉娥（廖）
     - 新增: 陳云英（詹）、王陳玉英（張獻元）、黃秋煌（黃睦翔）
  2. 3 位新病人跑 EMR + process_emr auto-detect F/G
     - 陳云英 AS / Left heart cath.（詹 04/02 門診）
     - 王陳玉英 **無門診 + fallback 空 = 無資料**（F/G 使用者手動 PAOD / PTA for FG）
     - 黃秋煌 CHF / Left heart cath. → 使用者改 G=空、H=TTEER
  3. N-V 入院序：使用者指定 1=鄭沈盈 2=黃秋煌（手動），3-5 round-robin（陳云英/黃彭玉娥 時段前、王陳玉英 非時段後）
  4. V 欄延後標記：
     - 黃秋煌 V=20260428（改 Tue，使用者手動排 4/28）
     - 王陳玉英 V=20260429（改 Wed 張獻元時段，使用者手動排 4/29 PM）
  5. 4/27 Mon cathlab keyin（cathlab_keyin_0427.py）
     - 3 人 WEBCVIS 早已 pre-keyed → ADD SKIP 全部、UPT 只補 F/G pdijson/phcjson（照 `feedback_webcvis_preserve_existing_slot.md`）
     - verify_cathlab.py 20260426 → 3 OK / 0 MISSING / 2 SKIP（V 標記的兩位）
  6. **新增 memory `reference_lottery_by_weekday.md`** — 各日（Mon/Tue/Wed/Thu/Fri）時段醫師清單，lottery 時對照用，以後不要靠 schedule_readable.txt 猜
     - 觸發原因：本 session 我把張獻元/劉嚴文誤當 Mon 時段醫師，使用者糾正並明確要求「記在 memory 對著抽」
     - 權威來源：Google Sheet 工作表 `主治醫師抽籤表`

【當前狀態】
  - Branch: main
  - 20260426 sheet 完整（主資料 5 人 + N-V 入院序 + 5 子表格 + V 延後 2 筆）
  - 20260427 WEBCVIS: 3 人 F/G 補完
  - 20260428 / 20260429: 使用者自行手動 WEBCVIS keyin（V 已標記 skip 自動化）
  - Memory index 已更新

【下一步該做什麼】
  - 使用者手動 4/28 黃秋煌（黃睦翔 PM C2）、4/29 王陳玉英（張獻元 Wed PM C2 or H2）
  - 若 user 授權，修 2 個過時 SKILL.md（HANDOFF 4/23 也提過，未動）：
    1. admission-lottery — xlsx/openpyxl 整份改 gspread、續等清單已下線、加 *2 直讀 sheet、加詹週五非時段、加 五→五 規則、**加 reference_lottery_by_weekday.md 引用**
    2. admission-ordering — N-S 6 col → N-V 9 col、續等段落刪、補詹週五非時段 + 五→五

【已知問題 / 卡關】
  - 無；verify_cathlab 通過

【不要重蹈覆轍】
  - **Lottery 時段醫師一定要查 `主治醫師抽籤表` 或 `reference_lottery_by_weekday.md` memory，不要看 `schedule_readable.txt` 自己猜**。兩表用途不同：抽籤表權威 lottery、時段表查 cathlab 房間。
  - Diff-update 前先讀既有 sheet → 用病歷號 diff → 保留 EMR/F/G
  - WEBCVIS ADD SKIP 後只做 F/G UPT，不要改 examroom/time/doctor

【相關檔案（本 session 產出）】
  - `cathlab_keyin_0427.py`（latest template）
  - `_update_0426.py` / `_ordering_0426.py`（ephemeral）
  - `_cathlab_keyin_0427.log` / `_verify_cathlab_20260426.txt`
  - `emr_data_20260426.json`
  - `memory/reference_lottery_by_weekday.md`（新）
