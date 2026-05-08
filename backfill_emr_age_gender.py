"""Backfill: prepend `<age> y/o <gender>\\n` to sub-table C col (raw EMR) on
date sheets where it's missing. Idempotent — skips rows already prefixed.

Usage:
    python backfill_emr_age_gender.py YYYYMMDD [YYYYMMDD ...]
    python backfill_emr_age_gender.py --all-recent   # scan all 2026MMDD sheets

Sources demographics from the date sheet's main data (G=gender, H=age) by
chart-no lookup. If a sub-table chart isn't in main data → log + skip.

Trigger condition: C col is non-empty and does NOT match `^\\d+ y/o [男女]`.
"""
import sys
import re
import time

from gsheet_utils import get_spreadsheet, batch_write_cells

PREFIX_RE = re.compile(r'^\d+\s+y/o\s+[男女]')
TITLE_RE = re.compile(r'.+（\d+人）$')
SUBHEADER_NAMES = ('姓名',)


def backfill_one(sh, date: str) -> dict:
    ws = sh.worksheet(date)
    if ws is None:
        return {'date': date, 'status': 'sheet_missing'}

    grid = ws.get('A1:H200')

    # Build main-data chart -> (gender, age) map (rows 2 through first blank/title)
    main_map = {}
    for i, row in enumerate(grid[1:], start=2):
        if not row or not row[0]:
            break
        if TITLE_RE.match(row[0] or ''):
            break
        # Main data: A=date, ..., F=name(idx5), G=gender(idx6), H=age(idx7), I=chart(idx8)
        # But sub-tables share col-A onwards too; main data ends when col-A no longer
        # looks like a YYYY-MM-DD date.
        if not re.match(r'^\d{4}-\d{2}-\d{2}', row[0] or ''):
            break
        # main_full row needs cols up to I — re-read full A-L for this row to get chart
        pass

    # Re-read main data A-L explicitly (avoids col cap)
    main_full = ws.get('A2:L100')
    for r in main_full:
        if not r or not r[0] or not re.match(r'^\d{4}-\d{2}-\d{2}', r[0] or ''):
            break
        gender = r[6] if len(r) > 6 else ''
        age = r[7] if len(r) > 7 else ''
        chart = r[8] if len(r) > 8 else ''
        if chart:
            main_map[chart] = (gender.strip(), str(age).strip())

    # Walk sub-tables in grid (A1:H200)
    updates = []
    skipped = []
    no_main = []
    no_emr = []
    in_sub = False
    for i, row in enumerate(grid, start=1):
        a = row[0] if row else ''
        if TITLE_RE.match(a or ''):
            in_sub = True
            continue
        if not in_sub:
            continue
        if not row or not a:
            continue
        if a in SUBHEADER_NAMES:
            continue
        # Patient row in sub-table: A=name, B=chart, C=EMR
        b = row[1] if len(row) > 1 else ''
        c = row[2] if len(row) > 2 else ''
        if not b:
            continue
        if not c:
            no_emr.append((i, a, b))
            continue
        if PREFIX_RE.match(c.strip()):
            skipped.append((i, a, b))
            continue
        # Lookup demographics
        demo = main_map.get(b)
        if not demo or not demo[0] or not demo[1]:
            no_main.append((i, a, b))
            continue
        gender, age = demo
        new_c = f'{age} y/o {gender}\n{c}'
        updates.append((f'C{i}', new_c))

    if updates:
        batch_write_cells(ws, updates)

    return {
        'date': date,
        'status': 'ok',
        'updated': len(updates),
        'already_prefixed': len(skipped),
        'no_emr': len(no_emr),
        'no_main_demo': len(no_main),
        'mains_seen': len(main_map),
        'no_main_details': no_main[:5],
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sh = get_spreadsheet()
    if sys.argv[1] == '--all-recent':
        targets = sorted(
            w.title for w in sh.worksheets()
            if re.match(r'^2026\d{4}$', w.title)
        )
    else:
        targets = sys.argv[1:]
    for d in targets:
        try:
            res = backfill_one(sh, d)
            print(res)
        except Exception as e:
            print({'date': d, 'status': 'error', 'msg': str(e)})
        time.sleep(0.5)


if __name__ == '__main__':
    main()
