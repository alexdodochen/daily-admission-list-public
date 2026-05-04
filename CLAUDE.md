# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repo.

## Session start

Before any work:

1. **`git fetch origin && git status -sb`** — if origin is ahead, `git pull --rebase` first. Multi-device user: another machine may have pushed helper code, ID maps, or per-date input.
2. **`ls local_config.py`** — must exist. If missing, copy from another machine or rebuild from `memory/_private_setup.md` (gitignored). Without it, `gsheet_utils` falls back to the public mirror demo sheet — every PHI write goes public. See `memory/feedback_local_config_required.md`.
3. Run the `check-previous-progress` skill to load `memory/MEMORY.md` and prior feedback.
4. Check whether `cathlab_patients_<today>.json` / `emr_data_<today>.json` already exist — if yes, **use them**, don't rewrite.

The user actively maintains `每日入院清單工作流程.txt` as the workflow source-of-truth — **if it disagrees with this file, the txt wins**.

## Public mirror

- Public mirror: https://github.com/alexdodochen/daily-admission-list-public
- `origin` push is dual-routed (private + public); `origin` fetch only pulls private.
- **Never** add a `public` remote or `git fetch <public_url>` — public history may have unrelated commits from others.
- If public push is blocked due to divergence: `git push https://github.com/alexdodochen/daily-admission-list-public.git main --force` (only if private push already succeeded). Don't merge public history back.
- See `memory/project_public_mirror_sync.md`.

### Public must-not-contain (HARD RULE — pre-push hook enforced)

`origin push` mirrors to public. The following content **must never be committed** to tracked files:
- Private SHEET_ID (literal in `memory/_private_setup.md`)
- LINE push bot infra: bot URL, bot ID (@-prefix), `trigger-*` endpoints
- Service account JSON (PEM private key blocks)

Exact regex blocked patterns are in `scripts/pre_push_check.py` `FORBIDDEN`. Reference values live in gitignored `memory/_reference_line_reminder_bot.md` / `memory/_private_setup.md`.

All such content goes to gitignored files: root `_*.md` / `_*.txt`, or `memory/_*.md`. Never add LINE-related rules or bot details to tracked files (CLAUDE.md / 每日入院清單工作流程.txt) — always use `_*` prefixed files.

**Push-time enforcement** (`scripts/pre_push_check.py` + `.githooks/pre-push`):
- One-time setup per clone: `git config core.hooksPath .githooks`
- Each `git push` automatically runs `pre_push_check.py`; a hit aborts the push.
- Never use `--no-verify` — instead, move violating content to `_*.md`.

Run `python scripts/pre_push_check.py` manually before each push as a double-check.

## Project Overview

Hospital admission management system for the cardiology department (成大醫院心臟科行政總醫師). Automates the daily workflow: patient list intake → lottery ordering → EMR extraction → admission sequencing → cathlab scheduling.

## Environment

- **Platform**: Windows 11, Python 3.14, `python` (not `python3`). Cross-machine setup / WindowsApps stub gotchas: `memory/reference_machine_python_path.md`.
- **Terminal encoding**: cp950 — Chinese with emojis (❌✅) crashes `print()`. Write output to UTF-8 files and read with the Read tool. All `open(..., 'w')` must specify `encoding='utf-8'`. **Stdout redirect is also cp950 by default** — `python x.py > f.txt 2>&1` produces mojibake. Prefix with `PYTHONIOENCODING=utf-8` or add `sys.stdout.reconfigure(encoding='utf-8')`. If you see garbled output, stop and re-run with UTF-8 — never guess names from mojibake.
- **Google Sheets API**: `gspread` + service account (JSON file).
- **Sheet ID (private)**: provided by `local_config.py` (gitignored); never hardcoded in tracked files.
- **Sheet ID (public mirror default)**: `1u2FZE6-Ldich_b2jI-i0gNnxu1ZsZtZ2Ra6ffCU2Er8` — `gsheet_utils.py` fallback for clones lacking `local_config.py`.
- **Browser automation**: Playwright (Chromium, non-headless). EMR scripts use sentinel-stamping for race-condition safety between frame loads.
- **gspread rate limits**: per-minute quotas. Batch writes need `time.sleep(0.3–1)` between API calls. Use `batch_update` for bulk formatting (capped at 500 per batch).
- **Worksheet access**: `sh.worksheet('name')`. Key sheets: `下拉選單`, `麻醉`, `主治醫師導管時段表`, `主治醫師抽籤表`, `CathDuration`, plus date sheets (`20260406`, `20260407`, ...).
- **Two doctor schedule sheets — don't confuse**:
  - `主治醫師抽籤表` (col A-E = Mon-Fri, `*2` suffix = 2 lots) → **lottery sole reference**
  - `主治醫師導管時段表` (AM/PM × H1/H2/C1/C2 × Mon-Fri) → **cathlab key-in room/time reference**

## Architecture

All scripts share `gsheet_utils.py` (singleton gspread client, read/write/format/dropdown helpers). Each workflow step has a corresponding skill in `.claude/skills/`. Data flow:

1. **Image → Sheet** (`admission-image-to-excel`): OCR screenshot → write A-L of date sheet (e.g., `20260408`). If sheet exists, performs **diff-update** (match by chart no → add new / remove cancelled / preserve existing EMR/F/G/ordering).
2. **Lottery** (`admission-lottery`): Random draw → doctor sub-tables (A-H below main data) + round-robin ordering basis.
3. **EMR extraction** (`admission-emr-extraction`): Playwright reads Web EMR (`http://hisweb.hosp.ncku/Emrquery/`) → writes C (raw EMR) in sub-tables → auto-prefills E (術前診斷) / F (預計心導管). **Summary feature dropped 5/4** — D column removed entirely from sub-table layout (see `memory/feedback_no_emr_summary.md`).
4. **Ordering** (`admission-ordering`): After user confirms F/G, writes N-V columns.
5. **Cathlab keyin** (`admission-cathlab-keyin`): `python cathlab_keyin.py cathlab_patients_YYYYMMDD.json` (generic driver) — Phase 1 ADD patients (dedupe by chart), Phase 2 UPT to fix pdijson/phcjson. ID maps from `cathlab_id_maps.json`.

**EMR data pipeline**: `fetch_emr.py` (Playwright → `emr_data_<date>.json`) → `process_emr.py` (JSON → F/G auto-detect → Sheet writes; summary generation removed 5/4). The JSON intermediary allows re-processing without re-fetching. Auto-detect uses keyword rules (`DIAG_RULES` for E=術前診斷, `CATH_RULES` for F=預計心導管 in `process_emr.py`) — runs on raw EMR text.

**Reschedule is a manual flag.** V column with YYYYMMDD = patient skipped from N+1 cathlab. User decides handling (manual reschedule / notify). No auto sheet move, no auto WEBCVIS DEL/ADD, no sub-table changes. Both cathlab keyin and verify must skip rows where V has a value.

**Each step is independent — don't auto-chain.** Even if user provides multiple resources upfront (image + EMR URL + JSON), only run the step the user explicitly triggered. The next step waits for the user's command. See `memory/feedback_no_auto_lottery.md`.

**Ephemeral vs permanent files**:
- **Permanent** (reference implementations): `gsheet_utils.py`, `generate_ordering.py`, `verify_cathlab.py`, `fetch_emr.py`, `process_emr.py`, `cathlab_keyin.py`, `rebuild_date_sheet.py`, `refresh_emr.py`, plus active skills under `.claude/skills/`.
- **Ephemeral** (do not commit, do not copy patterns from): `_*.py` / `_*.txt` scratch, `emr_data*.json`, `cathlab_patients_*.json`, `每日入院名單*.xlsx` local backups, `20260*.jpg` screenshots.

## Key Files

- `gsheet_utils.py` — Shared Google Sheets module. `get_worksheet()`, `write_range()`, `batch_write_cells(updates)` (batched cell/range writes for quota efficiency), `format_header_row()`, `write_doctor_table()`, `set_dropdown_from_range()`, `enforce_sheet_format()`.
- `generate_ordering.py` — Reads doctor sub-tables + round-robin order, generates N-V ordering. The full 9-col N-V write (序號|主治醫師|病人姓名|備註(住服)|備註|病歷號|術前診斷|預計心導管|改期) is handled by the `admission-ordering` skill.
- `rebuild_date_sheet.py` — Rebuilds a date sheet (main data + sub-tables + formatting) in ≈6 API calls. Driven by the `admission-sheet-rebuild` skill.
- `refresh_emr.py` — Orchestrates `fetch_emr` + `process_emr` across multiple dates in one browser session, dedup by chart. Driven by the `admission-emr-refresh` skill.
- `cathlab_keyin.py` — Generic cathlab keyin driver. `python cathlab_keyin.py cathlab_patients_YYYYMMDD.json`. ID maps from `cathlab_id_maps.json` (never hardcode IDs — see `feedback_cathlab_id_maps_only.md`). Two phases: ADD then UPT, dedupe by chart.
- `fetch_emr.py` — Playwright-based EMR fetcher. Session URL + (chart, doctor) pairs → `emr_data_<date>.json`. Sentinel-stamping for race safety. Falls back to whitelist doctors when target has no clinic visit.
- `process_emr.py` — Generic EMR processor. Reads `emr_data_<date>.json`, auto-detects 術前診斷/預計心導管 (no summary post 5/4), corrects names/age/gender from `#divUserSpec`, writes C (raw EMR) / E (術前診斷) / F (預計心導管) to sub-tables + main data. Usage: `python process_emr.py 20260419`.
- `verify_cathlab.py` — Verifies admission patients appear in WEBCVIS cathlab schedule. Reads sub-table (統整資料), respects V column (skip if value). Handles Friday same-day cathlab. Usage: `python verify_cathlab.py 20260409`.
- `每日入院清單工作流程.txt` — Canonical workflow spec. **Read first for any workflow question — if it disagrees with CLAUDE.md, the txt wins** (user actively maintains).
- `memory/MEMORY.md` — Persistent memory index. **Run `check-previous-progress` skill at session start.**
- `_*.py` / `_*.txt` — Underscore-prefixed = throwaway debug/verification. Not reference implementations.
- `cathlab_page.html` — Saved HTML of WEBCVIS cathlab system for form field analysis.
- `cathlab_id_maps.json` — pdijson/phcjson ID mappings (diagnosis→PDI ID, procedure→PHC ID).
- `schedule_readable.txt` — Human-readable doctor schedule (Mon-Fri, AM/PM rooms). A named cell = doctor has a slot that day, even with annotations like "結構", "齡", "寬" (those are secondary-doctor / theme tags, not "no slot").

## Workflow (6 steps)

```
截圖 → OCR 匯入 Sheet → 抽籤排序 → EMR 提取 → 排住院序 → 導管排程 → /workflow-doc
                    ↘ format-check after each write step ↗
```

Full details in `每日入院清單工作流程.txt`. Critical rules:

1. **Ordering columns N-V (9 columns)**: 序號 | 主治醫師 | 病人姓名 | 備註(住服) | 備註 | 病歷號 | 術前診斷 | 預計心導管 | 改期. The user has corrected this multiple times — do not reorder, do not omit 病歷號 or 備註(住服). N-Q (first 4 cols) = subset for 住服 push consumers. **V = 改期**: pure manual marker. User writes YYYYMMDD to defer that patient → row excluded from N+1 cathlab keyin and skipped by `verify_cathlab.py`. Manual V writes must match by P (name) or S (chart no) since round-robin reorders rows.
2. **Round-robin lottery (two independent RR groups)**: 時段組 (in same-day cathlab pool) round-robin among themselves first → 非時段組 (not in pool) round-robin among themselves after. **Never mix the two groups in one RR** (per `feedback_lottery_roundrobin.md` — the user has corrected this multiple times). Within a group: A1→B1→C1→A2→C2... true RR, skip exhausted doctors. Doctor draw order within a group = pure random (`random.shuffle()`); **don't borrow the sub-table doctor order** (those are independent events).
3. **Friday admission → Friday schedule**: Friday admission uses Friday's lottery (no Saturday schedule). Sun→Mon, Mon→Tue, Tue→Wed, Wed→Thu, Thu→Fri, **Fri→Fri**.
4. **Non-schedule doctors**: Never include in main round-robin.
5. **Cathlab direction**: Day-N admit → day N+1 cathlab. **Exception**: Friday admit → Friday cathlab (same day; no Saturday schedule).
6. **Cathlab safety**: Only ADD new entries; never modify or delete existing ones.
7. **Cathlab times**: scheduled AM=0600+, scheduled PM=1800+, non-schedule=H1 2100+ (note="本日無時段").
8. **No-data patients**: Still key into cathlab schedule at the doctor's time slot, note="無資料病人".
9. **Skip rule**: 備註 contains 「不排程」 or 「檢查」 → skip cathlab keyin (「非導管床」「HF AE」 don't auto-skip; only 「檢查」 confirms skip).
10. **Sheet no-overwrite**: Read target area before write; confirm empty first; never overwrite existing data.
11. **EMR auto-write**: After EMR fetch, write raw EMR to C col without re-confirming.
12. **EMR manual login**: Don't open browser yourself — wait for user to manually log in and paste session URL; then use Playwright with that session.
13. **Ordering timing**: Wait for user to confirm sub-table F (術前診斷) / G (預計心導管) before writing N-U.
14. **EMR prefill 術前診斷/預計心導管**: After EMR fetch, auto-prefill sub-table F and G (8-col layout); list for user review.
15. **Second doctor priority**: 時段表 entries like 「黃鼎鈞(浩、晨)」 (two seconds) → first (葉立浩=浩) → `attendingdoctor2`; second (洪晨惠=晨) → **`recommendationDoctor`**. `cathlab_keyin.py` supports `third` JSON field; old "put in note" approach is obsolete. See `memory/feedback_cathlab_third_doctor.md`. **黃鼎鈞 Mon cathlab forces second=洪晨惠** (even if 時段表 Mon doesn't list her).
16. **詹世鴻 Friday exception**: Friday admission with 詹世鴻 → treat as **non-schedule doctor** — lottery/ordering goes after schedule doctors; cathlab is non-schedule (H1 2100+, note="本日無時段"). Both systems consistent.
17. **Post-edit format check**: After any write/modify to a date sheet's patient data, **always** read back to verify (main A-L, N-V ordering, sub-table title/count/blank gap, no residual merges, chart no consistent). Fix on the spot, don't leave loose ends (see `memory/feedback_post_edit_format_check.md`). **Easiest**: `from gsheet_utils import enforce_sheet_format; enforce_sheet_format('YYYYMMDD')` — idempotent, refreshes BLUE/WHITE bg + LEFT align + bold + WRAP. **Required** after any diff/insert/delete/write_range.
18. **N-V write must re-read sub-table F/G/H NOW** (HARD): Cached values from earlier in session don't count. The user manually adjusts 術前診斷/預計心導管/註記 between lottery/EMR/format-check and your N-V write. Skip this → ordering's diagnosis/cathlab/note all wrong. 8-col layout: F=術前診斷, G=預計心導管, H=註記. See `memory/feedback_subtable_H_to_R_ordering.md`.
19. **Cathlab ADD must scan whole week (Mon-Fri)** (HARD): For each patient in JSON, Playwright-query 5 days for chart no. If chart exists on **any** day (not just N+1) → STOP, list "patient already scheduled MM/DD ROOM TIME", remove from JSON, **never auto-ADD** to N+1. See `memory/feedback_cathlab_week_check_before_keyin.md` (5/2: 康李金春 5/6 CRT existed, mistakenly ADDed to 5/5 廖瑀 H1 2100).
20. **陳則瑋 + 劉秉彥 OPD → cathlab second=劉秉彥**: 陳則瑋 admission patient with sub-table C col 「(門診)... 劉秉彥 ...」 → JSON `second=劉秉彥`. Limited to 劉秉彥 (not a general rule). See `memory/feedback_chen_zewei_liu_bingyan_second.md`.
21. **Workflow auto-chain boundary**: Image → Sheet is one step. **Every other step (lottery / EMR / ordering / cathlab) requires explicit user trigger** — even if the user provides multiple resources upfront ("把工作都跑完" + image + EMR URL + JSON). Stop after each step. See `memory/feedback_no_auto_lottery.md`.
22. **EMR summary on demand only**: Sub-table is 8-col A-H. D=EMR摘要 is a placeholder — `process_emr.py` writes only C (raw EMR) + F (術前診斷) + G (預計心導管). D stays empty until the user explicitly asks for a summary (then call Gemini to fill that single row). No auto-generated summary. See `memory/feedback_no_emr_summary.md`.

## WEBCVIS Cathlab System

- **URL**: `http://cardiopacs01.hosp.ncku:8080/WEBCVIS/HCO/HCO1W001.do`
- **Login**: 107614 / 107614
- **Date fields** (`daySelect1`/`daySelect2`): readonly — must `removeAttribute('readonly')` via JS before setting.
- **QueryButton**: `<button>` not `<input>` — use `document.getElementById("QueryButton").click()`.
- **Form name**: `HCO1WForm`; `buttonName` input is renamed (`.name = "ADD"/"SAVE"/"QRY"`) before each submit.
- **JSON fields**: `pdijson` (diagnosis), `phcjson` (planned procedure), `hctjson` (registration codes) are hidden inputs holding JSON arrays like `[{"name":"","id":"PDI20090908120009"}]`.
- **Popup pages**: HCO1N002.do (diagnosis tree), HCO1N004.do (procedure tree), HCO1N001.do (registration codes) — set values directly via JS to skip popup handling.
- **SaveButton**: jQuery click handler must fire (sets `finishjson`/`refernojson`) — use `page.click('#SaveButton')`, not manual form submit.

## Sheet Layout (date sheets like `20260420`)

```
Main data A-L (row 1 = header, row 2+ = patients):
  A=實際住院日 | B=開刀日 | C=科別 | D=主治醫師 | E=主診斷(ICD) | F=姓名
  G=性別 | H=年齡 | I=病歷號碼 | J=病床號 | K=入院提示 | L=住急

N-V (row 1 = header, row 2+ = ordered list):
  N=序號 | O=主治醫師 | P=病人姓名 | Q=備註(住服) | R=備註
  S=病歷號 | T=術前診斷 | U=預計心導管 | V=改期

Below main data: doctor sub-tables (8 cols A-H per block):
  [Doctor title row, merged]    e.g. "柯呈諭（2人）"
  [Sub-header row]              A=姓名 | B=病歷號 | C=EMR | D=EMR摘要 | E=手動設定入院序 | F=術前診斷 | G=預計心導管 | H=註記
  [Patient rows]
  [blank row gap]

  D=EMR摘要 is a placeholder column (left empty by process_emr; user calls Gemini on demand to fill).
```

**Creating a new date sheet** — duplicate a recent sheet → `unmergeCells` on the entire range → `batch_clear` → write new main data → build doctor sub-tables with `write_doctor_table`. Unmerge is critical: merged title rows from the source (e.g. "李文煌（1人）" at A:H) will otherwise swallow writes at the same row index.

`generate_ordering.py` parses sub-tables by detecting "X人）" title patterns.

## Common Commands

```bash
python <script>.py
pip install gspread google-auth playwright
playwright install chromium
```

## External tools

- **Claude-Gemini-Dialogue** (`~/repos/Claude-Gemini-Dialogue/scripts/delegate.sh`): Token-saving delegation wrapper — push grunt work (long-text search, translation, CSV→md, structural transforms) to Gemini CLI. See `memory/reference_claude_gemini_dialogue.md`. Don't use for admission-list business logic (Gemini lacks our context).
