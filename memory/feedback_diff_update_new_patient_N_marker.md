---
name: diff-update-new-patient-N-marker
description: Newly added patients in diff-update must be marked "N" in sub-table H 註記 column so user can spot them at a glance
metadata:
  type: feedback
---

When `admission-image-to-excel` diff-update inserts a new patient (chart not previously in sheet), **write "N" to that patient's sub-table H 註記 column** in the same write pass.

**Why:** During the week, users diff-update sheets multiple times as the admission system updates. Without a marker, the new row blends in and is easy to miss when reviewing what changed. "N" = newly-added; user scans H col for N to triage what needs fresh EMR/ordering.

**How to apply:**
- Trigger condition: existing date sheet + chart in image not in sheet → ADD path of [[diff-update-subtable-minimal]]
- Write: sub-table row H col = `"N"` (string literal, single char)
- Apply alongside the main A-L insert + sub-table title (N人) bump
- Do **not** add to: existing rows (preserve their H notes), DEL'd rows (they're removed entirely)
- Pre-existing H content on a new row (rare — usually empty for fresh insert): append `" N"` instead of overwriting; new mark wins visibility but don't lose existing context

5/15 origin: 王玉珍 case + 李全福 5/18 case — user wanted to spot diff-inserts without diffing column-by-column.
