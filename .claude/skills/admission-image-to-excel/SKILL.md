---
name: admission-image-to-excel
description: Use when importing daily admission list data from a screenshot/image (JPG/PNG) into the Google Sheet's date-named worksheet. Triggered by "匯入入院名單", "讀取圖片匯入", or when given an admission list image file to process. Despite the historical name, writes to Google Sheet (not local xlsx).
---

# 每日入院名單圖片匯入 Google Sheet

## Overview
從每日入院名單截圖提取病人資料，寫入 **Google Sheet**（SHEET_ID 由 `local_config.py` 提供，gitignored）的日期工作表，複製既有格式並建立醫師子表。

**重要：** 本 skill 歷史名稱叫 image-to-excel，但實際目標是 Google Sheet，不寫本地 `每日入院名單.xlsx`。user 明確要求所有資料寫 Google Sheet。

## When to Use
- 收到入院名單截圖（JPG/PNG）需匯入
- 使用者說「匯入」「讀取圖片」搭配日期或圖檔名
- 圖檔名通常為 `YYYYMMDD.jpg`

## 欄位結構（主資料 A-L）

| 欄 | 名稱 | 格式 | 範例 |
|----|------|------|------|
| A | 實際住院日 | 文字 YYYY-MM-DD | 2026-04-20 |
| B | 開刀日 | 文字 YYYY-MM-DD 或空 | 2026-04-21 |
| C | 科別 | 文字 | 心臟血管科 |
| D | 主治醫師 | 文字 | 劉嚴文 |
| E | 主診斷 | 文字(ICD碼) | 42731 |
| F | 姓名 | 文字 | 陳啟和 |
| G | 性別 | 文字 | 男/女 |
| H | 年齡 | 整數 | 78 |
| I | 病歷號碼 | 文字(8碼) | 09494520 |
| J | 病床號 | 文字或空 | |
| K | 入院提示 | 文字 | 3.2 |
| L | 住急 | 文字或空 | |

## 流程

1. **讀取圖片** — 用 Read tool 讀取圖片，逐列提取 11 欄（A-K，L 通常空）
2. **檢查目標** — 用 `gsheet_utils.list_sheets()` 確認目標日期工作表是否已存在
   - 已存在且有資料 → 走【差異更新模式】（見下方）
   - 不存在 → 走【新建模式】
3. **新建模式**：
   1. `duplicateSheet` 複製最近一份日期工作表作為格式範本
   2. **unmerge 全部 cells**（A1:V200）— 若省略這步，來源的醫師子表合併列會吃掉主資料的 B-H 欄
   3. `batch_clear(['A2:V200'])` 清空除 header 外所有資料
   4. `write_range(f'A2:K{n+1}', data)` 寫主資料
   5. 主資料下方 +2 空列，用 `write_doctor_table` 依序建立每位醫師子表
   6. 格式化 `A2:L{n+1}`：白底（`{"red":1,"green":1,"blue":1}`）+ `horizontalAlignment=LEFT` + `verticalAlignment=MIDDLE`
4. **回報結果** — 列出匯入的病人清單，標記任何無法辨識的欄位

## 建新日期表的關鍵步驟（python + gsheet_utils）

```python
import time
from gsheet_utils import (get_spreadsheet, get_worksheet, write_range,
                          write_doctor_table, batch_update_requests)

DST = 'YYYYMMDD'   # e.g. 20260420
SRC = 'YYYYMMDD'   # 最近一份已存在的日期工作表

sh = get_spreadsheet()

# 刪除既有同名（若 rebuild）
if get_worksheet(DST):
    sh.del_worksheet(get_worksheet(DST))
    time.sleep(1)

# Duplicate
src_ws = sh.worksheet(SRC)
resp = sh.batch_update({'requests': [{
    'duplicateSheet': {'sourceSheetId': src_ws.id, 'newSheetName': DST}
}]})
new_id = resp['replies'][0]['duplicateSheet']['properties']['sheetId']
time.sleep(1)
dst_ws = sh.worksheet(DST)

# 【關鍵】Unmerge 全部 — 否則來源子表合併列會吃掉主資料行
batch_update_requests([{
    'unmergeCells': {
        'range': {'sheetId': new_id, 'startRowIndex': 0, 'endRowIndex': 200,
                  'startColumnIndex': 0, 'endColumnIndex': 22}
    }
}])
time.sleep(1)

# 清空
dst_ws.batch_clear(['A2:V200'])
time.sleep(1)

# 寫主資料 A-K
main_data = [
    ['2026-04-20', '2026-04-21', '心臟血管科', '陳儒逸', '4010', '王翠月', '女', '98', '01305368', '', '3'],
    # ...
]
write_range(dst_ws, f'A2:K{1+len(main_data)}', main_data)

# 白底 + 靠左對齊（主資料列）
batch_update_requests([{
    "repeatCell": {
        "range": {"sheetId": new_id, "startRowIndex": 1,
                  "endRowIndex": 1 + len(main_data),
                  "startColumnIndex": 0, "endColumnIndex": 12},
        "cell": {"userEnteredFormat": {
            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
            "horizontalAlignment": "LEFT",
            "verticalAlignment": "MIDDLE",
            "textFormat": {"fontSize": 11},
        }},
        "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,textFormat)"
    }
}])

# 建醫師子表（從 main_data_end_row + 3 開始）
next_row = 1 + len(main_data) + 3
for doctor, patients in DOCTORS:
    next_row = write_doctor_table(dst_ws, next_row, doctor, patients)
```

## 差異更新模式（同日期工作表已存在）
入院清單在實際入院日前會變動，user 會重發截圖。此時做 diff：
1. 解析新截圖 → 與現有 sheet 用「病歷號」做 diff
2. 列出：新增 N 人 / 取消 M 人 / 保留 X 人 → 等 user 確認
3. 新增 → append 主表 + 醫師子表 + 跑 EMR + 預填 F/G
4. 取消 → 刪主表 row + 子表 row + N-V 入院序
5. 保留 → 完全不動（EMR/F/G/入院序/註記都保留）
6. 更新醫師人數標題（如「劉嚴文（2人）」→「劉嚴文（3人）」）

## 圖片辨識注意事項

- **主治醫師必須比對正確名單**，不在名單中代表讀錯，需修正：
  陳柏升、許志新、詹世鴻、李柏增、陳昭佑、廖瑀、黃鼎鈞、陳柏偉、
  劉嚴文、陳儒逸、鄭朝允、劉秉彥、陳則瑋、張獻元、黃睦翔、
  林佳凌、張倉惟、王思翰、柯呈諭、李文煌
- **病歷號** 固定 8 碼，以文字存入（保留前導零如 `09494520`）
- **姓名** OCR 讀不全沒關係，步驟三 EMR 會用病歷號自動校正
- **主診斷** 為 ICD-9 碼，以文字存入
- **日期** 以 `YYYY-MM-DD` 文字存入（非 datetime 物件）
- **年齡** 以整數存入
- **入院提示** 可能有複合值如 `2.3` 或 `3.2`，以文字存入
- 工作表名稱固定用 `YYYYMMDD` 格式（無分隔符）
