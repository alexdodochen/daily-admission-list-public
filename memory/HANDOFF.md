============================================
  HANDOFF — Last Updated: 2026-05-05 evening (post-reschedule day-2)
============================================

[What this session did]
  1. 5/6 admission ordering — wrote N-V 15 rows + sub-table E (黃嬌子=3, 黃周笑=1) + enforce_sheet_format
  2. 5/10 — added 王福財 (chart 09835366) main r9 + 許志新 sub-table r27 (title → 2人); 王雅音 already there
  3. Cathlab verify 5/6+5/7 → found 3 missing → ADDed (黃周笑 5/7 H1 0601, 黃和泉 5/7 C2 1801, 陳建諭 5/8 C2 0606); all OK after re-verify
  4. Updated WEBCVIS DEL feedback (twice): list candidates → wait for user OK → run automated Playwright DEL → fallback manual only if automation fails
  5. Q col fix: cleared Q2:Q16 on 5/6 after user pushed back ("為何Q欄多了這些勾勾"); the V's in 5/5 are user's manual marks, NOT a convention to mimic
  6. Patched verify_cathlab.py SKIP_KEYWORDS to include "不排檢" (黃嬌子 case)

[Current state]
  - Branch: main, working tree dirty (script edits + memory + HANDOFF + workflow.txt + 1 ephemeral JSON)
  - WEBCVIS: 5/7 18 entries verified, 5/8 16 entries verified
  - Sheets clean: 5/6 (15 N-V + format), 5/10 (8 main + sub-table 許志新 2人 + format)
  - Latest commit: e747da4 (before today's work) → 0f12b46 (pulled at session start)

[Next steps]
  - Wait for 5/8 admission list screenshot (Friday admit)
  - 5/11+ next-week admission lists when user sends them
  - (long-term) memory full-English migration; public mirror sheet 1u2FZE6... PHI cleanup

[Known issues / blockers]
  - cathlab_keyin.py silent ADD failure case observed: 陳建諭 was in 5/5 reschedule JSON but never appeared in WEBCVIS 5/8 — script reported success. Root cause unclear (possibly query timing / dialog handling). Recommend: post-Phase-1 verify per chart, retry once if missing
  - SKIP_KEYWORDS extension to "不排檢" deployed — re-verify 5/6 should now show 黃嬌子 as SKIP not NG (test on next run)

[Don't repeat these mistakes]
  - **Q col 備註(住服) defaults to '' — never write 'V' as placeholder.** The V's in 5/5 are user's own manual marks (notification tracking). Don't mimic patterns from existing sheets — source Q values from K col text or reschedule date only.
  - **Don't infer column conventions from peer sheets** — when in doubt, ask. Old data may contain user's manual annotations.
  - **WEBCVIS DEL flow is now: list → user OK → automate** (NOT punt-to-manual by default, NOT auto-DEL without confirmation)
  - **cathlab_keyin.py only queries cathlab_date** — must do separate week-scan (Mon-Fri) before ADD for any chart, per CLAUDE.md rule 19 (HARD)

[Relevant files]
  - 每日入院名單/cathlab_patients_3missing.json — today's 3-patient ADD JSON (delete after retain-window)
  - 每日入院名單/verify_cathlab.py — SKIP_KEYWORDS patched
  - 每日入院名單/CLAUDE.md — rule 5 reschedule DEL flow updated
  - 每日入院名單/每日入院清單工作流程.txt — 改期 V 欄段落改為雙模式描述
  - 每日入院名單/.claude/skills/admission-reschedule/SKILL.md — PHASE 5 rewritten

[Important memory files]
  - feedback_q_col_no_default_v.md (NEW)
  - feedback_webcvis_del_manual.md (rewritten — list → OK → automate)
  - MEMORY.md (index updated)
