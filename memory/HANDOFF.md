============================================
  HANDOFF — Last Updated: 2026-05-18 (afternoon)
============================================

[What this session did]
  1. Sister repo (line-reminder-bot) feature: dual-source admission push
     (private + public mirror sheet) + empty-guard ("no N-U data -> don't push",
     applies to both sources). Implemented locally, NOT yet pushed.
  2. Updated gitignored memory (_reference_line_reminder_bot, _feedback_line_
     public_push_skip_if_empty) + user-level admission-line-push skill to match.
  3. No daily-admission workflow data changes this session (no sheet writes).

[Current state]
  - Branch: main, clean.
  - Sister repo: cloned to C:\Users\dr\repos\line-reminder-bot, commit on main
    local-only (unpushed).
  - Latest daily-admission commit: 7e1e518 (unchanged this session).

[Next steps]
  - !! USER ACTION: push the sister-repo commit. Claude's git push to that repo
    is hard-blocked (data-exfil class, not overridable). User must run, e.g.:
      ! cd /c/Users/dr/repos/line-reminder-bot && git push origin main
    (forward-slash path — backslash path mangles in Git Bash). Then Render
    auto-deploys; verify via the trigger endpoint (details in gitignored
    memory/_reference_line_reminder_bot.md).
  - Resume daily-admission workflow: 20260519 lottery/ordering still pending
    per prior handoff (emr_data_20260519.json exists; verify sheet state first).

[Known issues / blockers]
  - Sister-repo commit unpushed: Claude cannot push it; waiting on user.

[Don't repeat these mistakes]
  - `! cd C:\path\with\backslashes && ...` fails in Git Bash (backslashes eaten).
    Use forward slashes or quote the path.
  - git push to repos outside trusted source control with embedded private IDs
    is hard-blocked for Claude — don't retry; hand to user immediately.

[Relevant files]
  - C:\Users\dr\repos\line-reminder-bot\line_reminder_bot\admission_push.py (local commit)
  - _line_bot_public_push_spec.md (gitignored, project root — spec/background)

[Important memory files]
  - memory/_reference_line_reminder_bot.md  (updated: repo now cloneable + push caveat)
  - memory/_feedback_line_public_push_skip_if_empty.md  (updated: implemented, unpushed)
