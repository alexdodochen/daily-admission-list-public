============================================
  HANDOFF — Last Updated: 2026-05-19
============================================
(No patient names / chart numbers — origin dual-routes to a public mirror.
 Next session: re-derive specifics from the live Sheet by date.)

[What this session did]
  1. 20260519 admission ordering: wrote N-V 6-patient round-robin (Tue admit,
     Wed 5/20 cathlab pool). Doctor RR 張獻元→廖瑀→陳儒逸, per-doctor order
     from sub-table E. 3 V改期 patients mirrored to N-V V col.
  2. Cathlab verify 5/18 + 5/19 admits (verify_cathlab.py).
     5/18: 7 OK; 5/19: 1 already OK.
  3. Keyin 2 missing patients: one 張獻元 → 5/19 CATH2 1600 PAOD/PTA;
     one 陳儒逸 → 5/20 CATH1 0801 (+葉建寬) CAD/LHC. Both verified OK.
  4. One cancelled admission removed from 20260518 (main A-L, N-V renum,
     sub-table 陳儒逸 2→1人, gap fixed, enforce_sheet_format OK).
  5. 3 V改期-but-already-scheduled patients: left untouched per user.

[Current state]
  - Branch: main; new memory + handoff committed, push pending user decision
  - Deploy / run state: cathlab keyin done, 0 errors, verified
  - Latest pushed commit pre-session: 1d3d35c

[Next steps]
  - None pending. 5/19 ordering + 5/20 cathlab keyin complete.
  - New admit screenshot → admission-image-to-excel as usual.

[Known issues / blockers]
  - PHI-vs-public-mirror: workflow-docs commits memory/HANDOFF which dual-push
    to a PUBLIC mirror; pre_push_check.py does NOT scrub patient names/MRN.
    This session's content was scrubbed; raw PHI must never go in tracked docs.
  - admission-cathlab-keyin SKILL.md 張獻元-Tue section still says
    "W2 PM H2 1800+"; corrected behavior is in memory; SKILL.md body edit
    needs user authorization.

[Don't repeat these mistakes]
  - 張獻元 Tue PM cathlab room = CATH2 (actual WEBCVIS), NOT 時段表 H2.
    Read live WEBCVIS, append after his same-day CATH2 block; no fixed 1800.
  - V改期 patient already in WEBCVIS = NOT an error to auto-DEL. Surface,
    default leave-as-is.
  - Destructive shared-PHI-sheet edits / public push: auto-mode classifier
    may block even after AskUserQuestion consent; need explicit user "同意".
  - Never put patient names / chart numbers in memory/ or HANDOFF (public).

[Relevant files]
  - (no permanent code changed; scratch already cleaned)

[Important memory files]
  - memory/feedback_zhang_xianyuan_tuewed_manual.md  (updated — CATH2 not H2)
  - memory/feedback_vmark_already_scheduled_dont_touch.md  (NEW)
  - memory/MEMORY.md  (index updated, 2 entries)
