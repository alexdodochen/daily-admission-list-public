"""Rebuild date sheets from a patient list with minimal Google Sheets API calls.

Reusable library. Import `rebuild_one(date8, patients)` to rebuild a single
sheet. The CLI `main()` reads from `_patients.py` (ephemeral scratch).

Per date this module uses ≈6 API calls to respect the 60/min quota:
  1. Duplicate template (1)
  2. appendDimension / unmerge / clear (1 batch)
  3. Write main data A-L (1)
  4. Write all sub-tables as one block A:G (1)
  5. Single batch_update for all formatting/merges/borders/dropdowns (1)

Sleeps 45s between dates (see feedback_gsheet_quota_batching.md).

`patients` format (12-col tuple per row, matches main data A-L):
  (實住日, 開刀日, 科別, 醫師, 主診斷, 姓名, 性別, 年齡, 病歷號, 床號, 入院提示, 住急)

Called from the `admission-sheet-rebuild` skill when date sheets are
accidentally deleted or need a clean slate.
"""
import sys, time, random, io
sys.path.insert(0, '.')
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

import gsheet_utils as gu
from _patients import PATIENTS

TEMPLATE = '20260417'
random.seed(42)

SUB_HEADERS = ['姓名', '病歷號', 'EMR', '手動設定入院序',
               '術前診斷', '預計心導管', '註記']


def build_sub_table_data(by_doctor, doctor_order, start_row):
    """Return (data_2d_rows, block_metas) where:
    - data_2d_rows is a list of [7 cols] rows to write at A{start_row}:G{end}
    - block_metas = list of {title_row, header_row, data_start, data_end, doctor, count}
    """
    rows = []
    metas = []
    cur = start_row
    for doc in doctor_order:
        pts = by_doctor[doc]
        title = f'{doc}（{len(pts)}人）'
        rows.append([title, '', '', '', '', '', ''])
        title_r = cur
        cur += 1
        rows.append(SUB_HEADERS[:])
        header_r = cur
        cur += 1
        data_start = cur
        for p in pts:
            rows.append([p[5], p[8], '', '', '', '', ''])
            cur += 1
        data_end = cur - 1
        metas.append({
            'doctor': doc,
            'title_row': title_r,
            'header_row': header_r,
            'data_start': data_start,
            'data_end': data_end,
            'count': len(pts),
        })
        # blank row gap
        rows.append(['', '', '', '', '', '', ''])
        cur += 1
    return rows, metas


def build_format_requests(ws_id, main_end_row, metas):
    """All formatting, merges, borders, dropdowns in one batch."""
    requests = []
    # Doctor sub-tables
    for m in metas:
        # Merge title row A:G
        requests.append({
            'mergeCells': {
                'range': {
                    'sheetId': ws_id,
                    'startRowIndex': m['title_row'] - 1,
                    'endRowIndex': m['title_row'],
                    'startColumnIndex': 0,
                    'endColumnIndex': 7,
                },
                'mergeType': 'MERGE_ALL',
            }
        })
        # Title + header row blue formatting
        for r in (m['title_row'], m['header_row']):
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': ws_id,
                        'startRowIndex': r - 1,
                        'endRowIndex': r,
                        'startColumnIndex': 0,
                        'endColumnIndex': 7,
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': gu.BLUE_HEADER,
                            'textFormat': {'bold': True, 'fontSize': 11},
                            'horizontalAlignment': 'CENTER',
                            'verticalAlignment': 'MIDDLE',
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)',
                }
            })
        # Borders
        border_style = {'style': 'SOLID', 'color': gu.BLACK}
        requests.append({
            'updateBorders': {
                'range': {
                    'sheetId': ws_id,
                    'startRowIndex': m['title_row'] - 1,
                    'endRowIndex': m['data_end'],
                    'startColumnIndex': 0,
                    'endColumnIndex': 7,
                },
                'top': border_style, 'bottom': border_style,
                'left': border_style, 'right': border_style,
                'innerHorizontal': border_style, 'innerVertical': border_style,
            }
        })
        # Dropdowns E (術前診斷) / F (預計心導管) on data rows (post 5/4 layout)
        if m['data_end'] >= m['data_start']:
            for col_idx, src_range in (
                (4, "='下拉選單'!$A$2:$A$66"),
                (5, "='下拉選單'!$D$2:$D$23"),
            ):
                requests.append({
                    'setDataValidation': {
                        'range': {
                            'sheetId': ws_id,
                            'startRowIndex': m['data_start'] - 1,
                            'endRowIndex': m['data_end'],
                            'startColumnIndex': col_idx,
                            'endColumnIndex': col_idx + 1,
                        },
                        'rule': {
                            'condition': {
                                'type': 'ONE_OF_RANGE',
                                'values': [{'userEnteredValue': src_range}],
                            },
                            'showCustomUi': True,
                            'strict': False,
                        }
                    }
                })
    return requests


def rebuild_one(date8, patients):
    sh = gu.get_spreadsheet()

    # 1. Delete existing + duplicate template
    existing = gu.get_worksheet(date8)
    if existing:
        sh.del_worksheet(existing)
        time.sleep(0.3)
    tpl = gu.get_worksheet(TEMPLATE)
    sh.batch_update({'requests': [{
        'duplicateSheet': {'sourceSheetId': tpl.id, 'newSheetName': date8}
    }]})
    time.sleep(0.8)
    ws = gu.get_worksheet(date8)
    if ws is None:
        raise RuntimeError(f'failed to create {date8}')

    # 2. Combine resize + unmerge + clear into one batch
    sh_meta = sh.fetch_sheet_metadata()
    merges = []
    for s in sh_meta.get('sheets', []):
        if s['properties']['sheetId'] == ws.id:
            merges = s.get('merges', [])
            break

    requests = []
    if ws.row_count < 80:
        requests.append({
            'appendDimension': {
                'sheetId': ws.id,
                'dimension': 'ROWS',
                'length': 80 - ws.row_count,
            }
        })
    for m in merges:
        requests.append({'unmergeCells': {'range': m}})
    # Clear A2:W80
    requests.append({
        'updateCells': {
            'range': {
                'sheetId': ws.id,
                'startRowIndex': 1, 'endRowIndex': 80,
                'startColumnIndex': 0, 'endColumnIndex': 23,
            },
            'fields': 'userEnteredValue',
        }
    })
    sh.batch_update({'requests': requests})
    time.sleep(0.5)

    # 3. Write main data A-L
    main_rows = []
    for p in patients:
        chart = p[8]
        main_rows.append([
            p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7],
            f"'{chart}" if chart else '', p[9], p[10], p[11],
        ])
    main_end = 1 + len(main_rows)
    ws.update(values=main_rows, range_name=f'A2:L{main_end}',
              value_input_option='USER_ENTERED')
    time.sleep(0.5)

    # 4. Build doctor groups and sub-table data
    doctors_in_order = []
    by_doctor = {}
    for p in patients:
        doc = p[3]
        if doc not in by_doctor:
            by_doctor[doc] = []
            doctors_in_order.append(doc)
        by_doctor[doc].append(p)

    shuffled = doctors_in_order[:]
    random.shuffle(shuffled)
    for d in shuffled:
        random.shuffle(by_doctor[d])

    sub_start = main_end + 2  # 1 blank row after main data
    sub_rows, metas = build_sub_table_data(by_doctor, shuffled, sub_start)
    sub_end = sub_start + len(sub_rows) - 1

    # Write sub-table block with USER_ENTERED so '01382096 → text
    # Prepend ' to chart cells so leading zeros preserved
    sub_rows_write = []
    for r in sub_rows:
        rr = r[:]
        if rr[1] and not rr[1].startswith("'"):
            rr[1] = f"'{rr[1]}"
        sub_rows_write.append(rr)
    ws.update(values=sub_rows_write, range_name=f'A{sub_start}:G{sub_end}',
              value_input_option='USER_ENTERED')
    time.sleep(0.5)

    # 5. One batch_update for all formatting
    fmt_requests = build_format_requests(ws.id, main_end, metas)
    if fmt_requests:
        # Split into batches if huge
        batch_size = 200
        for i in range(0, len(fmt_requests), batch_size):
            sh.batch_update({'requests': fmt_requests[i:i+batch_size]})
            time.sleep(0.3)

    print(f'[{date8}] {len(patients)} patients, {len(shuffled)} doctors, sub-tables rows {sub_start}-{sub_end}')


def main():
    dates = list(PATIENTS.keys())
    for i, d8 in enumerate(dates):
        if i > 0:
            print(f'[sleep 45s]')
            time.sleep(45)
        try:
            rebuild_one(d8, PATIENTS[d8])
        except Exception as e:
            print(f'[{d8}] ERROR: {e}')
            import traceback; traceback.print_exc()
            # Don't break — try remaining dates after quota recovers
            print('[sleep 70s extra]')
            time.sleep(70)


if __name__ == '__main__':
    main()
