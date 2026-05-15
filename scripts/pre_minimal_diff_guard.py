"""
PreToolUse Bash guard: block full-sheet rewrites on existing date sheets.

Fires when ALL of these are true:
  1. Command targets a date sheet (`20YYMMDD` token)
  2. Command contains a "full wipe" pattern:
     - `batch_clear(['A` or `batch_clear(["A`  (clears column A onward)
     - `ws.clear()`
     - `clear_area(`
     - `batch_clear([` with a range that includes row 2
     - bulk `unmergeCells` covering ≥30 rows + subsequent writes
  3. Command is NOT one of the sanctioned rebuilders:
     - `rebuild_date_sheet.py` (legitimate clean-slate rebuild)
     - `process_emr.py` (writes cell-by-cell, doesn't clear)

When triggered, exits 2 with stderr telling Claude to use minimal-diff
(INSERT/DELETE specific rows, preserve existing sub-table EMR/F/G/H).

Rule origin (5/15): user explicit instruction after I wiped 6 patients' EMR
on 5/18 by `batch_clear(['A2:V50'])` + rebuild. Per
memory/feedback_diff_update_subtable_minimal.md the diff-update rule was
already documented (5/4) — I broke it again, so hook-level enforcement.

To bypass legitimately (full rebuild on broken sheet):
  - Use rebuild_date_sheet.py (driven by admission-sheet-rebuild skill)
  - Or set env: ALLOW_FULL_SHEET_WIPE=1 in the same Bash invocation
"""
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
except Exception:
    pass

DATE_RE = re.compile(r"\b(20\d{6})\b")

WIPE_PATTERNS = [
    re.compile(r"batch_clear\(\s*\[\s*['\"]A[1-9]"),   # batch_clear(['A2:..., ['A10:...
    re.compile(r"\.clear\(\s*\)"),                       # ws.clear()
    re.compile(r"clear_area\("),                         # clear_area(...)
    re.compile(r"clear_range\("),                        # clear_range(...)
]

SANCTIONED_REBUILDERS = (
    "rebuild_date_sheet.py",
    "refresh_emr.py",     # batches process_emr — handled internally
)


def _is_full_wipe(cmd: str) -> bool:
    return any(p.search(cmd) for p in WIPE_PATTERNS)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd = (payload.get("tool_input") or {}).get("command", "") or ""
    if not cmd:
        sys.exit(0)

    # Sanctioned rebuilders are exempt
    if any(s in cmd for s in SANCTIONED_REBUILDERS):
        sys.exit(0)

    # Explicit override
    if "ALLOW_FULL_SHEET_WIPE=1" in cmd:
        sys.exit(0)

    if not DATE_RE.search(cmd):
        sys.exit(0)

    if not _is_full_wipe(cmd):
        sys.exit(0)

    # BLOCK with explanation Claude will see
    msg = (
        "[minimal-diff guard] BLOCKED — this command looks like a full-sheet wipe "
        "on a date sheet (batch_clear / .clear() / clear_area covering main+sub-table area).\n"
        "\n"
        "Diff-update HARD RULE (memory/feedback_diff_update_subtable_minimal.md):\n"
        "  • Sub-table rows that EXIST in both new + old → DO NOT TOUCH\n"
        "  • Rows only in new → INSERT (sheets API insertRange + write A=name, B=chart)\n"
        "  • Rows only in old → DELETE (sheets API deleteRange)\n"
        "  • Update doctor title 「（N人）」 count after add/delete\n"
        "  • Empty doctor block → delete entire title+header+gap together\n"
        "\n"
        "Why blocked: full clear wipes manual H notes (e.g. '全麻 Affera', '劉秉彥'), "
        "user-set E 手動序, and the auto-detected F/G the user has already vetted. "
        "Reconstructing from emr_data JSON loses anything not stored in JSON.\n"
        "\n"
        "Fix path:\n"
        "  1. Compute existing_charts vs new_charts per doctor block\n"
        "  2. For to_add: use sheets API insertRange + batch_write_cells for A/B\n"
        "  3. For to_remove: use sheets API deleteRange\n"
        "  4. For to_keep: SKIP — do not read, do not rewrite\n"
        "  5. Update doctor block counts in batch_write_cells\n"
        "  6. enforce_sheet_format at end\n"
        "\n"
        "Legitimate full rebuild → use rebuild_date_sheet.py (admission-sheet-rebuild skill).\n"
        "Forced override → prefix command with ALLOW_FULL_SHEET_WIPE=1 (and justify in chat)."
    )
    sys.stderr.write(msg + "\n")
    sys.exit(2)


if __name__ == "__main__":
    main()
