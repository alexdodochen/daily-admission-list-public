---
name: Reschedule workflow active — overrides "manual flag only" rule
description: when user says 「重啟改期功能」/ 「改X月X日住院」, do the full move — V mark + main A-L copy + sub-table merge on target + cathlab DEL/ADD
type: feedback
---

When user explicitly invokes reschedule (e.g. lists patients with 「改 X/Y 住院」), execute the full move workflow. This OVERRIDES the older "reschedule is purely a manual V-column flag" rule in CLAUDE.md (rule 5).

**Workflow per reschedule patient:**
1. Source sheet (e.g. 5/5): keep all data intact, mark V column on N-V row with target YYYYMMDD
2. Target sheet (target date): append main A-L row (A=target date, B=target+1) + insert into sub-table under attending doctor
   - If doctor's sub-table doesn't exist on target → create new block (write_doctor_table)
   - If doctor's sub-table exists → REBUILD entire sub-table region (capture all blocks, add new patients, clear, re-render)
3. enforce_sheet_format on source + target sheets
4. Cathlab: DEL old (N+1 from source admit date) → ADD new (N+1 from target admit date) following 主治醫師導管時段表 rules
   - DEL: NOT automatable per memory feedback_webcvis_del_manual.md → list and ask user
   - ADD: cathlab_keyin.py with new JSON

**Why:**
- User on 2026-05-05 explicitly said 「我要重啟改期功能」 + 「複製到對應的工作表，若尚未有那日的工作表 就創建一個」 + 「你的確要幫我連導管排程都一起移動 要注意移動後也要按照當日主治醫師的導管室規則喔 然後把舊的刪除」
- Three explicit confirmations override the conservative "manual flag" default
- Without sheet move, the V flag alone leaves data in wrong sheets → admission/cath workflows downstream see stale state

**How to apply:**
- Trigger on 「重啟改期功能」, 「改 MM/DD 住院」 with patient list, or similar.
- Confirm scope before destructive moves: ask whether to keep V mark on source, whether to write target main A-L + sub-table, whether to handle cathlab DEL list.
- Sub-table rebuild on target sheet must capture ALL existing blocks (incl unrelated doctors) before clear, otherwise data loss (踩過 5/7 陳柏偉 case 2026-05-05 — patient EMR/F/G lost when 429 rate limit interrupted mid-rebuild).
- Always enforce_sheet_format after writes (or rely on the post-Bash hook once it activates).

**Anti-pattern (踩過):**
- Quoting 「reschedule is a manual flag, don't auto move」 from CLAUDE.md when user explicitly asks for the move — that rule is stale, the user has reactivated the feature.
