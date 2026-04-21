---
name: write_doctor_table 格式繼承 bug 待修
description: rebuild_date_sheet 後子表格第一個病人 row 會繼承前一張 sheet 的 blue header 背景，永久修正尚未套用
type: project
---

當用 `rebuild_date_sheet.py` 從既有 sheet 複製建新 date sheet 時，若前一張 sheet 的子表格結構與新 sheet 不同（人數/醫師數不同），**會有部分病人 row 殘留 blue header 背景（RGB 0.741/0.843/0.933）而不是白底**。

**根因：**
1. `batch_clear` 只清 VALUE，不清 formatting
2. `write_doctor_table()`（`gsheet_utils.py:354`）只把 title row + sub-header row 塗 BLUE_HEADER，沒有明確把病人 data row 塗 WHITE → 繼承舊 sheet 的 bg

**現況：** 2026-04-22 sheet row 19 (吳鄭錦綿)、row 24 (郭蔡富美) 被發現為藍底，已手動 batch_update 修正。

**Why:** 使用者 2026-04-22 指出「4/22的入院清單格式怪怪 沒有白底」並要求「要檢討為甚麼這次格式跑掉喔」。

**How to apply（待做的永久修正）：**
- **方案 A**（在 `write_doctor_table` 寫病人 row 時，同時 batch_update A:H 塗 WHITE）—— 改動小
- **方案 B**（`rebuild_date_sheet.py` 在 `batch_clear` 之後加 full-range reset 塗白）—— 更徹底
- 選一個套用後執行現有 date sheets 的 format check（或 `_fix_0422_format.py` 的模式）驗證
- 修完後將此 memory 標為 resolved 或刪除
