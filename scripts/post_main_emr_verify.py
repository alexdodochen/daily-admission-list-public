"""PostToolUse hook: after `process_emr.py YYYYMMDD` finishes, run
`verify_main_emr.py YYYYMMDD` to cross-check every main A-L row's
姓名/性別/年齡 against EMR divUserSpec.

Why: process_emr only corrects rows whose chart is present in
emr_data_<date>.json (i.e., freshly fetched). Existing rows (from
prior sessions or whose chart wasn't re-fetched) get no name/age check.
After the 5/12 「董相路 vs 董相鉻」 incident the user added this rule:
「主表做完後 都用EMR那個欄位確認姓名 年紀 性別」.

Triggers when the Bash command contains:
    process_emr.py  AND  a 20YYMMDD token.

Skips silently if:
- No `_emr_session.txt` present (no session URL → cannot verify)
- Hook can't import or run verify_main_emr (any error)
The verify script itself is also silent-on-failure.
"""
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
except Exception:
    pass

DATE_RE = re.compile(r"\b(20\d{6})\b")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd = (payload.get("tool_input") or {}).get("command", "")
    if "process_emr.py" not in cmd:
        sys.exit(0)

    dates = sorted(set(DATE_RE.findall(cmd)))
    if not dates:
        sys.exit(0)

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    session_path = os.path.join(repo_root, "_emr_session.txt")
    if not os.path.exists(session_path):
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "[emr-verify hook] no _emr_session.txt — run fetch_emr.py first to enable EMR verify",
            }
        }
        print(json.dumps(out))
        sys.exit(0)

    results = []
    for d in dates:
        try:
            proc = subprocess.run(
                [sys.executable, "verify_main_emr.py", d],
                cwd=repo_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=240,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            tail = (proc.stdout or "").strip().splitlines()
            tail_msg = tail[-1] if tail else "no output"
            results.append(f"{d}: {tail_msg}")
        except subprocess.TimeoutExpired:
            results.append(f"{d}: timeout")
        except Exception as e:
            results.append(f"{d}: error {e}")

    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "[emr-verify hook] verify_main_emr → " + "; ".join(results),
        }
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
