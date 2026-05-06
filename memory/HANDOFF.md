============================================
  HANDOFF — Last Updated: 2026-05-06 (Tue, evening)
============================================

[What this session did]
  1. 5/7 admission ordering: N-V written for 16 patients (RR 詹→劉→陳儒→陳柏→柯). 黃嬌子 H = 不排檢 CTV; 潘美香 H residue cleared; S-col TEXT format applied.
  2. 5/10-14 cathlab keyin batch: 23 ADD / 0 errors across 5 dates. Week-scan caught 6 same-date dups already pre-keyed manually (王雅音/王福財/姜滄源/王樹英/楊瑪露/譚翠翠) → removed from JSONs (Plan A) so manual room/time stays untouched.
  3. 5/12 sub-table B chart-no fix: 6 entries lost leading zeros (莊永慶 9488011 etc) — applied TEXT format + zfill(8); verify ALL CLEAR after fix.
  4. Global CLAUDE.md (~/.claude/CLAUDE.md): added «Don't reinvent the wheel» section (search OSS first; high-star + maintained + clean; ASK before any install/clone).
  5. Two new project memories (English): feedback_leverage_cache_files.md, feedback_just_execute_after_prep.md.

[Current state]
  - Branch: main (clean before commit step)
  - Latest commit: 66a833e feat: WEBCVIS helpers (query/del/schedule) + reschedule skill rewrite
  - WEBCVIS: 5/11-15 fully scheduled; 5/7 ordering on Google Sheet ready for 5/8 cathlab
  - Cache files (kept on purpose per user feedback): emr_data_20260503-07 + 20260510-14, cathlab_patients_20260503-07 + 20260510-14, cathlab_patients_reschedule

[Next-up actions when next session opens]
  - 5/8 (Fri) admission workflow: 截圖 → image-to-sheet → lottery (Fri uses col E; 詹世鴻 non-slot) → EMR → ordering → SAME-DAY cathlab (Fri rule).
  - 5/9 (Sat): typically no admissions.
  - 5/10-14 sheets: ordering N-V is NOT yet written, only cathlab is keyed. If 住服 push needs N-V for those dates, run admission-ordering for each.
  - Before Fri evening push, verify 5/8 batch.

[Known issues / waiting on user]
  - verify_cathlab.py false positives discovered this session:
      • «不排導管» not in skip-keyword set (5/10 林魏金英 reported NG even though user-confirmed SKIP).
      • «檢查» substring match is too aggressive — flags «肺功能檢查» / «需檢查等等» even when user wants to schedule (5/12 鄭蘇金葉 reported as «竟然在排程中»).
    Fix candidate: tighten to whole-word «不排程» / «檢查»; add «不排導管» / «不排檢» to skip set.
  - Mid-session user flipped Plan A↔B↔A on dup-handling. For SAME-DATE dups, Plan B (UPT refresh) is probably the right default in future — kept conservative this time.

[Don't repeat]
  - Wrote a new MEMORY.md index entry in Chinese while global CLAUDE.md says «internal docs → English» — user caught; rewritten to English. ALL memory/skill/handoff/CLAUDE.md goes English from now on.
  - Initially picked admission-lottery skill when sub-tables already existed; correct skill was admission-ordering. Read sheet state before picking skill.

[Key artifacts touched]
  - Google Sheet 20260507 (N-V + sub-table H cleanup)
  - Google Sheet 20260512 (B-col TEXT format + zero-padded chart no)
  - WEBCVIS schedule 2026/05/11 ~ 2026/05/15 (23 ADD)
  - C:\Users\dr\.claude\CLAUDE.md (added OSS no-reinvent section)
  - cathlab_patients_20260510.json ~ 20260514.json (built fresh, 6 dups removed)

[Memory files updated]
  - memory/feedback_leverage_cache_files.md (NEW)
  - memory/feedback_just_execute_after_prep.md (NEW)
  - memory/MEMORY.md (+2 index lines)
