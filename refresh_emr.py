"""Refresh EMR for multiple date sheets using a single browser session.

Usage:
  python refresh_emr.py <session_url> <date8> [<date8> ...]

Reads each date sheet's sub-tables to build the (chart, doctor) patient list,
fetches EMR in one browser session, splits results per date, and calls
process_emr.main() to write back safely.
"""
import sys, json, re
sys.path.insert(0, '.')
import gsheet_utils as gu
import fetch_emr
import process_emr


def get_patients(date8):
    """Return list of {chart, doctor, name, row} from sub-tables."""
    ws = gu.get_worksheet(date8)
    if ws is None:
        print(f'ERROR: sheet {date8} not found')
        return []
    vals = ws.get('A1:B80')
    out = []
    cur_doc = None
    for ri, r in enumerate(vals, 1):
        a = (r[0] if len(r) > 0 else '').strip()
        b = (r[1] if len(r) > 1 else '').strip().lstrip("'")
        if '人）' in a:
            m = re.match(r'^([^（(]+)', a)
            cur_doc = m.group(1).strip() if m else ''
            continue
        if cur_doc and b and b.isdigit() and len(b) >= 7:
            out.append({'chart': b, 'doctor': cur_doc, 'name': a, 'row': ri})
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    url = argv[0]
    dates = argv[1:]

    # Build master list across all dates (dedupe by chart — same patient on
    # multiple dates still queries once)
    per_date = {}
    seen_charts = {}
    master = []
    for d in dates:
        pts = get_patients(d)
        per_date[d] = pts
        print(f'[{d}] {len(pts)} patients')
        for p in pts:
            if p['chart'] not in seen_charts:
                master.append({'chart': p['chart'], 'doctor': p['doctor']})
                seen_charts[p['chart']] = (d, p['doctor'])

    print(f'\n=== Fetching {len(master)} unique patients in one session ===')
    fetch_emr.fetch(url, master, '_emr_combined.json')

    with open('_emr_combined.json', encoding='utf-8') as f:
        combined = json.load(f)

    # Split JSON per date (same chart in multiple dates uses same EMR)
    for d in dates:
        charts = {p['chart'] for p in per_date[d]}
        date_data = {ch: combined[ch] for ch in charts if ch in combined}
        with open(f'emr_data_{d}.json', 'w', encoding='utf-8') as f:
            json.dump(date_data, f, ensure_ascii=False, indent=2)
        print(f'[{d}] wrote emr_data_{d}.json with {len(date_data)} patients')

    # Process each date (writes C/D/F/G with safety checks)
    for d in dates:
        print(f'\n=== Processing {d} ===')
        process_emr.main(d)


if __name__ == '__main__':
    main(sys.argv[1:])
