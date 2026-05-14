---
name: doctor-name-variant-lin-jialing
description: EMR uses 林佳淩 (淩 三點水), our sheets/code use 林佳凌 (凌 二點水) — fetch_emr.py NAME_ALIASES handles both variants; expect more doctors with similar character mismatches
metadata:
  type: feedback
---

`fetch_emr.py` had been silently failing for **every** 林佳凌 admission patient over 2+ weeks (5/13 董相路 confirmed). Root cause: EMR clinic links use **林佳淩 (淩, 氵 three-water)**; our sheets / `cathlab_keyin.py` / `schedule_readable.txt` / 工作流程.txt all use **林佳凌 (凌, 冫 two-water)**. JS `t.includes('林佳凌')` never matched `'林佳淩'` → fall through to fallback whitelist (`劉秉彥/趙庭興/蔡惟全/許志新/陳柏升/李貽恒`) which doesn't include either variant → `no_visit`.

Verification (5/14): re-ran `fetch_emr.py 08473654 林佳凌` → matched `(門診)2026/04/24 林佳淩 心臟血管科07診`, returned 883-char EMR.

**Why:** Patient names in EMR are sourced from HR records; doctor self-registered with 淩. Our schedule sheets were typed by hand and used the more common 凌. Without normalisation, EMR matching fails 100% of the time for her patients.

**How to apply:**
- `fetch_emr.py` `NAME_ALIASES` dict expanded — `林佳凌`/`林佳淩` accept both variants when matching link text.
- **Don't** edit sheet content / cathlab_keyin / schedule_readable to "fix" the spelling — alignment in `fetch_emr.py` is the right surface (one place to maintain, doesn't disturb user-facing materials).
- **Watch for similar failures**: any other doctor with persistent 0 EMR matches → check EMR link text manually for character variants (凌/淩, 鈞/鈞, 諭/諭, 翔/翔, 簡繁/異體字). Add to `NAME_ALIASES` rather than rewriting all systems.
- Quick diagnostic: `python -c "import json; d=json.load(open('emr_data_YYYYMMDD.json')); [print(c, v) for c,info in d.items() for v in [info.get('visit','')]]"` — patients with empty visit + matched_doctor=False are the failing ones.
