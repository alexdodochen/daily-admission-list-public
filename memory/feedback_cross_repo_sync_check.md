---
name: After every project update, check if other alexdodochen repos need parallel sync
description: User maintains 4 GitHub repos (daily-admission-list / line-reminder-bot / euroscore_NCKUH / cv-scheduling). After each project update, audit whether the change is reusable elsewhere — generic patterns (hooks, conventions, shared utilities) propagate; project-specific business logic stays.
type: feedback
---

**Rule (5/10):** After completing a non-trivial change in any one of the four projects, audit whether the change should be propagated to the other three. The user's GitHub: https://github.com/alexdodochen?tab=repositories

**Repo map (workflow-docs Step 6d, kept here for cross-checks):**

| Project folder | GitHub repo | Domain |
|---|---|---|
| `每日入院名單` | `daily-admission-list` (+ `daily-admission-list-public` mirror) | Admission list / cathlab / EMR automation |
| `LINE提醒機器人 (行政總醫師)` | `line-reminder-bot` | LINE bot for the admission group |
| `Euroscore` | `euroscore_NCKUH` | EuroSCORE II calculator |
| `排班` | `cv-scheduling` | Duty roster automation |

**What to propagate (audit checklist):**

| Change type | Propagate? | Why |
|---|---|---|
| New hook pattern (UserPromptSubmit / PostToolUse) | **Yes** — adapt per-project | Keeps Claude behavior consistent across projects |
| Memory rule about Claude conduct (read-fresh-from-source-of-truth, English-only artifacts, etc.) | **Yes** — copy verbatim | These are universal collaboration rules |
| Skill route-reminder mechanism | **Yes** — adapt skill list | Same anti-bypass logic applies everywhere |
| `enforce_sheet_format` / Google Sheets utilities | Sometimes — only if the target project also writes Sheets | Domain-specific |
| Patient-specific business logic (`feedback_chen_zewei_liu_bingyan_second`, `feedback_monday_ep_hong_chenhui_second`) | **No** | Admission-list-specific clinical rules |
| EMR scraping logic (Playwright, frame.aspx) | **No** unless target project also reads EMR | Currently only admission-list does |
| `.gitignore` PHI guards | **Yes** — every clinical project | Patient data must never leak |
| Cross-machine setup notes (`local_config.py`, Python WindowsApps stub) | **Yes** — every project that runs on user's machines | Universal env issue |

**How to apply:**

1. **End-of-session audit (Step 6 of workflow-docs):** before commit+push, ask "is any change in this session generic enough to apply to other repos?" Make the list explicit.
2. **For propagatable changes:** state the list and ask the user — don't auto-edit other repos. Each repo lives in its own folder; the user opens the relevant project to apply.
3. **For non-propagatable changes:** note in HANDOFF.md the rationale ("admission-list-specific, not propagated") so future-you doesn't re-audit.
4. **Don't push to other repos from this session.** Cross-repo edits happen when the user opens that project's Claude Code session — not from this one.

**Why:** User asked 5/10 「以後你這個專案的更新 都要看看需不需要同步改動到 https://github.com/alexdodochen?tab=repositories」. The four repos share the same author + collaboration patterns + Claude Code setup, so anti-bypass hooks, English-only rules, and PHI guards drift fast if not consciously synced.

**Example from this session (5/10):**
- ✅ Generic & should propagate: `EXTRA_REMINDERS` mechanism in `skill_route_reminder.py` (per-skill HARD-RULE injection). Useful pattern for any project with route-reminder hooks.
- ✅ Generic & should propagate: "read fresh from source-of-truth before computing" rule (we phrased it as `feedback_subtable_E_must_read_fresh.md` — admission-list-specific phrasing, but the principle generalizes).
- ❌ Specific: D=EMR摘要 column retirement, 馬允吉 patient diff-update, 黃鼎鈞-pin re-do — admission-list only.
