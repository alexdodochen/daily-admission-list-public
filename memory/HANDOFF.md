============================================
  HANDOFF — Last Updated: 2026-05-07 evening
============================================

[What this session did]
  1. Reschedule 6 patients off 5/7 admission: 3 to 5/8 Fri (黃和泉/陳建諭/歐黃江),
     3 to 5/12 Tue (許慶山/宋哲光/蔡建添). V-mark on 5/7, created 5/8 (3 patients),
     rebuilt 5/12 (existing 7 + new 3 = 10 patients, 5 doctor blocks).
  2. Cathlab ADD via cathlab_keyin: 黃和泉 5/8 H2 1801, 蔡建添 5/13 H1 2100. Verified OK.
     Other 4 charts left at existing positions per user (rule 19 + user "leave for now").
  3. Generated 5/8 N-V ordering (3 rows).
  4. Re-discovered chk-checkbox DEL flow during this session — already-known on remote
     (5/6 from another machine: webcvis_del.py + memory/feedback_webcvis_del_checkbox.md).
     Rebased onto remote, dropped duplicate work.

[Current state]
  - Branch: main, after rebase onto origin (took remote's webcvis_del.py + skill rewrite).
  - Sheets touched: 20260507 (V col), 20260508 (new), 20260512 (rebuilt).
  - Cathlab state on WEBCVIS:
      5/8: 22 entries (added 黃和泉; 陳建諭/歐黃江 stayed at H2 1230/1530 per user).
      5/13: 12 entries (added 蔡建添; 許慶山/宋哲光 already at C1 0800).
  - Pending push: this commit (today's reschedule + 2 new memory files).

[Next steps]
  - User may manual-DEL 陳建諭 (5/8 H2 1230) and 歐黃江 (5/8 H2 1530) if they want
    rule-16 non-schedule H1 2100 placement; user said leave for now.
  - Verify 5/8 admission list push next morning (07:50 cron).
  - Hook design pending: SessionStart -> /check-previous-progress; project end -> /workflow-docs.

[Known issues / blockers]
  - rebuild_date_sheet.py has A:G->A:H sub-table bug — workaround: inline rewrite or fix
    upstream. See memory/reference_rebuild_date_sheet_subtable_bug.md.

[Don't repeat these mistakes]
  - Always git fetch + check origin/main BEFORE starting work. Today I duplicated 5/6's
    DEL discovery + reinvented the chk-checkbox approach because I skipped the fetch.
    CLAUDE.md project-level Session-start step #1 says fetch + git status -sb first.
  - Don't auto-create date sheets without unhiding — user wants every sheet visible.
  - Don't import rebuild_date_sheet.rebuild_one — A:G bug; inline 8-col write to A:H.
  - When rebuilding an existing sheet, capture sub-table data from the JSON snapshot
    (tgt_state) BEFORE deletion, not from live (live may be wiped after a failed retry).
  - Use webcvis_del.py / webcvis_query.py / schedule_lookup.py as permanent helpers for
    WEBCVIS work — don't write _cathlab_*.py / _inspect_*.py one-offs.

[Relevant files]
  - Permanent: webcvis_del.py, webcvis_query.py, schedule_lookup.py (added 5/6 from
    other machine — rebased into local).
  - Skill: .claude/skills/admission-reschedule/SKILL.md (now references the 3 helpers).
  - Today's ephemerals to clean: _reschedule_*.py, _cathlab_*.py, _inspect_row.py,
    _row_dump.html, _reschedule_data.json, _cathlab_keyin_*.log.

[Important memory files]
  - memory/feedback_new_sheet_must_unhide.md (NEW today — unhide newly created sheets)
  - memory/reference_rebuild_date_sheet_subtable_bug.md (NEW today — 8-col write bug)
  - memory/feedback_webcvis_del_checkbox.md (5/6 — chk-checkbox DEL mechanism, primary)
  - memory/reference_webcvis_helpers.md (5/6 — 3 permanent Playwright helpers)
  - memory/feedback_cathlab_json_unique_filename.md (5/6 — never reuse generic JSON name)
  - Global CLAUDE.md: language policy strengthened — internal docs ENGLISH ONLY (incl.
    MEMORY.md index hooks).
