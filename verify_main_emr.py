"""Verify main A-L 姓名/性別/年齡 against EMR divUserSpec for a date sheet.

Usage:
  python verify_main_emr.py YYYYMMDD [session_url]

If session_url omitted, reads from _emr_session.txt (gitignored).
Exits silently (rc=0) if no URL available or session expired — verify is
opportunistic; absence of session doesn't fail the workflow.

For each chart in main A-L, opens Playwright (headless), enters chart_no
in the EMR query frame, reads `<span id="divUserSpec">`, parses
(name, DOB, gender), computes age from DOB→today, and compares vs
sheet F (姓名) / G (性別) / H (年齡). Differences are batched and applied.

EMR divUserSpec is canonical for these three fields per
feedback_emr_auto_name_fix.md / feedback_age_emr_canonical.md /
feedback_name_conflict_refetch_emr.md.
"""
import sys, os, re, time, io
from datetime import date

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass


def parse_divuserspec(text):
    """Returns (name, birth 'YYYY/M/D', gender '男'/'女') or (None, None, None)."""
    m_name = re.search(r'姓名\s*:\s*([^\s,，]+)', text)
    m_birth = re.search(r'生日\s*:\s*(\d{4}/\d{1,2}/\d{1,2})', text)
    m_gender = re.search(r'性別\s*:\s*([男女])', text)
    name = m_name.group(1) if m_name else None
    birth = m_birth.group(1) if m_birth else None
    gender = m_gender.group(1) if m_gender else None
    return name, birth, gender


def compute_age(birth_str):
    try:
        y, mo, d = map(int, birth_str.split('/'))
    except Exception:
        return None
    today = date.today()
    return today.year - y - ((today.month, today.day) < (mo, d))


def _query_and_read(page, chart):
    """Stamp BOTH leftFrame AND divUserSpec with a sentinel, fire query, then
    wait until divUserSpec has been refreshed by the system (no longer
    contains the sentinel, and has '姓名 :' content).

    Root cause of earlier bug: divUserSpec lives in a different frame and
    refreshes asynchronously after BTQuery click. Waiting only on leftFrame
    let the read return the PREVIOUS chart's divUserSpec — produced an
    off-by-one corruption across all rows (5/12 incident).
    """
    sentinel = f'VERIFY-SENT-{chart}-{int(time.time()*1000) % 1000000}'
    # Stamp divUserSpec in whichever frame contains it
    page.evaluate(f"""() => {{
        for (let i = 0; i < window.frames.length; i++) {{
            try {{
                let el = window.frames[i].document.querySelector('#divUserSpec');
                if (el) el.innerText = '{sentinel}';
            }} catch(e) {{}}
        }}
        try {{ window.frames['leftFrame'].document.body.innerHTML = '<!--{sentinel}-->'; }} catch(e) {{}}
    }}""")
    page.evaluate(f"""() => {{
        let d = window.frames['topFrame'].document;
        let inp = d.getElementById('txtChartNo');
        inp.value = '{chart}';
        d.getElementById('BTQuery').click();
    }}""")
    # Wait for divUserSpec to refresh (sentinel gone AND has 姓名 marker)
    for _ in range(30):
        time.sleep(0.5)
        st = page.evaluate(f"""() => {{
            for (let i = 0; i < window.frames.length; i++) {{
                try {{
                    let el = window.frames[i].document.querySelector('#divUserSpec');
                    if (!el) continue;
                    let t = el.innerText || '';
                    if (t.indexOf('{sentinel}') >= 0) return 'stamped';
                    if (t.indexOf('姓名') >= 0) return 'ready';
                }} catch(e) {{}}
            }}
            return 'wait';
        }}""")
        if st == 'ready':
            break
    # Extra settle — divUserSpec text may still be partially updating
    time.sleep(0.4)
    txt = page.evaluate(f"""() => {{
        for (let i = 0; i < window.frames.length; i++) {{
            try {{
                let el = window.frames[i].document.querySelector('#divUserSpec');
                if (!el) continue;
                let t = (el.innerText || '').trim();
                if (t && t.indexOf('{sentinel}') < 0 && t.indexOf('姓名') >= 0) return t;
            }} catch(e) {{}}
        }}
        return '';
    }}""")
    return txt


def main():
    if len(sys.argv) < 2:
        print('Usage: python verify_main_emr.py YYYYMMDD [session_url]')
        sys.exit(1)

    date_sheet = sys.argv[1]

    if len(sys.argv) >= 3:
        url = sys.argv[2].strip()
    elif os.path.exists('_emr_session.txt'):
        with open('_emr_session.txt', encoding='utf-8') as f:
            url = f.read().strip()
    else:
        print('[verify_main_emr] no _emr_session.txt and no URL arg — skipping')
        sys.exit(0)

    if not url.startswith('http'):
        print(f'[verify_main_emr] URL invalid: {url[:50]!r} — skipping')
        sys.exit(0)

    from gsheet_utils import get_worksheet, batch_write_cells
    try:
        ws = get_worksheet(date_sheet)
    except Exception as e:
        print(f'[verify_main_emr] worksheet {date_sheet} not found: {e}')
        sys.exit(0)

    main_data = ws.get('A1:L30')

    rows = []
    for ri, row in enumerate(main_data, 1):
        if ri == 1:
            continue
        if len(row) < 9:
            continue
        chart = (row[8] if len(row) > 8 else '').strip()
        if not chart:
            continue
        rows.append({
            'row': ri, 'chart': chart,
            'sheet_name': row[5] if len(row) > 5 else '',
            'sheet_gender': row[6] if len(row) > 6 else '',
            'sheet_age': str(row[7]) if len(row) > 7 else '',
        })

    if not rows:
        print('[verify_main_emr] no charts in main — skip')
        sys.exit(0)

    print(f'[verify_main_emr] verifying {len(rows)} charts vs EMR divUserSpec...')

    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print(f'[verify_main_emr] playwright not available: {e}')
        sys.exit(0)

    updates = []
    diffs = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=15000)
            time.sleep(2)
        except Exception as e:
            print(f'[verify_main_emr] page.goto failed (session probably expired): {e}')
            browser.close()
            sys.exit(0)

        valid = page.evaluate("""() => {
            try {
                let d = window.frames['topFrame'].document;
                return !!d.getElementById('txtChartNo');
            } catch(e) { return false; }
        }""")
        if not valid:
            print('[verify_main_emr] session URL no longer has query box (expired) — skip')
            browser.close()
            sys.exit(0)

        for r in rows:
            chart = r['chart']
            try:
                div_text = _query_and_read(page, chart)
            except Exception as e:
                print(f'  [{chart}] query failed: {e}')
                continue
            name, birth, gender = parse_divuserspec(div_text)
            if not (name and birth and gender):
                print(f'  [{chart}] divUserSpec empty/unparseable — skip')
                continue
            age = compute_age(birth)
            ri = r['row']
            row_diffs = []
            row_updates = []
            if r['sheet_name'].strip() != name:
                row_updates.append((f'F{ri}', name))
                row_diffs.append(f"name {r['sheet_name']!r}→{name!r}")
            if r['sheet_gender'].strip() != gender:
                row_updates.append((f'G{ri}', gender))
                row_diffs.append(f"gender {r['sheet_gender']!r}→{gender!r}")
            if r['sheet_age'].strip() != str(age):
                row_updates.append((f'H{ri}', str(age)))
                row_diffs.append(f"age {r['sheet_age']!r}→{age}")
            if row_updates:
                updates.extend(row_updates)
                diffs.append(f"  [{chart}] row {ri}: " + ', '.join(row_diffs))
            else:
                print(f'  [{chart}] {name} {gender} {age} OK')
            time.sleep(0.3)

        browser.close()

    if updates:
        print('Corrections to apply:')
        for d in diffs:
            print(d)
        batch_write_cells(ws, updates, raw=True)
        print(f'[verify_main_emr] applied {len(updates)} cell updates')
    else:
        print('[verify_main_emr] all rows match EMR divUserSpec, no changes')


if __name__ == '__main__':
    main()
