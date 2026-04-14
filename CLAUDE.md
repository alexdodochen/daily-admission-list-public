# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hospital admission list management system for a cardiology department (成大醫院心臟科行政總醫師). Automates the daily workflow: patient list intake → lottery ordering → EMR extraction → admission sequencing → cathlab scheduling → LINE notifications.

## Environment

- **Platform**: Windows 11, Python 3.14, `python` (not `python3`)
- **Terminal encoding**: cp950 — Chinese characters with special Unicode (emojis, ❌✅) will crash `print()`. Write output to UTF-8 files and read with the Read tool instead. All `open(..., 'w')` calls must pass `encoding='utf-8'` explicitly.
- **Google Sheets API**: `gspread` + service account (`sigma-sector-492215-d2-0612bef3b39b.json`)
- **Sheet ID**: `1DTIRNy10Tx3GfhuFq46Eu2_4J74Z3ZiIh7ymZtetZUI`
- **Browser automation**: Playwright (`playwright.sync_api`, Chromium, non-headless)
- **Worksheet access**: `sh.worksheet('name')` works for named sheets. Key sheets: 無資料病人, 下拉選單, 麻醉, 每天續等清單, 主治醫師導管時段表, 主治醫師抽籤表, CathDuration, plus date sheets (20260406, 20260407, ...)

## Architecture

All scripts share `gsheet_utils.py` (singleton gspread client, read/write/format/dropdown helpers). Each workflow step has a corresponding skill in `.claude/skills/`. The typical data flow:

1. **Image → Sheet** (`admission-image-to-excel`): OCR screenshot → write patient data to columns A–L of a date sheet (e.g., `20260408`). If the date sheet already exists, performs **diff-update** (match by 病歷號 → add new / remove cancelled / preserve existing EMR/F/G/ordering).
2. **Lottery** (`admission-lottery`): Random draw → doctor sub-tables (A–H below main data) + round-robin ordering (N–P)
3. **EMR extraction** (`admission-emr-extraction`): Playwright reads Web EMR (`http://hisweb.hosp.ncku/Emrquery/`) → writes C/D cols in sub-tables → auto-prefills F/G
4. **Ordering** (`admission-ordering`): Reads sub-tables F/G after user confirms → writes N–W columns
5. **Cathlab keyin** (`admission-cathlab-keyin`): Per-date scripts (`cathlab_keyin_04XX.py`) drive Playwright against WEBCVIS — Phase 1 ADDs patients, Phase 2 UPTs to fix pdijson/phcjson

**Reschedule is a manual flag, not a feature.** W 欄填入 YYYYMMDD 的 row 表示「該病人不做當日的 N+1 cathlab」— 使用者自行決定如何另行處理（手動加排/手動通知）。沒有自動搬 sheet、沒有自動 DEL/ADD WEBCVIS、沒有子表格異動。cathlab keyin 和 verify 兩側都必須把 W 有值的 row 當作 skip。

Scripts write results to `_*.txt` files (e.g., `_ordering_result.txt`) because cp950 terminal can't print Chinese+emoji. Read these with the Read tool.

**Ephemeral artifacts** (do not commit): `_*.txt` debug dumps, `emr_data.json`, `每日入院名單*.xlsx` local backups, `20260*.jpg` source screenshots, and `cathlab_keyin_04XX.py` per-date scripts once the date has passed.

## Key Files

- `gsheet_utils.py` — Shared Google Sheets module. Provides `get_worksheet()`, `write_range()`, `format_header_row()`, `write_doctor_table()`, `set_dropdown_from_range()`, etc. All scripts import from here.
- `generate_ordering.py` — Reads doctor sub-tables + round-robin order from a date sheet, generates N–T ordering. Pattern: `extract_doctor_tables()` → `generate_ordering()` → `write_ordering_to_sheet()`.
- `cathlab_keyin_04XX.py` — One script per cathlab date. Contains PATIENTS list (hardcoded per day), login/date-query/add/fix_diag functions. Copy the latest one as template for new dates.
- `process_emr_04XX.py` / `write_emr_04XX.py` — Per-date EMR extraction and write-back scripts. Same copy-latest-as-template pattern as cathlab scripts.
- `每日入院清單工作流程.txt` — Canonical workflow spec with all rules, doctor codes, room codes, column layouts, and dropdown mappings. **Read this first for any workflow question — if it disagrees with `CLAUDE.md`, the txt file wins** (user actively maintains it).
- `memory/MEMORY.md` — Persistent memory index. **Run the `check-previous-progress` skill at session start before any work** to load prior feedback and corrections.
- `_*.py` / `_*.txt` — Underscore-prefixed files are throwaway debugging/verification scratch (one-off checks, patches, logs). Not reference implementations; do not copy their patterns into permanent code.
- `cathlab_page.html` — Saved HTML of WEBCVIS cathlab system for form field analysis.
- `cathlab_id_maps.json` — pdijson/phcjson ID mappings (diagnosis→PDI ID, procedure→PHC ID).
- `schedule_readable.txt` — Human-readable doctor schedule table (Mon–Fri, AM/PM rooms). A named cell = that doctor has a slot that day, even if tagged like "結構", "齡", "寬" — those are secondary-doctor / theme annotations, not "no slot".
- `verify_cathlab.py` — Verify all admission patients appear in the corresponding WEBCVIS cathlab schedule. Reads from **sub-table (統整資料)**, cross-references N-W 的 W 欄（有值 → skip）。Handles Friday same-day cathlab. Usage: `python verify_cathlab.py 20260409`

## Workflow (6 steps)

```
截圖 → OCR匯入Sheet → 抽籤排序 → EMR摘要 → 排住院序 → 導管排程 → /workflow-doc
```

Full details in `每日入院清單工作流程.txt`. Critical rules:

1. **Ordering columns N–W (10 columns)**: 序號 | 主治醫師 | 病人姓名 | 備註(住服) | 備註 | 病歷號 | 術前診斷 | 預計心導管 | 每日續等清單 | 改期 (user has corrected this multiple times — do not reorder, do not omit 病歷號 or 備註(住服)). LINE 07:50 push only sends N-Q (first 4 cols) to 住服. **W 欄=改期**：純人工標記欄位。使用者手動在該 ordering row 填 YYYYMMDD 表示此病人延後處理 → 該 row 不會進入 N+1 cathlab keyin，也會被 `verify_cathlab.py` skip。手動寫 W 時必須用 P 欄姓名或 S 欄病歷號比對 ordering row（不是主資料 row，round-robin 後 row 順序不同）。
2. **Round-robin lottery**: True round-robin (A1→B1→C1→A2→B2→C2→A3...), not block-by-doctor
3. **Friday admission → Friday schedule**: 週五入院查週五抽籤表（週六無抽籤表）。日→一、一→二、二→三、三→四、四→五、**五→五**
4. **Non-schedule doctors**: Never include in main round-robin. Ask user before merging with daily waitlist.
5. **Cathlab direction**: Patients admitted on day N → cathlab scheduled on day N+1. **Exception**: Friday admissions → Friday cathlab (same day, since Saturday has no schedule).
6. **Cathlab safety**: Only add new entries, never modify or delete existing ones
7. **Cathlab times**: scheduled AM=0600+, scheduled PM=1800+, non-schedule=H1 2100+ (note="本日無時段")
8. **No-data patients**: Still key into cathlab schedule at doctor's time slot, note="無資料病人"
9. **Skip rule**: 備註含「不排程」或「檢查」→ skip cathlab keyin（「非導管床」「HF AE」不一定跳過，只有「檢查」才確定跳過）
10. **Sheet no-overwrite**: 寫入 Sheet 前必須先讀取目標區域，確認為空才寫入，絕不覆蓋現有資料
11. **EMR auto-write**: EMR 摘要完成後自動寫入 Sheet，不需再問使用者確認
12. **EMR manual login**: 不要自己開瀏覽器登入 EMR，等使用者手動登入後貼 session URL，再用 Playwright 帶 session 查詢
13. **Waitlist merge**: 續等清單整合 → 有時段醫師接 round-robin、無時段最後，U欄標1
14. **Ordering timing**: Claude 必須等使用者手動確認 F/G 欄後才能寫入 N-U 欄
15. **EMR prefill F/G**: EMR 摘要完成後自動預填術前診斷(F)和預計心導管(G)，列出讓使用者檢查
16. **Second doctor priority**: 第二醫師多人時（如浩、晨），葉立浩優先 key attendingdoctor2，其餘放備註
17. **Post-edit format check**: 任何寫入/修改日期 sheet 病人清單之後，**一定要** 讀回驗證格式（主資料 A-L、N-W ordering、子表格 title/人數/空白隔行、無殘留合併、病歷號一致）。跑掉就當場修，不留尾巴給使用者（見 `memory/feedback_post_edit_format_check.md`）。

## WEBCVIS Cathlab System

- **URL**: `http://cardiopacs01.hosp.ncku:8080/WEBCVIS/HCO/HCO1W001.do`
- **Login**: 107614 / 107614
- **Date fields** (`daySelect1`/`daySelect2`): readonly — must `removeAttribute('readonly')` via JS before setting
- **QueryButton**: Is a `<button>`, not `<input>` — use `document.getElementById("QueryButton").click()`
- **Form name**: `HCO1WForm`; `buttonName` input gets renamed (`.name = "ADD"/"SAVE"/"QRY"`) before each submit
- **JSON fields**: `pdijson` (diagnosis), `phcjson` (planned procedure), `hctjson` (registration codes) are hidden inputs with JSON arrays like `[{"name":"","id":"PDI20090908120009"}]`
- **Popup pages**: HCO1N002.do (diagnosis tree), HCO1N004.do (procedure tree), HCO1N001.do (registration codes) — set values directly via JS to avoid popup handling
- **SaveButton**: jQuery click handler must fire (sets `finishjson`/`refernojson`) — use `page.click('#SaveButton')`, not manual form submit

## Sheet Layout (date sheets like `20260420`)

Current layout (since ~2026-04 — note: older sheets like `20260330` used a different column order):

```
Main data columns A–L (row 1 = header, row 2+ = patients):
  A=實際住院日 | B=開刀日 | C=科別 | D=主治醫師 | E=主診斷(ICD) | F=姓名
  G=性別 | H=年齡 | I=病歷號碼 | J=病床號 | K=入院提示 | L=住急

Columns N–W (row 1 = header, row 2+ = ordered list):
  N=序號 | O=主治醫師 | P=病人姓名 | Q=備註(住服) | R=備註
  S=病歷號 | T=術前診斷 | U=預計心導管 | V=每日續等清單 | W=改期

Below main data: Doctor sub-tables (8 cols A–H per doctor block):
  [Doctor title row, merged]  e.g. "柯呈諭（2人）"
  [Sub-header row]            A=姓名 | B=病歷號 | C=EMR | D=EMR摘要 | E=手動設定入院序 | F=術前診斷 | G=預計心導管 | H=註記
  [Patient rows]
  [blank row gap]
```

**Creating a new date sheet** — duplicate a recent sheet → `unmergeCells` on the entire range → `batch_clear` → write new main data → build doctor sub-tables with `write_doctor_table`. The unmerge step is critical: merged title rows from the source sheet (e.g. "李文煌（1人）" at A:H) will otherwise swallow writes to the patient data row at the same index.

`generate_ordering.py` parses these sub-tables by detecting "X人）" title patterns.

## Common Commands

```bash
# Run any script
python <script>.py

# Install dependencies
pip install gspread google-auth playwright
playwright install chromium
```
