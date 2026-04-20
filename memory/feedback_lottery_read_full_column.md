---
name: 抽籤必須直接讀 Google Sheet「主治醫師抽籤表」工作表
description: 不要靠使用者口述或記憶重建抽籤表欄位，一律 gspread 讀取該工作表當日欄，儲存格原樣解讀
type: feedback
originSessionId: 2dd6a095-9910-4773-ad5e-a4a191e9e9f1
---
做任何日期的入院抽籤前，**一律直接從 Google Sheet 讀取「主治醫師抽籤表」工作表**對應星期欄（col A=一 … col E=五），不要靠使用者口述訊息或記憶重建。

**籤數規則（儲存格原樣解讀）：**
- 儲存格值帶 `*2` 後綴 → **2 支籤**（例：`詹世鴻*2`、`張獻元*2`、`李柏增*2`、`黃鼎鈞*2`）
- 儲存格值是純名字 → **1 支籤**（例：`林佳凌`、`陳儒逸`）
- 同一名字若出現在多列 → 每列各自計（通常不會，因為抽籤表已用 `*2` 表示）
- 空白儲存格 → 跳過

**標準讀法（`_read_lottery_sheet.py` 已寫好範本）：**
```python
ws = get_worksheet('主治醫師抽籤表')
data = read_all_values(ws)
col_idx = {'一':0,'二':1,'三':2,'四':3,'五':4}[weekday_char]
tickets = []
for row in data[1:]:
    name = (row[col_idx] if col_idx < len(row) else '').strip()
    if not name:
        continue
    count = 2 if '*2' in name else 1
    tickets.extend([name.replace('*2','').strip()] * count)
```

**Why:** 20260421 抽籤過程中我連續抽錯三次（漏籤、誤加 *2、把非表格人員算進去），都是因為我在腦中重組使用者口述而非直接讀 sheet。使用者下最後指令：「重新閱讀 主治醫師抽籤表 工作表 好好學習」。

**20260422 (週三) 正確籤池 = 8 支**（僅供對照，每次仍須重讀 sheet）：詹世鴻*2(2) + 林佳凌(1) + 陳儒逸(1) + 張獻元*2(2) + 黃睦翔(1) + 廖瑀(1)

**How to apply:**
1. 接到抽籤指令 → 算出隔天星期幾 → 直接 gspread 讀「主治醫師抽籤表」該欄
2. 把讀到的 raw 籤池和解讀結果先列給自己看（寫 `_lottery_sheet_dump.txt`），確認後再抽
3. 不要把使用者輸入文字當作唯一來源——使用者可能簡寫或漏列
4. 有病人但不在籤池的醫師 = 非時段醫師；籤池有但無病人的醫師仍進 shuffle 影響機率
