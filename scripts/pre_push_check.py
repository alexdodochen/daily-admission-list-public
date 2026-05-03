"""
Pre-push safeguard — block leaks of private values to public mirror.

This repo's `origin` pushes to BOTH the private repo and the public mirror
(daily-admission-list-public). Anything tracked is visible publicly. Run
this before any push to ensure private SHEET_ID, LINE bot infrastructure,
and service account material never hit a tracked file.

Install once per clone:

    git config core.hooksPath .githooks

After that, `git push` will fail if any forbidden pattern is found in a
tracked file. To bypass for emergencies (don't), use `git push --no-verify`
— but you should never need to.

Forbidden content goes to `_*.md` / `_*.txt` files (gitignored).
"""
import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN = [
    (r"1DTIRNy10Tx3GfhuFq46Eu2_4J74Z3ZiIh7ymZtetZUI", "private SHEET_ID"),
    (r"line-reminder-bot-wvwo\.onrender\.com", "LINE bot URL"),
    (r"@500wcxsy", "LINE bot ID"),
    (r"/trigger-admission", "LINE bot endpoint /trigger-admission*"),
    (r"/trigger-(?:bed|schedule|reschedule|combined|cath-reminder|waitlist)",
     "LINE bot endpoint /trigger-*"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key PEM block"),
    # Note: service account email + JSON filename are metadata already
    # present in public git history; gitignore prevents the JSON CONTENT
    # itself from ever entering a commit, which is what actually matters.
]


def list_tracked():
    out = subprocess.check_output(["git", "ls-files"], text=True, encoding="utf-8")
    return out.splitlines()


def main():
    self_path = Path(__file__).resolve()
    repo_root = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, encoding="utf-8"
    ).strip())
    bad = []
    for rel in list_tracked():
        abs_path = (repo_root / rel).resolve()
        if abs_path == self_path:
            continue
        try:
            content = abs_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat, label in FORBIDDEN:
            if re.search(pat, content):
                bad.append((rel, label))
    if bad:
        sys.stderr.write("pre-push check FAILED — private values in tracked files:\n")
        for f, label in bad:
            sys.stderr.write(f"  {f}: {label}\n")
        sys.stderr.write(
            "\nMove the offending content to a gitignored file "
            "(_*.md / _*.txt / memory/_*.md) or scrub the value.\n"
        )
        sys.exit(1)
    print("pre-push check: OK")


if __name__ == "__main__":
    main()
