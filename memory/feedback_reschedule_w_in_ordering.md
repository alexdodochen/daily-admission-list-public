---
name: 改期 W 欄屬於 N-W 排序區塊，不是主資料列
description: 手動寫 W 改期標記必須用 ordering 區塊的 row（P/S 比對），不可用主資料 row 編號
type: feedback
---

**規則：** W 欄（col 23）屬於 **N-W 排序區塊**。主資料 row 和 ordering row 共用 row 編號但內容不同（round-robin 打散了順序）。手動寫 W 時，必須先在 ordering 區塊用 **P 欄姓名**或 **S 欄病歷號**找到該病人的 ordering row，再寫那一 row 的 W cell。

**反例（曾踩過的雷）：**
主資料 row 6 = 陳亭亭 → 直接寫 `W6='20260416'`
但 ordering row 6 的 P 欄是 梁淳斌（round-robin 第 5 位）
→ `reschedule_patients.py` 讀 ordering 區塊看到梁淳斌 W 被標記，就把**錯誤的病人**搬到目標日。

**正確寫法：**
```python
vals = ws.get_all_values()
for i, row in enumerate(vals):
    if i == 0: continue
    if row[15] == '陳亭亭':   # P = col 16 (0-idx 15)
        ws.update_acell(f'W{i+1}', '20260416')
        break
```

**Why:** `reschedule_patients.py` 的 `collect_reschedules()` 從 ordering 區塊讀（`row[15]=P 姓名`、`row[18]=S 病歷號`、`row[22]=W 改期`），不看主資料。把 W 寫到錯的 row 會讓腳本搬錯病人。
**How to apply:** 任何需要設定改期標記的情境 — 人手操作、輔助腳本、或 code 裡 assert — 都必須先透過 P/S 欄比對找 ordering row。若要 assert 驗證，也要檢查 P 欄姓名而不是主資料 F 欄姓名。

**延伸規則：** 每次 reschedule 移動完（或手動介入後），都要讀來源日和目標日的「主資料 A-L」+「ordering N-W」+「子表格」三處狀態，驗證格式一致、人數正確。
