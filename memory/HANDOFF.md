============================================
  HANDOFF — Last Updated: 2026-05-08 evening
============================================

[What this session did]
  1. 5/10 admission list audit (image vs sheet vs EMR): rejected image age (admission system shows EMR_age+1, NOT canonical), kept sheet ages. Fixed 4 fields (王雅音/王福財 科別 內科重症→心臟血管科, 王福財 床號 09B37D, 林魏金英 入院提示 1). Fetched 王福財 EMR (chart 09835366 was missing from cache); corrected age 88→87 (EMR DOB 1938/11/06). Merged into emr_data_20260510.json (now 8 entries).
  2. New rule: Mon cathlab + EP (RF ablation/PFA/etc) → second=洪晨惠 強制 (broader than old 黃鼎鈞-Mon special case). Applied to 5/11: UPT 郭永泉 + 蘇招治 added 洪晨惠 as doctor2 (陳清發 already had her).
  3. cathlab_keyin.py.fix_diag extended: now UPTs attendingdoctor2 (`second`) too, not just recommendationDoctor (`third`). Backwards-compatible.
  4. V1 header drift fixed across 14 sheets: 5/9, 5/10, 5/12-17, 5/19-20, 5/11-14 had `每日續等清單` → now `改期` (CLAUDE.md spec).
  5. New rule: EMR cell first line = `<age> y/o <gender>`. Updated process_emr.py (auto-prefix on future writes); built backfill_emr_age_gender.py and ran across 29 sheets (~210 EMR cells now prefixed). Old archive sheets (4/06–4/12) skipped — sub-table charts not in main data.
  6. PostToolUse format hook upgraded: now fires on any Bash with date + sheet-mutation hint (was: only 4 named scripts). Catches `python -c batch_write_cells` etc that previously bypassed it.

[Current state]
  - Branch: main, will be pushed via this /workflow-docs run.
  - Cache: emr_data_20260503-07 + 20260510-14 retained (week-of, this is Friday so week_sunday=2026-05-03).
  - WEBCVIS: 5/11 has 12 entries; all 3 EP cases have 洪晨惠 as doctor2.
  - User-level hooks (~/.claude/hooks/session_start_handoff.py, session_end_marker.py) live from prior session; this session benefited from the SessionStart auto-injection.

[Next steps]
  - 5/8 (Fri) admission workflow: image OCR → lottery → EMR → ordering → SAME-DAY cathlab (Friday rule).
  - 5/9 (Sat): typically no admissions.
  - 5/10-14 sheets ordering N-V is NOT yet written (only cathlab keyed). If 住服 push needs N-V, run admission-ordering per date.
  - Verify 5/8 morning push results.

[Known issues / waiting on user]
  - Old sheets 4/06-4/12 have sub-table chart numbers not present in main data (different layout era) → backfill skipped them (no_main_demo). If user wants those backfilled, would need separate strategy (probably parse age/gender from the EMR text body).
  - verify_cathlab.py false-positives (logged in prior HANDOFF): «不排導管» not in skip-keyword set, «檢查» substring too aggressive — still pending fix.

[Don't repeat]
  - Don't write `python -c "...batch_write_cells..."` without the format hook catching it. Hook is now broad enough, but if you add a new mutation API, update SHEET_API_HINTS.
  - Don't trust admission-list image age — always cross-reference EMR DOB. Image is consistently +1 (likely 虛歲).
  - Don't add doctor2 update in a one-off script — use cathlab_keyin.py with second= field; fix_diag now UPTs attendingdoctor2.
  - Don't introduce ad-hoc `_query_5_11.py` etc — use webcvis_query.py / webcvis_del.py / schedule_lookup.py / cathlab_keyin.py permanent helpers.
  - Don't run --all-recent backfill in one shot — 60 reads/min quota; split into 15-sheet batches with a 75s gap.

[Key artifacts touched]
  - Google Sheet 20260510 (4 main fields + 8 EMR prefixes + 王福財 EMR write + age fix)
  - Google Sheet 20260507 onwards (29 sheets EMR prefix backfill, 14 sheets V1 header)
  - WEBCVIS 5/11 (UPT 2 EP entries with 洪晨惠 as doctor2)
  - Code: process_emr.py, cathlab_keyin.py, scripts/post_sheet_format_check.py
  - New: backfill_emr_age_gender.py
  - CLAUDE.md (rules 15, 22→23 added; Key Files updated)
  - Skills: admission-cathlab-keyin.md (rule 8 broadened), admission-emr-extraction.md (C col format)

[Memory files updated/added]
  - memory/feedback_monday_ep_hong_chenhui_second.md (NEW)
  - memory/feedback_emr_cell_age_gender_prefix.md (NEW)
  - memory/feedback_age_emr_canonical.md (NEW)
  - memory/reference_post_sheet_format_hook.md (REWRITTEN — broader trigger)
  - memory/MEMORY.md (+3 index lines, 1 line edited)
