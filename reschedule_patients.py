"""
改期病人搬運腳本 — 把來源日 W 欄填了目標日期的病人搬到目標日 sheet

用法: python reschedule_patients.py <source_date>

例: python reschedule_patients.py 20260413

流程:
  1. 讀來源日 N-W 入院序表格, 掃 W 欄找 YYYYMMDD (跳過「已改期至...」)
  2. 對每位病人: 讀 A-L 主資料 + 醫師子表格該列 (by 病歷號)
  3. 目標日 sheet 必須已存在 (否則該筆 skip)
  4. 主資料 A-L append 到目標日主資料末
  5. 醫師子表 → insert_rows 到目標日對應醫師區尾 (inherit_from_before)
     + 更新「X人）」計數
  6. 目標日無此醫師 → write_doctor_table 新增完整模塊
  7. 目標日 W1 若無 header → 補寫「改期」
  8. 來源日 W 欄改為「已改期至 YYYYMMDD」(保留 row)

結果寫入 _reschedule_result.txt
"""
import sys
import re
import time
import traceback

import gsheet_utils as gu

LOG = []
DATE_RE = re.compile(r'^\d{8}$')
DONE_RE = re.compile(r'^已改期至')
TITLE_RE = re.compile(r'^(.+?)（\s*(\d+)\s*人\s*）\s*$')


def normalize_date(raw, source_date):
    """
    Parse a variety of date formats and return YYYYMMDD string (or None).
    Accepts: 20260416, 2026/4/16, 2026-04-16, 4/16, 04-16, 4.16, 0416
    Year defaults to source_date's year when missing.
    """
    s = (raw or '').strip()
    if not s:
        return None
    # Already YYYYMMDD
    if DATE_RE.match(s):
        return s
    year = source_date[:4]
    # Split on common separators
    parts = re.split(r'[/\-.\s]+', s)
    parts = [p for p in parts if p]
    if len(parts) == 3:
        # YYYY M D  or  M D YYYY
        if len(parts[0]) == 4:
            y, m, d = parts
        elif len(parts[2]) == 4:
            m, d, y = parts
        else:
            return None
    elif len(parts) == 2:
        m, d = parts
        y = year
    elif len(parts) == 1 and len(s) == 4 and s.isdigit():
        # MMDD
        m, d = s[:2], s[2:]
        y = year
    else:
        return None
    try:
        y_i, m_i, d_i = int(y), int(m), int(d)
    except ValueError:
        return None
    if not (1 <= m_i <= 12 and 1 <= d_i <= 31):
        return None
    return f'{y_i:04d}{m_i:02d}{d_i:02d}'


def log(msg):
    LOG.append(msg)


def save_log():
    with open('_reschedule_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(LOG))


def cell(row, idx):
    return (row[idx] if idx < len(row) else '').strip()


def ensure_cols(ws, min_cols):
    """Ensure worksheet has at least min_cols columns; add if short."""
    if ws.col_count < min_cols:
        ws.add_cols(min_cols - ws.col_count)
        time.sleep(0.3)


def find_main_data_range(vals):
    """Return (start_idx, end_idx) 0-indexed of main A-L patient rows. Header=row 0."""
    if len(vals) < 2:
        return 1, 0
    start = 1
    end = start - 1
    for i in range(start, len(vals)):
        row = vals[i]
        if not any((c or '').strip() for c in row[:12]):
            break
        if TITLE_RE.match(cell(row, 0)):
            break
        end = i
    return start, end


def find_in_main(vals, chart_no, main_start, main_end):
    """Find 0-indexed row in main data by 病歷號 (col I = idx 8)."""
    for i in range(main_start, main_end + 1):
        if cell(vals[i], 8) == chart_no:
            return i
    return -1


def parse_sub_tables(vals, start_row):
    """
    Parse doctor sub-tables from start_row (0-indexed).
    Returns list of:
      {name, title_row, header_row, patient_start, patient_end, count, patients}
    where patients is a list of 8-item lists (A-H).
    """
    tables = []
    i = start_row
    while i < len(vals):
        m = TITLE_RE.match(cell(vals[i], 0))
        if not m:
            i += 1
            continue
        name = m.group(1).strip()
        count = int(m.group(2))
        title_row = i
        header_row = i + 1
        patient_start = i + 2
        patients = []
        j = patient_start
        while j < len(vals):
            prow = vals[j]
            if not any((c or '').strip() for c in prow[:8]):
                break
            if TITLE_RE.match(cell(prow, 0)):
                break
            patients.append([cell(prow, k) for k in range(8)])
            j += 1
        patient_end = j - 1
        tables.append({
            'name': name,
            'title_row': title_row,
            'header_row': header_row,
            'patient_start': patient_start,
            'patient_end': patient_end,
            'count': count,
            'patients': patients,
        })
        i = j + 1  # skip blank gap row
    return tables


def find_template_sheet(target_date):
    """Pick the most recent YYYYMMDD sheet (by name sort) to use as format template."""
    sh = gu.get_spreadsheet()
    date_sheets = sorted(
        [ws.title for ws in sh.worksheets() if re.match(r'^\d{8}$', ws.title)],
        reverse=True,
    )
    # Prefer a sheet that isn't the target itself
    for name in date_sheets:
        if name != target_date:
            return name
    return None


def create_empty_date_sheet(target_date):
    """Duplicate a recent date sheet, unmerge + clear, leave only row-1 header."""
    sh = gu.get_spreadsheet()
    template = find_template_sheet(target_date)
    if template is None:
        log(f'  ERROR: no existing date sheet to use as template for {target_date}')
        return None

    log(f'  Creating empty sheet "{target_date}" from template "{template}"')
    template_ws = sh.worksheet(template)
    resp = sh.batch_update({'requests': [{
        'duplicateSheet': {
            'sourceSheetId': template_ws.id,
            'newSheetName': target_date,
        }
    }]})
    new_id = resp['replies'][0]['duplicateSheet']['properties']['sheetId']
    time.sleep(1)
    new_ws = sh.worksheet(target_date)

    # Unmerge all to avoid merged sub-table titles swallowing data
    gu.batch_update_requests([{
        'unmergeCells': {
            'range': {
                'sheetId': new_id,
                'startRowIndex': 0, 'endRowIndex': 300,
                'startColumnIndex': 0, 'endColumnIndex': 23,
            }
        }
    }])
    time.sleep(1)

    # Clear everything except row 1 (A-L main header + any N-W header)
    new_ws.batch_clear(['A2:W300'])
    time.sleep(0.5)

    # Ensure W1 = 改期 (template may be old sheet without W header)
    header_vals = new_ws.get_all_values()
    h = header_vals[0] if header_vals else []
    if cell(h, 22) != '改期':
        gu.write_cell(new_ws, 1, 23, '改期')
        time.sleep(0.3)
    # Ensure N-W headers are present (if template had them they're preserved,
    # otherwise we fill the standard set)
    nw_headers = ['序號', '主治醫師', '病人姓名', '備註(住服)', '備註',
                  '病歷號', '術前診斷', '預計心導管', '每日續等清單', '改期']
    needs_nw = False
    for k in range(10):
        if cell(h, 13 + k) != nw_headers[k]:
            needs_nw = True
            break
    if needs_nw:
        gu.write_range(new_ws, 'N1:W1', [nw_headers])
        time.sleep(0.3)

    log(f'  Created empty sheet "{target_date}" (id={new_id})')
    return new_ws


def find_in_subtable(tables, chart_no):
    """Return (table_idx, patient_idx) for chart_no; (-1,-1) if not found."""
    for ti, t in enumerate(tables):
        for pi, p in enumerate(t['patients']):
            if cell(p, 1) == chart_no:
                return ti, pi
    return -1, -1


def collect_reschedules(vals, source_date):
    """Scan N-W block, return list of {chart_no, name, target, row(1-idx)}."""
    out = []
    for i in range(1, len(vals)):
        row = vals[i]
        w = cell(row, 22)  # W col = idx 22
        if not w:
            continue
        if DONE_RE.match(w):
            continue
        target = normalize_date(w, source_date)
        if target is None:
            log(f'  WARN row {i+1}: W="{w}" not parseable as date, skipped')
            continue
        if target == source_date:
            log(f'  WARN row {i+1}: target==source, skipped')
            continue
        chart_no = cell(row, 18)  # S col
        name = cell(row, 15)      # P col
        if not chart_no:
            log(f'  WARN row {i+1}: no chart_no, skipped')
            continue
        if target != w:
            log(f'  Parsed W="{w}" → {target}')
        out.append({'chart_no': chart_no, 'name': name,
                    'target': target, 'row': i + 1})
    return out


def migrate_to_target(tgt, target_date, migrations):
    """Apply migrations (list of dicts) to target worksheet."""
    ensure_cols(tgt, 23)
    tvals = tgt.get_all_values()

    # Ensure W1 header
    header = tvals[0] if tvals else []
    if cell(header, 22) != '改期':
        gu.write_cell(tgt, 1, 23, '改期')
        log(f'  [{target_date}] Added W1 header "改期"')
        time.sleep(0.3)

    tmain_start, tmain_end = find_main_data_range(tvals)
    tsub = parse_sub_tables(tvals, tmain_end + 1)
    log(f'  [{target_date}] main rows {tmain_start+1}-{tmain_end+1}, '
        f'{len(tsub)} doctor blocks')

    # 1. Append main data A-L
    append_start = tmain_end + 2  # 1-indexed row after current last
    new_main = [m['main_data'] for m in migrations]
    rng = f'A{append_start}:L{append_start + len(new_main) - 1}'
    gu.write_range(tgt, rng, new_main)
    log(f'  [{target_date}] Appended {len(new_main)} rows to main at {rng}')
    time.sleep(0.5)

    # 2. Group by doctor, separate existing vs new
    by_doctor = {}
    for m in migrations:
        by_doctor.setdefault(m['doctor_name'], []).append(m)

    existing_map = {t['name']: t for t in tsub}
    existing_pairs = [(d, ms) for d, ms in by_doctor.items() if d in existing_map]
    new_pairs = [(d, ms) for d, ms in by_doctor.items() if d not in existing_map]

    # Process existing blocks BOTTOM-UP to avoid index shifts
    existing_pairs.sort(key=lambda x: existing_map[x[0]]['title_row'], reverse=True)

    for doctor, ms in existing_pairs:
        t = existing_map[doctor]
        insert_at = t['patient_end'] + 2  # 1-indexed row
        new_rows = [m['sub_row'] for m in ms]
        try:
            tgt.insert_rows(new_rows, row=insert_at,
                            value_input_option='RAW',
                            inherit_from_before=True)
        except TypeError:
            # Older gspread: no inherit_from_before kwarg
            tgt.insert_rows(new_rows, row=insert_at,
                            value_input_option='RAW')
        log(f'  [{target_date}] Inserted {len(new_rows)} row(s) into {doctor} '
            f'at row {insert_at}')
        time.sleep(0.5)

        new_count = t['count'] + len(ms)
        gu.write_cell(tgt, t['title_row'] + 1, 1, f'{doctor}（{new_count}人）')
        log(f'  [{target_date}] Updated title: {doctor}（{new_count}人）')
        time.sleep(0.3)

    # 3. New doctor blocks — append below everything
    if new_pairs:
        tvals2 = tgt.get_all_values()
        last_row = 0
        for i in range(len(tvals2) - 1, -1, -1):
            if any((c or '').strip() for c in tvals2[i]):
                last_row = i + 1
                break
        next_row = last_row + 2
        for doctor, ms in new_pairs:
            pts = [{
                'name': cell(m['sub_row'], 0) or m['main_data'][5],
                'chart_no': cell(m['sub_row'], 1) or m['rec']['chart_no'],
                'emr': cell(m['sub_row'], 2),
                'emr_summary': cell(m['sub_row'], 3),
                'order': cell(m['sub_row'], 4),
                'diagnosis': cell(m['sub_row'], 5),
                'cathlab': cell(m['sub_row'], 6),
                'note': cell(m['sub_row'], 7),
            } for m in ms]
            block_start = next_row
            next_row = gu.write_doctor_table(tgt, block_start, doctor, pts)
            log(f'  [{target_date}] Created new doctor block {doctor}（{len(pts)}人） '
                f'at row {block_start}')


def process(source_date):
    log(f'=== Reschedule from {source_date} ===')
    src = gu.get_worksheet(source_date)
    if src is None:
        log(f'ERROR: source sheet "{source_date}" not found')
        return

    ensure_cols(src, 23)
    vals = src.get_all_values()

    # Ensure source W1 header (lazy backfill)
    if cell(vals[0] if vals else [], 22) != '改期':
        gu.write_cell(src, 1, 23, '改期')
        log('Source: added W1 header "改期"')
        time.sleep(0.3)

    main_start, main_end = find_main_data_range(vals)
    log(f'Source main data: rows {main_start+1}-{main_end+1}')

    src_tables = parse_sub_tables(vals, main_end + 1)
    log(f'Source has {len(src_tables)} doctor sub-tables')

    recs = collect_reschedules(vals, source_date)
    if not recs:
        log('No reschedule entries in W column.')
        save_log()
        return

    log(f'Found {len(recs)} reschedule(s):')
    for r in recs:
        log(f'  {r["name"]} ({r["chart_no"]}) row {r["row"]} → {r["target"]}')

    # Group by target date
    by_target = {}
    for r in recs:
        by_target.setdefault(r['target'], []).append(r)

    for target_date, group in by_target.items():
        log(f'\n--- Target {target_date} ({len(group)} patients) ---')
        tgt = gu.get_worksheet(target_date)
        if tgt is None:
            log(f'  Target sheet "{target_date}" does not exist → creating')
            tgt = create_empty_date_sheet(target_date)
            if tgt is None:
                log(f'  ERROR: failed to create "{target_date}", SKIPPED')
                continue

        migrations = []
        for r in group:
            mi = find_in_main(vals, r['chart_no'], main_start, main_end)
            if mi < 0:
                log(f'  ERROR: {r["name"]} ({r["chart_no"]}) not in main data')
                continue
            main_data = [cell(vals[mi], k) for k in range(12)]
            doctor_name = main_data[3]

            ti, pi = find_in_subtable(src_tables, r['chart_no'])
            if ti < 0:
                log(f'  WARN: {r["name"]} not in any sub-table, building minimal row')
                sub_row = [main_data[5], r['chart_no'], '', '', '', '', '', '']
            else:
                sub_row = list(src_tables[ti]['patients'][pi])
                if src_tables[ti]['name']:
                    doctor_name = src_tables[ti]['name']

            migrations.append({
                'rec': r,
                'main_data': main_data,
                'doctor_name': doctor_name,
                'sub_row': sub_row,
            })

        if not migrations:
            log(f'  No valid migrations for {target_date}')
            continue

        migrate_to_target(tgt, target_date, migrations)

        # Mark source W col
        for m in migrations:
            r = m['rec']
            gu.write_cell(src, r['row'], 23, f'已改期至 {target_date}')
            log(f'  Source W row {r["row"]} → 已改期至 {target_date}')
            time.sleep(0.3)

    log('\n=== Done ===')
    save_log()


def main():
    if len(sys.argv) < 2:
        print('Usage: python reschedule_patients.py <source_date>')
        sys.exit(1)
    try:
        process(sys.argv[1])
    except Exception as e:
        log(f'FATAL: {e}')
        log(traceback.format_exc())
        save_log()
        raise
    print('Done. See _reschedule_result.txt')


if __name__ == '__main__':
    main()
