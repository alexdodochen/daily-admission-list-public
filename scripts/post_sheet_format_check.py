"""
PostToolUse hook: after Bash mutates a date sheet (any way), run
gsheet_utils.enforce_sheet_format(YYYYMMDD) so format never silently drifts.

Triggers when the Bash command contains BOTH:
    1. A date-sheet token  (20YYMMDD, e.g. 20260510)
    2. ANY sheet-mutation hint:
       - Named scripts: process_emr.py / generate_ordering.py /
         rebuild_date_sheet.py / refresh_emr.py
       - Direct gsheet_utils API: batch_write_cells, write_range,
         write_doctor_table, set_dropdown_from_range, format_header_row,
         enforce_sheet_format, create_worksheet
       - Generic gspread mutation: .update( , .batch_update(, .clear(,
         .append_row(, .insert_row(, .delete_rows(, .format(

Skips: explicit `enforce_sheet_format(` calls inside cmd (already a format
refresh — no need to double-fire) — but only if it's the ONLY hint.

Silent (exit 0, empty stdout) for non-matching commands so unrelated Bash
calls don't pollute the transcript.
"""
import json
import os
import re
import sys

TRIGGER_SCRIPTS = (
    "process_emr.py",
    "generate_ordering.py",
    "rebuild_date_sheet.py",
    "refresh_emr.py",
    "backfill_emr_age_gender.py",
)

SHEET_API_HINTS = (
    "batch_write_cells",
    "write_range",
    "write_doctor_table",
    "set_dropdown_from_range",
    "format_header_row",
    "create_worksheet",
    ".update(",
    ".batch_update(",
    ".clear(",
    ".append_row(",
    ".insert_row(",
    ".delete_rows(",
    ".format(",
)

DATE_RE = re.compile(r"\b(20\d{6})\b")


def _has_real_mutation(cmd: str) -> bool:
    """True if cmd hints at sheet mutation beyond a bare enforce_sheet_format call."""
    if any(s in cmd for s in TRIGGER_SCRIPTS):
        return True
    if any(h in cmd for h in SHEET_API_HINTS):
        return True
    return False


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd = (payload.get("tool_input") or {}).get("command", "")
    if not _has_real_mutation(cmd):
        sys.exit(0)

    dates = sorted(set(DATE_RE.findall(cmd)))
    if not dates:
        sys.exit(0)

    # Avoid double-fire: if cmd is purely an enforce_sheet_format call (no
    # other mutation API), skip — that command already refreshed format.
    other_hints = [h for h in SHEET_API_HINTS if h in cmd and h != "format_header_row"]
    if "enforce_sheet_format" in cmd and not other_hints \
       and not any(s in cmd for s in TRIGGER_SCRIPTS):
        sys.exit(0)

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, repo_root)
    os.chdir(repo_root)

    try:
        from gsheet_utils import enforce_sheet_format
    except Exception as e:
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"[format-check hook] import gsheet_utils failed: {e}",
            }
        }
        print(json.dumps(out))
        sys.exit(0)

    results = []
    for d in dates:
        try:
            enforce_sheet_format(d)
            results.append(f"OK {d}")
        except Exception as e:
            results.append(f"FAIL {d}: {e}")

    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "[format-check hook] enforce_sheet_format → " + "; ".join(results),
        }
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
