============================================
  HANDOFF — Last Updated: 2026-05-17 (evening)
============================================

[What this session did]
  1. Image import (20260519): diff-update detected zero changes (screenshot identical
     to existing sheet, all 6 chart numbers matched) — no writes, EMR/F/G/V preserved.
  2. Admission ordering (20260518): wrote N-V 10-patient round-robin for 2026-05-18
     (Monday admission → Tuesday cathlab). All 5 doctors have Tue schedule slots.
     E col was pre-filled by user; no manual ordering prompt needed.
  3. User correction (Q col): numeric bed/floor codes ("3","1","2,3") must NOT go into
     Q 備註(住服) — Q stays empty unless K col has genuine住服 free-text instruction.

[Current state]
  - Branch: main, clean (only .claude/settings.local.json unstaged — gitignored)
  - Deploy / run state: N/A (no server changes this session)
  - Latest commit: 95db651 feat(diff-update): N marker for new patients

[Next steps]
  - 20260518 ordering done → cathlab keyin for 5/19 Tue: trigger admission-cathlab-keyin
  - 20260519 lottery + ordering: emr_data_20260519.json exists; sub-tables appear done
    (EMR + F/G written, E col filled, V markers set) — run admission-ordering for 20260519
  - Verify 20260519 sheet state before starting (check if ordering already done)

[Known issues / blockers]
  - None

[Don't repeat these mistakes]
  - Q 備註(住服): do NOT copy K col bed/floor numbers ("3","1","2,3","3C") into Q.
    Only genuine住服 free-text (e.g., "住南投提早通知") belongs in Q. K parenthetical
    delay notes ("(5/4無床延期)") go into R 備註. (Corrected 2026-05-17)
  - Wrong gspread function: use `get_worksheet()`, NOT `get_sheet()` (doesn't exist).

[Relevant files]
  - memory/feedback_q_col_no_floor_numbers.md  ← NEW this session
  - emr_data_20260519.json  ← keep (current week), used by process_emr.py if re-run
  - _emr_session.txt  ← keep (EMR session URL for post_main_emr_verify hook)

[Important memory files]
  - memory/feedback_q_col_no_floor_numbers.md  (new — Q col must not contain floor codes)
  - memory/MEMORY.md  (index updated with new Q col entry)
