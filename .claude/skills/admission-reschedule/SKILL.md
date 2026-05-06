---
name: admission-reschedule
description: Use when user wants to reschedule admission patients to other dates — full move (not just V flag). Triggered by 「重啟改期功能」, 「改 MM/DD 住院」 with patient list, 「改期」 + new date, or similar. Performs V mark on source sheet + main A-L copy to target sheet + sub-table merge/rebuild + builds cathlab ADD JSON + presents DEL list for user confirmation, then runs automated Playwright DEL. Overrides the conservative "V flag only" rule.
---

# Admission Reschedule (full move)

Move admission patients from one date sheet to another, including main A-L, sub-table under attending doctor, and cathlab schedule (ADD via cathlab_keyin.py; DEL via automated Playwright after user confirms the candidate list).

## Triggers

- 「重啟改期功能」 — explicit reactivation
- 「改 MM/DD 住院」 followed by patient list (N column / doctor / name / target date)
- 「改期」 with target date(s)
- Any clear ask to MOVE patients between date sheets (not just flag)

## Default mode boundary

If the user only says 「改期」 vaguely or marks V manually without listing patients → DON'T auto-move. The default is still V-flag-only (per CLAUDE.md rule 5). Trigger this skill only when the user explicitly lists patients + target dates.

## Inputs needed from user

For each patient:
- Source sheet (which day's admission, e.g. 5/5)
- Patient name (or N column index)
- Target date YYYYMMDD or MM/DD

Common format the user sends:
```
N    主治醫師    病人姓名    改 MM/DD 住院
2    張獻元      王樹英      改5/12住院
9    陳儒逸      吳昆山      改5/7住院
...
```

## Confirm before destructive moves

Before any sheet/cathlab writes, confirm via AskUserQuestion (3 questions):

1. **Source sheet handling**: keep + V mark / keep no mark / remove from source
   - Default recommendation: **keep + V mark** (preserves audit trail)
2. **Target sheet write scope**: main A-L + sub-table / sub-table only / main only
   - Default: **main A-L + sub-table**
3. **Cathlab old entries**: list DEL candidates / no list (default: list)

## Execution sequence

### PHASE 0 — Capture source

For each reschedule patient:
- `capture_main_row(source_ws, name)` — full 12-col list from main A-L
- `capture_sub_row(source_ws, name)` — full 8-col sub-table row (preserves EMR/diagnosis/cathlab/note)

### PHASE 1 — Mark V column on source

- Source N-V row index map (N=1 → row 2, N=K → row K+1)
- For each: `write_cell(source_ws, n_row, 22, target_yyyymmdd)`
- Sleep 0.4s between writes

### PHASE 2 — Update target sheet(s) — group patients by target date

For each target date:

**2a. Append main A-L:**
- `find_main_end` — MUST use YYYY-MM-DD regex on col A, NOT just blank-row scan (sub-table titles trip up naive logic). Reference: `gsheet_utils.enforce_sheet_format` source.
- For each patient: copy source 12-col row, set A=target date, B=target+1, write at main_end+1

**2b. Sub-table strategy:**
- Capture ALL existing blocks on target sheet (not just affected doctors)
- For each reschedule patient:
  - Doctor's block exists → append patient to its list
  - Doctor's block missing → add new block to list
- Decision:
  - No overlap (all reschedule doctors are NEW on target) → APPEND each new block at end of sub-table region (gap row 3 below last_used)
  - Overlap (any reschedule doctor already has a block on target) → REBUILD entire sub-table region:
    1. unmergeCells from sub_start to last_used+5 (cols A..H)
    2. batch_clear A{sub_start}:H{last_used+5}
    3. Re-render all blocks via `write_doctor_table`

**Critical:** when rebuilding, MUST capture all existing blocks BEFORE clear, including blocks for unrelated doctors. Otherwise unrelated patients are lost. (踩過 5/7 陳柏偉 case 2026-05-05 — rate limit 429 hit mid-rebuild, 4th block lost; rebuilt with placeholder)

If main A-L grows past current sub-table start row → push sub-tables down. Cleanest: REBUILD scenario where the entire main+sub region is rewritten in one pass.

**2c. Rate limit defense:**
- `batch_write_cells` for main A-L (one API call vs one-per-row)
- `time.sleep(1.5+)` between sub-table block renders
- If 429 hits mid-flow → save progress, wait 90s+ before retry. Rebuild is NOT idempotent (already-cleared blocks must be re-rendered with captured data — script crash mid-rebuild = data loss on uncaptured blocks)

### PHASE 3 — Format check

```python
from gsheet_utils import enforce_sheet_format
for d in [source_date, *target_dates]:
    enforce_sheet_format(d)
    time.sleep(2.5)
```

Always — don't rely on the post-Bash hook (only fires for specific scripts; this skill's writes are inline).

### PHASE 4 — Cathlab ADD

**Step 4a — schedule + week-scan via permanent helpers (no ad-hoc scripts):**

```python
from schedule_lookup import lookup
slots = lookup("黃鼎鈞", "Thu")  # → [{session, room, second, third, ...}]
# Pick AM or PM based on diag/procedure preference; non-schedule fallback if empty.
```

Week-scan per CLAUDE.md rule 19 (HARD) — verify chart not already keyed Mon-Fri:

```bash
python webcvis_query.py 20260511 20260512 20260513 20260514 20260515 --chart 01808613
```

**Step 4b — build cathlab_keyin JSON (UNIQUE FILENAME, gitignored):**

⚠️ **NEVER write to a generic `cathlab_patients_reschedule.json`** — stale tracked content can re-run prior session's data (踩過 5/6, 10-patient mishap). Per `memory/feedback_cathlab_json_unique_filename.md`:

```python
# Use unique filename per run
fn = f"cathlab_patients_reschedule_{chart}_{cathlab_date_yyyymmdd}.json"
# OR Read-then-Write the generic one to surface "file exists" error
```

Schema:
```json
[{
  "cathlab_date": "YYYY/MM/DD",     // = target admit date + 1 (Mon-Thu) or same (Fri admit)
  "name": "...", "chart": "...", "doctor": "...",
  "second": "...",                   // schedule_lookup result['second'] (CLAUDE.md rule 15)
  "third": "...",                    // schedule_lookup result['third']
  "room": "H1/H2/C1/C2",            // schedule_lookup result['room']
  "time": "HHMM",                   // AM=0601+, PM=1801+, sequential per doctor
  "diagnosis": "...",               // sub-table F
  "procedure": "...",               // sub-table G
  "note": ""
}]
```

Non-schedule fallback (doctor has no slot that day): room=H1, time=2100+, note="本日無時段".

**Step 4c — run + verify:**

```bash
python cathlab_keyin.py cathlab_patients_reschedule_<chart>_<date>.json
# verify section at end confirms ADD success per chart
rm cathlab_patients_reschedule_<chart>_<date>.json   # delete after run
```

### PHASE 5 — Cathlab DEL (list → user OK → automated Playwright)

Per `memory/feedback_webcvis_del_manual.md`: present DEL candidates, wait for user OK, then run automation.

**Step 5a — list candidates** (use `webcvis_query.py` to fetch fresh state):

```bash
python webcvis_query.py 20260507 --chart 01808613    # confirm row exists with current room/time
```

```
WEBCVIS 5/{old_cath_date} DEL 候選清單（請確認後說 OK）：
| 病歷號 | 姓名 | 主治 | 房間 | 時間 | 改到 → 新 cath 日 |
|---|---|---|---|---|---|
| 02742922 | 蘇正勝 | 黃睦翔 | H1 | 2100 | 5/6 admit → 5/7 cath |
```

**Step 5b — wait for user explicit OK.**

**Step 5c — run via permanent helper:**

```bash
python webcvis_del.py CHART YYYYMMDD [CHART YYYYMMDD ...]
```

`webcvis_del.py` uses the verified per-row checkbox approach (per `memory/feedback_webcvis_del_checkbox.md`):
1. Login + query date
2. Find row by `#hes_patno`
3. Set chk checkbox `checked=true` + fire `chk.onclick()` → enables `#deleteButton`
4. Click `#deleteButton` → confirm dialog auto-accept → form submits buttonName=DEL
5. Re-query → verify chart removed

DO NOT write a one-off Playwright DEL script. The 5/6 session burned 3 trial-and-error iterations (form submit / diagnostic / checkbox); the helper encodes the working answer.

**Step 5d — verify:** webcvis_del.py reports per-chart success/fail. If FAIL → automation broke; report exact DOM/error and ask user to manual-DEL.

## Files this skill writes

- `cathlab_patients_reschedule_<chart>_<date>.json` — ADD source of truth (gitignored ephemeral; delete after run)
- Date sheet writes via `gsheet_utils` (PHASES 1-3)
- ⚠️ Do NOT create `_reschedule_*.py` scratch for queries/DEL — use `webcvis_query.py` / `webcvis_del.py` directly.

## Anti-patterns (踩過)

- Quoting CLAUDE.md "manual flag only" when user explicitly invoked reschedule — that's the OLD rule. CLAUDE.md rule 5 has dual mode now.
- `find_main_end` via blank-row scan — fails when sub-table is right below main A-L. Use YYYY-MM-DD regex on col A.
- Rebuild without capturing unrelated doctor blocks first — rate-limit interruption = data loss.
- Punting WEBCVIS DEL to "user does it manually" by default. Correct flow: list → user OK → `webcvis_del.py` → verify → fallback to manual only if helper provably fails.
- ❌ **Writing to generic `cathlab_patients_reschedule.json`** when prior session left a tracked stale version → cathlab_keyin runs the wrong data. Use unique filename or Read-then-Write. (5/6 踩過 10-patient Phase 2 UPT)
- ❌ **Re-writing one-off Playwright DEL scripts** — burned 3 versions to find the checkbox mechanism. Use `webcvis_del.py`. If it breaks, fix the helper, don't fork a new script.

## Coordination with other skills

- After PHASE 4 (cathlab ADD via cathlab_keyin.py): the existing PostToolUse hook does NOT fire (it only matches specific sheet-write scripts, not cathlab_keyin). Format check is already done in PHASE 3.
- If user wants 5/{old_cath} verify after DEL: similar to admission-cathlab-keyin verify_cathlab.py logic but needs to check absence (residual chart list).
- Sub-table data captured here may include the EMR raw text in C column — preserve verbatim through rebuild.

## Memory references

- `memory/feedback_reschedule_active.md` — workflow rules
- `memory/feedback_webcvis_del_manual.md` — DEL flow: list → user OK → automated Playwright
- `memory/feedback_webcvis_del_checkbox.md` — verified DEL mechanism (chk checkbox)
- `memory/feedback_cathlab_json_unique_filename.md` — JSON safety pattern
- `memory/reference_webcvis_helpers.md` — webcvis_query / webcvis_del / schedule_lookup
- `memory/feedback_post_edit_format_check.md` — enforce_sheet_format mandatory
- `memory/feedback_subtable_H_to_R_ordering.md` — 8-col sub-table layout

## Example invocation flow (2026-05-05 case)

User: 「我要重啟改期功能 把 5/5 [10 人] 改到 5/6/5/7/5/12」

1. AskUserQuestion (3 confirm)
2. PHASE 0: capture 10 patients from 5/5 (main + sub)
3. PHASE 1: 10 V column writes on 5/5
4. PHASE 2:
   - 5/6 (1 patient 蘇正勝): main append + new 黃睦翔 block (no overlap)
   - 5/7 (7 patients): main append + REBUILD (詹世鴻/陳儒逸 overlap — captured all 4 existing blocks first)
   - 5/12 (2 patients): main append + new 張獻元 block (no overlap)
5. PHASE 3: enforce_sheet_format on 5/5/5/6/5/7/5/12
6. PHASE 4: build JSON, run cathlab_keyin.py — 7 ADD + 3 SKIP (already on target date) — verify OK
7. PHASE 5: list 10 charts on 5/6 for user manual DEL → user confirms → query verify all gone
