---
name: 病歷號儲存格一律文字格式
description: 主資料 I 欄、子表格 B 欄、N-W S 欄的病歷號都要強制為文字格式，避免前導 0 被吃掉
type: feedback
---

**規則：** 任何寫入病歷號的儲存格都**必須先把該欄位格式設為文字 `@`**，再寫入字串值。不能依賴 gspread 的 `RAW` 傳值 — 儲存格本身若是數字格式，Sheets UI 顯示時會把 `06815735` 砍成 `6815735`，下次讀回也會變錯。

**涉及的欄位：**
- 主資料 I 欄（病歷號碼）
- 子表格 B 欄（病歷號）
- N-W 區 S 欄（病歷號）

**How to apply:**
1. 建立/重寫日期 sheet 時，**先** 用 `batch_update_requests` 把上述欄位的整欄（或 ws 全欄）`numberFormat.type = 'TEXT'`：
   ```python
   batch_update_requests([{
       'repeatCell': {
           'range': {'sheetId': ws.id, 'startRowIndex': 1, 'endRowIndex': 500,
                     'startColumnIndex': 8, 'endColumnIndex': 9},
           'cell': {'userEnteredFormat': {'numberFormat': {'type': 'TEXT'}}},
           'fields': 'userEnteredFormat.numberFormat'
       }
   }])
   ```
2. **之後**才用 `write_range` 寫病歷號字串（`RAW` 模式即可）。
3. 驗證：讀回時 `'06815735'` 應完整保留前導 0。

**Why:** 之前 20260416 林根田 `06815735` 被存成 `6815735`、林茂松 `09444431` 變 `9444431`，原因都是 Sheets 把儲存格當數字格式。user 已經要求過多次，這次把規則固化。
