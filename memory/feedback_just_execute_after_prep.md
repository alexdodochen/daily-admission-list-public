---
name: After prep + sensible default, just execute (don't re-confirm)
description: When analysis/scan/JSON-build is done and the safest default is identified, run it — don't ask "shall I proceed?"
type: feedback
---

When prep work (JSON build, week scan, edge-case enumeration, default selection) is complete and a sensible default action is clearly stated, **execute it** — do not wait for an explicit "OK" or "go ahead" from the user.

**Why:** The user has already endorsed the workflow at a higher level (e.g. «幫我把 5/10-14 keyin 導管排程»). Re-asking «要走 (A) 還是 (B)? 預設 (A)» when (A) is already the conservative correct path just adds friction. The user's time is more valuable than insurance against a default they would have approved anyway.

**How to apply:**
- Show the analysis: scan results, decisions made, edge cases handled, default chosen.
- State the planned action in one sentence.
- Then **run it** in the same response (or the next tool turn) — don't end the turn with «要我跑嗎？».
- Only pause for input when there is **genuine ambiguity that affects clinical/safety semantics**, e.g.:
  - F/G fields empty for a real procedure (need diag/proc)
  - Conflicting data the user must arbitrate
  - Destructive ops outside the originally-approved scope (delete sheet, force-push, drop existing schedule)
- HARD rules (e.g. CLAUDE.md rule 19 «week-scan before ADD») require **listing dups**, not blocking on confirmation. Listing + sensible default + execute is compliant.

Source quote (5/6 session, mid cathlab batch keyin):
> 你設定好就直接key in 不用問我

Companion to `feedback_no_reconfirm_workflow.md` (no per-phase «要繼續嗎»). This one extends to the decision-confirmation pattern: even at decision points, if a default is reasonable and stated, execute.
