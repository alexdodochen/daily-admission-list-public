---
name: Doctor RR order is ALWAYS random — never ask
description: When generating N-V ordering, doctor round-robin order must be random.shuffle by default. Only when the user explicitly pins a doctor (e.g. «許志新順位第一») does that override apply. Don't ask the user to choose between random vs default — always shuffle.
type: feedback
---

When building the N-V admission ordering, doctor round-robin order is **always** randomized by default.

**Why:** User instruction (5/8): «主治醫師順序除非我特別指定 都要用lottery隨機抽阿!! 你之前都沒抽嗎?? 這一步不用特別問!!». The lottery IS random shuffle of doctors — that's the whole point of "抽籤". Asking «random or default?» is redundant noise.

**How to apply:**
- Default: `random.shuffle(<schedule_doctors>)` for the 時段組 doctor order, then again separately for 非時段組. Never preserve sub-table order or any other deterministic order without an explicit override.
- Exception: if user pins a doctor («許志新順位第一», «讓陳昭佑最後»), respect that constraint and randomize the unpinned slice. Pinned-first → first slot; pinned-last → last slot; etc.
- **Within-doctor patient order** (when one doctor has 2+ patients) is a separate question — DO ask the user, since clinical judgement (urgency, room availability, OR readiness) drives that.
- Do NOT ask «要隨機還是依照子表格順序？» — random is the default, just do it.
- Save randomly-rolled order with the rest of the result; user may approve or re-roll.

**Two RR groups stay independent**: shuffle 時段組 separately from 非時段組 (per `feedback_lottery_roundrobin.md`).
