---
name: PostToolUse hook auto-runs enforce_sheet_format after sheet writes
description: scripts/post_sheet_format_check.py fires after Bash runs process_emr/generate_ordering/rebuild_date_sheet/refresh_emr.py with a YYYYMMDD arg
type: reference
---

`.claude/settings.json` has a PostToolUse Bash hook that runs `scripts/post_sheet_format_check.py` after every Bash tool call.

**What it does:**
- Reads stdin JSON (the Bash command from `tool_input.command`)
- Matches against trigger scripts: `process_emr.py`, `generate_ordering.py`, `rebuild_date_sheet.py`, `refresh_emr.py`
- Extracts any `20\d{6}` token from the command (the date arg)
- For each matched date → calls `gsheet_utils.enforce_sheet_format(date)`
- Returns `additionalContext` JSON describing OK/FAIL per date

**Silent for non-matching commands** (most Bash calls), so transcript stays clean.

**Doesn't fire for:**
- Manual `python -c "..."` snippets (even if they write to sheets)
- One-off `_*.py` scratch scripts (doesn't match trigger list)
- enforce_sheet_format already-existing sheets that have format drift but aren't being written today

**Activation caveat:**
- Hook is registered in `.claude/settings.json` but the settings watcher only watches dirs that had a settings file at session start.
- New `.claude/settings.json` doesn't activate mid-session — needs `/hooks` reload OR next session.

**Trigger list maintenance:**
- If a new sheet-writing script appears (e.g. one for ordering, one-off rebuild), add to the `TRIGGER_SCRIPTS` tuple in `scripts/post_sheet_format_check.py`.
