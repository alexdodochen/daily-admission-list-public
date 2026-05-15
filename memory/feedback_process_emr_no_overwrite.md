---
name: process_emr.py must not overwrite human-vetted F/G
description: Auto-detect F/G in sub-tables is fire-and-forget — re-runs preserve any non-empty F/G that the human has already set. Rule changes in DIAG_RULES / CATH_RULES / PLAN_*_RULES must never silently rewrite vetted data.
type: feedback
---

User instruction (5/15): «你這個學習過程不要去改我原本設定好的FG喔».

Auto-detect F (術前診斷) / G (預計心導管) is best-effort. Once the human has reviewed and (possibly) edited the value in the Sheet, that vetted value is authoritative. Subsequent `process_emr.py` runs (e.g. after rule improvements, re-fetch with fresh session URL, backfill) must NOT overwrite it.

## Implementation
`process_emr.py main()` reads each patient row from the sub-table BEFORE writing:
```python
cur_f = (row[5].strip() if len(row) > 5 else '')
cur_g = (row[6].strip() if len(row) > 6 else '')
...
if f_diag and not cur_f:
    updates.append((f'F{pr}', f_diag))
if g_cath and not cur_g:
    updates.append((f'G{pr}', g_cath))
```

C (raw EMR) is still always overwritten — that's mechanical text from EMR, not a human judgment.

## Why this matters
On 5/15 a rule-learning session improved auto-detect from 58% F-disagreement baseline to 26% (`feedback_fg_autodetect_learning.md`). If `process_emr.py` re-ran on the 248-row historical corpus, every vetted F/G across two weeks of admissions would have been overwritten by the new (still imperfect) rules — and disagreement-finding would become impossible because the ground truth would be gone.

Safe pattern: rules can improve indefinitely. Existing vetted F/G is preserved. New patients (empty cells) get the latest rules. Win-win.

## How to apply
- Default: never overwrite non-empty F/G.
- If user explicitly says «重跑 EMR 全部覆寫» / «force re-detect all» → consider a `--force` flag (not yet implemented; if asked, add to `process_emr.py argparse` rather than removing the safety).
- Rule of thumb for ANY auto-detect feature: read current value first, write only when empty.

Related: [[F/G auto-detect learning from 248-row corpus]], [[Sub-table E col (manual order) must be read fresh]].
