============================================
  HANDOFF — Last Updated: 2026-05-07 late evening
============================================

[What this session did]
  1. Reschedule 6 patients off 5/7 admission: 3 to 5/8 Fri (黃和泉/陳建諭/歐黃江),
     3 to 5/12 Tue (許慶山/宋哲光/蔡建添). V-mark on 5/7, created 5/8 (3 patients),
     rebuilt 5/12 (existing 7 + new 3 = 10 patients).
  2. Cathlab ADD: 黃和泉 5/8 H2 1801, 蔡建添 5/13 H1 2100. Other 4 left as-is per user.
  3. 5/8 ordering N-V (3 rows: 黃和泉/陳建諭/歐黃江).
  4. Re-discovered chk-checkbox DEL flow — already known on remote 5/6. Rebased + dedup.
  5. Deployed user-level SessionStart + SessionEnd hooks for cross-session continuity.

[Current state]
  - Branch: main, clean, pushed up to 68086ed.
  - Sheets touched: 20260507 (V col), 20260508 (new), 20260512 (rebuilt). All unhidden.
  - Cathlab on WEBCVIS:
      5/8: 22 entries (added 黃和泉; 陳建諭/歐黃江 stay at H2 1230/1530 per user).
      5/13: 12 entries (added 蔡建添; 許慶山/宋哲光 already at C1 0800).
  - User-level hooks live (effective NEXT session — not this one):
      ~/.claude/hooks/session_start_handoff.py — injects HANDOFF/MEMORY at session start
      ~/.claude/hooks/session_end_marker.py — writes memory/.session_end_marker.json on end
      Registered in ~/.claude/settings.json hooks.SessionStart + hooks.SessionEnd

[Next steps]
  - Verify next morning's 7:50 admission push for 5/8.
  - User may manual-DEL 陳建諭 (5/8 H2 1230) and 歐黃江 (5/8 H2 1530) if they want
    them re-keyed at H1 2100 non-schedule per rule 16 — they said leave for now.
  - Confirm next session that the hooks fire correctly: SessionStart should inject this
    HANDOFF + MEMORY into context. If not visible → check
    ~/.claude/hooks/session_start_handoff.py runs OK (test snippet in
    memory/reference_user_level_hooks.md).

[Known issues / blockers]
  - rebuild_date_sheet.py has A:G->A:H sub-table bug — workaround: inline write to A:H.
    See memory/reference_rebuild_date_sheet_subtable_bug.md.

[Don't repeat these mistakes]
  - Always git fetch + check origin/main BEFORE starting work. This session I duplicated
    5/6's DEL discovery + reinvented the chk-checkbox approach because I skipped fetch.
    Project CLAUDE.md Session-start step #1 says fetch + git status -sb first.
  - Don't auto-create date sheets without unhiding — user wants every sheet visible.
  - Don't import rebuild_date_sheet.rebuild_one — A:G bug; inline 8-col write to A:H.
  - When rebuilding an existing sheet, capture sub-table data from the JSON snapshot
    (tgt_state) BEFORE deletion, not from live (live may be wiped after a failed retry).
  - Use webcvis_del.py / webcvis_query.py / schedule_lookup.py as permanent helpers for
    WEBCVIS work — don't write _cathlab_*.py / _inspect_*.py one-offs.
  - Internal docs are ENGLISH ONLY (incl. MEMORY.md index hooks). Use Chinese only when
    talking to the user, or in `*工作流程*.txt`.

[Relevant files]
  - Permanent (added 5/6 from another machine):
      webcvis_del.py, webcvis_query.py, schedule_lookup.py
  - Skill: .claude/skills/admission-reschedule/SKILL.md (PHASE 5 references helpers)
  - Hooks (user-level, NOT in this repo):
      ~/.claude/hooks/session_start_handoff.py
      ~/.claude/hooks/session_end_marker.py
      ~/.claude/settings.json (hooks section)

[Important memory files]
  - memory/reference_user_level_hooks.md (NEW — hook locations + testing)
  - memory/feedback_new_sheet_must_unhide.md (5/7 — unhide newly created sheets)
  - memory/reference_rebuild_date_sheet_subtable_bug.md (5/7 — 8-col write bug)
  - memory/feedback_webcvis_del_checkbox.md (5/6 — chk-checkbox DEL mechanism, primary)
  - memory/reference_webcvis_helpers.md (5/6 — 3 permanent Playwright helpers)
  - Global ~/.claude/CLAUDE.md: language policy strengthened — internal docs ENGLISH ONLY.
