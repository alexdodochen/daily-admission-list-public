---
name: admission-ordering
description: Use when assigning patient admission order (排住院序) for a specific date's admission list. Triggered when user says "排住院序", "排入院序", "設定入院順序", "生成入院序列", or after EMR extraction completes. Reads sub-tables, asks user for multi-patient order, writes E column + N-V round-robin. Google Sheets only (no xlsx).
---

# 排住院序（入院順序確認）

## Overview
根據抽籤結果（醫師順序）+ 使用者決定的醫師內部順序，寫入 N-V 入院序列（9 欄）+ 子表格 E 欄「手動設定入院序」。

## 前置條件

進入本 skill 之前，同日 Google Sheet `YYYYMMDD` 應該已具備：
- 主資料 A-L（A-L 12 欄 × N 人）
- 子表格（各醫師 8 欄 A-H × 病人數，含姓名、病歷號、EMR、EMR摘要、手動設定入院序、術前診斷、預計心導管、註記）
- F/G（術前診斷、預計心導管）已由 EMR 預填並經使用者審核

若 N-V 空且子表格也空 → 回到 `admission-lottery` 先抽籤建子表格。
若主資料存在但抽籤未做 → `admission-lottery` 要先跑。

## 日期 → 隔天門診對應（抽籤表 col 順位）

| 入院日 | 抽籤/cathlab 依據 | 抽籤表欄 | 特例 |
|---|---|---|---|
| 日 | 隔日週一 | A (col 1) | |
| 一 | 隔日週二 | B (col 2) | |
| 二 | 隔日週三 | C (col 3) | 張獻元週三入院 → 同日 PM |
| 三 | 隔日週四 | D (col 4) | |
| 四 | 隔日週五 | E (col 5) | |
| 五 | **當日週五**（週六無抽籤表） | E (col 5) | **詹世鴻週五 = 非時段醫師** |
| 六 | 無（通常無入院） | — | |

## 流程

### 1. 讀取資料

```python
from gsheet_utils import get_worksheet

ws = get_worksheet('20260424')
data = ws.get_all_values()

# 主資料 A-L: data[1:N] (row 2 起，header 是 row 1)
# N-V 序列: data[i][13:22] (N=13, V=21)
# 子表格: 掃描 A 欄尋找「醫師名（N人）」模式
```

### 2. 核對抽籤表醫師名單

直接 gspread 讀 `主治醫師抽籤表` 對應星期欄（見上表）：
- `*2` 後綴 = 2 支籤
- 同名重複列 = 累加
- 純名字 = 1 支

離線交叉驗證可參考 `reference_lottery_by_weekday.md`（各日時段醫師清單 snapshot）。**不要查 `schedule_readable.txt`**（那是 cathlab 房間表，不是抽籤表）。

若 round-robin 醫師不在抽籤表 → 該醫師應該在 lottery 階段就被排除，不該到 ordering。若出現 → 停下警示使用者，不要自動搬動。

**（續等清單已於 2026-04-19 下線，不要再寫入該 sheet。）**

### 3. 詹世鴻週五特例

週五入院時：
- 詹世鴻 **視為非時段醫師** → 不進主 round-robin，排在有時段醫師之後
- cathlab 排非時段（H1 2100+, note="本日無時段"）
- 兩邊一致

即使詹本人週五 AM C2 有時段，週五入院病人仍走此規則（CLAUDE.md rule #16）。

### 4. 詢問使用者多病人醫師順序

找出子表格中病人 ≥ 2 的醫師，列給使用者決定：

```
**{醫師名}（{N}人）：**
1. **{病人A}** ({病歷號}) — {EMR摘要首段}
2. **{病人B}** ({病歷號}) — {EMR摘要首段}
```

等使用者回覆才繼續寫。單病人醫師無需詢問。

### 5. 寫入子表格 E 欄 + N-V 9 欄

#### 5a. 子表格 E 欄（手動設定入院序）

掃描 A 欄找到每個醫師的 block，在 E 欄（col 5）填入使用者指定的順序（1, 2, 3...）。單病人醫師填 1 即可（或留空照舊習慣）。

#### 5b. N-V 9 欄 round-robin

Header (row 1)：

| 欄 | 內容 |
|---|---|
| N (14) | 序號 |
| O (15) | 主治醫師 |
| P (16) | 病人姓名 |
| Q (17) | 備註(住服) |
| R (18) | 備註 |
| S (19) | 病歷號 |
| T (20) | 術前診斷 |
| U (21) | 預計心導管 |
| V (22) | 改期 |

若 header 仍是舊版「每日續等清單」→ 寫 V1 = `改期`。

Round-robin 規則（**兩段獨立 round-robin，絕對不要把時段+非時段醫師混在一起 RR**）：

1. **時段組** (在當日 cathlab 抽籤池內的醫師) 彼此抽籤決定組內順序 → round-robin **排完所有時段組病人**
   - A1 → B1 → C1 → A2 → C2 → C3 ...（時段醫師之間真 RR，醫師用完就 skip）
2. **非時段組** (不在抽籤池) 彼此抽籤決定組內順序 → 接在時段組**之後**，自己再 round-robin
   - D1 → E1 → D2 ...（非時段醫師之間真 RR）

**範例（5/3 sheet, cathlab 5/4 Mon col A pool）：時段=黃鼎鈞(2)/廖瑀(1)/詹世鴻(3) 共 6 人，非時段=黃睦翔(1)/鄭朝允(1) 共 2 人**

✅ 正確（兩段 RR）：
```
1. 黃鼎鈞 - 徐豐淇   ┐
2. 廖瑀  - 陳薏安    │ 時段組 RR
3. 詹世鴻 - 周明仁   │ (6 人)
4. 黃鼎鈞 - 吳宇豪   │
5. 詹世鴻 - 謝添福   │
6. 詹世鴻 - 吳峰欽   ┘
7. 黃睦翔 - 劉廖寶蓮 ┐ 非時段組 RR
8. 鄭朝允 - 陳吉忠   ┘ (2 人)
```

❌ 錯誤（5 醫師全部一起 RR，把非時段插在時段中間）：
```
1. 黃鼎鈞 - 徐豐淇
2. 廖瑀  - 陳薏安
3. 詹世鴻 - 周明仁
4. 黃睦翔 - 劉廖寶蓮  ← 錯
5. 鄭朝允 - 陳吉忠     ← 錯
...
```

**組內醫師順序的 lottery（權威算法）**：

```python
import random
from gsheet_utils import get_spreadsheet
sh = get_spreadsheet()
lottery_ws = sh.worksheet('主治醫師抽籤表')
COL_IDX = weekday + 1  # 1=Mon, 2=Tue, ...

# Step 1: 建 weighted pool — *2 = 兩支籤 (出現 2 次)
pool = []
for v in lottery_ws.col_values(COL_IDX)[1:]:
    v = str(v or '').strip()
    if not v: continue
    name = v.replace('*2', '').strip()
    weight = 2 if '*2' in v else 1
    pool.extend([name] * weight)

# Step 2: 詹週五特例 — 週五入院時詹世鴻強制非時段
if weekday == 4:  # Friday
    pool = [d for d in pool if d != '詹世鴻']

# Step 3: random.shuffle + first-appear dedupe → lottery 順序
random.shuffle(pool)
seen, order = set(), []
for d in pool:
    if d not in seen: seen.add(d); order.append(d)

# Step 4: 分時段/非時段 (admit_doctors 從主資料 D 欄取)
slot_docs = [d for d in order if d in admit_doctors]
non_slot  = [d for d in admit_doctors if d not in pool]
random.shuffle(non_slot)  # 非時段組組內也要 random shuffle
final_doctor_order = slot_docs + non_slot
```

**重點規則：**
- `*2` 後綴 = 兩支籤（pool 中出現 2 次，shuffle 後早被抽中機率高）
- Sub-table 順序和 N-V lottery 是**獨立事件** — sub-table 只反映 rebuild 當下的 shuffle，N-V 排序時必須跑新的 `random.shuffle()`
- 不可拿 sub-table 內醫師出現順序當 N-V lottery 結果（**萬萬不可**，使用者明確糾正）

#### 5c. 欄位資料來源

| 欄 | 來源 |
|---|---|
| Q 備註(住服) | 主資料 K 欄（入院提示）中 住服相關 free text（如「住南投提早通知」「非導管床」） |
| R 備註 | **優先：子表格 H 欄『註記』**（如「12C可」「張倉惟 12C可」「王思翰 4/21無床延期」「Afib」「CTA for TAVI 可能住到5/1」「改周一住」）；H 為空才 fallback 到主資料 K 欄 parenthetical（如「(4/13無床延床)」） |
| S 病歷號 | 主資料 I 欄（**TEXT 格式寫入**，前導 0 不可丟） |
| T 術前診斷 | 子表格 F 欄 |
| U 預計心導管 | 子表格 G 欄 |
| V 改期 | 空白（使用者事後手動填 YYYYMMDD 表示延後） |

**重點：子表格 H 欄是使用者實際寫備註的地方** — 排住院序時 R 欄一定要從 H 欄移植，K 欄 paren 只是沒 H 時的退路。漏了這步會被使用者糾正。

```python
# Build chart -> H from sub-tables
chart_to_H = {}
for i, row in enumerate(data, 1):
    m = re.search(r'^(.+?)（(\d+)人）', (row+['']*8)[0])
    if m:
        n = int(m.group(2))
        for j in range(i+2, i+2+n):
            r = (data[j-1]+['']*8)[:8]
            if not any(r): break
            if r[1]: chart_to_H[r[1]] = r[7]  # B=chart, H=note

# When building each N-V row:
R = chart_to_H.get(chart, '').strip() or K_paren
```

### 6. S 欄 TEXT 格式（病歷號）

病歷號寫入前先把目標 range 設為 TEXT，避免前導 0 被 Google Sheets 吃掉：

```python
from gsheet_utils import batch_update_requests

batch_update_requests([{
    'repeatCell': {
        'range': {
            'sheetId': ws.id,
            'startRowIndex': 1, 'endRowIndex': 1 + N_patients,
            'startColumnIndex': 18, 'endColumnIndex': 19,  # S = col 19 (0-indexed 18)
        },
        'cell': {'userEnteredFormat': {'numberFormat': {'type': 'TEXT'}}},
        'fields': 'userEnteredFormat.numberFormat',
    }
}])
# 然後 write_range(ws, f'N2:V{N+1}', rows, raw=True)
```

見 `memory/feedback_chart_no_text_format.md`。

### 7. 取消住院處理

使用者告知某病人取消 → 從主資料 A-L、N-V、子表格全部清除；N-V 重新編號不留空。

### 8. Post-edit format check（必做，CLAUDE.md rule #17）

寫完後讀回驗證：
- 主資料 A-L（原地未動）
- N-V 每行完整、序號連續、病歷號有前導 0
- 子表格 title「X（N人）」+ 人數 + 空白隔行 + 無殘留合併
- S 欄病歷號與子表格 B 欄一致

跑掉就當場修。

## 最小範本（一次寫完）

```python
import time
from gsheet_utils import get_worksheet, get_spreadsheet, write_range, batch_update_requests

DATE = '20260424'
ws = get_worksheet(DATE)
sh = get_spreadsheet()

# 1. 修 V1 header（如需）
write_range(ws, 'V1', [['改期']], raw=True); time.sleep(0.4)

# 2. 子表格 E 欄（使用者指定順序）
for cell, val in [('E8','1'), ('E12','1'), ('E13','2')]:
    write_range(ws, cell, [[val]], raw=True); time.sleep(0.4)

# 3. S 欄 TEXT 格式
batch_update_requests([{
    'repeatCell': {
        'range': {'sheetId': ws.id, 'startRowIndex': 1, 'endRowIndex': 1+N,
                  'startColumnIndex': 18, 'endColumnIndex': 19},
        'cell': {'userEnteredFormat': {'numberFormat': {'type': 'TEXT'}}},
        'fields': 'userEnteredFormat.numberFormat',
    }
}]); time.sleep(0.4)

# 4. N-V round-robin
rows = [
    ['1', '李文煌', '林裕興', '住南投提早通知', '',               '09719954', 'CAD', 'Left heart cath.', ''],
    ['2', '詹世鴻', '劉清和', '',               '(4/23無床延床)', '00123065', 'CAD', 'Left heart cath.', ''],
    ['3', '詹世鴻', '郭慶彰', '',               '(4/23無床延床)', '06538637', 'CAD', 'Left heart cath.', ''],
]
write_range(ws, f'N2:V{1+len(rows)}', rows, raw=True)

# 5. 驗證
data = ws.get_all_values()
for i in range(1, 1+len(rows)+1):
    print(i, data[i-1][13:22])
```

## 注意事項

- 所有 gspread 呼叫之間加 `time.sleep(0.3-1)`，避免 rate limit
- **絕不覆蓋主資料 A-L**
- 每次操作後顯示完整入院序表格供使用者確認
- 不要自己觸發外部推播 endpoint（即使在私有環境）— 改 code OK，自動觸發禁止
