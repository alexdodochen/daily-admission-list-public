---
name: 動過病人清單必做格式防呆檢查
description: 任何寫入/修改日期 sheet 的病人資料後，都要讀回驗證格式，若跑掉必須當場重整而非留給使用者
type: feedback
---

**規則：** 只要有動日期 sheet 的病人清單（匯入、diff 更新、抽籤、EMR 寫入、排序、reschedule、cathlab keyin 後修改、手動修補…都算），在 commit 本次工作前**一定要**讀回該 sheet 做格式驗證。若驗證不過 → 當場修復，不要丟回給使用者。

**要檢查的項目（最低標）：**
1. **主資料 A-L**：
   - row 1 header 12 欄齊全（實際住院日/開刀日/科別/主治醫師/主診斷(ICD)/姓名/性別/年齡/病歷號碼/病床號/入院提示/住急）
   - 每筆 patient row 至少 A-I 有值，沒有被合併儲存格吃掉
2. **N-W ordering**（若已跑過）：
   - row 1 header 10 欄齊全（序號/主治醫師/病人姓名/備註(住服)/備註/病歷號/術前診斷/預計心導管/每日續等清單/改期）
   - 序號連續、P 姓名非空、S 病歷號非空
3. **子表格**（每個醫師區塊）：
   - 先有 title row `X（N人）` 合併 A:H
   - 緊接 sub-header row `姓名/病歷號/EMR/EMR摘要/手動設定入院序/術前診斷/預計心導管/註記`
   - 然後 N 筆 patient rows（數量要等於 title 聲明的 N）
   - 區塊之間**有空白 row 隔開**
   - title 聲明人數 ≠ 實際人數 → 失敗
4. **無殘留合併**：寫入的 data row 不應被上一個合併區塊吃掉（寫入前有 unmerge 就不會發生，這是驗證用）
5. **病歷號一致性**：同一病人的主資料 I 欄、子表格 B 欄、N-W S 欄應相同

**失敗後怎麼修：**
- 主資料欄位錯位（例如多了一欄） → 重寫該 row 的 A-L
- 子表格 title 不見（像 20260421 row 13 那種）→ 用 `write_doctor_table` 或 insert + merge 補回，重算人數
- 合併吃掉資料 → unmerge 該區塊 + 重寫 data
- 整個 sheet 結構亂到無法局部修 → 以最近一份乾淨 sheet 為範本 duplicate + unmerge + clear + 重跑流程

**Why:** 之前 reschedule flow 在 20260421 把詹世鴻 title row 蓋掉卻沒發現，直到驗證 cathlab 才浮現；類似的合併/換欄/蓋 title 問題歷史上多次發生。使用者明確說「有跑掉就重新整理一番」，不要留尾巴。
**How to apply:** 任何 `write_range` / `batch_update` / `insert_rows` / `unmergeCells` 動到 sheet 之後都得跑這個檢查。簡單做法：寫一個 `verify_sheet_format(sheet_name)` 函式回傳 issue list，每個修改腳本結尾 call 一次，若有 issue 就 log + 嘗試自動修，修不完報給使用者。
