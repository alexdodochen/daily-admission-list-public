---
name: EMR #divUserSpec 可推姓名/年齡/性別
description: EMR frame.aspx 的 #divUserSpec 包含姓名/生日/性別，可反推年齡寫回 Google Sheet 主資料
type: feedback
---

EMR 系統 `frame.aspx` 頁面的 `<span id="divUserSpec">` 內含該病歷號的完整基本資料，格式固定：

```
姓名 : 林裕興 , 生日 : 1957/12/06 , 性別 : 男 , 血型 : O+, 初診時間 : 2003/04/16 , 最近看診 : 2026/04/15
```

只要 `txtChartNo` 查詢成功（不管後續點不點得到該醫師的門診），`#divUserSpec` 就會回填 → 可用來校正 Google Sheet 主資料：
- **F 欄 姓名** ← 姓名
- **G 欄 性別** ← 性別（男/女）
- **H 欄 年齡** ← 生日推算至實際住院日（`A` 欄）。若生日未到：age -= 1

`process_emr.py` 的 `parse_name_from_raw` / `parse_birth_from_raw` / `parse_gender_from_raw` / `compute_age` 四個 helper 已實作。無論 EMR visit 有沒有抓到、matched 與否，只要 `info['name']` 有值就套用校正（見 session 2026-04-16 實驗結論）。

**Why:** 使用者以前必須手動在 OCR 辨識失敗時修正這三欄，既然 EMR 同頁就有 ground truth，應該自動同步。年齡從生日推算比 OCR 截圖更準。

**How to apply:** 改 `process_emr.py` 時，把 name/age/gender 校正邏輯放在 `info.get('name')` 有值的分支，和 `status == 'ok'` 的分支**分開處理** —— no_visit 的無資料病人也要校正。
