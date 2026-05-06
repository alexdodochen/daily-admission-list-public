---
name: WEBCVIS Playwright helpers (permanent scripts)
description: Use these instead of writing one-off Playwright scripts for cathlab queries / DEL / schedule lookup
type: reference
---

Three permanent helpers in repo root — use them, don't reinvent:

## webcvis_query.py
```
python webcvis_query.py YYYYMMDD [YYYYMMDD ...] [--chart CHART] [--json]
```
Login + query 1+ dates. Returns chart/name/room/time/doctors/pdi/phc per row.
Importable: `from webcvis_query import query_dates`. Replaces ad-hoc query scripts (e.g. week-scan per CLAUDE.md rule 19).

## webcvis_del.py
```
python webcvis_del.py CHART YYYYMMDD [CHART YYYYMMDD ...]
```
Per-row checkbox approach (verified). See `feedback_webcvis_del_checkbox.md` for mechanism. Replaces one-off DEL scripts. Single login session for multiple DELs.

## schedule_lookup.py
```
python schedule_lookup.py DOCTOR WEEKDAY     # e.g. 黃鼎鈞 Thu
python schedule_lookup.py --weekday Thu       # all doctors
```
Reads 主治醫師導管時段表. Returns `[{session, room, second, third, tags, raw}, ...]`.
Importable: `from schedule_lookup import lookup`.
- Auto-resolves abbreviations: 浩→葉立浩, 晨→洪晨惠, 寬→葉建寬, 嘉→蘇奕嘉
- Skips non-doctor tags: 齡, 結構
- Per CLAUDE.md rule 15: 1st paren tag → second (attendingdoctor2); 2nd → third (recommendationDoctor)
- Caveat: 黃鼎鈞 Mon special rule (force second=洪晨惠) is NOT encoded here — caller handles.
