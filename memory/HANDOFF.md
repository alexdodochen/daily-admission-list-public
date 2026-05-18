============================================
  HANDOFF — Last Updated: 2026-05-19
============================================
(No patient names / chart numbers — origin dual-routes to a public mirror.
 Sister-bot infra specifics live in gitignored memory/_*.md, not here.)

[What this session did]
  1. Sister repo (line-reminder-bot) admission push: dual-source (private +
     public mirror sheet). commit 1ea1571 — PUSHED, deployed, verified live
     (curl returned correct SENT-private / SKIP-public).
  2. Added date-gated empty behavior at 2026-06-01 (GATE_DATE=20260601):
     before 6/1 private-empty pushes a no-data notice / public-empty skips;
     from 6/1 the two swap (private-empty skips / public-empty pushes notice).
     commit 22d92f2 — LOCAL ONLY, NOT pushed.
  3. (Prior session, same date) 20260519 ordering + 20260520 cathlab keyin
     completed & verified — nothing pending there.

[Current state]
  - daily-admission repo: main, clean, in sync with origin.
  - Sister repo clone C:\Users\dr\repos\line-reminder-bot: main ahead 1
    (22d92f2 unpushed).
  - Latest daily-admission pushed commit: 1d3d35c (+ this workflow-docs sync).

[Next steps]
  - !! USER ACTION: push the sister-repo date-gate commit. Claude's push to
    that repo is hard-blocked (data-exfil class). User runs:
      ! cd /c/Users/dr/repos/line-reminder-bot && git push origin main
    (forward-slash path — backslashes mangle in Git Bash). Render auto-deploys.
  - Verify after deploy via the trigger endpoint (specifics in gitignored
    memory/_reference_line_reminder_bot.md). Today (5/19) is pre-gate so
    behavior change only observable from 2026-06-01.
  - Daily-admission workflow: resume normally on next admit screenshot.

[Known issues / blockers]
  - Sister-repo commit 22d92f2 unpushed: Claude cannot push; waiting on user.
  - PHI-vs-public-mirror: memory/HANDOFF dual-push to a PUBLIC mirror;
    pre_push_check.py does NOT scrub patient names/MRN. Keep raw PHI and LINE
    infra strings out of all tracked docs.
  - 6/1+ side effect: on normal days the group will get TWO messages (real
    private list + public "無入院序資料" notice). User-requested; not a bug.

[Don't repeat these mistakes]
  - `! cd C:\path\with\backslashes` fails in Git Bash — use /c/Users/... .
  - git push to external repo w/ embedded private ID is hard-blocked for
    Claude — hand to user immediately, don't retry.
  - Never put patient names / chart numbers / LINE infra in tracked docs.

[Relevant files]
  - C:\Users\dr\repos\line-reminder-bot\line_reminder_bot\admission_push.py
  - _line_bot_public_push_spec.md (gitignored) — being retired (superseded by memory)

[Important memory files]
  - memory/_feedback_line_public_push_skip_if_empty.md  (date-gate table, side-effect)
  - memory/_reference_line_reminder_bot.md  (repo cloneable + push caveat)
