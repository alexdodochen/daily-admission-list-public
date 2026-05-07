---
name: New date sheets must not be hidden by default
description: When creating a new date sheet (e.g. via duplicateSheet), explicitly set hidden=False or run unhide afterward. User wants every sheet visible in the tab bar.
type: feedback
---

When creating a new date sheet through `duplicateSheet` or any other path, the new sheet may inherit the source's `hidden=True` property. The user always wants every date sheet visible in the tab bar.

**Why:**
- 2026-05-07: created 20260508 via reschedule build, default-hidden, user pushed back ("新創見的工作表又預設隱藏了 不要這樣 我都要看到")
- Hidden sheets are easy for the user to miss when verifying data — surface area the user can't see is surface area for bugs

**How to apply:**
- After any `duplicateSheet` / `addSheet` request, queue a follow-up `updateSheetProperties` with `{hidden: False, fields: 'hidden'}` for the new sheet ID
- For the existing rebuild flow (`rebuild_date_sheet.py` / inline rebuild), add the unhide request to the same batch_update that handles unmerge + clear
- When in doubt after creating sheets, run a quick visibility check and unhide
