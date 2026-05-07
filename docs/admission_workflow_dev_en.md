# Admission Workflow Developer Reference

This document provides a concise developer-oriented reference for the cardiology admission list workflow, focusing on system concepts, inputs/outputs, and operational logic. The original Chinese operation manual (`in/admission_workflow.txt`) remains the canonical source for user-facing instructions.

## 1. Project Overview

The project automates the daily processing of cardiology admission lists. Its primary purpose is to streamline patient data handling from image recognition to cathlab scheduling. It operates within a Google Sheet ecosystem, interfacing with external systems such as Google Sheets (for data storage and collaboration), Web EMR (for patient record extraction), and WEBCVIS (for cathlab scheduling). Deployment context involves a local setup where Claude interacts with Chrome for EMR and WEBCVIS.

## 2. The 6-Step Pipeline

The workflow is structured around six main stages, often initiated by specific trigger phrases.

### Step 1: Import Patient Data (Image → Sheet)
*   **Skill Name:** `admission-image-to-excel`
*   **Trigger Phrases:** `這是 20260407-09 的三天預約入院清單，請幫我整理` (This is the 3-day admission list for 20260407-09, please help me organize it.)
*   **Input:** Screenshot(s) of daily admission lists provided to Claude.
*   **Output:** New or updated date-specific Google Sheet worksheet (A-L columns populated).
*   **Permanent Scripts:** None explicitly mentioned as permanent. The process involves OCR and Google Sheet interaction, likely via `gsheet_utils.py`.
*   **Key Constraints:**
    *   Identifies 12 columns (A-L).
    *   Automatically corrects OCR errors against a master doctor list.
    *   Formats the sheet with specific colors, borders, and alignment.
    *   Handles "diff update" mode for existing date sheets: identifies added, canceled, and retained patients by chart number, updating accordingly. Patient Chart N is crucial for diffing.
    *   Patient Chart number is always 8 digits, stored as text (preserving leading zeros).
    *   Truncated patient names are not corrected here; EMR extraction in Step 3 handles this.

### Step 2: Attending Doctor Lottery & Ordering (Sheet → Lottery)
*   **Skill Name:** `admission-lottery`
*   **Trigger Phrases:** `抽籤` (Lottery), `排入院順序` (Order admission), `抽籤，陳則瑋排第一` (Lottery, Chen Tse-Wei first), `無條件讓 XXXXXXXX 第一個入院，備註員工家屬` (Unconditionally assign Patient X first for admission, note family member).
*   **Input:** Data from the date-specific Google Sheet (A-L columns).
*   **Output:**
    *   N-P columns (Admission Order, Attending Doctor, Patient Name) in the main sheet.
    *   Doctor-specific sub-tables (8 columns A-H) below the main data.
*   **Permanent Scripts:** Implied logic within the `admission-lottery` skill, likely interacting with `gsheet_utils.py` and a doctor lottery configuration.
*   **Key Constraints:**
    *   Determines admission day's corresponding clinic doctors (e.g., Sunday admit → Monday clinic doctor).
    *   Distinguishes "in-lottery" doctors (from `主治醫師抽籤表`) and "out-of-lottery" doctors.
    *   Performs random lottery with *2 chances for specific doctors.
    *   Strict two-stage Round-Robin (RR) for ordering: "In-lottery" doctors' patients are ordered first, then "Out-of-lottery" doctors' patients follow. These two groups are never mixed during RR.
    *   Internal patient order for multi-patient doctors is also randomized unless manually specified (E column in sub-table).
    *   Doctors not in the lottery table still have their patients listed but are sequenced after all "in-lottery" patients.
    *   Sub-tables are formatted with specific colors, borders, and dropdowns for F/G columns.

### Step 3: Automatic EMR Summary Extraction (Lottery → EMR)
*   **Skill Name:** `admission-emr-extraction` (single-day), `admission-emr-refresh` (multi-day batch)
*   **Trigger Phrases:** Automatically initiated after lottery completion; can be triggered manually with `提取 EMR` (Extract EMR).
*   **Input:** Patient chart numbers from the Google Sheet, existing Web EMR session (requires manual login by user).
*   **Output:**
    *   Updated F (Name), G (Gender), H (Age) columns in the main sheet.
    *   C (Full SOAP), D (Four-segment Summary) columns in doctor-specific sub-tables.
*   **Permanent Scripts:** `fetch_emr.py`, `process_emr.py`. Uses local HTTP server (port 18234) or Playwright.
*   **Key Constraints:**
    *   Batches queries (approx. 2-3 sec/patient).
    *   Corrects patient names, age, and gender from EMR's `#divUserSpec` based on chart number.
    *   Generates a four-segment summary (Cardiology Diagnosis, Medical History, Objective Exam, Hospitalization Plan).
    *   SOAP notes are truncated at `[Medicine]` or similar markers.
    *   Handles "no record" cases (`無本院一年內主治醫師門診紀錄`).
    *   Fallback doctors for EMR extraction are limited to a specific whitelist if the attending doctor has no EMR record. Non-cardiology department records are ignored.
    *   Avoids printing `\xa0` characters to the terminal.

### Step 4: Set Admission Order & Dropdowns (EMR → Ordering)
*   **Skill Name:** `admission-ordering`
*   **Trigger Phrases:** `下拉選單填好了，幫我整合入院序` (Dropdowns are filled, please integrate admission order), `自動生成入院序` (Automatically generate admission order).
*   **Input:** Filled F (Pre-op Diagnosis) and G (Expected Cathlab) dropdowns in the doctor-specific sub-tables.
*   **Output:** N-V columns (9 columns) in the main sheet are populated.
*   **Permanent Scripts:** Logic within `admission-ordering` skill.
*   **Key Constraints:**
    *   Crucially, Claude *must not* write to N-V columns until the user confirms dropdowns are filled.
    *   Re-confirms doctor status (in/out of lottery) before finalizing.
    *   If a doctor has multiple patients, checks E column for manual ordering.
    *   Populates N-V columns: N=Order, O=Attending Doctor, P=Patient Name, Q=Remark (Admission Svc), R=Remark, S=Chart No., T=Pre-op Diagnosis, U=Expected Cathlab, V=Reschedule.
    *   `備註(住服)` (Q) is left blank. `備註` (R) pulls from sub-table H column.
    *   `病歷號` (S) is text format.
    *   `術前診斷` (T) uses sub-item names only (e.g., pAf).
    *   `改期` (V) contains YYYYMMDD for manual reschedule notes; patients with a V value are skipped for N+1 cathlab key-in.

### Step 5: Cathlab Scheduling Key-in (Ordering → Cathlab)
*   **Skill Name:** `admission-cathlab-keyin`
*   **Trigger Phrases:** `導管排程` (Cathlab Scheduling), `key-in 導管` (Key-in Cathlab).
*   **Input:** Doctor-specific sub-tables (A-H columns) from the sheet.
*   **Output:** Entries made in the WEBCVIS system.
*   **Permanent Scripts:** `cathlab_keyin.py`.
*   **Key Constraints:**
    *   **Source of Patient List:** Sub-tables (doctor-specific patient list), NOT N-V ordering list.
    *   **Pre-ADD Scan:** Before adding any patient, a scan of WEBCVIS for the entire week (Mon-Fri) is performed to prevent duplicate scheduling. If Patient X is already scheduled, the item is removed from the JSON and reported to the user.
    *   Excludes patients with "不排程" (Do not schedule) or "檢查" (Check) in remarks, or if V column (reschedule) has a value.
    *   Generates a `cathlab_patients_YYYYMMDD.json` file.
    *   Driver `python cathlab_keyin.py <json>` handles login, date setting (N+1 day, or same day for Friday admits, or Wed PM for Zhang Xian-Yuan Wed admits), and two-phase key-in (ADD/UPT).
    *   Uses `cathlab_id_maps.json` for PDI/PHC IDs.
    *   Fills Room, Time, Attending Doctor (main, second, third) based on `主治醫師時段表`.
    *   Specific rules for second and third attending doctors (e.g., `黃鼎鈞 Mon cathlab → second 強制 = 洪晨惠`).
    *   `陳則瑋住院 + 劉秉彥門診` rule: if EMR sub-table C column indicates `劉秉彥` as clinic doctor, `second` defaults to `劉秉彥`.
    *   Pre-op Diagnosis and Expected Cathlab from Sheet F/G are used. If not in WEBCVIS dropdown, they go into the note field (except for TAVI, which is directly entered into "開刀房").
    *   **Safety Rule:** Never modify existing schedules, only add new ones. Existing patients are skipped for ADD.
    *   **Safety Rule:** Li Po-Tseng (`李柏增`) is excluded from main/second attending doctor fields before 2026/08.
    *   **Zhang Xian-Yuan (`張獻元`) Tuesday Admission Rules:**
        *   If H (note) contains `王思翰` or `張倉惟`: Schedule for Wednesday (N+1) using Zhang's Wednesday slot (W3 AM C2), with Wang/Zhang as second doctor.
        *   If H does not contain Wang/Zhang: First 3 patients schedule for same-day Tuesday PM Zhang slot (W2 PM H2). From 4th patient onwards, schedule for N+1 Wednesday AM Zhang slot (W3 AM C2).
    *   **Zhang Xian-Yuan (`張獻元`) Wednesday Admission Rules:** Cathlab is on the same day (W3 AM C2 or PM C2). Lottery/ordering consider him "out-of-lottery" for N+1 day (Thursday has no slot), but cathlab is still on Wednesday.
    *   **Pre-op Diagnosis "Others:XXX" Rule:** Custom diagnoses are handled by falling back to a generic "Others" PDI ID, with the full string in the name field.
    *   **Zhan Shi-Hong (`詹世鴻`) Friday Admission Rules:** Treated as "out-of-lottery" for ordering, and scheduled for non-scheduled time (H1 2100+, note `本日無時段`) on the same Friday.
    *   **Time Slot Parentheses:** Parentheses in a doctor's slot (e.g., `劉嚴文(寬)`) indicate the second attending doctor. A standalone parenthesis entry (e.g., `(陳則瑋)`) indicates a co-attending doctor for that slot, and should use scheduled times (AM 0600+/PM 1800+), not "no slot" times.

### Step 6: Clear Temporary Files (Cleanup)
*   **Skill Name:** `workflow-docs` stage 4.5
*   **Trigger Phrases:** `/workflow-docs`, `清理檔案` (Clear files).
*   **Input:** None.
*   **Output:** Deletion report.
*   **Permanent Scripts:** Logic within `workflow-docs` skill.
*   **Key Constraints:**
    *   Deletes temporary files matching patterns like `_*.py`, `_*.txt`, `_*.json`, `_*.png`, `_*.log`, `emr_data_*.json`, `cathlab_patients_*.json`, and old `cathlab_keyin_*.py` scripts.
    *   Does *not* delete permanent modules, config files (`cathlab_id_maps.json`), documentation, or `memory/` directory.

## 3. Sheet Schema Reference

### Main A-L 12 Columns (Header Row)
*   **A:** (Not explicitly named, assumed to be Date or similar initial identifier)
*   **B-L:** (Patient data fields, 12 total, specific names not provided but context implies fields like Patient Name, Chart Number, Admission Date, etc.)
    *   Specific widths are `100/100/90/80/70/189/160/40/90/50/120/40`.
    *   Column G (width 160) is for `預計心導管` (Expected Cathlab) content within the sub-table.

### N-V 9 Columns Ordering
*   **N:** 序號 (Order Number)
*   **O:** 主治醫師 (Attending Doctor)
*   **P:** 病人姓名 (Patient Name)
*   **Q:** 備註(住服) (Remark - Admission Service)
*   **R:** 備註 (Remark)
*   **S:** 病歷號 (Chart Number) - Text format, preserves leading zeros.
*   **T:** 術前診斷 (Pre-op Diagnosis)
*   **U:** 預計心導管 (Expected Cathlab)
*   **V:** 改期 (Reschedule) - YYYYMMDD for manual reschedule notes.

### Sub-table 8 Columns A-H per Doctor Block
*   Displayed below the main A-L data, for each doctor.
*   **A:** 姓名 (Name)
*   **B:** 病歷號 (Chart Number)
*   **C:** EMR (Full SOAP note, truncated at Medicine)
*   **D:** EMR摘要 (EMR Summary - placeholder, on-demand, four-segment)
*   **E:** 手動設定入院序 (Manual Admission Order)
*   **F:** 術前診斷 (Pre-op Diagnosis) - Dropdown.
*   **G:** 預計心導管 (Expected Cathlab) - Dropdown.
*   **H:** 註記 (Note)

## 4. Doctor Reference Data

### `主治醫師抽籤表` (Lottery Table)
*   Located in the 3rd sheet of the Google Sheet.
*   Columns A-E map to Monday-Friday.
*   Row 1 is the header.
*   Doctors marked with `*2` get two lottery chances.
*   Used to determine the order of doctors for patient admission sequencing (Step 2).

### `主治醫師導管時段表` (Cathlab Time Slot Table)
*   Detailed table of clinic time slots, including examination room mappings.
*   Columns C-G map to Monday-Friday.
*   Details AM (H1,H2,C1,C2) and PM (H1,H2,C1,C2) slots.
*   Parenthetical abbreviations (寬/浩/晨/齡/嘉) indicate second attending doctors.
*   Used to assign rooms, times, and attending/second/third doctors for cathlab scheduling (Step 5).

### Difference between the two
*   The `主治醫師抽籤表` (`lottery`) dictates the logical ordering of patients for admission based on doctor availability for *clinic hours relevant to admission sequencing*.
*   The `主治醫師導管時段表` (`cathlab`) dictates the physical scheduling of cathlab procedures based on *cathlab room and personnel availability*.
*   A doctor might have a cathlab slot but not be part of the `lottery` for patient admission ordering on a given day (e.g., `詹世鴻` on Friday). These are independent determinations, and sometimes lead to a doctor being "out-of-lottery" but still having a cathlab time.

## 5. Cathlab Time Conventions

*   **Scheduled AM:** 0600 onwards, incrementing by 1 minute per patient (e.g., 0600, 0601, 0602...).
*   **Scheduled PM:** 1800 onwards, incrementing by 1 minute per patient (e.g., 1800, 1801, 1802...).
*   **Non-scheduled (No Time Slot):** For doctors without a regular slot, H1 room at 2100 onwards, incrementing by 1 minute per patient. The note field in WEBCVIS is filled with `本日無時段` (No slot today).
*   **`詹世鴻` (Zhan Shi-Hong) Friday:** Despite having a Friday AM C2 slot, patients admitted on Friday for `詹世鴻` are scheduled at non-scheduled times (H1 2100+) on the same day, with the `本日無時段` note.

## 6. Reschedule (Full Move) Flow

*   **Manual Reschedule (V Column):** Filling YYYYMMDD in the V column of the N-V ordering table is a manual note. This entry causes `cathlab keyin` and `verify_cathlab.py` to skip the patient for N+1 cathlab scheduling, implying separate manual handling. Matching is done via P (Patient Name) and S (Chart Number) to correctly identify the row.
*   **Full Move Reschedule:** Triggered by phrases like `重啟改期功能` (Restart reschedule function) or `改 MM/DD 住院` (Reschedule admission to MM/DD) with a patient list. Claude runs the `admission-reschedule` skill. This involves:
    1.  Marking the V column.
    2.  Moving main data and sub-table entries to the target date.
    3.  Deleting the original cathlab entry (after user confirmation of the list).
    4.  Adding a new cathlab entry via `cathlab_keyin.py` automatically.

## 7. PHI Safety Boundaries

The source document emphasizes the need to correctly handle patient data, including chart numbers, names, age, and gender, ensuring accuracy and redaction during display or logging where necessary (e.g., avoiding `\xa0` in terminal output). It specifies `local_config.py` (which contains `SHEET_ID`) is gitignored. Temporary files like `_*.json` are explicitly deleted at the end of the workflow. Generally, patient-specific data should be processed carefully, and ephemeral files used during processing are cleared. *The source document does not provide details about specific `_*.md` files being gitignored for PHI or patterns blocked by a `pre_push_check.py` script.*

## 8. Operational Rules Summary

The provided `admission_workflow.txt` does not contain a numbered list of 1-22 rules as suggested in the prompt's `CLAUDE.md` reference. However, several operational principles and rules are embedded throughout the document:

*   **Google Sheet Canonical:** Google Sheet is the primary data source, not local Excel.
*   **Service Account:** Automated read/write to Google Sheets via Service Account API.
*   **OCR Verification:** User *must* manually verify OCR-read chart numbers.
*   **Name Correction:** EMR auto-corrects patient names.
*   **Diff Update Mode:** For existing date sheets, only differences (add/cancel/retain) are applied, not full overwrites.
*   **No Mixed Round-Robin:** In-lottery and out-of-lottery doctors' patients must be ordered in separate Round-Robin stages.
*   **Real Random Shuffle:** Lottery must use `random.shuffle()` for doctors and internal patient ordering.
*   **EMR Batch Query:** EMR queries are batched.
*   **EMR Name/Age/Gender Correction:** EMR data updates sheet automatically without user confirmation.
*   **EMR Truncation:** SOAP notes are truncated at `[Medicine]` and similar markers.
*   **EMR Fallback Whitelist:** Limited whitelist of doctors for EMR fallback if attending doctor has no record.
*   **Dropdown Confirmation:** Claude must wait for user confirmation after filling dropdowns before populating N-V columns.
*   **No Modification of Existing Cathlab:** The system only adds new cathlab entries, never modifies or deletes existing ones (except during a full reschedule flow).
*   **Duplicate Cathlab Prevention:** Existing patients in WEBCVIS are not re-added.
*   **Li Po-Tseng Exclusion:** `李柏增` (`053146`) cannot be assigned as main or second surgeon before 2026/08.
*   **Temporary File Cleanup:** Workflow concludes with deletion of temporary processing files.
