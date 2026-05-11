---
name: 改期單病人精簡流程
description: 單一病人改期的最省 token / 最快流程。重複讀整 EMR、印整段 C/D 欄、分多次 API 寫入都是浪費。
type: feedback
---

單病人改期（admission-reschedule 觸發）時避免下列行為，以省時間與 token：

**規則：**

1. **讀 sheet 時不要 print 整段 EMR/summary（C/D 欄）**。只 print 必要欄位：N-V 整列、sub-table title 列、A/B/E/F/G/H 欄。C 欄超過幾百字就只印長度，不印內容。
2. **多個寫入合併成一次 `batch_write_cells`**：V mark + 新 main row + sub-title 更新 + sub-row append → 一次 batch update 而非 4 個 API call。
3. **WEBCVIS 週掃用 `webcvis_query.py` 一次帶 5 天**（已是最省），不要分天查。
4. **`schedule_lookup.py` 一行解決 room/second/third**，不要手動翻 schedule_readable.txt 或讀 sheet。

**Why:** 5/11 王玉珍 reschedule 時整流程印了兩段超長 EMR (>4000 chars) + 多次 update_cell，使用者抱怨「每次都做好久」。EMR 內容對 reschedule 流程**完全沒用**——只是要 copy verbatim 過去，不需要 LLM 看內容。

**How to apply:** 
- 觸發 `admission-reschedule` skill 時，預設啟用此精簡模式。
- 抓 source 資料時，用 `capture only` 模式：把 C/D 欄存成變數但不 print。
- 寫入用 `batch_write_cells({(sheet, row, col): value, ...})` 合併。
- 多病人 reschedule 仍照原 skill 流程（有 rebuild 風險時要謹慎）；單病人才開精簡模式。
