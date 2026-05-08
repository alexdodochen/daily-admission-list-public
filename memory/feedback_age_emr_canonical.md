---
name: Age = EMR DOB-based, NOT admission-system display
description: Patient age in Sheet H column must be computed from EMR DOB (today − DOB, with birthday-this-year check), not from the admission-list image's displayed age — admission system shows EMR_age+1 (likely 虛歲-style).
type: feedback
---

When updating patient age (main data H col), the canonical source is **EMR's DOB-derived age** — not the age shown in the daily admission-list image.

**Why:** User instruction (5/8): «以EMR資料為準 ... 年齡計算都要EMR的計算原則為準喔». Discovered when 5/10 image showed age=64 for 邱啓芳 but EMR DOB 1962/08/15 → today 2026/05/08 yields 63. Same +1 offset across 6 patients (邱啓芳, 陳榮吉, 郭永泉, 蘇招治, 林魏金英, 陳清發). The admission system likely uses 虛歲 or admit-date-based rounding; EMR uses true DOB-based age. EMR is canonical.

**How to apply:**
- `process_emr.py compute_age(birth, admission_date)` is the canonical implementation.
- When user shows an admission-list image and asks "is the age right?" — DON'T trust the image. Fetch/read EMR (or cached `emr_data_<date>.json`) for DOB → recompute → compare.
- If image age ≠ EMR age, sheet age should match EMR.
- Same rule applies to the demographic prefix added to EMR cells (`feedback_emr_cell_age_gender_prefix.md`).
- This is an EMR-vs-image conflict only; if the image is the only source (e.g. patient just admitted, EMR not yet fetched), use image age temporarily then update on next EMR fetch.
