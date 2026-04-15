"""Fetch EMR records for a batch of patients via Playwright using an existing session URL.

Usage:
  python fetch_emr.py <session_url> <out_json> <chart1> <doctor1> <chart2> <doctor2> ...

The session URL should be the frameset entry point the user pasted, e.g.
http://hisweb.hosp.ncku/Emrquery/(S(xxxxx))/tree/frame.aspx

Writes {chart: {status, name, emr, visit, matched_doctor}} to out_json.

Anti-race-condition strategy:
- Before each query, stamp leftFrame+mainFrame with a per-chart sentinel
  (`<!--FETCH:<chart>:QUERY-->` / `<!--FETCH:<chart>:CLICK-->`).
- Poll until leftFrame body no longer contains the sentinel AND has real
  visit links — only then is the new chart's visit tree loaded.
- Same for mainFrame after visit click.
- On duplicate EMR content detection, re-query the whole chart from scratch
  (once) instead of just re-reading.
"""
import sys, json, time, io
from playwright.sync_api import sync_playwright

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass


def _stamp_left(page, sentinel):
    page.evaluate(f"""() => {{
        try {{ window.frames['leftFrame'].document.body.innerHTML = '<!--{sentinel}-->'; }} catch(e) {{}}
    }}""")


def _stamp_main(page, sentinel):
    page.evaluate(f"""() => {{
        try {{ window.frames['mainFrame'].document.body.innerHTML = '<!--{sentinel}-->'; }} catch(e) {{}}
    }}""")


def _query_chart(page, chart):
    page.evaluate(f"""() => {{
        let d = window.frames['topFrame'].document;
        d.getElementById('txtChartNo').value = '{chart}';
        d.getElementById('BTQuery').click();
    }}""")


def _wait_left_ready(page, sentinel, max_s=12):
    """Wait until leftFrame is reloaded with visit links (sentinel gone)."""
    for _ in range(int(max_s * 2)):
        time.sleep(0.5)
        state = page.evaluate(f"""() => {{
            try {{
                let d = window.frames['leftFrame'].document;
                let html = d.body.innerHTML || '';
                if (html.indexOf('{sentinel}') >= 0) return 'stamped';
                let links = d.querySelectorAll('a');
                let count = 0;
                for (let l of links) if ((l.innerText || '').includes('門診')) count++;
                return count > 0 ? 'ready' : 'empty';
            }} catch(e) {{ return 'err:' + e.message; }}
        }}""")
        if state == 'ready':
            return True
    return False


def _wait_main_ready(page, sentinel, max_s=12):
    for _ in range(int(max_s * 2)):
        time.sleep(0.5)
        state = page.evaluate(f"""() => {{
            try {{
                let d = window.frames['mainFrame'].document;
                let html = d.body.innerHTML || '';
                if (html.indexOf('{sentinel}') >= 0) return 'stamped';
                let txt = (d.body.innerText || '').trim();
                return txt.length > 80 ? 'ready' : 'short';
            }} catch(e) {{ return 'err:' + e.message; }}
        }}""")
        if state == 'ready':
            return True
    return False


def _read_name(page):
    try:
        return page.evaluate("""() => {
            for (let i = 0; i < window.frames.length; i++) {
                try {
                    let el = window.frames[i].document.querySelector('#divUserSpec');
                    if (el && el.innerText.trim()) return el.innerText.trim();
                } catch(e) {}
            }
            return '';
        }""")
    except Exception:
        return ''


FALLBACK_DOCTORS = ['劉秉彥', '趙庭興', '蔡惟全', '許志新', '陳柏升', '李貽恒']


def _click_visit(page, doctor):
    fallback_js = json.dumps(FALLBACK_DOCTORS, ensure_ascii=False)
    return page.evaluate(f"""() => {{
        let d = window.frames['leftFrame'].document;
        let links = d.querySelectorAll('a');
        for (let link of links) {{
            let t = (link.innerText || '').trim();
            if (t.includes('門診') && t.includes('{doctor}')) {{
                link.click();
                return {{visit: t, matched: true}};
            }}
        }}
        let allow = {fallback_js};
        for (let fb of allow) {{
            for (let link of links) {{
                let t = (link.innerText || '').trim();
                if (t.includes('門診') && t.includes(fb)) {{
                    link.click();
                    return {{visit: t, matched: false}};
                }}
            }}
        }}
        return null;
    }}""")


def _extract_emr(page):
    return page.evaluate("""() => {
        let d = window.frames['mainFrame'].document;
        let divs = d.querySelectorAll('div.small');
        let texts = [];
        for (let div of divs) {
            let t = (div.innerText || '').trim();
            if (t && !t.includes('iportlet-content')) texts.push(t);
        }
        if (texts.length === 0) return (d.body.innerText || '').trim();
        return texts.join('\\n');
    }""")


def _fetch_one(page, chart, doctor, prev_emr, attempt=1):
    sentinel_q = f'FETCH-{chart}-{attempt}-QUERY'
    sentinel_c = f'FETCH-{chart}-{attempt}-CLICK'

    _stamp_left(page, sentinel_q)
    _stamp_main(page, sentinel_q)
    _query_chart(page, chart)

    if not _wait_left_ready(page, sentinel_q):
        return {'status': 'left_timeout', 'name': '', 'emr': '', 'visit': '', 'matched_doctor': False}

    name = _read_name(page)

    _stamp_main(page, sentinel_c)
    click_result = _click_visit(page, doctor)
    if click_result is None:
        return {'status': 'no_visit', 'name': name, 'emr': '', 'visit': '', 'matched_doctor': False}
    clicked = click_result['visit']
    matched_doctor = bool(click_result['matched'])

    if not _wait_main_ready(page, sentinel_c):
        return {'status': 'main_timeout', 'name': name, 'emr': '', 'visit': clicked, 'matched_doctor': matched_doctor}

    emr_text = _extract_emr(page)
    if emr_text and emr_text == prev_emr:
        return {'status': 'duplicate', 'name': name, 'emr': emr_text, 'visit': clicked, 'matched_doctor': matched_doctor}

    status = 'ok' if emr_text and len(emr_text) > 50 else 'empty'
    return {'status': status, 'name': name, 'emr': emr_text, 'visit': clicked, 'matched_doctor': matched_doctor}


def fetch(session_url, patients, out_path):
    results = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(session_url, wait_until='domcontentloaded')
        time.sleep(2)

        prev_emr = ''
        for pt in patients:
            chart = pt['chart']
            doctor = pt['doctor']
            try:
                r = _fetch_one(page, chart, doctor, prev_emr, attempt=1)
                if r['status'] == 'duplicate':
                    print(f'[{chart}] duplicate content, re-query from scratch')
                    time.sleep(1)
                    r = _fetch_one(page, chart, doctor, prev_emr, attempt=2)
            except Exception as e:
                r = {'status': f'error: {e}', 'name': '', 'emr': '', 'visit': '', 'matched_doctor': False}

            results[chart] = r
            if r.get('emr'):
                prev_emr = r['emr']
            tag = 'OK' if r.get('matched_doctor') else 'FALLBACK'
            print(f"[{chart}] {r.get('name','')[:40]}: {r['status']} ({len(r.get('emr','') or '')} chars) [{tag}: {(r.get('visit') or '')[:50]}]")
            time.sleep(0.5)

        browser.close()

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'wrote {out_path}')


if __name__ == '__main__':
    if len(sys.argv) < 4 or (len(sys.argv) - 3) % 2 != 0:
        print(__doc__)
        sys.exit(1)
    url = sys.argv[1]
    out = sys.argv[2]
    pts = []
    i = 3
    while i < len(sys.argv):
        pts.append({'chart': sys.argv[i], 'doctor': sys.argv[i + 1]})
        i += 2
    fetch(url, pts, out)
