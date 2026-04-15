"""Fetch EMR records for a batch of patients via Playwright using an existing session URL.

Usage:
  python fetch_emr.py <session_url> <out_json> <chart1> <doctor1> <chart2> <doctor2> ...

The session URL should be the frameset entry point the user pasted, e.g.
http://hisweb.hosp.ncku/Emrquery/(S(xxxxx))/tree/frame.aspx

Writes {chart: {status, name, emr}} to out_json.
"""
import sys, json, time
from playwright.sync_api import sync_playwright

def fetch(session_url, patients, out_path):
    results = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(session_url, wait_until='domcontentloaded')
        time.sleep(2)

        # EMR frameset has topFrame (search), leftFrame (visit tree), mainFrame (content)
        prev_emr = ''
        for pt in patients:
            chart = pt['chart']
            doctor = pt['doctor']
            name = ''
            emr_text = ''
            status = 'missing'
            try:
                # Clear mainFrame first so we can detect stale content
                page.evaluate("""() => {
                    try { window.frames['mainFrame'].document.body.innerHTML = '<!--CLEARED-->'; } catch(e) {}
                }""")

                # Query chart number in topFrame
                page.evaluate(f"""() => {{
                    let d = window.frames['topFrame'].document;
                    d.getElementById('txtChartNo').value = '{chart}';
                    d.getElementById('BTQuery').click();
                }}""")

                # Poll leftFrame until it reloads with new visit list (max 8s)
                visit_ready = False
                for _ in range(16):
                    time.sleep(0.5)
                    links_count = page.evaluate("""() => {
                        try {
                            let d = window.frames['leftFrame'].document;
                            let links = d.querySelectorAll('a');
                            let count = 0;
                            for (let l of links) if (l.innerText.includes('門診')) count++;
                            return count;
                        } catch(e) { return -1; }
                    }""")
                    if links_count > 0:
                        visit_ready = True
                        break

                # Read patient name from divUserSpec (any frame)
                try:
                    name = page.evaluate("""() => {
                        for (let i = 0; i < window.frames.length; i++) {
                            try {
                                let el = window.frames[i].document.querySelector('#divUserSpec');
                                if (el && el.innerText.trim()) return el.innerText.trim();
                            } catch(e) {}
                        }
                        return '';
                    }""")
                except Exception:
                    pass

                # Click a visit matching the target doctor; else any visit
                clicked = page.evaluate(f"""() => {{
                    let d = window.frames['leftFrame'].document;
                    let links = d.querySelectorAll('a');
                    for (let link of links) {{
                        let t = link.innerText.trim();
                        if (t.includes('門診') && t.includes('{doctor}')) {{
                            link.click();
                            return t;
                        }}
                    }}
                    for (let link of links) {{
                        let t = link.innerText.trim();
                        if (t.includes('門診')) {{ link.click(); return t; }}
                    }}
                    return null;
                }}""")
                if clicked is None:
                    results[chart] = {'status': 'no_visit', 'name': name, 'emr': ''}
                    print(f'[{chart}] {name or "?"}: NO VISIT FOUND')
                    prev_emr = ''
                    continue

                # Poll mainFrame until content is different from "cleared" and > 100 chars
                for _ in range(16):
                    time.sleep(0.5)
                    current = page.evaluate("""() => {
                        try {
                            let d = window.frames['mainFrame'].document;
                            return d.body.innerText.trim();
                        } catch(e) { return ''; }
                    }""")
                    if current and 'CLEARED' not in current and len(current) > 100 and current != prev_emr:
                        break

                # Extract SOAP text from mainFrame
                emr_text = page.evaluate("""() => {
                    let d = window.frames['mainFrame'].document;
                    let divs = d.querySelectorAll('div.small');
                    let texts = [];
                    for (let div of divs) {
                        let t = div.innerText.trim();
                        if (t && !t.includes('iportlet-content')) texts.push(t);
                    }
                    if (texts.length === 0) {
                        return d.body.innerText.trim();
                    }
                    return texts.join('\\n');
                }""")

                if emr_text == prev_emr:
                    print(f'[{chart}] WARN: duplicate EMR content, retrying once...')
                    time.sleep(3)
                    emr_text = page.evaluate("""() => {
                        let d = window.frames['mainFrame'].document;
                        let divs = d.querySelectorAll('div.small');
                        let texts = [];
                        for (let div of divs) {
                            let t = div.innerText.trim();
                            if (t && !t.includes('iportlet-content')) texts.push(t);
                        }
                        return texts.length ? texts.join('\\n') : d.body.innerText.trim();
                    }""")

                prev_emr = emr_text

                if emr_text and len(emr_text) > 50:
                    status = 'ok'
                else:
                    status = 'empty'

            except Exception as e:
                status = f'error: {e}'
                print(f'[{chart}] ERROR: {e}')

            results[chart] = {'status': status, 'name': name, 'emr': emr_text}
            print(f'[{chart}] {name}: {status} ({len(emr_text)} chars)')
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
        pts.append({'chart': sys.argv[i], 'doctor': sys.argv[i+1]})
        i += 2
    fetch(url, pts, out)
