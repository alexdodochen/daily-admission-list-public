---
name: admission-lottery
description: Use when performing daily admission doctor lottery (抽籤). Triggered when user says "抽籤", "排序", "排入院順序", "抽住院籤". Reads 主治醫師抽籤表 → 隨機抽籤決定醫師順序 → 建子表格（A-G 7 欄）。Google Sheets only (gspread, no xlsx). 抽籤完接 admission-emr-extraction → admission-ordering。
---

# 每日入院主治醫師抽籤

## Overview
依據隔天門診抽籤表隨機抽籤，決定主治醫師入院優先順序，並在日期 sheet 主資料下方建立各醫師子表格。Round-robin 寫入 N-V 由 `admission-ordering` 處理（抽籤本身只決定醫師順序＋建空殼子表格）。

## 前置條件
日期 sheet `YYYYMMDD` 主資料 A-L 已寫好（由 `admission-image-to-excel` 完成）。

## 日期 → 隔天門診對應（抽籤表 col 順位）

| 入院日 | 抽籤依據 | 抽籤表欄 | 特例 |
|---|---|---|---|
| 日 | 隔日週一 | A (col 1) | |
| 一 | 隔日週二 | B (col 2) | |
| 二 | 隔日週三 | C (col 3) | 張獻元週三入院 → 同日 PM |
| 三 | 隔日週四 | D (col 4) | |
| 四 | 隔日週五 | E (col 5) | |
| 五 | **當日週五**（週六無抽籤表） | E (col 5) | **詹世鴻週五 = 非時段醫師**（CLAUDE.md rule #16） |
| 六 | 無（通常無入院） | — | |

（每天續等清單已於 2026-04-19 下線，不要再使用該 sheet。）

## 流程

### 1. 讀抽籤表

直接 gspread 讀 `主治醫師抽籤表` 對應星期欄：

```python
from gsheet_utils import get_spreadsheet

DATE = '20260424'  # 週五
COL_IDX = 5        # E 欄（週五）

sh = get_spreadsheet()
lottery_ws = sh.worksheet('主治醫師抽籤表')
col_values = lottery_ws.col_values(COL_IDX)  # row 1 = header「週五」, row 2+ = 醫師名

pool = []
for v in col_values[1:]:
    v = str(v or '').strip()
    if not v:
        continue
    # *2 後綴 = 2 支籤；同名重複列 = 累加；純名字 = 1 支
    name = v.replace('*2', '').strip()
    count = 2 if '*2' in v else 1
    pool.extend([name] * count)
```

**重要**：絕不靠口述/記憶重建抽籤表，永遠直接讀 sheet（見 `feedback_lottery_read_full_column.md`）。離線交叉驗證可參考 `reference_lottery_by_weekday.md`（各日時段醫師清單 snapshot），但 lottery 本身仍以 sheet 直讀為準。**絕對不要查 `schedule_readable.txt` — 那是 cathlab 房間/時段表，不是抽籤表**（見 `feedback_two_doctor_sheets.md`）。

### 2. 比對當日醫師 + 篩有時段

從主資料 D 欄（主治醫師）抓出當日所有醫師：

```python
ws = sh.worksheet(DATE)
data = ws.get_all_values()
admit_doctors = set()
for r in data[1:]:
    if r[3].strip():  # D 欄
        admit_doctors.add(r[3].strip())
```

對每位 `admit_doctors` 中的醫師：
- 若在 `pool` 中 → 進主 round-robin
- 若不在 `pool` 中 → 該醫師是**非時段醫師**，排在主 round-robin 最後（不丟掉，不進「續等」——續等已下線）

### 3. 詹世鴻週五特例（CLAUDE.md rule #16）

週五入院時：
- 若入院名單中有詹世鴻 → **強制視為非時段醫師**，從 pool 中移除（即使他在抽籤表中）
- 排在主 round-robin 之後（與其他非時段醫師同一段）
- cathlab 也走非時段（H1 2100+, note="本日無時段"）

```python
if weekday_of_admission == 4:  # 週五
    pool = [d for d in pool if d != '詹世鴻']
    # 詹世鴻仍會在 admit_doctors，自動成為非時段醫師
```

### 4. 抽籤

```python
import random

random.shuffle(pool)
seen = set()
order = []  # 醫師抽籤順序（去重，保留首次出現）
for t in pool:
    if t in admit_doctors and t not in seen:
        seen.add(t)
        order.append(t)

# 非時段醫師（不在 pool 但在 admit_doctors）接後面
non_slot = [d for d in admit_doctors if d not in seen]
order.extend(non_slot)
```

### 5. 建子表格（A-H 8 欄）

每位 `order` 中的醫師都建一個 block，寫入主資料下方：

```python
from gsheet_utils import write_doctor_table

# write_doctor_table 會處理：
# - 標題列「醫師（N人）」合併 A-H + 淺藍底
# - 子 header「姓名 病歷號 EMR EMR摘要 手動設定入院序 術前診斷 預計心導管 註記」+ 淺藍底
# - 病人資料行白底（C/D/E/F/G/H 欄留空待 EMR/Gemini/ordering 填）
# - block 之間 ≥ 2 列空白 + 顯式刷白底（避免 duplicate sheet 殘留藍底透出）
# 詳見 feedback_post_edit_format_check.md
```

子表格 8 欄定義：

| 欄 | 內容 | 階段填入 |
|---|---|---|
| A | 病人姓名 | 抽籤（從主資料 F） |
| B | 病歷號 | 抽籤（從主資料 I，TEXT 格式保前導 0） |
| C | EMR 原文 | EMR extraction（raw text） |
| D | EMR摘要 | **placeholder** — 留空白；使用者按需 call Gemini 才填，process_emr 不主動寫 |
| E | 手動設定入院序 | ordering |
| F | 術前診斷 | EMR auto-prefill → user 審核 |
| G | 預計心導管 | EMR auto-prefill → user 審核 |
| H | 註記（如「無資料病人」「張倉惟」「不用排檢查」） | EMR / 手動 |

### 6. 不寫 N-V

抽籤階段**不**寫 N-V。N-V 由 `admission-ordering` 在 EMR/F/G 確認後寫入（避免病人順序未定就先佔位）。

### 7. Post-edit format check（CLAUDE.md rule #17）

寫完後讀回驗證：
- 主資料 A-L 原地未動
- 子表格 title「X（N人）」+ 人數 + ≥2 列空白隔行 + 無殘留合併
- 子表格 A/B 與主資料 F/I 一致（姓名 + 病歷號）
- 病歷號保留前導 0（B 欄需 TEXT 格式）

跑掉就當場修，不留尾巴給使用者。

## 最小範本

```python
import random, time
from gsheet_utils import get_spreadsheet, get_worksheet, write_doctor_table

DATE = '20260424'
COL_IDX = 5  # 週五
WEEKDAY = 4  # 0=Mon...4=Fri

sh = get_spreadsheet()

# 1. 讀抽籤表
lottery_ws = sh.worksheet('主治醫師抽籤表')
pool_raw = [str(v or '').strip() for v in lottery_ws.col_values(COL_IDX)[1:] if v]
pool = []
for v in pool_raw:
    name = v.replace('*2', '').strip()
    pool.extend([name] * (2 if '*2' in v else 1))

# 2. 詹週五特例
if WEEKDAY == 4:
    pool = [d for d in pool if d != '詹世鴻']

# 3. 讀當日醫師 + 病人
ws = get_worksheet(DATE)
data = ws.get_all_values()
patients_by_doc = {}
for r in data[1:]:
    if not r[3].strip():
        continue
    doc = r[3].strip()
    patients_by_doc.setdefault(doc, []).append({
        'name': r[5].strip(),       # F
        'chart_no': r[8].strip(),   # I
    })

admit_doctors = set(patients_by_doc.keys())

# 4. 抽籤
random.shuffle(pool)
seen, order = set(), []
for t in pool:
    if t in admit_doctors and t not in seen:
        seen.add(t)
        order.append(t)
order.extend([d for d in admit_doctors if d not in seen])  # 非時段接後

# 5. 建子表格（依 order，每個 block 用 write_doctor_table）
N = len(data)  # 主資料總列數
cur_row = N + 3  # 主資料下方空 2 行
for doc in order:
    pts = patients_by_doc[doc]
    write_doctor_table(ws, cur_row, doc, pts)  # 內含 ≥2 列空白 gap
    cur_row += 2 + len(pts) + 2
    time.sleep(0.5)

print('抽籤順序：', ' → '.join(order))
```

## 注意事項
- 所有 gspread 呼叫之間加 `time.sleep(0.3-1)` 避免 rate limit
- **絕不覆蓋主資料 A-L**
- 抽籤完顯示順序給使用者確認後，直接接 `admission-emr-extraction`
- 不要自己觸發外部推播 endpoint（即使在私有環境）— 改 code OK，自動觸發禁止
- 已成文規則（如詹週五非時段、五→五、*2 抽籤）不要反覆問使用者，直接套用（`feedback_no_reconfirm_workflow.md`）
