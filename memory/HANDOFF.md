============================================
  HANDOFF — Last Updated: 2026-05-10 (5/10 evening session)
============================================

[What this session did]
  1. 5/11 admission list diff-update: image had 9 patients, sheet had 8 → inserted 馬允吉 (15943833) under 陳昭佑 + added L=急 for 梁淳斌; ran EMR fetch (PSVT / RF ablation auto-detected)
  2. EMR summary feature fully retired (was on-demand Gemini-fill since 5/4; now header-only D column, no auto / no on-demand, "做摘要" trigger removed)
  3. 5/11 N-V ordering written, then re-written with pin (黃鼎鈞#1, 黃睦翔#2 manual override)
  4. Added EXTRA_REMINDERS mechanism to skill_route_reminder.py — per-skill HARD-RULE injection on UserPromptSubmit; first user is admission-ordering with "read sub-table E fresh" rule
  5. New cross-repo sync rule: after every update, audit whether change should propagate to other 3 alexdodochen repos

[Current state]
  - Branch: main, 1 commit ahead of origin/main, modified files staged in working tree
  - Latest sheet state (20260511): main A-L 9 patients, sub-tables 6 doctors (張獻元/劉嚴文/陳昭佑(2)/黃鼎鈞/黃睦翔/陳儒逸(3)) all populated with EMR + F/G + E manual order, N-V written with 黃鼎鈞 pin
  - Format check (PostToolUse hook) passed on every write
  - No PHI leak; no public mirror push attempted yet

[Next steps]
  - 5/12 cathlab keyin (排導管 / key-in導管) — all 9 patients, 6 doctors all have Tue slots:
      劉嚴文 AM-H1 / 陳昭佑 AM-H2 / 陳儒逸 AM-C1 / 張獻元 PM-H2 / 黃鼎鈞 PM-C1 / 黃睦翔 PM-C2
    Special: 陳莊梅 H 欄=「建議再入院日2026/05/15」 — possibly skip 5/12 cathlab and reschedule; ask user
    Special: Mon 5/11 admit → Tue 5/12 cathlab; Mon-EP-洪晨惠 rule does NOT apply (that rule fires only on Mon cathlab)
  - User instruction: cross-repo audit — none of this session's changes auto-applied to other 3 repos; user should manually open them if propagating EXTRA_REMINDERS / cross-repo-sync rule

[Known issues / blockers]
  - None

[Don't repeat these mistakes]
  - DO NOT skip reading sub-table E col before asking user about multi-patient doctor order — user keys order into E directly. Hook now injects this reminder when admission-ordering trigger fires; respect it.
  - DO NOT call Gemini to fill D=EMR摘要 even on user request — feature retired 5/10. If user says "做摘要", explain feature is removed and offer to show C col raw.
  - DO NOT auto-edit other repos when implementing a generic change — list it in workflow-docs Step 6 audit and let user open the other repo separately.

[Relevant files]
  - CLAUDE.md (rules 18, 22; skill mapping table; sheet layout note)
  - .claude/skills/admission-emr-extraction.md (summary section reworded)
  - .claude/skills/admission-ordering.md (HARD RULE preamble + Step 1 code template with E parsing)
  - scripts/skill_route_reminder.py (EXTRA_REMINDERS dict + apply logic)
  - 每日入院清單工作流程.txt (D col placeholder description x2)
  - memory/feedback_no_emr_summary.md (rewritten in English with retirement policy)
  - memory/feedback_subtable_E_must_read_fresh.md (new)
  - memory/feedback_cross_repo_sync_check.md (new)

[Important memory files]
  - feedback_no_emr_summary.md (5/10 retirement update — D never written, no auto/no on-demand)
  - feedback_subtable_E_must_read_fresh.md (5/10 new — read E from live Sheet before computing N-V)
  - feedback_cross_repo_sync_check.md (5/10 new — propagate generic changes across alexdodochen repos)
