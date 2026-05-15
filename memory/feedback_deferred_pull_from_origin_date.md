---
name: deferred patients — pull EMR from original date sheet first
description: K col 入院提示 marked "(N/N無床延期)" → try fetching EMR/F/G/H from that original date sheet before fresh fetch_emr
type: feedback
---

If a patient's K col 入院提示 contains a 無床延期 marker referencing an earlier date — e.g. `3(5/12無床延期)`, `3(5/4無床延期)` — that patient was already on a previous date's sub-table. **Try pulling their EMR (C), 術前診斷 (F), 預計心導管 (G), 註記 (H) from that origin date sheet first** before launching a fresh `fetch_emr.py` call.

**Why:** the origin sheet already has user-vetted F/G/H values (auto-detect from EMR + manual touch-ups). Re-running `fetch_emr.py` + `process_emr.py` gets you the raw EMR back but loses any manual H notes (e.g. "全麻 Affera", "劉秉彥") and may re-auto-detect F/G differently than the user previously chose. Saves a Playwright session round-trip and preserves clinical context.

**How to apply:**
1. When prepping a new date sheet (or diff-update), scan main K col for `(YYYY/MM/DD ...延期)` or `(N/N無床延期)` patterns.
2. For each such patient, query the origin date sheet's sub-table by **病歷號** (most efficient — `feedback_search_by_chart_no.md`).
3. If found with EMR-length C > 50 chars → copy C/F/G/H into new sheet's sub-table.
4. If not found in origin sheet → fall back to standard `fetch_emr.py` flow.
5. Patient without 延期 marker (i.e. fresh admit) → always `fetch_emr.py`.

**Source quotes (5/15):**
> 5/12延期的 從5/12工作表把EMR 術前診斷 預計心導管 註記帶入
> 事實上 以後如果有標記延期 都可以從原日期試著找資料看看

Related: [[diff-update sub-table 只動 ADD/DELETE 不要重寫]] (don't clear+rewrite — wipes manual H), [[Leverage retained week-of cache JSON]] (alt fallback if origin sheet was cleared but JSON still exists).
