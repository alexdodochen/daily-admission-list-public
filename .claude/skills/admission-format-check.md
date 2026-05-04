---
name: admission-format-check
description: Use when user asks to check/fix/整理 formatting on date sheets (格式檢查, 格式修復, 整理格式, 檢查格式). Also invoke automatically after any write to date sheet to verify format. Validates main data A-L, N-V ordering, sub-tables, 2-row gaps, and chart number text format.
triggers:
  - "格式檢查"
  - "檢查格式"
  - "整理格式"
  - "格式修復"
  - "確保格式"
  - "整理[日期]的入院清單"
---

# admission-format-check

## Overview

Read-back verification + fix pass for any date sheet (e.g. `20260416`). Enforces the format rules stored in `memory/feedback_sheet_formatting.md` and `memory/feedback_post_edit_format_check.md`. Every write-script that touches a date sheet should invoke this skill at the end, and the user can invoke it directly to clean up any sheet.

## When to Use

- After any `admission-image-to-excel` / `admission-lottery` / `admission-emr-extraction` / `admission-ordering` / manual fix-up that writes to a date sheet.
- When the user says 「整理 4/19-23 的入院清單」/ 「格式檢查」/ 「確保整個工作表都符合我要求的格式」.
- After any cathlab reschedule or sub-table surgery.

## Rules (minimum bar)

### 1. Main data A-L (rows 2+)
- Row 1 header = 12 cols: `實際住院日 | 開刀日 | 科別 | 主治醫師 | 主診斷(ICD) | 姓名 | 性別 | 年齡 | 病歷號碼 | 病床號 | 入院提示 | 住急`
- Each patient row has A = `YYYY-MM-DD`, D (醫師), F (姓名), I (病歷號) non-empty
- Col I (病歷號碼) must be **text format** (`@`) so leading zeros are preserved

### 2. N-V ordering (if populated)
- Row 1 header = 9 cols: `序號 | 主治醫師 | 病人姓名 | 備註(住服) | 備註 | 病歷號 | 術前診斷 | 預計心導管 | 改期`
- 序號 connected 1..N, O (醫師) and P (姓名) non-empty for filled rows
- S (病歷號) **text format**

### 3. Sub-tables (each doctor block — post 5/4 7-col layout)
- Title row: `醫師名（N人）` merged A:G, blue header background, bold, left-align
- Sub-header row: `姓名 | 病歷號 | EMR | 手動設定入院序 | 術前診斷 | 預計心導管 | 註記`
- Patient rows: count must equal title's declared `N`
- Col B (病歷號) text format
- E/F cells have dropdowns from `下拉選單!A2:A66` / `下拉選單!D2:D23` (E=術前診斷, F=預計心導管)

### 4. Gaps (critical — user has corrected this multiple times)
- **Main data last row → first sub-table title: ≥ 2 blank rows**
- **Between every sub-table block: ≥ 2 blank rows** (not 1)

### 5. 藍底 / 白底 / 邊框 (critical — user has flagged this multiple times)
**每次叫你檢查格式時都必須把這段跑一次。不是「選擇性」的，是必跑項目。**

`BLUE = {red:0.741, green:0.843, blue:0.933}`, `WHITE = {red:1,green:1,blue:1}`

對於主資料以下（子表格區域）每一列：
- **title row** `X（N人）`: 合併 A:G（post 5/4 — 7 欄）、藍底、粗體、靠左、四邊細框
- **sub-header row** `姓名/病歷號/...`: 藍底、粗體、靠左、四邊細框
- **patient row**: 白底、不粗體、靠左、四邊細框、`wrapStrategy=WRAP`
- **blank row**: 白底、無邊框、無粗體（不能留「沒背景」的預設狀態）
- 主資料 row 1 header 也是藍底粗體；rows 2..main_end 白底加邊框

修復：用 `repeatCell` 把背景色/邊框/粗體/對齊一次刷上，並先對主資料以下區塊 `unmergeCells` 再重新 merge title rows，避免殘留合併吃掉資料。

### 6. No stray merges
- No merged range from a previous layout should be overlapping with a data row
- If a data row reads as empty when it should have a value, suspect a leftover merge above

### 6.5 EMR 必須跟著病人 row 一起搬（critical — 使用者多次回報）
**格式修復時絕不能只搬 A-B 欄而把 C 欄留在原位。** C (EMR 原文 + visit header) 是 row-level 資料。post 5/4 D 欄已改為「手動設定入院序」（普通字串，沒有 cell note），原 D=EMR摘要 已停用。

- 移 row **一律用 `insertDimension` / `deleteDimension` / `moveDimension`** — 原生 row op 會連同 values + format + cell notes 一起平移。
- **禁止** 讀值 → reshape in memory → 寫回的模式（絕對無法搬 notes）。
- `repeatCell` 修 format 時 fields 限定 `userEnteredFormat(...)`，**不得包含 `note`**。
- 寫入/修復**結束後必做對齊驗證**：用 chart number 當 key，確認每個 sub-table patient row：
  1. A 姓名 ↔ 主資料 F 姓名相符
  2. B 病歷號 ↔ 主資料 I 病歷號相符
  3. C 開頭 visit header 中醫師姓名 ↔ 該 row 所屬 sub-table 醫師（跨醫師誤置會被抓出來）
  不符 → 當場報 + 重抽該病人 EMR，不沉默。

### 6. Chart number consistency
- Same patient's 病歷號 in main I / sub B / N-V S must match (leading zeros preserved)

## Quick fix（首選）

```python
from gsheet_utils import enforce_sheet_format
enforce_sheet_format('20260428')  # idempotent
```

`enforce_sheet_format(sheet_name)` 會掃整個 sheet 結構，把：
- Row 1 + 子表格 title + 子表格 sub-header → BLUE 藍底/粗體/LEFT
- 主資料 row 2..end + 子表格 patient rows + 中間 gap rows → WHITE 白底/不粗體/LEFT
- 全部 LEFT 對齊

一次刷上。任何 diff / insertDimension / deleteDimension / write_range 動到 sheet 之後**收尾必呼叫一次**。比手寫 batch_update_requests 安全，且 idempotent（重複呼叫不會壞）。

`format_header_row(ws, row, num_cols)` 從 4/27 起也改成 LEFT 對齊（不再 CENTER）— 對應 memory `feedback_sheet_formatting.md` 的「全部 LEFT」規則。

## Workflow

1. **Read sheet** (`gsheet_utils.get_worksheet(sheet_name)`)
2. **Parse structure**:
   - Main data: col A scan from row 2, accept while A matches `^\d{4}-\d{2}-\d{2}$`
   - Sub-tables: after main_end, scan for rows where col A matches `^(.+)（(\d+)人）$`
   - For each sub, find sub-header (`姓名`) and patient rows until next blank-then-title or end
3. **Emit issue list** — check each rule above.
4. **Fix** (if auto-fixable):
   - **Gap < 2**: insert `2 - current_gap` blank rows BEFORE the title row (bottom-up so indexes stay valid). Use `insertDimension` with `inheritFromBefore: False`.
   - **Missing title row** (sub-header `姓名` appears without a `X（N人）` above): look up the doctor from main data D col using patient names, insert 3 blank rows before the sub-header, write the title at the topmost new row, merge A:G (post 5/4 — 7 cols), apply blue header format.
   - **Title-declared N ≠ actual patient count**: rewrite the title text with corrected count.
   - **Wrong N-V header** (old layout instead of current 9-col): rewrite row 1 of N:V.
   - **病歷號 not text format**: `repeatCell` with `numberFormat.type = TEXT` on col I / B / S.
5. **Verify** — re-read and re-check. If still failing, report to user.

## Python template

```python
import re
from gsheet_utils import get_worksheet, get_spreadsheet

def parse_structure(sheet_name):
    ws = get_worksheet(sheet_name)
    col_a = ws.col_values(1)
    main_end = 1
    i = 1
    while i < len(col_a):
        if re.match(r'^\d{4}-\d{2}-\d{2}$', col_a[i]):
            main_end = i + 1
            i += 1
        else:
            break
    subs = []
    j = main_end
    while j < len(col_a):
        v = col_a[j] if j < len(col_a) else ''
        m = re.match(r'^(.+)（(\d+)人）$', v)
        if m:
            doc, declared = m.group(1), int(m.group(2))
            title_row = j + 1
            k = j + 1  # sub-header expected
            # skip sub-header
            if k < len(col_a) and col_a[k] == '姓名':
                k += 1
            last = title_row
            while k < len(col_a):
                vv = col_a[k] if k < len(col_a) else ''
                if not vv or re.match(r'.+（\d+人）', vv):
                    break
                last = k + 1
                k += 1
            subs.append({'doc': doc, 'declared': declared,
                         'title_row': title_row, 'last_row': last,
                         'actual': last - title_row - 1})
            j = k
        elif v == '姓名':
            # missing title — mark as issue
            subs.append({'doc': 'MISSING', 'declared': None,
                         'title_row': None, 'subheader_row': j + 1,
                         'last_row': None})
            j += 1
        else:
            j += 1
    return main_end, subs

def check_gaps(main_end, subs):
    issues = []
    for i, s in enumerate(subs):
        title = s.get('title_row') or s.get('subheader_row')
        prev_last = main_end if i == 0 else subs[i-1]['last_row']
        if prev_last is None:
            continue
        gap = title - prev_last - 1
        need = 2 - gap
        if need > 0:
            issues.append((title, need, s['doc']))
    return issues

def fix_gaps(sheet_name, sheet_id, issues):
    # bottom-up
    issues = sorted(issues, key=lambda x: -x[0])
    sh = get_spreadsheet()
    requests = []
    for title_row, need, _doc in issues:
        requests.append({
            'insertDimension': {
                'range': {'sheetId': sheet_id, 'dimension': 'ROWS',
                          'startIndex': title_row - 1,
                          'endIndex': title_row - 1 + need},
                'inheritFromBefore': False,
            }
        })
    if requests:
        sh.batch_update({'requests': requests})
```

## Report format

Write findings to `_format_check_<sheet>.txt` (cp950 terminal can't print Chinese+emoji reliably). One section per sheet:

```
[20260419]
  main_end = 8
  subs:
    詹世鴻(4) title=9 last=14   GAP=0 (want≥2) — insert 2
    陳昭佑(1) title=16 last=18  GAP=1 — insert 1
    廖瑀(2) title=20 last=23   GAP=1 — insert 1
  action: bottom-up insert at 20, 16, 9
  verified: ALL GAPS OK
```

## Notes

- Do NOT attempt to rebuild entire sheets from scratch unless the user explicitly asks — the EMR cell comments and formatting are expensive to re-derive. Prefer row insertion + small targeted writes.
- Always pass `value_input_option='USER_ENTERED'` and keep the chart-number text-format rule.
- After fixing, run `_verify_gaps.py`-style re-check to confirm; report any remaining issues to the user rather than silently giving up.
