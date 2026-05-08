---
name: Post-sheet-write format hook (broad trigger)
description: PostToolUse hook in .claude/settings.json runs enforce_sheet_format(YYYYMMDD) after ANY Bash command mutating a date sheet — covers named scripts AND inline `python -c` with gspread mutation calls.
type: reference
---

`scripts/post_sheet_format_check.py` is a PostToolUse:Bash hook that auto-runs `enforce_sheet_format(YYYYMMDD)` so format never silently drifts.

**Trigger condition (both must match):**
1. A `20YYMMDD` date token (sheet name) in the cmd
2. Any sheet-mutation hint:
   - Named scripts: `process_emr.py` / `generate_ordering.py` / `rebuild_date_sheet.py` / `refresh_emr.py` / `backfill_emr_age_gender.py`
   - Direct gsheet_utils API: `batch_write_cells`, `write_range`, `write_doctor_table`, `set_dropdown_from_range`, `format_header_row`, `create_worksheet`
   - Generic gspread mutation: `.update(`, `.batch_update(`, `.clear(`, `.append_row(`, `.insert_row(`, `.delete_rows(`, `.format(`

**Skip:** bare `enforce_sheet_format(<date>)` calls — that command IS a format refresh, no need to double-fire.

**Why this matters:** Pre-5/8 the hook only matched 4 named scripts. Inline `python -c "...batch_write_cells..."` bypassed it → format drifted on 5/10 (5/8 incident). Broad-trigger upgrade (5/8) catches all sheet-mutating Bash, including future ad-hoc inline scripts.

**Activation caveat:** New `.claude/settings.json` only activates next session or via `/hooks` reload. **Script content updates** (changing the .py the hook calls) take effect immediately on next Bash. Both files are tracked → push propagates to other machines.

**Don't bypass:** if you find a sheet write that isn't picked up, ADD the new pattern to `SHEET_API_HINTS` or `TRIGGER_SCRIPTS` in the hook script — don't manually call `enforce_sheet_format` every time.
