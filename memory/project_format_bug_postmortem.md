---
name: 格式跑掉根因分析 (2026-04-21 postmortem)
description: 紀錄為什麼「萃取病人資料表格 白底跑掉」重複發生的五個根因，以及已做/待做的修復。寫程式碰到 sub-table 或主資料格式時必讀。
type: project
originSessionId: 726bb693-3593-4f39-838b-e29a5122e8cb
---
# 為什麼每日入院清單的表格格式會跑掉 — 根因分析 + 修復清單

## 現象
User 2026-04-21（以及之前多次）回報：萃取病人資料（image-to-excel diff-update / EMR extraction / sub-table surgery）之後，子表格的病人 row 不是白底、或空列殘留藍底/框線。

## 根因（五個一起造成的）

**1. `write_doctor_table` 只格式化 header，patient row 裸奔**
`gsheet_utils.py` 舊版對 title/subheader 下 `format_header_row`（藍底+粗體），但 patient data row 只用 `write_row` 寫值 — **沒有任何 `repeatCell` 指定 backgroundColor**。
→ duplicated sheet 原位置若有殘留格式（前一份 sheet 的藍底/orange/merge），新病人 row 就透出來。

**2. 1-列 gap vs 2-列 rule 打架**
舊版 `return end_row + 2` 只留 1 列 gap；`admission-format-check` skill 規定 ≥ 2 列。每個 sub-table 之間的 gap 違反格式驗證但程式碼自己製造它。

**3. Blank gap 列沒清**
每兩個 sub-table 之間的空白列從來沒被 `repeatCell` 刷 WHITE/no-border。duplicated sheet 原位置的殘留色/框直接保留 → user 看到「白中夾藍一條」。

**4. Diff-update insertDimension 沒後續 format pass**
歷次 diff-update 用 `insertDimension` 加新 row，但插進去的 row 繼承上一行的格式（或是空白格式視 `inheritFromBefore`）→ 若要寫新病人進去卻沒跟著下 `repeatCell`，format 就沒定下來。

**5. process_emr.py 只寫 C/D/F/G 值，不 touch 格式**
`updateCells`/`update_cell` 只更新 value + note，不改 format。若 row 的 format 已經壞掉，process_emr 完全修不回來。

## 已做修復 (2026-04-21)

`gsheet_utils.py::write_doctor_table`:
- Patient rows → 顯式 `repeatCell` WHITE bg + `bold:False` + LEFT + WRAP
- Blank gap rows (2 列) → 顯式 WHITE + `updateBorders style:NONE`
- Return `end_row + 3` (2 列 gap)

`_update_20260423_phaseB.py::insert_patient_into_subtable` 範式：
- `insertDimension` (inheritFromBefore=False)
- 寫值
- `repeatCell` WHITE + text + WRAP
- `updateBorders` 補四邊框
- F/G dropdown
- update title 人數

## 還沒做（建議）

- `admission-format-check` skill 的「rule 5 藍底/白底/邊框」要被自動呼叫 — 任何寫入 date sheet 之後 Claude 自己跑一次讀回檢查（目前只有 CLAUDE.md rule 17 文字規定，沒有 hook）。
- 把 `admission-image-to-excel` 的 SKILL.md 裡「差異更新模式」step 3「新增 → append」擴寫成明確「insert+重新刷 format」的範式（現在只有一行描述）。
- 舊的 sub-table 病人 row（在 2026-04-21 之前建立、我沒重新 touch 的）如果格式已壞，需要一次性全部 sweep。目前只有動到的 row 是乾淨的。

## How to apply

寫任何會碰 sub-table 的程式碼時，做完值的寫入後**永遠要**下一組 repeatCell + updateBorders 把 WHITE bg + 邊框定住。不要相信 duplicateSheet 或 insertDimension 留下來的默認格式。
