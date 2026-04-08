# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hospital admission list management system for a cardiology department (成大醫院心臟科行政總醫師). Automates the daily workflow: patient list intake -> lottery ordering -> EMR extraction -> admission sequencing -> cathlab scheduling -> LINE notifications.

## Environment

- **Platform**: Windows 11, Python 3.14, `python` (not `python3`)
- **Terminal encoding**: cp950 — Chinese characters with special Unicode (emojis) will crash `print()`. Write output to UTF-8 files (prefix `_`) and read with the Read tool instead.
- **Google Sheets API**: `gspread` + service account (`sigma-sector-492215-d2-0612bef3b39b.json`)
- **Sheet ID**: `1DTIRNy10Tx3GfhuFq46Eu2_4J74Z3ZiIh7ymZtetZUI`
- **Browser automation**: Playwright (`playwright.sync_api`, Chromium, non-headless) for EMR and WEBCVIS
- **Dependencies**: `gspread`, `google-auth`, `playwright`. `openpyxl` only in legacy migration script.

## Startup Checklist

Every new conversation, before any work:
1. Read `memory/MEMORY.md` for prior progress, feedback, and references
2. Read relevant feedback memory files (user corrections — highest priority)
3. Check the Google Sheet for the latest worksheet state
4. Report status: "上次進度到 [X]，下一步是 [Y]"
5. Show workflow progress bar each reply (done/in-progress/pending)

## Architecture

All scripts share `gsheet_utils.py` (singleton gspread client, read/write/format/dropdown helpers). The typical data flow:

1. **Image -> Sheet**: OCR screenshot -> write patient data to columns A-L of a date sheet (e.g., `20260408`)
2. **Lottery -> Doctor Tables**: Random draw determines round-robin order, builds doctor sub-tables below main data (8 cols A-H per doctor block)
3. **EMR Extraction**: Playwright queries hospital EMR system, writes summaries to doctor sub-tables C/D columns
4. **Ordering**: `generate_ordering.py` reads doctor sub-tables + round-robin order, applies E-column manual overrides, writes N-V columns
5. **Cathlab keyin**: Per-date scripts (`cathlab_keyin_04XX.py`) drive Playwright against WEBCVIS — Phase 1 ADDs patients, Phase 2 UPTs to fix pdijson/phcjson

Scripts write results to `_*.txt` files because cp950 terminal can't print Chinese+emoji. Read these with the Read tool.

## Key Files

- `gsheet_utils.py` — Shared Google Sheets module (singleton client). All CRUD, formatting, dropdown, grouping operations. Key functions: `get_worksheet()`, `write_range()`, `write_doctor_table()`, `set_dropdown_from_range()`, `batch_update_requests()` (chunks at 500 with 1s sleep for API rate limits). All cell coordinates are 1-indexed.
- `generate_ordering.py` — Reads doctor sub-tables + round-robin order from a date sheet, generates N-V ordering. Core pattern: `extract_doctor_tables()` -> `generate_ordering()` -> `write_ordering_to_sheet()`.
- `cathlab_keyin_04XX.py` — One script per cathlab date. Contains PATIENTS list (hardcoded per day), login/date-query/add/fix_diag functions. Copy the latest one as template for new dates.
- `cathlab_id_maps.json` — pdijson/phcjson ID mappings (diagnosis->PDI ID, procedure->PHC ID). Use this for looking up WEBCVIS form IDs.
- `cathlab_page.html` — Saved HTML of WEBCVIS cathlab system for form field analysis.
- `schedule_readable.txt` — Human-readable doctor schedule table (Mon-Fri, AM/PM rooms with second-doctor abbreviations).
- `每日入院清單工作流程.txt` — Complete workflow spec with all rules, doctor codes, room codes, column layouts, and dropdown mappings. **Read this first for any workflow question.**
- `memory/MEMORY.md` — Persistent memory index. Read at session start for prior feedback and corrections.
- `.claude/commands/workflow-doc.md` — End-of-session slash command: saves memory, evaluates skills, updates docs.

## Workflow (6 steps)

```
截圖 -> OCR匯入Sheet -> 抽籤排序 -> EMR摘要 -> 排住院序 -> 導管排程 -> /workflow-doc
```

| Step | Skill | Trigger phrase |
|------|-------|---------------|
| 1. OCR import | `admission-image-to-excel` | paste screenshot(s) |
| 2. Lottery | `admission-lottery` | 「抽籤」 |
| 3. EMR extraction | `admission-emr-extraction` | auto after lottery |
| 4. Admission ordering | `admission-ordering` | 「整合入院序」(after user fills F/G dropdowns) |
| 5. LINE push | (via parent project `/trigger-admission`) | manual |
| 6. Cathlab key-in | `admission-cathlab-keyin` | 「導管排程」 |

Full details in `每日入院清單工作流程.txt`.

## Sheet Layout (date sheets like `20260408`)

**Columns A-L** (row 1=header, row 2+=patients): Main patient data from OCR (12 columns). Col J=病歷號碼, Col L=入院提示.

**Columns N-V** (row 1=header, row 2+=ordered list): 序號 | 主治醫師 | 病人姓名 | 備註(住服) | 備註 | 病歷號 | 術前診斷 | 預計心導管 | 每日續等清單. (9 columns). LINE 07:50 push to 住服 only includes first 4 columns (序號/主治醫師/病人姓名/備註(住服)). This column order has been corrected by the user multiple times — do not change it.

**Below main data**: Doctor sub-tables (8 cols A-H per doctor block). Title row pattern: "柯呈諭（2人）". Sub-header: 姓名|病歷號|EMR|EMR摘要|手動設定入院序|術前診斷|預計心導管|註記. F/G columns have dropdown validation linked to 下拉選單 sheet.

`generate_ordering.py` parses sub-tables by detecting "X人）" title patterns.

## Critical Rules (from repeated user corrections)

### Lottery & Ordering
1. **Round-robin**: True round-robin (A1->B1->C1->A2->B2->C2->A3...), not block-by-doctor
2. **Next-day doctors**: Use NEXT day's clinic doctors from 主治醫師抽籤表 (Sun->Mon, Mon->Tue, ..., Thu->Fri; Fri/Sat = ask user)
3. **Non-schedule doctors**: Never include in main round-robin. Their patients stay in the daily worksheet (not moved to waitlist). After all scheduled doctors' patients are ordered, ask user whether to merge with waitlist before continuing.
4. **Columns N-V timing**: Never write admission order columns until user confirms F/G dropdown selections are complete.
5. **Waitlist merge**: 有時段醫師接round-robin排續等、無時段醫師最後，T欄標1

### OCR & EMR
6. **Chart number verification**: After OCR import, always list all 病歷號 for user confirmation. Chart numbers are 8 digits, stored as text (preserve leading zeros).
7. **Image OCR**: Low-resolution screenshots must be enlarged 3-6x with PIL and cropped in sections before reading. Never rely on raw Read tool preview for table data.
8. **EMR name authority**: EMR system names override OCR-imported names. Update all locations in the sheet. No records = C欄 write "無本院一年內主治醫師門診紀錄", H欄 auto-write "無資料病人", and auto-populate 無資料病人 worksheet.
9. **EMR manual login**: Never auto-open browser to login EMR. Wait for user to manually login and paste session URL, then use Playwright with that session.
10. **EMR auto-write**: After extraction, write summaries to Sheet immediately without asking user confirmation.

### Cathlab
11. **Cathlab direction**: Patients admitted on day N -> cathlab scheduled on day N+1
12. **Cathlab safety**: Only add new entries, never modify or delete existing schedules
13. **Cathlab times**: AM=0600+, PM=1730+, non-schedule=H1 1800+
14. **No-data patients**: Still key into cathlab schedule at doctor's time slot, note="無資料病人"
15. **Skip rule**: 備註含「不排程」-> skip cathlab keyin
16. **李柏增**: Never fill as attendingdoctor1 or attendingdoctor2 in cathlab key-in
17. **Note fallback**: If 預計心導管 value is not in WEBCVIS dropdown, write it to the note field instead

### Sheet Operations
18. **No overwrite**: Before writing to Sheet, read target area first, confirm it's empty. Never overwrite existing data.
19. **create_worksheet()**: Deletes existing sheet of same name before creating — this is intentional (daily sheets get rebuilt).

## WEBCVIS Cathlab System

- **URL**: `http://cardiopacs01.hosp.ncku:8080/WEBCVIS/HCO/HCO1W001.do`
- **Login**: 107614 / 107614
- **Date fields** (`daySelect1`/`daySelect2`): readonly — must `removeAttribute('readonly')` via JS before setting
- **QueryButton**: Is a `<button>`, not `<input>` — use `document.getElementById("QueryButton").click()`
- **Form**: `HCO1WForm`; `buttonName` input gets renamed (`.name = "ADD"/"SAVE"/"QRY"`) before each submit
- **JSON fields**: `pdijson` (diagnosis), `phcjson` (procedure), `hctjson` (registration codes) are hidden inputs with JSON arrays like `[{"name":"","id":"PDI20090908120009"}]`
- **Popup pages**: HCO1N002.do (diagnosis), HCO1N004.do (procedure), HCO1N001.do (registration) — set values directly via JS to avoid popup handling
- **SaveButton**: jQuery handler must fire (sets `finishjson`/`refernojson`) — use `page.click('#SaveButton')`, not manual form submit
- **Room codes**: H1->xa-Hybrid1, H2->xa-Hybrid2, C1->xa-CATH1, C2->xa-CATH2

## Key Worksheets in Google Sheet

| Sheet | Purpose |
|-------|---------|
| `每天續等清單` | Daily waitlist (A-E data, H-I-J lottery results) |
| `主治醫師導管時段表` | Doctor schedule + cathlab room assignments (see schedule_readable.txt) |
| `主治醫師抽籤表` (3rd sheet) | Cols A-E = Mon-Fri, `*2` = double lottery tickets |
| `下拉選單` | Col A = 術前診斷 (65 items), Col D = 預計心導管 (22 items) |
| `無資料病人` | Patients with H欄="無資料病人" get organized here on command |
| `CathDuration` | Estimated cathlab procedure durations by category |
| `YYYYMMDD` | Daily sheet: A-L patient data, N-V admission order, doctor tables below |
| `YYYYMMDD 定案` | Finalized admission list (daily + waitlist merged) |

## Common Commands

```bash
python <script>.py                 # Run any script
pip install gspread google-auth playwright
playwright install chromium
```

Quick trigger phrases:
- 「這是今天的入院名單截圖，請匯入並抽籤」— runs steps 1+2+3 (auto-continues EMR after lottery)
- 「抽籤，陳則瑋排第一」— lottery with priority
- 「下拉選單填好了，幫我整合入院序」— step 4
- 「導管排程」— step 6
- `/workflow-doc` — end-of-session review
