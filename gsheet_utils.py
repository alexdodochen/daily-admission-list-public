"""
Google Sheet 工具模組 — 取代 openpyxl 的所有操作
所有 admission skill 共用此模組
"""
import time
import gspread
from google.oauth2.service_account import Credentials

# --- Constants ---
# SHEET_ID 預設指向 public demo sheet（給 daily-admission-list-public clone 出去用）。
# 私有環境：在 repo 根目錄放 local_config.py（已 gitignore）覆寫成私有 sheet。
try:
    from local_config import SHEET_ID
except ImportError:
    SHEET_ID = '1u2FZE6-Ldich_b2jI-i0gNnxu1ZsZtZ2Ra6ffCU2Er8'
CREDS_FILE = 'sigma-sector-492215-d2-0612bef3b39b.json'
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# --- Color constants (Google Sheets RGB format) ---
BLUE_HEADER = {"red": 0.741, "green": 0.843, "blue": 0.933}    # FFBDD7EE
ORANGE_DATA = {"red": 0.988, "green": 0.894, "blue": 0.839}    # FFFCE4D6
WHITE = {"red": 1, "green": 1, "blue": 1}
GREEN_SECTION = {"red": 0.886, "green": 0.937, "blue": 0.855}  # E2EFDA
BLACK = {"red": 0, "green": 0, "blue": 0}

# --- Connection ---
_gc = None
_sh = None

def get_client():
    """Get authenticated gspread client (singleton)"""
    global _gc
    if _gc is None:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        _gc = gspread.authorize(creds)
    return _gc

def get_spreadsheet():
    """Get the main spreadsheet (singleton)"""
    global _sh
    if _sh is None:
        gc = get_client()
        _sh = gc.open_by_key(SHEET_ID)
    return _sh

def get_worksheet(name):
    """Get worksheet by name, returns None if not found"""
    sh = get_spreadsheet()
    try:
        return sh.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        return None

def create_worksheet(name, rows=100, cols=20):
    """Create a new worksheet, delete if exists first"""
    sh = get_spreadsheet()
    existing = get_worksheet(name)
    if existing:
        sh.del_worksheet(existing)
        time.sleep(1)
    ws = sh.add_worksheet(title=name, rows=rows, cols=cols)
    time.sleep(1)
    return ws

def list_sheets():
    """List all worksheet names"""
    sh = get_spreadsheet()
    return [ws.title for ws in sh.worksheets()]

# --- Read operations ---

def read_all_values(ws):
    """Read all values from worksheet as 2D list"""
    return ws.get_all_values()

def read_cell(ws, row, col):
    """Read single cell value (1-indexed)"""
    return ws.cell(row, col).value

def read_range(ws, range_str):
    """Read a range like 'A1:C10'"""
    return ws.get(range_str)

def get_max_row(ws):
    """Get last row with data"""
    vals = ws.get_all_values()
    for i in range(len(vals) - 1, -1, -1):
        if any(v.strip() for v in vals[i]):
            return i + 1
    return 0

# --- Write operations ---

def write_cell(ws, row, col, value):
    """Write single cell (1-indexed)"""
    ws.update_cell(row, col, value)

def write_range(ws, range_str, data, raw=True):
    """Write 2D data to range. data = [[row1], [row2], ...]"""
    ws.update(values=data, range_name=range_str,
              value_input_option='RAW' if raw else 'USER_ENTERED')

def batch_write_cells(ws, updates, raw=True):
    """One API call for many cell/range writes.

    updates = [(range_str, value_or_2d_list), ...]
      e.g. [('H2', '55'), ('J2', '09B37C'), ('N2:V8', [[...], [...]])]
    Single string/number values are wrapped to [[v]] automatically.
    Pairs that share no dependency on prior writes can all go in one call.
    """
    body = []
    for rng, val in updates:
        if not isinstance(val, list):
            val = [[val]]
        elif val and not isinstance(val[0], list):
            val = [val]
        body.append({'range': rng, 'values': val})
    ws.batch_update(body, value_input_option='RAW' if raw else 'USER_ENTERED')

def write_row(ws, row, values, start_col=1, raw=True):
    """Write a row of values starting from start_col"""
    col_letter = gspread.utils.rowcol_to_a1(row, start_col).split('$')[-1][0] if start_col > 26 else chr(64 + start_col)
    end_letter = chr(64 + start_col + len(values) - 1) if start_col + len(values) - 1 <= 26 else gspread.utils.rowcol_to_a1(row, start_col + len(values) - 1)
    range_str = f"{gspread.utils.rowcol_to_a1(row, start_col)}:{gspread.utils.rowcol_to_a1(row, start_col + len(values) - 1)}"
    ws.update(values=[values], range_name=range_str,
              value_input_option='RAW' if raw else 'USER_ENTERED')

def clear_range(ws, range_str):
    """Clear a range of cells"""
    ws.batch_clear([range_str])

def clear_area(ws, start_row, start_col, end_row, end_col):
    """Clear a rectangular area"""
    range_str = f"{gspread.utils.rowcol_to_a1(start_row, start_col)}:{gspread.utils.rowcol_to_a1(end_row, end_col)}"
    ws.batch_clear([range_str])

# --- Formatting ---

def format_header_row(ws, row, num_cols, start_col=1):
    """Apply blue header formatting to a row.
    LEFT align per feedback_sheet_formatting.md: 全部儲存格一律靠左對齊，包含 header 列、合併標題列。"""
    sh = get_spreadsheet()
    requests = [{
        "repeatCell": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": row - 1,
                "endRowIndex": row,
                "startColumnIndex": start_col - 1,
                "endColumnIndex": start_col + num_cols - 1
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": BLUE_HEADER,
                    "textFormat": {"bold": True, "fontSize": 11},
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    }]
    sh.batch_update({"requests": requests})

def format_data_rows(ws, start_row, end_row, num_cols, start_col=1, bg_color=None):
    """Apply data formatting to rows"""
    sh = get_spreadsheet()
    cell_format = {
        "textFormat": {"fontSize": 11},
        "verticalAlignment": "MIDDLE"
    }
    fields = "userEnteredFormat(textFormat,verticalAlignment"
    if bg_color:
        cell_format["backgroundColor"] = bg_color
        fields += ",backgroundColor"
    fields += ")"

    requests = [{
        "repeatCell": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": start_row - 1,
                "endRowIndex": end_row,
                "startColumnIndex": start_col - 1,
                "endColumnIndex": start_col + num_cols - 1
            },
            "cell": {"userEnteredFormat": cell_format},
            "fields": fields
        }
    }]
    sh.batch_update({"requests": requests})

def set_column_widths(ws, widths_dict):
    """Set column widths. widths_dict = {col_index: pixel_width} (1-indexed)"""
    sh = get_spreadsheet()
    requests = []
    for col, width in widths_dict.items():
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": ws.id,
                    "dimension": "COLUMNS",
                    "startIndex": col - 1,
                    "endIndex": col
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })
    if requests:
        sh.batch_update({"requests": requests})

def merge_cells(ws, start_row, start_col, end_row, end_col):
    """Merge a range of cells"""
    sh = get_spreadsheet()
    requests = [{
        "mergeCells": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": start_row - 1,
                "endRowIndex": end_row,
                "startColumnIndex": start_col - 1,
                "endColumnIndex": end_col
            },
            "mergeType": "MERGE_ALL"
        }
    }]
    sh.batch_update({"requests": requests})

def add_borders(ws, start_row, start_col, end_row, end_col):
    """Add thin borders to a range"""
    sh = get_spreadsheet()
    border_style = {"style": "SOLID", "color": BLACK}
    requests = [{
        "updateBorders": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": start_row - 1,
                "endRowIndex": end_row,
                "startColumnIndex": start_col - 1,
                "endColumnIndex": end_col
            },
            "top": border_style,
            "bottom": border_style,
            "left": border_style,
            "right": border_style,
            "innerHorizontal": border_style,
            "innerVertical": border_style
        }
    }]
    sh.batch_update({"requests": requests})

def set_wrap_text(ws, start_row, start_col, end_row, end_col):
    """Enable text wrapping for a range"""
    sh = get_spreadsheet()
    requests = [{
        "repeatCell": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": start_row - 1,
                "endRowIndex": end_row,
                "startColumnIndex": start_col - 1,
                "endColumnIndex": end_col
            },
            "cell": {
                "userEnteredFormat": {"wrapStrategy": "WRAP"}
            },
            "fields": "userEnteredFormat.wrapStrategy"
        }
    }]
    sh.batch_update({"requests": requests})

def add_note(ws, row, col, note_text):
    """Add a note (comment) to a cell"""
    sh = get_spreadsheet()
    requests = [{
        "updateCells": {
            "rows": [{"values": [{"note": note_text[:5000]}]}],
            "range": {
                "sheetId": ws.id,
                "startRowIndex": row - 1,
                "endRowIndex": row,
                "startColumnIndex": col - 1,
                "endColumnIndex": col
            },
            "fields": "note"
        }
    }]
    sh.batch_update({"requests": requests})

# --- Data Validation (Dropdowns) ---

def set_dropdown(ws, start_row, start_col, end_row, end_col, values):
    """Set dropdown data validation for a range"""
    sh = get_spreadsheet()
    condition_values = [{"userEnteredValue": v} for v in values]
    requests = [{
        "setDataValidation": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": start_row - 1,
                "endRowIndex": end_row,
                "startColumnIndex": start_col - 1,
                "endColumnIndex": end_col
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": condition_values
                },
                "showCustomUi": True,
                "strict": False
            }
        }
    }]
    sh.batch_update({"requests": requests})

def set_dropdown_from_range(ws, start_row, start_col, end_row, end_col, source_sheet_id, source_range):
    """Set dropdown from another sheet range"""
    sh = get_spreadsheet()
    requests = [{
        "setDataValidation": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": start_row - 1,
                "endRowIndex": end_row,
                "startColumnIndex": start_col - 1,
                "endColumnIndex": end_col
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_RANGE",
                    "values": [{"userEnteredValue": source_range}]
                },
                "showCustomUi": True,
                "strict": False
            }
        }
    }]
    sh.batch_update({"requests": requests})

# --- Column Grouping ---

def group_columns(ws, start_col, end_col):
    """Group columns (collapsible). 1-indexed."""
    sh = get_spreadsheet()
    requests = [{
        "addDimensionGroup": {
            "range": {
                "sheetId": ws.id,
                "dimension": "COLUMNS",
                "startIndex": start_col - 1,
                "endIndex": end_col
            }
        }
    }]
    sh.batch_update({"requests": requests})

# --- Batch operations (for efficiency) ---

def batch_update_requests(requests):
    """Execute raw batch update requests"""
    sh = get_spreadsheet()
    if requests:
        batch_size = 500
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i+batch_size]
            sh.batch_update({"requests": batch})
            if i + batch_size < len(requests):
                time.sleep(1)

# --- Helper: build full doctor table section ---

def write_doctor_table(ws, start_row, doctor_name, patients, num_cols=8):
    """
    Write a doctor patient table block (8 cols A-H).
    patients = [{'name', 'chart_no', 'emr', 'emr_summary', 'order', 'diagnosis', 'cathlab', 'note'}]
    Returns next available row (≥ 2 blank rows after block).

    D=EMR摘要 column is kept as a placeholder; process_emr.py does NOT auto-fill it.
    User triggers Gemini summary on demand to fill D when needed.
    """
    sh = get_spreadsheet()
    sub_headers = ['姓名', '病歷號', 'EMR', 'EMR摘要', '手動設定入院序',
                   '術前診斷', '預計心導管', '註記'][:num_cols]

    # Doctor title (merged)
    title = f'{doctor_name}（{len(patients)}人）'
    write_cell(ws, start_row, 1, title)
    merge_cells(ws, start_row, 1, start_row, num_cols)
    format_header_row(ws, start_row, num_cols)

    # Sub-headers
    write_row(ws, start_row + 1, sub_headers)
    format_header_row(ws, start_row + 1, num_cols)

    # Patient data
    for pi, pt in enumerate(patients):
        row = start_row + 2 + pi
        vals = [
            pt.get('name', ''),
            pt.get('chart_no', ''),
            pt.get('emr', ''),
            pt.get('emr_summary', ''),
            pt.get('order', ''),
            pt.get('diagnosis', ''),
            pt.get('cathlab', ''),
            pt.get('note', '')
        ][:num_cols]
        write_row(ws, row, vals, raw=False)

    end_row = start_row + 1 + len(patients)

    # Explicit WHITE background + normal text on patient rows
    # (critical — duplicated sheets may retain blue/formatted residue;
    #  user has flagged 白底跑掉 multiple times. See
    #  memory/feedback_post_edit_format_check.md)
    if len(patients) > 0:
        sh.batch_update({"requests": [{
            "repeatCell": {
                "range": {"sheetId": ws.id,
                          "startRowIndex": start_row + 1,  # first patient row (0-indexed)
                          "endRowIndex": end_row,
                          "startColumnIndex": 0,
                          "endColumnIndex": num_cols},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": WHITE,
                    "textFormat": {"bold": False, "fontSize": 11},
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "WRAP",
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
            }
        }]})
        time.sleep(0.3)

    # Borders for entire block (title + subheader + patients)
    add_borders(ws, start_row, 1, end_row, num_cols)

    # Clean blank-gap rows: WHITE bg, no border, not bold
    # (must explicitly reset — otherwise duplicated formatting bleeds through)
    gap_start = end_row  # 0-indexed = end_row+1..end_row+2 (2 blank rows)
    sh.batch_update({"requests": [
        {"repeatCell": {
            "range": {"sheetId": ws.id,
                      "startRowIndex": gap_start,
                      "endRowIndex": gap_start + 2,
                      "startColumnIndex": 0,
                      "endColumnIndex": num_cols},
            "cell": {"userEnteredFormat": {
                "backgroundColor": WHITE,
                "textFormat": {"bold": False, "fontSize": 11},
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }},
        {"updateBorders": {
            "range": {"sheetId": ws.id,
                      "startRowIndex": gap_start,
                      "endRowIndex": gap_start + 2,
                      "startColumnIndex": 0,
                      "endColumnIndex": num_cols},
            "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
            "left": {"style": "NONE"}, "right": {"style": "NONE"},
            "innerHorizontal": {"style": "NONE"}, "innerVertical": {"style": "NONE"},
        }},
    ]})
    time.sleep(0.3)

    # Set dropdowns for F (col 6, 術前診斷) and G (col 7, 預計心導管) patient rows
    if num_cols >= 7 and len(patients) > 0:
        data_start = start_row + 2
        data_end = start_row + 1 + len(patients)
        set_dropdown_from_range(ws, data_start, 6, data_end, 6,
                                None, "='下拉選單'!$A$2:$A$66")
        set_dropdown_from_range(ws, data_start, 7, data_end, 7,
                                None, "='下拉選單'!$D$2:$D$23")
        time.sleep(0.3)

    time.sleep(0.5)
    return end_row + 3  # next available row (2 blank rows gap)


def enforce_sheet_format(sheet_name):
    """Re-apply standard format to an existing date sheet (for 4/27-style residual fixes).

    Fixes:
    - Main data row 1: BLUE bg, bold, LEFT align
    - Main data rows 2..main_end: WHITE bg, normal, LEFT align
    - Sub-table title rows (X（N人）): BLUE bg, bold, LEFT align
    - Sub-table sub-header rows (姓名/...): BLUE bg, bold, LEFT align
    - Sub-table patient rows: WHITE bg, normal, LEFT align, WRAP
    - Blank gap rows: WHITE bg, no bold
    - Thick black borders: main data A:L, ordering N:V (if filled), sub-table A:H
    - Gap rows: borders stripped (NONE)

    Per memory feedback_sheet_formatting.md (全部 LEFT) +
    feedback_post_edit_format_check.md (白底+左靠齊 必跑).
    """
    import re
    ws = get_worksheet(sheet_name)
    if not ws:
        raise ValueError(f"找不到工作表: {sheet_name}")
    sh = get_spreadsheet()
    sid = ws.id
    col_a = ws.col_values(1)
    n_rows = len(col_a)

    # Find main_end (rows starting YYYY-MM-DD in col A)
    main_end = 1
    for i, v in enumerate(col_a[1:], 2):
        if re.match(r'^\d{4}-\d{2}-\d{2}$', v or ''):
            main_end = i
        elif v.strip() == '':
            continue
        else:
            break

    # Find sub-table title + subheader + patient rows
    title_rows = []
    subheader_rows = []
    patient_rows = []
    sub_blocks = []  # (title_row, last_row) inclusive — for border framing
    i = main_end + 1
    while i <= n_rows:
        v = col_a[i-1] if i-1 < len(col_a) else ''
        m = re.match(r'^(.+)（(\d+)人）$', v.strip())
        if m:
            n = int(m.group(2))
            title_rows.append(i)
            if i + 1 <= n_rows and (col_a[i] if i < len(col_a) else '').strip() == '姓名':
                subheader_rows.append(i + 1)
                for k in range(i + 2, i + 2 + n):
                    if k - 1 < len(col_a) and col_a[k-1].strip():
                        patient_rows.append(k)
                sub_blocks.append((i, i + 1 + n))
                i = i + 2 + n
            else:
                sub_blocks.append((i, i))
                i += 1
        else:
            i += 1

    blue_rows = sorted(set([1] + title_rows + subheader_rows))
    white_data_rows = sorted(set(list(range(2, main_end + 1)) + patient_rows))

    # Compute used range (last row of last sub-table or main_end)
    last_used = max([main_end] + patient_rows + title_rows + [1])
    # Gap rows: any row in [main_end+1, last_used] NOT in blue/patient
    used_set = set(blue_rows) | set(patient_rows)
    gap_rows = [r for r in range(main_end + 1, last_used + 1) if r not in used_set]

    requests = []

    # BLUE bg + bold + LEFT on header rows (cols A:H = 1..8 for sub-tables)
    for r in blue_rows:
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": r - 1, "endRowIndex": r,
                          "startColumnIndex": 0, "endColumnIndex": 12 if r == 1 else 8},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": BLUE_HEADER,
                    "textFormat": {"bold": True, "fontSize": 11},
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE",
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)",
            }
        })

    # WHITE bg + LEFT on main data rows (A:L = 12 cols)
    if main_end >= 2:
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 1, "endRowIndex": main_end,
                          "startColumnIndex": 0, "endColumnIndex": 12},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": WHITE,
                    "textFormat": {"bold": False, "fontSize": 11},
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "WRAP",
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
            }
        })

    # WHITE bg + LEFT on gap rows (A:H = 8 cols)
    for r in gap_rows:
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": r - 1, "endRowIndex": r,
                          "startColumnIndex": 0, "endColumnIndex": 8},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": WHITE,
                    "textFormat": {"bold": False, "fontSize": 11},
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE",
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)",
            }
        })

    # WHITE bg + LEFT on sub-table patient rows (A:H = 8 cols)
    for r in patient_rows:
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": r - 1, "endRowIndex": r,
                          "startColumnIndex": 0, "endColumnIndex": 8},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": WHITE,
                    "textFormat": {"bold": False, "fontSize": 11},
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "WRAP",
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
            }
        })

    # Thick black borders — clear gap rows first, then paint blocks (so adjacent
    # block edges (sub-table top/bottom, main data bottom) re-overwrite the cleared
    # shared edge with SOLID_THICK).
    THICK = {"style": "SOLID_THICK", "color": BLACK}

    for r in gap_rows:
        requests.append({
            "updateBorders": {
                "range": {"sheetId": sid, "startRowIndex": r - 1, "endRowIndex": r,
                          "startColumnIndex": 0, "endColumnIndex": 22},
                "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
                "left": {"style": "NONE"}, "right": {"style": "NONE"},
                "innerHorizontal": {"style": "NONE"}, "innerVertical": {"style": "NONE"},
            }
        })

    if main_end >= 1:
        requests.append({
            "updateBorders": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": main_end,
                          "startColumnIndex": 0, "endColumnIndex": 12},
                "top": THICK, "bottom": THICK, "left": THICK, "right": THICK,
                "innerHorizontal": THICK, "innerVertical": THICK,
            }
        })

    col_n = ws.col_values(14)
    n_end = 0
    for idx, v in enumerate(col_n[1:], 2):
        if (v or '').strip():
            n_end = idx
    if n_end >= 2:
        requests.append({
            "updateBorders": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": n_end,
                          "startColumnIndex": 13, "endColumnIndex": 22},
                "top": THICK, "bottom": THICK, "left": THICK, "right": THICK,
                "innerHorizontal": THICK, "innerVertical": THICK,
            }
        })

    for (s, e) in sub_blocks:
        requests.append({
            "updateBorders": {
                "range": {"sheetId": sid, "startRowIndex": s - 1, "endRowIndex": e,
                          "startColumnIndex": 0, "endColumnIndex": 8},
                "top": THICK, "bottom": THICK, "left": THICK, "right": THICK,
                "innerHorizontal": THICK, "innerVertical": THICK,
            }
        })

    # Run in batches of 50 to avoid request size limits
    for batch in [requests[k:k+50] for k in range(0, len(requests), 50)]:
        if batch:
            sh.batch_update({"requests": batch})
            time.sleep(0.5)

    return {
        "main_end": main_end,
        "title_rows": title_rows,
        "subheader_rows": subheader_rows,
        "patient_rows": patient_rows,
        "sub_blocks": sub_blocks,
    }
