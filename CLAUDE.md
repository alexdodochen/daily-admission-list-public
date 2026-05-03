# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session start

**Before any work**:

1. **`git fetch origin && git status -sb`** — check if origin is ahead. If so, `git pull --rebase` BEFORE touching any file. Multi-device user — origin may have new helper code (e.g. `_normalize_diag` in `cathlab_keyin.py`), new map entries (`cathlab_id_maps.json`), or per-date input (`cathlab_patients_YYYYMMDD.json`) that another session/machine already wrote. Skipping this step → you'll run with stale code, re-invent existing rules, or overwrite per-date work. Do not start any task before this check.
2. **`ls local_config.py`** — 沒有就立刻從別台機器 copy 過來（或從 `memory/_private_setup.md` 重建，那檔 gitignored）。`gsheet_utils` 預設 fallback 到 public mirror（demo sheet），缺檔等於把所有 PHI 寫到公開 sheet。詳見 `memory/feedback_local_config_required.md`（5/1 踩過）。
3. Run the `check-previous-progress` skill to load `memory/MEMORY.md` and prior feedback.
4. Check whether `cathlab_patients_<today>.json` / `emr_data_<today>.json` already exist on disk or in git — if yes, **use them**, don't rewrite.

The user actively maintains `每日入院清單工作流程.txt` as the source-of-truth workflow spec — **if it disagrees with this file, the txt wins**.

## Public mirror（給別的行政總醫師 clone）

- 公開 mirror: https://github.com/alexdodochen/daily-admission-list-public
- `origin` remote 已設成 dual push URLs — `git push origin main` 自動推到私有 + 公開兩邊。
- `origin` fetch URL 只有私有那一個 — `git pull` / `git fetch origin` 結構上不會碰到 public。
- **絕對不要** `git remote add public ...` 或 `git fetch <public_url>` — public 上其他行政總醫師可能 push 過自己的改動，pull 回來會破壞我們的歷史。
- Public 已分歧（push 被擋）時：用 `git push https://github.com/alexdodochen/daily-admission-list-public.git main --force`（私有那邊已成功就不重推），不要 merge public 歷史回來。
- 詳見 `memory/project_public_mirror_sync.md`。

### Public 不能有的東西（HARD RULE — 在 push 環節強制檢查）

`origin push` 同時推到 public mirror。任何帶有以下內容的 tracked 檔案**永遠不可被 commit**：

- 私有 SHEET_ID（具體字串見 `memory/_private_setup.md`）
- LINE 推播 bot 任何 infra：bot URL、bot ID（@-前綴）、`trigger-*` 系列 endpoint 路徑
- Service account JSON 內容（PEM private key block）

具體被擋的 regex 模式以 `scripts/pre_push_check.py` 的 `FORBIDDEN` list 為準。要看實際字串去 gitignored 的 `memory/_reference_line_reminder_bot.md` / `memory/_private_setup.md`。

凡屬上面類別的內容**一律寫到 gitignored 檔案**：根目錄 `_*.md` / `_*.txt`、或 `memory/_*.md`。LINE 推播相關的工作流程細節都已搬到 `memory/_reference_line_reminder_bot.md` / `memory/_reference_line_monthly_quota.md` / `memory/_reference_cronjob_render_gotchas.md` / `_step5_line_push.md`，未來新增 LINE 相關規則或 bot 細節**一律加到 `_` 前綴檔案**，不要寫進 `CLAUDE.md` / `每日入院清單工作流程.txt` / 其他 tracked 檔案。

**Push-time 護欄**（`scripts/pre_push_check.py` + `.githooks/pre-push`）：
- 一次性 setup：`git config core.hooksPath .githooks`（每台 clone 機器各跑一次）
- 之後每次 `git push` git hook 自動呼叫 `pre_push_check.py`，掃 tracked 檔案有沒有上述禁忌字串
- 命中即 fail（exit 1），push 中止
- 千萬不要為了讓 push 過用 `--no-verify` — 中標就乖乖把違規內容搬到 `_*.md`

每次 commit + push 之前 Claude 也應自己跑 `python scripts/pre_push_check.py` 一次當作雙保險。

## Project Overview

Hospital admission list management system for a cardiology department (成大醫院心臟科行政總醫師). Automates the daily workflow: patient list intake → lottery ordering → EMR extraction → admission sequencing → cathlab scheduling.

## Environment

- **Platform**: Windows 11, Python 3.14, `python` (not `python3`). 跨機器 setup / WindowsApps stub 陷阱見 `memory/reference_machine_python_path.md`
- **Terminal encoding**: cp950 — Chinese characters with special Unicode (emojis, ❌✅) will crash `print()`. Write output to UTF-8 files and read with the Read tool instead. All `open(..., 'w')` calls must pass `encoding='utf-8'` explicitly. **Stdout redirect is also cp950 by default** — `python x.py > f.txt 2>&1` will still produce cp950 mojibake. Prefix with `PYTHONIOENCODING=utf-8 python x.py > f.txt 2>&1` (bash) or add `sys.stdout.reconfigure(encoding='utf-8')` at the top of the script. If you see garbled Chinese output like `��@�E`, stop and re-run with UTF-8 — never guess names from mojibake.
- **Google Sheets API**: `gspread` + service account (`sigma-sector-492215-d2-0612bef3b39b.json`)
- **Sheet ID（私有）**: 由 `local_config.py`（gitignored）提供，public-tracked 文件不再硬寫；私有值記在 `memory/_private_setup.md`（gitignored）
- **Sheet ID（public mirror 預設）**: `1u2FZE6-Ldich_b2jI-i0gNnxu1ZsZtZ2Ra6ffCU2Er8` — `gsheet_utils.py` 預設值；public clone 出去的人沒 `local_config.py` 自動用這個
- **Browser automation**: Playwright (`playwright.sync_api`, Chromium, non-headless). EMR scripts use sentinel-stamping to avoid race conditions between frame loads.
- **gspread rate limits**: Google Sheets API has per-minute quotas. All batch writes should include `time.sleep(0.3–1)` between API calls. Use `batch_update` for bulk formatting requests (capped at 500 per batch in `gsheet_utils.py`).
- **Worksheet access**: `sh.worksheet('name')` works for named sheets. Key sheets: 下拉選單, 麻醉, 主治醫師導管時段表, 主治醫師抽籤表, CathDuration, plus date sheets (20260406, 20260407, ...)
- **兩張主治醫師排程表分工**（不要混用）：
  - `主治醫師抽籤表`（col A-E = 週一-五，`*2` 後綴 = 2 支籤）→ **入院抽籤唯一依據**
  - `主治醫師導管時段表`（上午/下午 × H1/H2/C1/C2 × 週一-五）→ **Cathlab key-in 房間/時段依據**

## Architecture

All scripts share `gsheet_utils.py` (singleton gspread client, read/write/format/dropdown helpers). Each workflow step has a corresponding skill in `.claude/skills/`. The typical data flow:

1. **Image → Sheet** (`admission-image-to-excel`): OCR screenshot → write patient data to columns A–L of a date sheet (e.g., `20260408`). If the date sheet already exists, performs **diff-update** (match by 病歷號 → add new / remove cancelled / preserve existing EMR/F/G/ordering).
2. **Lottery** (`admission-lottery`): Random draw → doctor sub-tables (A–H below main data) + round-robin ordering (N–P)
3. **EMR extraction** (`admission-emr-extraction`): Playwright reads Web EMR (`http://hisweb.hosp.ncku/Emrquery/`) → writes C/D cols in sub-tables → auto-prefills F/G
4. **Ordering** (`admission-ordering`): Reads sub-tables F/G after user confirms → writes N–V columns
5. **Cathlab keyin** (`admission-cathlab-keyin`): `python cathlab_keyin.py cathlab_patients_YYYYMMDD.json` (generic driver) — Phase 1 ADDs patients (dedupe by chart), Phase 2 UPTs to fix pdijson/phcjson. ID maps loaded from `cathlab_id_maps.json`. **Old per-date `cathlab_keyin_MMDD.py` pattern is deprecated** as of 2026-04-26.

**EMR data pipeline**: `fetch_emr.py` (Playwright → `emr_data_<date>.json`) → `process_emr.py` (JSON → summary generation + F/G auto-detect → Sheet writes). The JSON intermediary allows re-processing without re-fetching. Auto-detection uses keyword rules (`DIAG_RULES` for F col, `CATH_RULES` for G col in `process_emr.py`).

**Reschedule is a manual flag, not a feature.** V 欄填入 YYYYMMDD 的 row 表示「該病人不做當日的 N+1 cathlab」— 使用者自行決定如何另行處理（手動加排/手動通知）。沒有自動搬 sheet、沒有自動 DEL/ADD WEBCVIS、沒有子表格異動。cathlab keyin 和 verify 兩側都必須把 V 有值的 row 當作 skip。

Scripts write results to `_*.txt` files (e.g., `_ordering_result.txt`) because cp950 terminal can't print Chinese+emoji. Read these with the Read tool.

**Ephemeral vs permanent files** — the repo mixes canonical modules with per-date scratch:

- **Permanent (reference implementations, safe to import/copy)**: `gsheet_utils.py`, `generate_ordering.py`, `verify_cathlab.py`, `fetch_emr.py`, `process_emr.py`, and the active skills under `.claude/skills/`.
- **Ephemeral** (do not commit, do not copy patterns from): `_*.py` / `_*.txt` scratch, `emr_data*.json`, `cathlab_patients_*.json` per-date input, `每日入院名單*.xlsx` local backups, `20260*.jpg` source screenshots, plus old per-date driver scripts (`cathlab_keyin_04XX.py`, `process_emr_04XX.py`, `cathlab_fix_*.py`, `cathlab_redo_04XX.py`, `cathlab_keyin_backfill_*.py`) — these are all **deprecated** as of 2026-04-26 in favor of generic `cathlab_keyin.py` + JSON input. Old date scripts are historical artifacts; never copy them as templates.

## Key Files

- `gsheet_utils.py` — Shared Google Sheets module. Provides `get_worksheet()`, `write_range()`, `batch_write_cells(updates)` (一次 API 推多 cell/range，省 quota + 加速), `format_header_row()`, `write_doctor_table()`, `set_dropdown_from_range()`, etc. All scripts import from here.
- `generate_ordering.py` — Reads doctor sub-tables + round-robin order from a date sheet, generates ordering for N–V columns. Pattern: `extract_doctor_tables()` → `generate_ordering()` → `write_ordering_to_sheet()`. Note: the script's internal `ORDERING_HEADERS` is still the old 6-col N-S layout; the full 9-col N-V write (adding 備註(住服), 病歷號, 改期) is handled by the `admission-ordering` skill.
- `rebuild_date_sheet.py` — Rebuilds a date sheet from scratch (main data + sub-tables + formatting) in ≈6 API calls to respect the 60/min Google Sheets quota. Driven by the `admission-sheet-rebuild` skill.
- `refresh_emr.py` — Orchestrates `fetch_emr` + `process_emr` across multiple dates in one browser session, de-duping patients. Driven by the `admission-emr-refresh` skill.
- `cathlab_keyin.py` — **Generic cathlab keyin driver**（取代每天 per-date `cathlab_keyin_MMDD.py` pattern）。Usage: `python cathlab_keyin.py cathlab_patients_YYYYMMDD.json`。JSON schema 在 driver docstring。ID maps 必從 `cathlab_id_maps.json` 載（見 `feedback_cathlab_id_maps_only.md` — 硬編 ID 會猜錯）。兩階段 ADD→UPT，dedupe by chart no。
- `fetch_emr.py` — Generic Playwright-based EMR fetcher. Takes session URL + chart/doctor pairs, writes results to `emr_data_<date>.json`. Uses sentinel-stamping anti-race-condition strategy (stamps leftFrame/mainFrame before query, polls until sentinel cleared + real content loaded). Handles fallback to whitelist doctors when attending doctor has no clinic visit.
- `process_emr.py` — Generic EMR processor. Reads `emr_data_<date>.json`, generates 4-section summaries, auto-detects F/G values via `DIAG_RULES`/`CATH_RULES` keyword matching, corrects names/age/gender from `#divUserSpec`, writes C/D/F/G to sub-tables + updates main data. Usage: `python process_emr.py 20260419`
- `process_emr_04XX.py` / `write_emr_04XX.py` / `extract_emr_04XX.py` — Per-date EMR scripts (ephemeral). Same copy-latest-as-template pattern as cathlab scripts.
- `每日入院清單工作流程.txt` — Canonical workflow spec with all rules, doctor codes, room codes, column layouts, and dropdown mappings. **Read this first for any workflow question — if it disagrees with `CLAUDE.md`, the txt file wins** (user actively maintains it).
- `memory/MEMORY.md` — Persistent memory index. **Run the `check-previous-progress` skill at session start before any work** to load prior feedback and corrections.
- `_*.py` / `_*.txt` — Underscore-prefixed files are throwaway debugging/verification scratch (one-off checks, patches, logs). Not reference implementations; do not copy their patterns into permanent code.
- `cathlab_page.html` — Saved HTML of WEBCVIS cathlab system for form field analysis.
- `cathlab_id_maps.json` — pdijson/phcjson ID mappings (diagnosis→PDI ID, procedure→PHC ID).
- `schedule_readable.txt` — Human-readable doctor schedule table (Mon–Fri, AM/PM rooms). A named cell = that doctor has a slot that day, even if tagged like "結構", "齡", "寬" — those are secondary-doctor / theme annotations, not "no slot".
- `verify_cathlab.py` — Verify all admission patients appear in the corresponding WEBCVIS cathlab schedule. Reads from **sub-table (統整資料)**, cross-references N-V 的 V 欄（有值 → skip）。Handles Friday same-day cathlab. Usage: `python verify_cathlab.py 20260409`

## Workflow (6 steps)

```
截圖 → OCR匯入Sheet → 抽籤排序 → EMR摘要 → 排住院序 → 導管排程 → /workflow-doc
                    ↘ format-check runs after each write step ↗
```

Full details in `每日入院清單工作流程.txt`. Critical rules:

1. **Ordering columns N–V (9 columns)**: 序號 | 主治醫師 | 病人姓名 | 備註(住服) | 備註 | 病歷號 | 術前診斷 | 預計心導管 | 改期 (user has corrected this multiple times — do not reorder, do not omit 病歷號 or 備註(住服)). N-Q (first 4 cols) 是「住服需要的子集」，下游若有外部推播 consumer 只取這 4 欄。**V 欄=改期**：純人工標記欄位。使用者手動在該 ordering row 填 YYYYMMDD 表示此病人延後處理 → 該 row 不會進入 N+1 cathlab keyin，也會被 `verify_cathlab.py` skip。手動寫 V 時必須用 P 欄姓名或 S 欄病歷號比對 ordering row（不是主資料 row，round-robin 後 row 順序不同）。
2. **Round-robin lottery (兩段獨立 RR)**: 時段組（在當日 cathlab 抽籤池）彼此 RR 排完 → 非時段組（不在池）再彼此 RR 接後面。**絕對不要時段+非時段混在一起 RR**（per `feedback_lottery_roundrobin.md` — 使用者多次糾正的關鍵規則）。組內：A1→B1→C1→A2→C2... 真 RR，醫師用完就 skip。組內醫師順序 = 真隨機抽籤 (`random.shuffle()`)，**不可**借用 sub-table 的醫師出現順序（兩者是獨立事件）。
3. **Friday admission → Friday schedule**: 週五入院查週五抽籤表（週六無抽籤表）。日→一、一→二、二→三、三→四、四→五、**五→五**
4. **Non-schedule doctors**: Never include in main round-robin.
5. **Cathlab direction**: Patients admitted on day N → cathlab scheduled on day N+1. **Exception**: Friday admissions → Friday cathlab (same day, since Saturday has no schedule).
6. **Cathlab safety**: Only add new entries, never modify or delete existing ones
7. **Cathlab times**: scheduled AM=0600+, scheduled PM=1800+, non-schedule=H1 2100+ (note="本日無時段")
8. **No-data patients**: Still key into cathlab schedule at doctor's time slot, note="無資料病人"
9. **Skip rule**: 備註含「不排程」或「檢查」→ skip cathlab keyin（「非導管床」「HF AE」不一定跳過，只有「檢查」才確定跳過）
10. **Sheet no-overwrite**: 寫入 Sheet 前必須先讀取目標區域，確認為空才寫入，絕不覆蓋現有資料
11. **EMR auto-write**: EMR 摘要完成後自動寫入 Sheet，不需再問使用者確認
12. **EMR manual login**: 不要自己開瀏覽器登入 EMR，等使用者手動登入後貼 session URL，再用 Playwright 帶 session 查詢
13. **Ordering timing**: Claude 必須等使用者手動確認 F/G 欄後才能寫入 N-U 欄
14. **EMR prefill F/G**: EMR 摘要完成後自動預填術前診斷(F)和預計心導管(G)，列出讓使用者檢查
15. **Second doctor priority**: 時段表寫「黃鼎鈞(浩、晨)」這類兩位 second → 第一位 (葉立浩=浩) → `attendingdoctor2`、第二位 (洪晨惠=晨) → **`recommendationDoctor` (推薦醫師欄位)**。`cathlab_keyin.py` 已支援 `third` JSON 欄位；舊「放 note」做法已廢。詳見 `memory/feedback_cathlab_third_doctor.md`。**黃鼎鈞 Mon cathlab 強制 second=洪晨惠**（即使時段表 Mon 沒寫他）。
16. **詹世鴻 Friday exception**: 週五入院時 詹世鴻 視為**非時段醫師**——lottery/入院序不進主 round-robin（排在無時段醫師後），cathlab 也排非時段（H1 2100+, note="本日無時段"）。兩邊一致。
17. **Post-edit format check**: 任何寫入/修改日期 sheet 病人清單之後，**一定要** 讀回驗證格式（主資料 A-L、N-V ordering、子表格 title/人數/空白隔行、無殘留合併、病歷號一致）。跑掉就當場修，不留尾巴給使用者（見 `memory/feedback_post_edit_format_check.md`）。**最簡解**：`from gsheet_utils import enforce_sheet_format; enforce_sheet_format('YYYYMMDD')` — idempotent，自動刷 BLUE/WHITE bg + LEFT 對齊 + 粗體 + WRAP。任何 diff/insert/delete/write_range 動到 sheet 之後**強制**收尾呼叫一次。
18. **N-V 寫入前必當下重讀子表格 F/G/H** (HARD): session 早期讀的 cached 值不算；使用者會在抽籤/EMR/format check 之後到你寫 N-V 之前手動修 F/G/H。漏這步 → 入院序的術前診斷/預計心導管/備註全寫錯。詳見 `memory/feedback_subtable_H_to_R_ordering.md`（5/2 踩過：8/11 病人 F/G/H 寫錯）。
19. **Cathlab ADD 前必掃整週 (Mon-Fri)** (HARD): 對 JSON 中每位病人，先用 playwright query 五天 chart no map。若 chart 已在當週**任何一天**（不只 N+1）→ STOP，列出「該病人已排在 MM/DD ROOM TIME」，從 JSON 移除該筆，**絕不自動 ADD** 到 N+1 那天。詳見 `memory/feedback_cathlab_week_check_before_keyin.md`（5/2 踩過：康李金春 5/6 CRT 已排，被誤 ADD 5/5 廖瑀 H1 2100）。
20. **陳則瑋 + 劉秉彥門診 → cathlab second=劉秉彥**: 陳則瑋住院病人若 EMR 子表格 C 欄寫「(門診)... 劉秉彥 ...」→ JSON `second=劉秉彥`。限劉秉彥（不是通則）。見 `memory/feedback_chen_zewei_liu_bingyan_second.md`。

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

Columns N–V (row 1 = header, row 2+ = ordered list):
  N=序號 | O=主治醫師 | P=病人姓名 | Q=備註(住服) | R=備註
  S=病歷號 | T=術前診斷 | U=預計心導管 | V=改期

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

## External tools

- **Claude-Gemini-Dialogue** (`~/repos/Claude-Gemini-Dialogue/scripts/delegate.sh`): Token-saving delegation wrapper — push grunt work (long-text search, translation, CSV→md, structural transforms) to Gemini CLI. See `memory/reference_claude_gemini_dialogue.md` for invocation patterns. Don't use for admission-list business logic (Gemini lacks our context).

