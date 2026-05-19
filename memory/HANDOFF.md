============================================
  HANDOFF — Last Updated: 2026-05-19 (late)
============================================
(No patient names / chart numbers — origin dual-routes to a public mirror.
 Sister-repo / LINE infra specifics live in gitignored memory/_*.md.)

[What this session did]
  1. Sibling app daily_admission_list_app (排班 Key班 DayList APP): Step 5
     editable dry-run (時段/房/時間/2nd-doctor/註記 overrides + auto time
     by session), OCR '?' stripped at source, EMR collapse UI contrast,
     ②/③ button relabels, 房→dropdown, black borders. Commits e9254d6 +
     acb012f — pushed (triggers public-app mirror Action).
  2. Rebuilt + repackaged the 麒翔 deliverable zip (PyInstaller full rebuild
     once, then fast-path loose-file patch). See new memory reference.
  3. line-reminder-bot: dual-source push (1ea1571, pushed/deployed/verified)
     + date-gated empty behavior @2026-06-01 (22d92f2).

[Current state]
  - daily-admission-list repo: main, clean, in sync (+ this workflow-docs sync).
  - daily_admission_list_app: main = acb012f, pushed.
  - line-reminder-bot clone (C:\Users\dr\repos\line-reminder-bot): main =
    22d92f2, AHEAD 1 — NOT pushed.

[Next steps]
  - !! USER ACTION: push line-reminder-bot date-gate commit 22d92f2. Claude
    push to that repo is hard-blocked. User runs:
      ! cd /c/Users/dr/repos/line-reminder-bot && git push origin main
    (forward-slash path). Behavior change only visible from 2026-06-01.
  - Daily-admission workflow: resume normally on next admit screenshot.

[Known issues / blockers]
  - line-reminder-bot 22d92f2 unpushed (waiting on user; carried 2 sessions).
  - 6/1+ side effect (by design): on normal days the LINE group gets TWO
    messages (real private list + public "無入院序資料" notice).

[Don't repeat these mistakes]
  - `! cd C:\back\slash\path` mangles in Git Bash — use /c/Users/... .
  - git push to repos outside trusted source control w/ embedded private ID
    is hard-blocked for Claude — hand to user, don't retry.
  - Re-zip deliverables with Python zipfile, NOT PowerShell 5.1 (.NET writes
    spec-violating backslash entries).
  - .py change in the app → needs full PyInstaller rebuild (frozen PYZ);
    static/templates are loose → fast-path patch only.

[Relevant files]
  - C:\Users\dr\Downloads\Y\排班 Key班 DayList APP\ (sibling app, own repo)
  - C:\Users\dr\Downloads\Y\每日入院名單 for 麒翔.zip (deliverable)

[Important memory files]
  - memory/reference_qixiang_app_deliverable.md  (NEW — build/zip pipeline)
  - memory/_feedback_line_public_push_skip_if_empty.md  (date-gate table)
  - memory/_reference_line_reminder_bot.md  (repo cloneable + push caveat)
