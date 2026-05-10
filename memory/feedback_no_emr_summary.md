---
name: D=EMR摘要 column is header-only placeholder; no summary ever written
description: Sub-table is 8-col canonical (A-H). D=EMR摘要 stays as a header-only placeholder forever. The summary feature is retired — no auto generation, no on-demand Gemini fill. Don't accept "做摘要" as a trigger.
type: feedback
---

**Canonical sub-table layout (8-col A-H):**
A=姓名 | B=病歷號 | C=EMR | **D=EMR摘要 (header-only placeholder; never written)** | E=手動設定入院序 | F=術前診斷 | G=預計心導管 | H=註記

**Rule (5/10):** The EMR summary feature is fully retired. The D column header (`EMR摘要`) stays for layout stability, but **no script, agent, or Gemini call ever writes content into D**. There is no auto path, no on-demand path, no Gemini-fill-this-row pattern. Don't offer "做摘要" as an action; don't accept it as a trigger.

**process_emr.py behavior:**
- Writes C (raw EMR + visit header, with `<age> y/o <gender>` prefix per 5/8 rule)
- Writes F (DIAG_RULES auto-detect — 術前診斷)
- Writes G (CATH_RULES auto-detect — 預計心導管)
- **Does not touch D** (no writes, no clears — leave whatever is there alone)
- Does not generate four-section summaries (`一、心臟科 / 二、病史 / 三、客觀檢查 / 四、住院計畫`)

**Why:**
- 5/4 morning: tried to drop D entirely (7-col layout migration). Caused chained breakage because pre-existing sheets were still 8-col and `r[:7]` truncated H=註記 → SKIP_KEYWORDS no longer matched → cathlab keyin/verify misjudged patients. Rolled back same day to 8-col canonical with on-demand Gemini fill.
- 5/4 evening - 5/9: on-demand Gemini summaries were filled into D for some patients (visible in older sub-table rows). User reviewed them and decided the summaries were not adding value vs reading C directly.
- 5/10: user says「我現在已經不需要自動EMR摘要功能了 這個功能要全面取消!!! 你只需留下EMR摘要這個空欄位即可!」— retire the feature entirely, including the on-demand path. Keep the column header so layout stays stable across old and new sheets.

**How to apply:**

- **Sub-table writes always assume 8 columns** (`r[:8]`, `endColumnIndex=8`, `A:H`). Anything using `r[:7]` / `A:G` is dead 5/4-morning code and must be reverted.
- **Patient row writes**: 術前診斷 → F (col 6); 預計心導管 → G (col 7); 註記 → H (col 8). D is left at whatever it currently holds — don't write, don't clear.
- N-V ordering R column (備註) reads from sub-table H (`row[7]`).
- N-V writes must re-read sub-table F/G/H at write time (CLAUDE.md rule #18).
- `write_doctor_table` num_cols default = 8 (D is empty by default for new rows — keep it that way).
- `emr_toggle_script.js` EMR_COLUMNS = [3, 4] is fine — it just collapses both C and D (D being empty is harmless).
- **Pre-existing D content on old sheets**: leave alone. Don't bulk-clear unless the user explicitly asks.
- **No Gemini summary call** anywhere in this project. If the user asks "做摘要", remind them the feature is retired and offer to show the raw C column instead.

**Dead language from earlier transitions** (treat as obsolete if seen):
- "post 5/4 column drop" / "post 5/4 7-col layout" / "A:G" / "r[:7]" / "D=手動設定入院序" — these are the 5/4 morning attempt that was reverted same day.
- "on-demand Gemini fill" / "user calls Gemini to fill D" / "summary on demand only" — these are the 5/4-5/9 transitional policy that was retired 5/10. **This file is the current truth.**
