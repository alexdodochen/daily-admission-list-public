---
name: Google Sheet 寫入配額 60/min 與 batch 策略
description: 大量重建/更新日期 sheet 時必須把 format/merge/border/dropdown 壓縮到最少 API calls 避免 429
type: feedback
---

Google Sheets API 對 service account 的限制是 **60 writes/minute/user**。散亂呼叫 `ws.update` / `format_header_row` / `merge_cells` / `add_borders` / `set_dropdown_from_range` 每次都算一次 write，一個日期 sheet 輕易就 40+ 次，兩個 sheet 就 429 Quota Exceeded。

**正確做法：把整個 sheet 的寫入壓成 ≤6 次 API call**

| # | 動作 | 工具 |
|---|------|------|
| 1 | 複製 template | `sh.batch_update({duplicateSheet})` |
| 2 | 擴列 + unmerge + clear | 一個 batch 裡塞 `appendDimension` + `unmergeCells[]` + `updateCells` |
| 3 | 寫主資料 A-L | `ws.update(range_name=..., values=...)` |
| 4 | 寫子表格 A-H | `ws.update(range_name=..., values=...)` |
| 5 | 格式化 | 一個 `sh.batch_update` 塞所有 `mergeCells` + `repeatCell` + `updateBorders` + `setDataValidation` |

多個日期連續處理時 **sleep 45-70 秒** 之間（60/min 限制是 rolling window，不是每分鐘歸零）。

**Why:** 2026-04-16 session 重建 4/19-4/24 共 6 個 sheet 時被 429 打到兩次，整個腳本崩潰，患者資料差點寫壞。後來把每個 sheet 壓到 ~6 calls 才順利完成。

**How to apply:**
- 寫「重建/初始化日期 sheet」腳本時，**一定**先規劃好每階段 batch，不要逐項 format
- 參考 `rebuild_date_sheet.py` 的 `build_format_requests()` 範本
- 多日期循環一律 `time.sleep(45)` 以上
- 單次補丁式小修正（3-5 個 cell）不受限，不需壓縮
