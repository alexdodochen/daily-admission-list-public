---
name: WEBCVIS DEL not automatable, user does manual
description: account 107614 has no DEL perm — Playwright form submit buttonName=DEL is silently rejected; ask user to manually delete
type: feedback
---

WEBCVIS account 107614 cannot delete cathlab schedule entries via automation.

**Why:**
- `#deleteButton` is rendered with `disabled=""` and no JS in the page enables it
- direct form submit (`document.HCO1WForm.buttonName.name="DEL"; submit()`) returns silently — server discards the action
- `#modButton` (UPT) gets enabled on row click, but deleteButton never does → suggests server-side role permission, not just UI
- 5/5 reschedule attempt (2026-05-05): both v1 (direct submit) and v2 (force-enable button + click via deleteButton handler with Playwright dialog accept) failed; verify still showed all 7 charts present

**How to apply:**
- For any cathlab DEL: do NOT try to automate. List the chart/name/date and ask user to manually delete via WEBCVIS UI.
- For workflows that need DEL+ADD (reschedule): automate the ADD via cathlab_keyin.py, but stop at DEL — output the DEL list and let user handle.
- If account changes someday → re-test before assuming DEL works.
