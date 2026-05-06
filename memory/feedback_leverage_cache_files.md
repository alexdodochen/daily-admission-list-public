---
name: Leverage retained cache files instead of re-running
description: User intentionally keeps a week of emr_data_*.json / cathlab_patients_*.json — reuse them, don't re-fetch / re-compute, especially for reschedule moves
type: feedback
---

The user keeps roughly a week of cache files in the project root on purpose so Claude can reuse them across sessions:

- `emr_data_YYYYMMDD.json` — Playwright-fetched EMR snapshot
- `cathlab_patients_YYYYMMDD.json` — generated cathlab keyin payload
- `cathlab_patients_reschedule.json` — last reschedule batch

**Why:** Re-fetching wastes the user's time, hits API quotas, and risks losing manual fixes already encoded in the JSON. Most importantly: cached data is the cleanest source for downstream work — especially **reschedule** (moving a patient between dates), where the source-date JSON already has the chart / room / time / pdijson / phcjson the target date needs.

**How to apply:**
- At session start, after running `check-previous-progress`, also `Glob` for `emr_data_*.json` and `cathlab_patients_*.json` to see what's available.
- For any operation on date X: check `emr_data_X.json` / `cathlab_patients_X.json` first — if present and content looks valid, reuse instead of running `fetch_emr.py` / regenerating JSON.
- For **reschedule** (move patient from date A to date B): pull the patient block from `cathlab_patients_A.json` (or build from `emr_data_A.json`) and adapt for date B. Don't re-fetch EMR or re-derive cathlab payload from scratch — the cache already has the correct pdijson/phcjson IDs the user verified.
- Only re-run when: (a) cache is older than a week / missing, (b) source data has changed (sub-table edited after cache was made), or (c) user explicitly asks for a refresh.
- Never delete these JSON files in cleanup unless explicitly instructed — they are deliberate, not scratch. (Distinguishes them from `_*.py` / `_*.txt` scratch.)

Source quote (5/6 session):
> 我留下一周的cache資料就是你之後做工可以拿來參考的 就不用每次重跑啊 包括改期也可參考之前資料 做搬移應該比較容易吧
