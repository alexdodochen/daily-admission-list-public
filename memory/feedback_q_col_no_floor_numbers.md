---
name: feedback_q_col_no_floor_numbers
description: Q 備註(住服) must NOT contain K col numeric bed/floor codes — only genuine住服 free text
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0c72c4df-d733-4d14-a008-6f3d19015d3e
---

Q 備註(住服) must remain empty unless K col contains genuine free-text instructions for住服 (e.g., "住南投提早通知", "非導管床"). Do NOT copy numeric bed/floor codes ("3", "1", "2,3", "3C", "321", "3 F2", etc.) from K col into Q.

**Why:** User corrected this on 2026-05-17 ordering run for 20260518. Those numbers are bed-floor codes for reference only — they are not住服 action items.

**How to apply:** When building N-V rows, parse K col → R only gets parenthetical date-delay notes like "(5/4無床延期)". Q gets only non-numeric descriptive text from K (e.g., "住南投", "提早通知"). If K is purely numeric or a simple floor code, Q = "".

**Related:** [[feedback_q_col_no_default_v]]
