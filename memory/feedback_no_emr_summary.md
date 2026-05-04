---
name: 取消 EMR 摘要功能 + 子表格 D 欄整欄移除
description: 5/4 起 sub-table 不再有 EMR摘要 (原 D 欄)；C 欄存 raw EMR、F/G 自動判讀仍跑 (在 raw EMR 上跑)，但欄位左移成 E/F
type: feedback
---

5/4 起：

- 子表格從 8 欄 (A-H) → **7 欄 (A-G)**：D=EMR摘要 整欄拿掉、E-H 全部左移 1 格
- 新 layout：A=姓名 | B=病歷號 | C=EMR (raw) | D=手動設定入院序 | E=術前診斷 | F=預計心導管 | G=註記
- `process_emr.py` 移除 `generate_summary()`；只寫 C (raw EMR + visit header)、E (DIAG_RULES auto-detect)、F (CATH_RULES auto-detect)
- F/G 自動判讀邏輯**保留** — 它本來就讀 raw EMR 的 [Diagnosis] / [Assessment & Plan] 區塊，跟摘要無關
- emr_toggle_script.js `EMR_COLUMNS` = `[3]` (只 C 欄；舊版同時刷 C+D)

**Why:** 使用者直接說「我要全面取消EMR摘要功能 我只需要你提取原始EMR就好 現有subtable D欄 不再需要 FG術前診斷 預計心導管 依照EMR原始資料判讀即可」。摘要是 keyword 拼貼出來的中段加工品，使用者寧可看 C 欄 raw 再自己判讀，跳過摘要層的失真。

**How to apply:**

- 動到子表格 column index 的程式碼**一律用 7 欄假設** (`r[:7]`、`endColumnIndex=7`、`A:G`)。任何看到 8/A:H 的舊 reference 都是 5/4 前的死碼，要改。
- 寫 sub-table patient row：原本寫 F (col 6) 的術前診斷 → 改寫 E (col 5)；原本寫 G (col 7) 的預計心導管 → 改寫 F (col 6)；原本讀 H (idx 7) 的註記 → 改讀 G (idx 6)。
- N-V ordering R 欄 (備註) 來源：以前是子表格 H 欄 (註記)，現在是 G 欄 (`row[6]`)。
- N-V 寫入前必當下重讀子表格 E/F/G (而非 F/G/H — 跟 CLAUDE.md rule #18 對齊更新)。
- **舊 sheet (5/3 之前) 不動**：使用者選 α，舊 sheet 仍是 8 欄，新 verify/ordering/process_emr 對舊 sheet 會抓錯欄。預期不再對舊 sheet 跑這些 script (那週已 cathlab 完)。如果使用者真要回頭跑某張舊 sheet，要明說「這張是舊 layout」並做臨時兼容。
- 不要再生成「四段式摘要」(`一、心臟科相關診斷 / 二、病史 / 三、客觀檢查 / 四、本次住院計畫`) — 使用者 5/4 明說捨棄。

**相關檔案 (5/4 改過)：** `gsheet_utils.py` (write_doctor_table + enforce_sheet_format)、`process_emr.py`、`generate_ordering.py`、`verify_cathlab.py`、`rebuild_date_sheet.py`、`emr_toggle_script.js`、4 個 admission-* skills、`每日入院清單工作流程.txt`、`CLAUDE.md` rule #14/#18/#22。
