---
name: 格式修復必須連動 EMR/EMR摘要 一起搬
description: 整理 sheet 格式（插列/移 row/重排子表格）時，必須確保每個病人的 C/D 欄 EMR 資料（含 cell value 與 cell note）仍對齊到同一個病人，不能只移 A-B 欄而把 C/D 留在原位
type: feedback
---

**規則：** 任何會「讓 sub-table 病人 row 移動位置」的格式修復（insert rows、delete rows、reshape subtable、reorder），**必須保證每一位病人的 A-H 整列內容（含 cell value 與 cell note）整體一起移動**。C 欄（EMR 標籤 / 原文 note）與 D 欄（EMR 摘要首行 / 完整摘要 note）是 row-level 的 per-patient 資料，絕不能與 A (姓名) / B (病歷號) 脫鉤。

**Why:** 使用者明確回報：格式整過之後，常常看到某病人 C/D 欄顯示的 EMR 是別的病人的，等於資料對錯人。使用者指出：「我覺得是你整理格式的時候 沒有同時好好對齊移動病人的資料 就會有這種情形」。一旦發生，不只影響閱讀，排導管/交班都會拿到錯的診斷，是安全問題。

**How to apply:**

1. **移動 row 一律用 `insertDimension` / `deleteDimension` / `moveDimension`**。這些是 Google Sheets 原生 row 操作，會連同 cell values、formatting、**cell notes** 一起平移。不要自己讀值 → 重排 → 寫回，因為這種做法絕對無法搬 cell note。
2. **禁止「只 update C/D 欄值而保留 row 位置不動」的錯位 fix**。若懷疑 C/D 被寫錯人，先 re-key-match 用 chart number 當 key 重抽/重寫，而不是就地 shift 欄位值。
3. **`repeatCell` 改 format 時**要限定 `fields: userEnteredFormat(...)`，絕不能包含 `note` 欄位，避免被一次刷掉。
4. **寫完之後必跑對齊驗證**：用 chart number 為 key，讀回每個 sub-table patient row，確認：
   - A 姓名 ↔ 主資料 F 姓名相符
   - B 病歷號 ↔ 主資料 I 病歷號相符
   - C 的 visit label 裡的醫師姓名 ↔ 該 row 所屬的 sub-table 醫師相符（跨醫師誤置就抓出來）
   - D 的首行摘要 ↔ 確實看得出是該病人的年齡性別
   若有不符 → 當場回報 + 重抽該病人的 EMR，不要沉默。
5. 若必須 bulk 修 sub-table 結構（例如補 title row、重排 block 順序），**先把該 block 所有病人的 (chart, A-H values, C/D notes) 讀到記憶體** → 刪掉舊 rows → 重建 rows → 把 values + notes 寫回到對應 chart 的新 row。**絕不允許**只搬 A-B 而讓 C-H 留在原地。
