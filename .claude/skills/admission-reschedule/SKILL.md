---
name: admission-reschedule
description: Use when a patient's admission date needs to change. Triggered by "改期", "幫我處理改期", "X月X日的改期", "病人改到另一天", or after user fills W 欄 (改期) in a date sheet with a target YYYYMMDD. Handles three stages — Sheet migration (reschedule_patients.py), WEBCVIS DEL sync on source cathlab date (reschedule_webcvis.py), and ADD sync on target cathlab dates (reschedule_add.py).
---

# 病人改期（Admission Reschedule）

## Overview

當病人入院日需要調整時，使用者在**來源日 sheet** 的 **W 欄（改期）** 填入目標日期 YYYYMMDD，然後由此 skill 負責把病人完整搬到目標日 sheet，並同步刪除 WEBCVIS 上來源日的導管排程。

來源日的 row **保留不刪**，只把 W 欄改為「已改期至 YYYYMMDD」作為痕跡。

## When to Use

- 使用者說「幫我處理 YYYYMMDD 的改期」「改期的都處理好」
- 使用者說「改期的 WEBCVIS 也同步」「源日導管幫我刪」
- 使用者已經在某日 sheet 的 W 欄填好目標日期並要求搬運

## 前提條件

1. **來源日 sheet** 的 W 欄已填入目標日期（YYYYMMDD，8 碼）
   - 未填 / 已是「已改期至...」的 row 會被跳過
2. **目標日 sheet 不存在時會自動建立**
   - 以最近一份 YYYYMMDD sheet 為格式範本 (`duplicateSheet` + `unmergeCells` + `batch_clear`)
   - 只保留 row 1 header（A-L + N-W），sub-table 全部清空
   - 之後搬入流程會建對應醫師的 sub-table
3. 目標日 sheet 可以有部分已排好的內容（主資料、sub-table、N-V 入院序），搬入時會 append 不覆蓋

## 三階段流程

### 階段一：Sheet 搬運（reschedule_patients.py）

```bash
python reschedule_patients.py <source_date>
```

對每位有填 W 欄的病人：
1. 由 S 欄（病歷號）對回主表 A-L → 完整複製 A-L 到目標日主表末
2. 由醫師子表格（sub-table）以病歷號找到該列 → 複製 A-H（姓名/病歷號/EMR/EMR摘要/順序/F/G/註記）
3. 目標日找對應醫師 sub-table：
   - **有** → 用 `insert_rows(inherit_from_before=True)` 塞到該醫師病人區尾，同步把「X人）」計數 +1
   - **無** → 用 `write_doctor_table()` 在最後一個 sub-table 之後新增完整模塊
4. 目標日 W1 若無「改期」header → 補寫
5. 來源日 W 欄改為「已改期至 YYYYMMDD」標記（row 不刪）
6. 執行結果寫到 `_reschedule_result.txt`

**注意**：
- **不會自動重跑目標日的 N-V 入院序** — user 必須手動到目標日說「自動生成入院序」
- 來源日的 N-V 入院序也不動（row 保留給使用者對照痕跡）
- 若病人不在主表 → 報錯並 skip 該筆
- 若病人在主表但不在 sub-table → 用 main_data 建最小 sub_row（後續欄位空白）

### 階段二：WEBCVIS 源日 DEL（reschedule_webcvis.py）

```bash
# 互動式（每筆停下讓你按 Enter 確認）
python reschedule_webcvis.py <source_date>

# 非互動 / 已先 dry-run 驗證過，要一次跑完
python reschedule_webcvis.py <source_date> --yes

# 只驗證 pattern，不送出
python reschedule_webcvis.py <source_date> --dry-run
python reschedule_webcvis.py <source_date> --first
```

流程：
1. 讀來源日 sheet 的 W 欄，找「已改期至 YYYYMMDD」標記（表示階段一已完成）
2. 登入 WEBCVIS，`page.on("dialog", accept)` 先掛確認彈窗處理
3. 查詢來源日對應的 cathlab 日（平日 N+1，星期五同日）
4. 對每位病人：
   - 點 row 載入表單 → 讀當前欄位秀給 user
   - **勾選該 row 的 `<input name="chk">` checkbox**（觸發 `checkedShowButton()` 自動 enable `#deleteButton`）
   - 按 Enter 確認（或 `--yes` 自動）
   - `page.click('#deleteButton')` → `deleteMsg()` confirm() 自動被接受 → 送出 DEL
   - 重新 QRY 驗證該病人已消失
5. 執行結果寫到 `_reschedule_webcvis_<date>.log`

**重要 DEL 技術細節**：不能直接 `form.submit()` with `buttonName="DEL"`，server 是靠 row checkbox `chk` 的勾選狀態決定要刪哪筆（這條曾踩雷過，見 `feedback_cathlab_keyin_flow.md`）。

### 階段三：WEBCVIS 目標日 ADD（reschedule_add.py）

```bash
python reschedule_add.py
```

流程：
1. 腳本開頭的 `PATIENTS` list 每筆帶**自己的 `cathlab_date`**（因為 3 位病人改到不同天 → 不同 cathlab 日）
2. 登入一次，`page.on("dialog", accept)`
3. Phase 1 ADD：逐筆 `set_date_and_query(cathlab_date)` → `add_patient` (fill patno → AJAX → date/time/room/doctor/pdijson/phcjson → `buttonName=ADD` submit)
4. Phase 2 UPT：逐筆 `set_date_and_query(cathlab_date)` → 點該 row → 重寫 pdijson/phcjson → `buttonName=UPT` submit
5. Verification：逐筆再 QRY 確認 chart 存在
6. 結果寫到 `_reschedule_add.log`

**要 key 的資料從哪取？** 嚴守 memory `feedback_subtable_is_source.md`：從**目標日 sheet 的主治醫師子表格**讀 F/G（術前診斷/預計心導管），不從 N-V 入院序。

**房間/時段怎麼定？**
1. 查 `schedule_readable.txt`，看該醫師在目標 cathlab 日那格有沒有名字
2. **格子有名字** → 走那間房的正常時段（AM 0600+ / PM 1800+）
3. **結構日** (如黃睦翔 Wed/Thu PM H2 結構) **仍然是正式時段**，照排不誤
4. **格子沒名字** → 走 H1 2100+ 非時段，note="本日無時段"
5. 第二醫師處理：多人並列時葉立浩優先 key attendingdoctor2，其餘放備註

## 參數

- `<source_date>`: 來源日工作表名（YYYYMMDD，如 `20260413`）
- `reschedule_webcvis.py --dry-run`: 只 print 動作不真正送出
- `reschedule_webcvis.py --first`: 只處理第一筆，用來驗證 DEL pattern
- `reschedule_webcvis.py --yes`: 跳過每筆 Enter 確認，非互動環境必加
- `reschedule_add.py`: 無參數，PATIENTS list 寫在腳本開頭（每位病人自帶 cathlab_date）

## Critical Rules

1. **來源 row 不刪**：只把 W 欄改為「已改期至 YYYYMMDD」，保留痕跡供使用者對照
2. **目標日不存在會自動建立**：以最近一份日期 sheet 為格式範本 (unmerge + clear)
3. **不自動重跑入院序**：階段一搬完後 N-V 不動，user 手動重跑 ordering
4. **DEL 預設互動確認**：正常情況一筆一筆 Enter；**已先 --dry-run 驗證過**才用 `--yes` 一次跑完
5. **DEL 一定要勾 chk checkbox**：直接 form submit with `buttonName=DEL` 無效。必須 `cb.checked=true; cb.onclick()` → `click('#deleteButton')`（見 `feedback_cathlab_keyin_flow.md` DEL 章節）
6. **ADD 資料以子表格為源**：讀目標日主治醫師子表格的 F/G，不讀 N-V 入院序
7. **結構日 = 正常時段**：`schedule_readable.txt` 格子有醫師名字就是有時段（括號註記如「結構」「齡」「寬」只是主題標示）
8. **sub-table 插入用 bottom-up**：同一目標日有多位不同醫師的病人時，從最下面的醫師區塊先處理，避免 row index shift
9. **idempotent**：重跑 reschedule_patients.py 會跳過已標記「已改期至...」的 row，不會重複搬

## 工作流定位

這不是 6 大主要步驟之一，而是一個**維護性 skill**，在入院序已經跑過、甚至 WEBCVIS 已 key 完之後，發現某病人需要改期時才用。

與其他 skill 的關係：
- 階段一搬完後 → 使用者手動觸發 `admission-ordering` 重跑目標日
- 階段二 DEL + 階段三 ADD 都由本 skill 自家腳本完成，不需要 `admission-cathlab-keyin`
- 若目標日正好是當日 cathlab keyin 排程時段，也可讓 ADD 併入正常的 `cathlab_keyin_MMDD.py`（兩條路都可行）
