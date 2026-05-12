============================================
  HANDOFF — Last Updated: 2026-05-12 (Tue evening session)
============================================

[What this session did]
  1. Built EMR divUserSpec verify hook: verify_main_emr.py + scripts/post_main_emr_verify.py + fetch_emr.py auto-saves session URL to `_emr_session.txt`. Fires after `process_emr.py YYYYMMDD` → cross-checks every main A-L row's 姓名/性別/年齡 against EMR divUserSpec, auto-corrects mismatches. Rule origin: 5/12 user mandate after 董相路/董相鉻 OCR-vs-sheet mismatch.
  2. Race-condition lesson: divUserSpec refresh is async vs leftFrame — must stamp divUserSpec.innerText before BTQuery click. Initial verify version waited only on leftFrame → off-by-one corrupted 9 cells (謝翠英→董相路 etc.), reverted, fixed.
  3. 5/13 sheet diff-update: image had 8 patients, sheet had 5 → added 徐郁貞 (黃鼎鈞) + 王坤楓 (黃睦翔, 無資料病人) + 段寶春 (柯呈諭; EMR fixed name 段晉春→段寶春). K col updates 譚翠翠 / 張皓傑. Verified 董相路 name via EMR re-fetch (sheet was correct, image OCR misread 路→鉻).
  4. 5/14 sheet diff-update: image had 4 patients, sheet had 3 → added 李高玉珠 (劉嚴文; EMR fixed name 李高玉→李高玉珠, age 85→84). 王玉珍 K col `3` → `3(5/11無床延期)` + sub-table H note.
  5. Cathlab keyin: 5/13 cathlab — 9 charts SKIP exists (all pre-keyed), 9 UPT OK. 5/14 cathlab — 3 ADD (徐郁貞 C1 0601, 段寶春 C2 1800, 王坤楓 H2 1800) + 5 SKIP exists, 8 UPT OK (including 黃鼎鈞 existing 3 補上 second=葉立浩 + third=洪晨惠).

[Current state]
  - Branch: main, fast-forward rebased to origin/main earlier this session
  - Local mods staged for commit: verify_main_emr.py, scripts/post_main_emr_verify.py, fetch_emr.py (URL save), .claude/settings.json (+2nd hook), CLAUDE.md (Key Files += verify + hook), memory/*.md (3 new + index)
  - Pre-existing local mods carried in: gsheet_utils.py (chart_no TEXT format in write_doctor_table), scripts/post_sheet_format_check.py + skill_route_reminder.py (stdin encoding fix), memory/feedback_subtable_order_from_main_table.md
  - 5/13 sheet (20260513): 8 patients, sub-tables 黃鼎鈞(4)/柯呈諭(2)/林佳凌(1)/黃睦翔(1) — EMR fully filled (王坤楓 = 無資料病人)
  - 5/14 sheet (20260514): 4 patients, sub-tables 陳儒逸(3)/劉嚴文(1) — EMR fully filled
  - WEBCVIS cathlab 5/13: 15 total entries, all 9 our patients OK; 5/14: 12 total entries, all 8 our patients OK
  - EMR verify hook tested end-to-end via manual hook payload — pipeline works

[Next steps]
  - Activate new hook in current Claude session: `/hooks` reload OR start fresh session (script edits already live; settings.json hook entry needs reload)
  - User must confirm: 李高玉珠 K col `3(6/13無床)` — `6/13` likely OCR typo for `5/13` (6/13 is future date, doesn't fit context). Need visual recheck of image.
  - Optional: 5/14 admit (4 patients) → 5/15 cathlab keyin not yet done. 王玉珍 17222056 already on 5/15 11:00 C1 (from her reschedule). If proceeding: 3 charts to ADD — 李高玉珠 (劉嚴文 Fri slot), 陳謝秀英 (陳儒逸 Fri slot), 林森政 (陳儒逸 Fri slot). User didn't explicitly request this.

[Known issues / blockers]
  - 李高玉珠 K col date ambiguity (6/13 vs 5/13) — awaiting user confirmation

[Don't repeat these mistakes]
  - DO NOT ask user to visually confirm name discrepancies between OCR and sheet — re-fetch EMR divUserSpec (it works even for no_visit charts). See feedback_name_conflict_refetch_emr.md.
  - DO NOT wait only on leftFrame when reading divUserSpec — divUserSpec lives in a different frame and refreshes async; must stamp divUserSpec.innerText and wait for sentinel-clear. See feedback_emr_verify_divuserspec_race.md.
  - DO NOT batch-apply verify corrections before validating the first one or two — if a race bug exists it silently corrupts every row. Spot-check first chart's output before applying.

[Relevant files]
  - verify_main_emr.py (new)
  - scripts/post_main_emr_verify.py (new)
  - fetch_emr.py (URL save at startup)
  - .claude/settings.json (2nd PostToolUse hook entry)
  - CLAUDE.md (Key Files += verify + hook entries)
  - _emr_session.txt (gitignored, current session URL)

[Important memory files]
  - reference_post_main_emr_verify_hook.md (new — hook design + activation)
  - feedback_emr_verify_divuserspec_race.md (new — race-fix rule with example)
  - feedback_name_conflict_refetch_emr.md (new — re-fetch instead of asking user)
