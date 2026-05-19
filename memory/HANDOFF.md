============================================
  HANDOFF — Last Updated: 2026-05-19 (5/20 pipeline run)
============================================
(No patient names / chart numbers — origin dual-routes to a PUBLIC mirror.
 Next session: re-derive specifics from the live Sheet by date.)

[What this session did]
  1. 20260520 sheet status review, then diff-update from user's late
     screenshot: +2 new patients (1 陳柏偉, 1 黃鼎鈞); existing 5 rows
     fully untouched (EMR/F/G/manual marks preserved), new sub-table
     rows stamped H="N" per diff-update new-patient rule.
  2. EMR fetch (fetch_emr.py) for the 2 new charts only, via user
     session URL; process_emr.py wrote C + age/gender prefix + auto
     F/G. verify_main_emr hook: all main rows match divUserSpec.
     EMR-DOB age corrected both new patients (image age was 虛歲 +1).
  3. 排住院序: N-V 7-patient round-robin. Weighted doctor RR
     林佳凌→陳柏偉→黃鼎鈞 (Wed admit → Thu lottery col, all 時段組).
     Per-doctor order from sub-table E (user keyed E directly in Sheet,
     also hand-adjusted F/G/H). R 備註 sourced from sub-table H.
  4. 導管排程 (5/21 Thu, N+1): week-scan (webcvis_query 5/18-5/22)
     caught 5/7 charts ALREADY scheduled 5/21 (prior session) →
     excluded per HARD RULE, no re-ADD. Built clean
     cathlab_patients_20260520.json (overwrote a STALE unrelated file;
     Read-then-Write exposed the staleness). cathlab_keyin.py ADDed
     only the 2 new (H2 0600 / C1 1100). verify_cathlab: 7 OK / 0 / 0.

[Current state]
  - Branch: main; working tree clean (operational-only, no repo code
    changed). This handoff/memory sync is the only commit.
  - Deploy / run state: 5/20 pipeline fully complete + verified.
  - Latest pushed commit pre-session: 3c3b764

[Next steps]
  - None for 5/20. New admit screenshot → admission-image-to-excel.

[Known issues / blockers]
  - CARRY-OVER (2 sessions): line-reminder-bot commit 22d92f2 still
    UNPUSHED. Claude push to that repo is hard-blocked. User must run:
      ! cd /c/Users/dr/repos/line-reminder-bot && git push origin main
    (forward-slash path). Date-gate behavior visible only from 6/1.
  - Intermittent DNS blip resolving sheets.googleapis.com this session;
    retry / dangerouslyDisableSandbox cleared it. Environment-transient.

[Don't repeat these mistakes]
  - cathlab_patients_<date>.json may be STALE from a prior week — always
    Read it before reuse; rebuild clean. (Hit + handled this session.)
  - Week-scan BEFORE any cathlab ADD: charts already scheduled on ANY
    Mon-Fri day must be dropped from JSON, never re-ADDed.
  - Never put patient names / chart numbers in memory/ or HANDOFF
    (dual-pushed to public mirror).

[Relevant files]
  - (no permanent code changed; scratch cleaned at session end)
  - cathlab_patients_20260520.json / emr_data_20260520.json kept
    (current week — prune next Monday)

[Important memory files]
  - No memory updates this session (pure operational; all behavior
    already covered by existing feedback_* rules).
