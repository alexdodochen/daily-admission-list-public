---
name: EMR cell first line = `XX y/o 性別`
description: Sub-table C col (raw EMR text) must start with `<age> y/o <gender>\n` so demographics are visible at a glance before EMR header.
type: feedback
---

Sub-table column C (raw EMR text) must always begin with a demographic line in the form `<age> y/o <gender>` (e.g. `63 y/o 男`), followed by `\n`, then the existing `【EMR來源門診：…】` header, then the raw EMR body.

**Why:** User instruction (5/8): «EMR 那一欄 請都在開頭顯示病人的年齡與性別». Reading EMR cells without demographics forces the reader to cross-reference main data — adding the prefix saves a glance.

**How to apply:**
- `process_emr.py` already does this for new writes — derives age from EMR DOB (parse_birth_from_raw → compute_age) and gender from `性別 : X`.
- `backfill_emr_age_gender.py` is the canonical helper for retroactive fixes — idempotent (skips rows already matching `^\d+ y/o [男女]`). Run on a date sheet or `--all-recent`.
- Format = `<age> y/o <gender>\n` (single line, no brackets, matches existing D-col summary convention).
- For `無本院一年內主治醫師門診紀錄` placeholder rows: still prepend the demographic line (source from main data G/H since EMR fetch returned nothing).
- Old archive sheets (4/06–4/12) where sub-table chart numbers don't match main data are skipped by the helper (logged as `no_main_demo`); leave as-is.
