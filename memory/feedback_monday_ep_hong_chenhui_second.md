---
name: Monday EP cathlab — 洪晨惠 forced as second attending
description: For any Monday cathlab whose planned procedure is EP (e.g. RF ablation, PFA, AF/AFL/PSVT ablation), 洪晨惠 must be set as second attending — even if 時段表 doesn't list her that day.
type: feedback
---

For any cathlab scheduled on **Monday** where the planned procedure is **EP** (electrophysiology — RF ablation, PFA, AF/AFL/PSVT ablation, EP study, etc.), set **洪晨惠** as the second attending physician (`attendingdoctor2`). Applies to **all** EP cases on Monday, regardless of who the primary attending is.

**Why:** User instruction (5/8): «以後禮拜一的導管排程 只要預計心導管是EP 如RF ablation 洪晨惠都要被放在第二主刀醫師!! 例如現在5/11 23284837 郭永泉 pAf RF ablation 就要排他». This is a generalization of the existing 黃鼎鈞 Mon rule (CLAUDE.md rule 15) to **any** Monday EP case.

**How to apply:**
- During cathlab keyin (`cathlab_keyin.py` JSON), set `second=洪晨惠` for any Monday-cathlab patient whose `planned` field maps to EP (RF ablation, PFA, AF/AFL/PSVT ablation, EP study, etc.).
- If the JSON already has `second=` from 時段表 (e.g. 葉立浩=浩 from 黃鼎鈞's Mon slot) → existing second goes to `attendingdoctor2`, push 洪晨惠 to `third` (which renders as `recommendationDoctor` per rule 15).
- If reschedule moves a patient from another day onto Monday, re-evaluate: if it's EP, add her.
- 黃鼎鈞 Mon (rule 15) is now a **subset** of this rule, not a special case. Keep rule 15 in CLAUDE.md but cross-reference to this one.
- Device implants (PPM/ICD/CRT) are also typically EP — apply the rule unless user says otherwise.

**Cathlab-day = Monday** means the day the cath is performed (not admission day). Per CLAUDE.md rule 5: Sun admit → Mon cathlab. So a Sunday admission with EP planned → triggers this rule.
