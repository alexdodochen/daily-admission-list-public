---
name: 建立新日期工作表必須先 unmerge
description: 複製既有日期工作表建新表時，必須先 unmerge 全部 cells 才能寫入主資料
type: feedback
---

在 Google Sheet 建新日期工作表（如 20260420）時：

**正確流程**：
1. `duplicateSheet` 複製最近一份日期工作表（格式最新）
2. **unmerge 全部 cells**（整張 sheet 範圍，A1:V200）
3. `batch_clear` 清空 A2:V（保留 header 列 1）
4. `write_range` 寫主資料 A2:K{n+1}
5. 主資料下方 +2 空列開始用 `write_doctor_table` 建各醫師子表
6. 格式化主資料列：白底 + horizontalAlignment=LEFT（header 列除外）

**Why:** 來源工作表的醫師子表標題列（如「李文煌（1人）」）是 merged cell（A:H）。如果沒先 unmerge 直接寫入，row 4 的 B-H 會被 merge 吃掉，只有 A 欄寫得進去，其他 7 欄變空。2026-04-13 建 20260420 時發生，R4 杜順興 B-H 整列被吃掉。

**How to apply:** 任何透過 `duplicateSheet` 建新日期表的腳本，都必須包含 unmergeCells 步驟。參考 `_rebuild_gsheet_20260420.py` 的 `unmerge_req` 區塊。