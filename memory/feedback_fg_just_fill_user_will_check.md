---
name: fg-just-fill-user-will-check
description: For F/G clinical judgment calls during EMR write, fill in best clinical guess instead of asking — user always re-checks before lottery/ordering
metadata:
  type: feedback
---

When writing sub-table F (術前診斷) / G (預計心導管) and auto-detect produces a plausible but uncertain answer, **just fill in your best clinical reading** rather than asking «要不要改成 X」or leaving blank.

**Why:** Source quote (5/15): «你覺得是怎樣就填阿 我都會再檢查». User does a final F/G review before lottery/ordering anyway — asking adds round-trips, slows the workflow, and treats the user as the F/G oracle instead of letting Claude exercise clinical judgment. The 5/10 review step is already in the workflow; F/G isn't load-bearing on a single auto-write.

**How to apply:**
- After auto-detect runs, scan the full EMR Dx + most-recent visit Plan + admitting doctor's specialty
- Pick the most clinically coherent F/G (use existing patient-block conventions: short diagnosis name, common procedure phrasing — see neighboring sub-table rows for style)
- Write the cell directly via batch_write_cells; don't end turn with «要不要改成…»
- Only pause to ask when the EMR is **genuinely ambiguous** between two clinically different paths (e.g. PCI vs CABG referral), not when picking between reasonable phrasings
- Related: [[just-execute-after-prep]] — same spirit, default to executing once you have what you need

5/15 origin: 李全福 case — auto-detect gave CAD/Left heart cath. but EMR is AF s/p ablation under EP doctor → I asked «要不要改成 AF/RF ablation» and user pushed back: just fill what I think.
