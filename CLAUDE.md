# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Daily admission list management for a cardiology department (心臟內科). Automates patient intake ordering via a 6-step workflow driven by Claude Code skills, operating on a shared Google Sheet.

## Startup checklist

Every new conversation, before any work:
1. Read `memory/MEMORY.md` for prior progress, feedback, and references
2. Read relevant feedback memory files (these are user corrections — highest priority)
3. Check the Google Sheet for the latest worksheet state
4. Report status: "上次進度到 [X]，下一步是 [Y]"
5. Show workflow progress bar each reply (✅/🔄/⬜)

## Running scripts locally

```bash
python gsheet_utils.py          # no standalone use — imported by skills
python migrate_to_gsheet.py     # one-time migration (already done)
```

Dependencies: `gspread`, `gspread-formatting`, `google-auth` (for Google Sheets API); `openpyxl` only used in migration script. Python 3.13+.

## Workflow overview

Full details in `每日入院清單工作流程.txt`. Each step maps to a skill:

| Step | Skill | Trigger phrase |
|------|-------|---------------|
| 1. OCR import | `admission-image-to-excel` | paste screenshot(s) |
| 2. Lottery | `admission-lottery` | 「抽籤」 |
| 3. EMR extraction | `admission-emr-extraction` | auto after lottery |
| 4. Admission ordering | `admission-ordering` | 「整合入院序」(after user fills F/G dropdowns) |
| 5. LINE push | (via parent project `/trigger-admission`) | manual |
| 6. Cathlab key-in | `admission-cathlab-keyin` | 「導管排程」 |

## Data layer: Google Sheet (not local Excel)

All operations use Google Sheets API via `gsheet_utils.py`. Never use openpyxl for production operations.

- **Sheet ID**: `1DTIRNy10Tx3GfhuFq46Eu2_4J74Z3ZiIh7ymZtetZUI`
- **Credentials**: `sigma-sector-492215-d2-0612bef3b39b.json` (Service Account — never commit to public repos)
- **Utility module**: `gsheet_utils.py` — singleton client, all CRUD + formatting + dropdown + grouping operations

Key worksheets:
- `每天續等清單` — daily waitlist (cols A-E data, H-I-J lottery results)
- `主治醫師時段表` — clinic schedule + cathlab room assignments
- `主治醫師抽籤表` (3rd sheet) — cols A-E = Mon-Fri, `*2` = double lottery tickets
- `下拉選單` — col A = 術前診斷 (65 items), col D = 預計心導管 (22 items)
- `YYYYMMDD` — daily sheet: rows A-L patient data, N-U admission order, doctor tables below
- `YYYYMMDD 定案` — finalized admission list (daily + waitlist merged)

## Architecture: gsheet_utils.py

Singleton pattern — `get_client()` and `get_spreadsheet()` cache connections. All skills import this module. Key design decisions:
- `batch_update_requests()` chunks at 500 requests with `time.sleep(1)` between batches (Google API rate limits)
- `create_worksheet()` deletes existing sheet of same name before creating — intentional (daily sheets get rebuilt)
- `write_doctor_table()` is the reusable block for doctor-patient sub-tables (8 cols A-H with merge + format)
- All cell coordinates are **1-indexed** (gspread convention)

## Daily worksheet layout (YYYYMMDD)

**Top section — patient master data (A-L, 12 cols)**:
A=預約入院日期, B=病歷號, C=姓名, D=主治醫師, E=性別, F=年齡, G=診斷, H=預計住院天數, I=入院提示, J=病房, K=護理站, L=備註

**Mid section — admission order (N-U, 8 cols)**:
N=序號, O=主治醫師, P=病人姓名, Q=備註, R=病歷號(文字格式), S=術前診斷, T=預計心導管, U=每日續等清單(填1=標記搬到續等)

**Below data — doctor sub-tables (A-H per doctor)**:
A=姓名, B=病歷號, C=EMR(collapsible), D=EMR摘要, E=手動設定入院序, F=術前診斷(dropdown), G=預計心導管(dropdown), H=註記

## Critical rules (from repeated user corrections)

**Lottery ordering**: Use NEXT day's clinic doctors from 主治醫師抽籤表 (Sun→Mon, Mon→Tue, ... Thu→Fri; Fri/Sat = ask user). MUST verify doctors against the 抽籤表 before any ordering step.

**Non-cathlab doctors**: Their patients stay in the daily worksheet. They are NOT moved to waitlist. They are NOT mixed into the main round-robin lottery. After all cathlab-slot doctors' patients are ordered, ask user whether to merge with waitlist before continuing.

**Column N-U timing**: Never write admission order columns until user confirms F/G dropdown selections are complete.

**Chart number verification**: After OCR import, always list all 病歷號 for user confirmation before proceeding. Chart numbers are 8 digits, stored as text (preserve leading zeros).

**EMR name authority**: EMR system names override OCR-imported names. Update all locations in the sheet. No records = write "無本院一年內主治醫師門診紀錄". Truncated names from OCR are fixed during EMR step, not before.

**Auto-continue after lottery**: Immediately start EMR extraction after lottery completes — don't ask.

**李柏增**: Never fill as attendingdoctor1 or attendingdoctor2 in cathlab key-in.

**LINE push safety**: Never push to 成醫-心內 group without explicit permission. Only the 07:50 auto-push is pre-authorized.

## EMR extraction details

- Uses Chrome browser automation (claude-in-chrome MCP) against `http://hisweb.hosp.ncku/Emrquery/`
- Local HTTP server on port 18234 exports EMR data
- Results cached in `emr_data.json` (reusable across retries)
- EMR summaries are 4-section format: 心臟科相關診斷 / 病史 / 客觀檢查 / 本次住院計畫

## Cathlab key-in (CVIS system)

- URL: `http://cardiopacs01.hosp.ncku:8080/WEBCVIS/HCO/HCO1W001.do`
- Only adds new entries — never modifies or deletes existing schedules
- Room codes: H1→xa-Hybrid1, H2→xa-Hybrid2, C1→xa-CATH1, C2→xa-CATH2
- Time encoding: AM 0600+1 per patient, PM 1230+1 per patient
- Second doctor (括號簡稱): 寬→葉建寬, 浩→葉立浩, 晨→洪晨惠, 齡→許毓軨, 嘉→蘇奕嘉

## Other files

- `migrate_to_gsheet.py` — one-time migration from local xlsx to Google Sheet (already run, kept for reference)
- `emr_data.json` — cached EMR extraction results per session
- `每日入院清單工作流程.txt` — authoritative workflow documentation (read this for full step details)
- `每日入院名單.xlsx` / `每日入院名單_backup.xlsx` — legacy local Excel files (superseded by Google Sheet)
