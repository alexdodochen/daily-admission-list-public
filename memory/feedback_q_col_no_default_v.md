---
name: N-V Q col 備註(住服) — empty by default; never copy "V" from existing sheets
description: Q (備註住服) defaults to ''. The "V" marks in old sheets like 5/5 are user's own manual annotations (e.g. tracking 住服 already notified) — NOT a system convention. Don't mimic patterns seen in existing sheet data; follow the spec instead.
type: feedback
---

When writing N-V ordering rows, **Q col (備註(住服)) defaults to empty string**.

**Why:**
- 2026-05-05 correction (two-step):
  1. "為何Q欄多了這些勾勾!!!" — user spotted I'd written 'V' for all 15 rows on 5/6
  2. "那是我手key 你不要隨便模仿" — clarification: the V's in 5/5 are user's own manual marks (likely tracking which patients have been notified to 住服), NOT a convention to copy
- Q col is for 住服-related free text only — must come from real source (K col 住服-related text, or reschedule note).

**How to apply:**
- Q = '' for ordinary patients (no reschedule, no special 住服 instruction)
- Q = '改M/D住院' when V col has a reschedule date
- Q = K-derived 住服 text (e.g. '限單', '住南投提早通知') when K col has such note
- **Never write 'V' as a placeholder** — even if a reference sheet shows V in many rows

**Meta-lesson — don't mimic existing-sheet patterns blindly:**
- The user manually annotates Q (and possibly other cols) for their own workflow
- Treating those annotations as "convention" → garbage propagation on every subsequent sheet
- Always source Q values from spec inputs (K col text, V reschedule date), not from peer sheets
- This applies generally: when in doubt about a column's intent, ask — don't infer from another date's data

**Anti-pattern (踩過 5/5 → 5/6):**
- Read 5/5 N-V → most Q cells = 'V' → infer 'V' is default flag → write 'V' to all 15 rows on 5/6 → user upset, had to re-clear
