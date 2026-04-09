# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hospital admission list management system for a cardiology department (成大醫院心臟科行政總醫師). Automates the daily workflow: patient list intake → lottery ordering → EMR extraction → admission sequencing → cathlab scheduling → LINE notifications.

## Environment

- **Platform**: Windows 11, Python 3.14, `python` (not `python3`)
- **Terminal encoding**: cp950 — Chinese characters with special Unicode (emojis, ❌✅) will crash `print()`. Write output to UTF-8 files and read with the Read tool instead.
- **Google Sheets API**: `gspread` + service account (`sigma-sector-492215-d2-0612bef3b39b.json`)
- **Sheet ID**: `1DTIRNy10Tx3GfhuFq46Eu2_4J74Z3ZiIh7ymZtetZUI`
- **Browser automation**: Playwright (`playwright.sync_api`, Chromium, non-headless)
- **Worksheet access**: `sh.worksheet('name')` works for named sheets. Key sheets: 無資料病人, 下拉選單, 麻醉, 每天續等清單, 主治醫師導管時段表, 主治醫師抽籤表, CathDuration, plus date sheets (20260406, 20260407, ...)

## Architecture

All scripts share `gsheet_utils.py` (singleton gspread client, read/write/format/dropdown helpers). The typical data flow:

1. **Image → Sheet**: OCR screenshot → write patient data to columns A–L of a date sheet (e.g., `20260408`)
2. **Lottery → Ordering**: `generate_ordering.py` reads doctor sub-tables (below main data), applies round-robin, writes N–T columns
3. **Cathlab keyin**: Per-date scripts (`cathlab_keyin_04XX.py`) drive Playwright against WEBCVIS — Phase 1 ADDs patients, Phase 2 UPTs to fix pdijson/phcjson

Scripts write results to `_*.txt` files (e.g., `_ordering_result.txt`) because cp950 terminal can't print Chinese+emoji. Read these with the Read tool.

## Key Files

- `gsheet_utils.py` — Shared Google Sheets module. Provides `get_worksheet()`, `write_range()`, `format_header_row()`, `write_doctor_table()`, `set_dropdown_from_range()`, etc. All scripts import from here.
- `generate_ordering.py` — Reads doctor sub-tables + round-robin order from a date sheet, generates N–T ordering. Pattern: `extract_doctor_tables()` → `generate_ordering()` → `write_ordering_to_sheet()`.
- `cathlab_keyin_04XX.py` — One script per cathlab date. Contains PATIENTS list (hardcoded per day), login/date-query/add/fix_diag functions. Copy the latest one as template for new dates.
- `每日入院清單工作流程.txt` — Complete workflow spec with all rules, doctor codes, room codes, column layouts, and dropdown mappings. **Read this first for any workflow question.**
- `memory/MEMORY.md` — Persistent memory index. Read at session start for prior feedback and corrections.
- `cathlab_page.html` — Saved HTML of WEBCVIS cathlab system for form field analysis.
- `cathlab_id_maps.json` — pdijson/phcjson ID mappings (diagnosis→PDI ID, procedure→PHC ID).
- `schedule_readable.txt` — Human-readable doctor schedule table (Mon–Fri, AM/PM rooms).
- `verify_cathlab.py` — Verify all admission patients appear in next-day WEBCVIS cathlab schedule. Usage: `python verify_cathlab.py 20260409`

## Workflow (6 steps)

```
截圖 → OCR匯入Sheet → 抽籤排序 → EMR摘要 → 排住院序 → 導管排程 → /workflow-doc
```

Full details in `每日入院清單工作流程.txt`. Critical rules:

1. **Ordering columns N–U (8 columns)**: 序號 | 主治醫師 | 病人姓名 | 備註 | 病歷號 | 術前診斷 | 預計心導管 | 每日續等清單 (user has corrected this multiple times — do not reorder, do not omit 病歷號)
2. **Round-robin lottery**: True round-robin (A1→B1→C1→A2→B2→C2→A3...), not block-by-doctor
2a. **Friday admission → Friday schedule**: 週五入院查週五抽籤表（週六無抽籤表）。日→一、一→二、二→三、三→四、四→五、**五→五**
3. **Non-schedule doctors**: Never include in main round-robin. Ask user before merging with daily waitlist.
4. **Cathlab direction**: Patients admitted on day N → cathlab scheduled on day N+1
5. **Cathlab safety**: Only add new entries, never modify or delete existing ones
6. **Cathlab times**: AM=0600+, PM=1730+, non-schedule=H1 1800+
7. **No-data patients**: Still key into cathlab schedule at doctor's time slot, note="無資料病人"
8. **Skip rule**: 備註含「不排程」或「檢查」→ skip cathlab keyin（「非導管床」「HF AE」不一定跳過，只有「檢查」才確定跳過）
9. **Sheet no-overwrite**: 寫入 Sheet 前必須先讀取目標區域，確認為空才寫入，絕不覆蓋現有資料
10. **EMR auto-write**: EMR 摘要完成後自動寫入 Sheet，不需再問使用者確認
11. **EMR manual login**: 不要自己開瀏覽器登入 EMR，等使用者手動登入後貼 session URL，再用 Playwright 帶 session 查詢
12. **Waitlist merge**: 續等清單整合 → 有時段醫師接 round-robin、無時段最後，U欄標1
13. **Ordering timing**: Claude 必須等使用者手動確認 F/G 欄後才能寫入 N-U 欄
14. **EMR prefill F/G**: EMR 摘要完成後自動預填術前診斷(F)和預計心導管(G)，列出讓使用者檢查
15. **Second doctor priority**: 第二醫師多人時（如浩、晨），葉立浩優先 key attendingdoctor2，其餘放備註

## WEBCVIS Cathlab System

- **URL**: `http://cardiopacs01.hosp.ncku:8080/WEBCVIS/HCO/HCO1W001.do`
- **Login**: 107614 / 107614
- **Date fields** (`daySelect1`/`daySelect2`): readonly — must `removeAttribute('readonly')` via JS before setting
- **QueryButton**: Is a `<button>`, not `<input>` — use `document.getElementById("QueryButton").click()`
- **Form name**: `HCO1WForm`; `buttonName` input gets renamed (`.name = "ADD"/"SAVE"/"QRY"`) before each submit
- **JSON fields**: `pdijson` (diagnosis), `phcjson` (planned procedure), `hctjson` (registration codes) are hidden inputs with JSON arrays like `[{"name":"","id":"PDI20090908120009"}]`
- **Popup pages**: HCO1N002.do (diagnosis tree), HCO1N004.do (procedure tree), HCO1N001.do (registration codes) — set values directly via JS to avoid popup handling
- **SaveButton**: jQuery click handler must fire (sets `finishjson`/`refernojson`) — use `page.click('#SaveButton')`, not manual form submit

## Sheet Layout (date sheets like `20260408`)

```
Columns A–L (row 1 = header, row 2+ = patients):
  Main patient data from OCR (12 columns). Col J=病歷號碼, Col L=入院提示

Columns N–T (row 1 = header, row 2+ = ordered list):
  序號 | 主治醫師 | 病人姓名 | 備註 | 術前診斷 | 預計心導管 | 每日續等清單

Below main data: Doctor sub-tables (8 cols A–H per doctor block):
  [Doctor title row, merged]  e.g. "柯呈諭（2人）"
  [Sub-header row]            姓名|病歷號|EMR|EMR摘要|手動設定入院序|術前診斷|預計心導管|註記
  [Patient rows]
  [blank row gap]
```

`generate_ordering.py` parses these sub-tables by detecting "X人）" title patterns.

## Common Commands

```bash
# Run any script
python <script>.py

# Install dependencies
pip install gspread google-auth playwright
playwright install chromium
```
