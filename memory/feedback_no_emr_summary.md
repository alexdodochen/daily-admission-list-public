---
name: D=EMR摘要 欄保留但不主動寫；使用者按需 call Gemini 才填
description: Sub-table 是 8-col canonical (A-H)。D=EMR摘要 欄留著當 placeholder，process_emr.py 不主動產 summary；user 要的時候自己 call Gemini 填那一個 row
type: feedback
---

**Canonical layout（8-col A-H）：**
A=姓名 | B=病歷號 | C=EMR | **D=EMR摘要 (placeholder, on-demand)** | E=手動設定入院序 | F=術前診斷 | G=預計心導管 | H=註記

**process_emr.py 行為：**
- 寫 C（raw EMR + visit header）
- 寫 F（DIAG_RULES auto-detect 術前診斷）
- 寫 G（CATH_RULES auto-detect 預計心導管）
- **不寫 D**（留空白）
- 不再生成「四段式摘要」(`一、心臟科 / 二、病史 / 三、客觀檢查 / 四、住院計畫`)

**使用者按需求生成摘要：** 等 user 明說「做摘要」「summarise X 病人」之類，再 call Gemini 對該 row 的 raw EMR 做摘要、寫進 D 欄。一次一個 row，不批次自動。

**Why:**
- 5/4 上午曾嘗試「整欄 D=EMR摘要 移除」→ 7-col layout migration（commit `a824e14`）。動到 gsheet_utils / process_emr / generate_ordering / verify_cathlab / rebuild_date_sheet / emr_toggle_script.js / 4 skills / 工作流程 txt / CLAUDE.md。
- 同日下午跑 5/4-5/5 cathlab verify 才發現連鎖副作用：5/3 之前的 sheet + 5/4 上午建的 5/10-5/14 + 5/4 下午 diff-update 的 5/5/5/6/5/7 都還是 8-col layout（migration 沒回頭改 sheet 內容），但 7-col code 用 r[:7] 切掉 H → 看不到 H=註記 → SKIP_KEYWORDS「檢查」永遠 match 不到（黃嬌子「不用排導管 要排CTV ... 入院檢查」被誤當 missing）+ 張獻元規則讀 G 欄當「註記」但 8-col G=預計心導管，整個判定錯位。
- User 改變決策：「我看妳還是保留 EMR摘要那一欄好了 ... 我以後需要的時候 會呼叫 gemini 幫我做摘要」→ 8-col 統一 canonical，5/4 上午的 7-col migration 整個反轉。
- 反轉 commit 範圍：gsheet_utils.py、process_emr.py、generate_ordering.py、verify_cathlab.py、rebuild_date_sheet.py、emr_toggle_script.js、4 skill md、CLAUDE.md rule #14/#18/#22 + Sheet Layout、工作流程 txt。

**How to apply:**

- **動到 sub-table column index 一律用 8 欄假設**（`r[:8]`、`endColumnIndex=8`、`A:H`）。看到 `r[:7]` / `A:G` 都是 5/4 上午短暫 7-col migration 的死碼，立刻改回。
- 寫 sub-table patient row：術前診斷 → F (col 6)；預計心導管 → G (col 7)；註記 → H (col 8)。
- N-V ordering R 欄（備註）來源：子表格 H 欄（`row[7]`）。
- N-V 寫入前必當下重讀子表格 F/G/H（與 CLAUDE.md rule #18 對齊）。
- write_doctor_table num_cols default = 8。
- emr_toggle_script.js EMR_COLUMNS = [3, 4]（C raw EMR + D 摘要 兩欄都收合，user call Gemini 填 D 之後也能整欄收）。
- **「四段式摘要」不再自動產**——若 user 要某 row 的 summary，個別 call Gemini，寫 D 欄那一格。

**5/4 那次 migration 留下的死語：**
- 「post 5/4 column drop」「post 5/4 layout」「7-col」「A:G」「r[:7]」「D=手動設定入院序」「D 欄已停用 EMR摘要」這些字串若還在某 memory 檔的旁註，**以本檔為準** — 8-col 是 canonical，那些是過渡期文字，未來看到請當廢字直接改。
