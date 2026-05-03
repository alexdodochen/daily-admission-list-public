---
name: 所有資料寫 Google Sheet 不寫本地 Excel
description: User 明確要求所有入院清單/EMR/排程資料只寫入 Google Sheet，不要碰本地 xlsx
type: feedback
---

所有入院清單工作的資料寫入目標是 **Google Sheet**（SHEET_ID 由 `local_config.py` 提供，gitignored；私有值記在 `memory/_private_setup.md`），**不是本地 `每日入院名單.xlsx`**。

**Why:** 本地 xlsx 是歷史檔（保留舊資料），目前主檔已完全遷到 Google Sheet。Claude 若誤寫到本地 xlsx，user 看不到，且會和 Sheet 不同步。2026-04-13 user 大聲明確要求「我全部都是要寫入google sheet!!!!」。

**How to apply:**
- `admission-image-to-excel` skill 名稱誤導，實際應寫到 Google Sheet。讀截圖後要用 `gsheet_utils` 的 `duplicateSheet` + `write_range` + `write_doctor_table`，不要用 `openpyxl`
- 任何時候想開 `每日入院名單.xlsx` 之前先停下，確認是否該改寫 Google Sheet
- 例外：純參考舊資料（讀舊工作表）可以讀本地 xlsx，但**不寫入**