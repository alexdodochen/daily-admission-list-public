---
name: admission-diff-update
description: Use when the user provides an updated admission list image for a date sheet that already exists. Triggered by "更新入院名單", "diff update", "新清單比對", or when given a screenshot for a date that has main data already. Diffs by 病歷號 → adds new / removes cancelled / preserves existing EMR/F/G/sub-tables/N-V. Replaces the manual hand-coded `_diff_update_MMDD.py` pattern.
---

# 入院名單 diff-update（已存在的日期 sheet）

## When to use

Triggered when使用者貼一張新版的入院名單截圖，且該日期 sheet（`YYYYMMDD`）**已經存在**且已有主資料/子表格/EMR。
**新建 sheet → 用 `admission-image-to-excel`，不用本 skill。**

## 核心原則

1. **病歷號是 primary key**（中文姓名院方可能截斷顯示，如「徐黃素」vs「徐黃素燕」— 信病歷號不信姓名）
2. **絕不覆蓋既有 EMR / F / G / N-V** — 保留病人資料，只動 diff
3. **diff = 三類**：
   - **保留**：兩邊都有 → 床號/年齡/入院提示等更新；EMR、F/G、N-V 順序不動
   - **新增**：圖片有、sheet 沒 → 加主資料 + 加子表格（空 EMR/F/G）→ 跑 EMR
   - **取消**：sheet 有、圖片沒 → 主資料整 row 清；對應子表格 row 清；N-V 重新編號

## 流程

### 1. 讀現有 sheet 主資料

```python
from gsheet_utils import get_worksheet
ws = get_worksheet('20260427')
data = ws.get_all_values()
existing = {}
for i, r in enumerate(data[1:], 2):  # row 2 起
    if not r[0]: break  # 主資料區結束
    chart = r[8].strip()
    if chart:
        existing[chart] = {'row': i, 'name': r[5], 'doctor': r[3]}
```

### 2. 從圖片抽病人清單

低解析度截圖**先 PIL zoom 3-6x**（見 `feedback_image_ocr_zoom.md`），再 Read 確認。圖片每 row：
- 實際住院日 / 開刀日 / 科別 / 主治醫師 / 主診斷
- 姓名 / 性別 / 年齡 / 病歷號 / 病床號 / 入院提示

把這些資料整理成 `incoming = {chart: {...all fields}}`。

### 3. 三向比對

```python
incoming_charts = set(incoming.keys())
existing_charts = set(existing.keys())

to_keep    = incoming_charts & existing_charts
to_add     = incoming_charts - existing_charts
to_cancel  = existing_charts - incoming_charts
```

向使用者報告 diff（**還不要寫**），等同意：

```
變更摘要：
- 保留 N 人（更新床號/年齡/提示）：[名字...]
- 新增 N 人（需跑 EMR）：[名字...]
- 取消 N 人（清主資料+子表格+重編 N-V）：[名字...]
```

### 4. 一次 batch_write_cells 寫完

```python
from gsheet_utils import batch_write_cells

updates = []
# 保留：只動床號/年齡/入院提示
for chart in to_keep:
    row = existing[chart]['row']
    inc = incoming[chart]
    if inc['age']  != data[row-1][7]: updates.append((f'H{row}', inc['age']))
    if inc['bed']  != data[row-1][9]: updates.append((f'J{row}', inc['bed']))
    if inc['hint'] != data[row-1][10]: updates.append((f'K{row}', inc['hint']))
# 新增：appended rows
next_row = len([c for c in existing]) + 2
for chart in to_add:
    inc = incoming[chart]
    updates.append((f'A{next_row}:L{next_row}', [[
        inc['admit_date'], inc['op_date'], inc['dept'], inc['doctor'],
        inc['diag_code'], inc['name'], inc['gender'], inc['age'],
        chart, inc['bed'], inc['hint'], '',
    ]]))
    next_row += 1
# 取消：clear row + sub-table row
for chart in to_cancel:
    row = existing[chart]['row']
    updates.append((f'A{row}:L{row}', [['', ''] * 6]))

batch_write_cells(ws, updates, raw=True)
```

**重要**：病歷號（I 欄、子表格 B 欄）必須先設 TEXT format（保留前導 0），見 `feedback_chart_no_text_format.md`。

### 5. 子表格 diff

對每個有變動的醫師子表格：
- **保留病人**：原 row 不動（含 EMR/F/G/E）
- **新增病人**：appended，C/D/F/G/E 留空（之後 EMR step 自動補）
- **取消病人**：清 row + 重組（壓掉空白）；title 「醫師（N人）」更新人數

如果是**新醫師**（既有沒有，新增的人有）：在最後一個子表格之後加新 block（用 `write_doctor_table`）。

如果是**整個醫師都被取消**：清掉 title + header + patient rows + gap line，且**顯式刷白底**（避免殘留藍底，見 `feedback_post_edit_format_check.md`）。

### 6. N-V 入院序

如果有 to_add 或 to_cancel：
- 提示使用者新的醫師順序＋每醫師內部順序
- 重跑 round-robin（見 `admission-ordering`）
- 整段 N2:V{N+1} clear 後重寫

如果只是 to_keep（只動床號/年齡）：N-V 不動。

### 7. EMR for to_add patients

只對新增病人跑 EMR：
```bash
python fetch_emr.py "<session_url>" emr_data_<DATE>_diff.json <chart1> <doctor1> <chart2> <doctor2> ...
python process_emr.py <DATE>  # 會跳過 sub-table 已有 EMR 的 row
```

### 8. Post-edit format check（CLAUDE.md rule #17）

讀回驗證：
- 主資料 A-L 完整、to_cancel rows 已清
- 子表格 title 人數正確、無殘留藍底
- N-V 序號連續、病歷號保留前導 0
- I 欄 / S 欄 / B 欄（子表格）三處病歷號一致

跑掉就當場修。

## 最小範本

見 `_diff_update_0427.py`（4/27 session 範例：3 保留更新 + 1 新增 + 1 取消）。實作差別：
- 用 `batch_write_cells` 一次 push 所有單元格 update
- TEXT format 用 `batch_update_requests` 一次 push 多個 range

## 注意事項

- **絕對不要把姓名當 PK** — 院方截圖會截斷（如徐黃素燕→徐黃素），病歷號才是唯一識別
- **取消的病人不只動主資料** — 子表格、N-V 都要連動清乾淨
- **新醫師加入時記得用 `write_doctor_table`** — 它會處理 ≥2 列空白 gap + 顯式白底刷新
- **EMR 不重跑** — 既有 EMR 不動（節省 EMR session 時間 + 避免覆蓋使用者已審核的 F/G）
- 寫完一條龍跑（per `feedback_no_reconfirm_workflow.md`），不要每 phase 問「要繼續嗎」
