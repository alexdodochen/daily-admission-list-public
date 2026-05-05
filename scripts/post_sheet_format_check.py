"""
PostToolUse hook: after Bash runs a date-sheet-writing script, run
gsheet_utils.enforce_sheet_format(YYYYMMDD) so format never silently drifts.

Triggers when the Bash command contains any of:
    process_emr.py, generate_ordering.py, rebuild_date_sheet.py, refresh_emr.py
AND a 20YYMMDD token is present in argv.

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
)

DATE_RE = re.compile(r"\b(20\d{6})\b")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd = (payload.get("tool_input") or {}).get("command", "")
    if not any(s in cmd for s in TRIGGER_SCRIPTS):
        sys.exit(0)

    dates = sorted(set(DATE_RE.findall(cmd)))
    if not dates:
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
