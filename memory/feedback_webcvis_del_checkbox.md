---
name: WEBCVIS DEL via per-row checkbox (verified mechanism)
description: How to automate cathlab schedule DEL — use the chk checkbox in row's first cell, NOT direct deleteButton click or buttonName=DEL form submit
type: feedback
---

WEBCVIS cathlab DEL mechanism (verified working 2026-05-06 on chart 01808613 / 5/7):

Each result row has `<input type=checkbox name=chk value=N>` in the first cell.
Its `onclick` calls `checkedShowButton(deleteButton, allChkBoxes)` which enables `#deleteButton`.
Then click `#deleteButton` → fires `confirm("您確定要刪除嗎？")` → form submits with buttonName=DEL.

**Why:** the bare `#deleteButton` is initially `disabled=""` and never enabled by row click (only modButton is enabled). Two prior failed attempts confirmed this:
1. `removeAttribute("disabled")` on deleteButton + click → silent fail (server has no row context)
2. Direct `buttonName="DEL"` form submit after row click → silent fail (`hes_referno` is OFTEN EMPTY for cathlab entries; server can't identify row)

The chk checkbox carries the row index that the server uses to identify the target.

**How to apply:** use `webcvis_del.py CHART YYYYMMDD` (permanent helper). Don't write one-off Playwright scripts. The helper:
1. Finds row by `#hes_patno` value
2. Sets `chk.checked = true` and fires `chk.onclick()` to enable deleteButton
3. Clicks `#deleteButton` (Playwright `page.on("dialog", ...)` accepts the confirm)
4. Re-queries to verify removal

For multi-DEL: `python webcvis_del.py CHART1 DATE1 CHART2 DATE2 ...` (single login session, sequential DELs).
