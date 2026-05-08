============================================
  HANDOFF — Last Updated: 2026-05-08 late evening
============================================

[What this session did]
  1. 5/10 admission audit + ordering: fixed 4 sheet fields, fetched 王福財 EMR (chart 09835366), corrected age 88→87 (EMR DOB-canonical). Generated N-V ordering for 8 patients with 許志新 pinned #1, mid 3 doctors random.shuffle (廖→詹→陳).
  2. New rule: Mon cathlab + EP procedure → second=洪晨惠 強制 (broader than 黃鼎鈞-Mon). Applied to 5/11: UPT 郭永泉/蘇招治 doctor2.
  3. cathlab_keyin.py.fix_diag extended to UPT attendingdoctor2 (was only third).
  4. New rule: EMR cell first line = `<age> y/o <gender>`. Built backfill_emr_age_gender.py + ran across 29 sheets (~210 cells).
  5. PostToolUse format hook upgraded: any Bash with date+sheet-mutation hint (was: 4 named scripts only). Catches inline `python -c batch_write_cells` that bypassed pre-5/8.
  6. V1 header drift fix on 14 sheets (每日續等清單→改期).
  7. Late-session — caught self-criticism + structural fix: built `lottery_utils.py` (weighted_doctor_shuffle), CLAUDE.md «Step → Skill mapping» HARD-RULE table, and `UserPromptSubmit` hook (`scripts/skill_route_reminder.py`) that injects system-reminder when user message matches a skill trigger phrase. 8 case smoke test passed.

[Current state]
  - Branch: main, latest commit pending push (commit 918c326 already pushed earlier this session; this round adds lottery_utils + skill_route_reminder hook + 4 new memory files + CLAUDE.md mapping table).
  - Sheets touched today: 20260510 (sub-tables shifted +2 rows for 2-blank-row gap, N-V ordering written, age/gender prefix on all 8 EMR cells), 20260511 cathlab UPT, 14 sheets V1 header fix, 29 sheets EMR prefix backfill.
  - User-level hooks (~/.claude/hooks/session_start_handoff.py + session_end_marker.py) live from prior session.
  - PROJECT-level hooks (this repo): PostToolUse format hook (broad trigger) + NEW UserPromptSubmit skill_route_reminder hook. Both registered in .claude/settings.json.

[Next steps]
  - 5/8 (Fri) admission workflow when ready: image OCR → lottery → EMR → ordering → SAME-DAY cathlab.
  - 5/9 (Sat): typically no admissions.
  - 5/11 cathlab is fully prepped (12 entries, 3 EP cases all have 洪晨惠).
  - When next session starts: SessionStart hook should auto-inject this HANDOFF + MEMORY. UserPromptSubmit hook will start advising on skill routing.
  - 5/10-14 sheets ordering N-V status: 5/10 NOW done; 5/11-14 still NOT done (only cathlab keyed).

[Known issues / pending]
  - 4/06–4/12 archive sheets EMR prefix (no_main_demo era) — only if user wants.
  - verify_cathlab.py false positives («不排導管», 「檢查」 substring too aggressive) — carried forward.
  - lottery_utils.py not yet wired into admission-ordering skill body — skill still has inline weighted-pool logic. Same algorithm, different code paths. If we want one source of truth, refactor skill to call helper. Optional.
  - Skill descriptions could mention lottery_utils for discovery — not done this session.

[Don't repeat]
  - Don't bypass skills when the user's message matches a skill trigger phrase. The new UserPromptSubmit hook will warn — read its system-reminder. The literal trigger phrases live in `scripts/skill_route_reminder.py` TRIGGERS dict + CLAUDE.md «Step → Skill mapping» table.
  - Don't write `python -c "...batch_write_cells..."` — fall back to Skill or named helper. Format hook now catches it (broad trigger), but inline still bypasses skill rules.
  - Don't `random.shuffle(names)` for doctor order — use lottery_utils.weighted_doctor_shuffle (or skill internals). *N tickets matter.
  - Don't ask the user «要隨機還是依默認» for doctor order — random is the only default.
  - Don't trust admission-list image age — always EMR DOB-based.
  - When creating/rebuilding date sheet, leave 2 blank rows between main A-L and first sub-table (not 1).

[Key artifacts touched]
  - Code: process_emr.py, cathlab_keyin.py, scripts/post_sheet_format_check.py
  - NEW: backfill_emr_age_gender.py, lottery_utils.py, scripts/skill_route_reminder.py
  - .claude/settings.json (UserPromptSubmit registered)
  - CLAUDE.md (rule 2 weighted, rule 15 Mon-EP broadened, rule 23 EMR prefix added, Step→Skill mapping table, Key Files updated)
  - Skills: admission-cathlab-keyin.md (rule 8 broadened), admission-emr-extraction.md (C col format)
  - Google Sheet: 20260510 (heavy edits), 20260511 (UPT 2 EP), 14×V1 header, 29×EMR prefix backfill
  - WEBCVIS: 5/11 doctor2 UPTs

[Memory files updated/added (this session)]
  - NEW memory/feedback_monday_ep_hong_chenhui_second.md
  - NEW memory/feedback_emr_cell_age_gender_prefix.md
  - NEW memory/feedback_age_emr_canonical.md
  - NEW memory/feedback_doctor_rr_auto_random.md
  - NEW memory/feedback_lottery_weighted_shuffle.md
  - NEW memory/feedback_main_to_subtable_two_blank_rows.md
  - NEW memory/feedback_skill_trigger_match_must_invoke.md
  - REWRITTEN memory/reference_post_sheet_format_hook.md (broader trigger)
  - memory/MEMORY.md (+7 index lines, 1 line edited)
