---
name: diff-update sub-table 只動 ADD/DELETE 不要重寫
description: 重新匯入住院清單截圖時，既有 sub-table row 完全不碰；只新增截圖多的、刪除截圖沒有的
type: feedback
---

收到新截圖跑 admission-image-to-excel diff-update 時，sub-table 操作必須是 **minimal diff**：

- **新截圖有、sub-table 已存在的病人** → 完全不動該 row（姓名、病歷號、C/D/E/F/G/H 全部維持）。**不要**為了「保留 EMR」而 read-then-rewrite，那本身就是動到資料。
- **新截圖有、sub-table 沒有的病人** → 在對應主治醫師區塊內 INSERT 新 row（連帶該醫師「（N人）」標題的計數+1）
- **新截圖沒有、sub-table 還在的病人** → DELETE 該 row（連帶計數-1）
- 主治醫師區塊整塊都沒人 → 連標題列一起刪

**Why:** 5/4 下午跑 5/5/5/6/5/7 diff-update 時我用「unmerge → clear A2:V60 → batch write 全部重建」的策略，把整個 sub-table 區重寫，雖然有 read 既有 EMR 進 map 再回填，但實作 bug 一發生就連鎖：
1. 第一輪 emr_map read 範圍 A12:H50 不夠寬，後寫的 黃睦翔 sub-table 在 row 50+，re-run 時讀不到 → 3 位病人 EMR 完全消失
2. write_doctor_table 用 USER_ENTERED 寫 chart no → 部分 leading-zero 被 Sheets parser 吃掉
3. 整塊 clear 把使用者手動填的 H 註記、E 手動序也一起洗掉（這次靠 emr_map 救回，但整塊重寫本身就是不必要的風險）

使用者糾正：「如果新的住院清單上的病人 原先就已經整理好在 subtable 那就不要更動 subtable 的資料!! 你只管新的要新增 最新住院截圖沒有的要把舊 subtable 刪除」。

**How to apply:**

1. **主資料 A-L** 維持原本邏輯（依截圖 row 順序重寫整塊 OK，因為主資料本來就是直接從截圖映射）
2. **Sub-table 操作改為 row-level diff**：
   ```
   existing_charts = {chart_no per sub-table row, keyed by doctor block}
   new_charts = {chart_no per new patient, keyed by doctor block}
   for doctor:
     to_add    = new_charts[doctor] - existing_charts[doctor]
     to_remove = existing_charts[doctor] - new_charts[doctor]
     to_keep   = existing_charts[doctor] & new_charts[doctor]   # NEVER touch these rows
   ```
3. **INSERT 用 sheets API insertRange**（往下推擠）+ 寫新 row 內容（A=姓名、B=病歷號 + 其餘空白）
4. **DELETE 用 sheets API deleteRange**（往上收）
5. **更新醫師標題「（N人）」** 計數
6. **整個區塊都被刪空**（醫師沒病人）→ 連標題 + 副標題 + 空白 gap 一起刪
7. 操作完跑 `enforce_sheet_format` 收尾保格式

**Edge cases:**
- 病歷號完全相同但姓名不同（OCR 跟 EMR 校正過的差異，如「陳建諭/論」「吳莉雄/菊雄」）→ 視為同一人不變動，姓名以 EMR 校正過的為準（既有 sub-table A 欄不動）
- 主治醫師換了（同 chart 從 詹世鴻 換到 陳儒逸）→ 視為「舊 doctor 區 DELETE + 新 doctor 區 ADD」，不是把 row 跨區搬，因為跨區搬會破壞順序
- 截圖 OCR 有截斷（K 入院提示字尾）→ 既有 row 不動就完全沒這個問題

**這個規則跟 admission-image-to-excel skill 的 diff-update 段落要對齊**。今天 (5/4) 寫的 `_diff_update_week.py` 是反面教材，下次重做要用這個 minimal-diff 模式。
