---
name: feedback_vmark_already_scheduled_dont_touch
description: When verify_cathlab flags a sub-table V改期 patient as already in WEBCVIS ("竟然在排程中!"), do NOT auto-DEL — surface to user; "leave it scheduled" is a valid outcome they may choose
type: feedback
---

When `verify_cathlab.py` reports a V改期-marked patient (sub-table col-I = `V`) as `SKIP ... → 竟然在排程中!` (expected not scheduled, but found in WEBCVIS), do **not** treat it as an error to fix and do **not** auto-DEL. List it for the user and let them decide.

**Why:** 2026-05-19, 5/19 admits — three V改期-marked patients were flagged by verify as already having WEBCVIS slots. User instruction: 「已經在排程就不要動」. The V mark just means "skip from N+1 auto-keyin"; it does NOT mandate removing an existing slot. The natural impulse (verify says NG/竟然 → go fix) is wrong here.

**How to apply:**
- V改期 + already scheduled → report (chart/name/date/room/time), default action = **leave untouched**.
- Only DEL if the user explicitly asks (then follow [[feedback_webcvis_del_manual]]: list DEL candidates → wait for OK → automated DEL).
- V mark's only hard effect: excluded from N+1 cathlab auto-ADD + skipped by verify expectation. It is not a delete trigger.

**Related:** [[feedback_webcvis_del_manual]], [[feedback_reschedule_active]]
