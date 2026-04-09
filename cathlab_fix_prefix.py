"""
Fix cathlab schedule: delete entries with parent prefix, re-add with child-only names.
Uses Playwright to automate WEBCVIS.
"""
import time
import json
from playwright.sync_api import sync_playwright

BASE_URL = "http://cardiopacs01.hosp.ncku:8080/WEBCVIS"
SCHEDULE_URL = f"{BASE_URL}/HCO/HCO1W001.do"
LOGIN_URL = f"{BASE_URL}/comm/logout.jsp"
ACCOUNT = "107614"
PASSWORD = "107614"

# 4/16 cathlab entries to add (from 20260415 admission data)
# All 黃鼎鈞 patients, Thu schedule: AM C1 黃鼎鈞(浩、晨)
PATIENTS_0416 = [
    {
        'patno': '17496914', 'name': '楊靜萍',
        'room': 'xa-CATH1', 'time': '0600', 'date': '2026/04/16',
        'doc1': '315452',  # 黃鼎鈞
        'doc2': '105430',  # 葉立浩(浩)
        'pdi_name': 'pAf', 'pdi_id': 'PDI20090908120040',
        'phc_name': 'RF ablation', 'phc_id': 'PHC20090907120009',
    },
    {
        'patno': '06821833', 'name': '陳秋賢',
        'room': 'xa-CATH1', 'time': '0601', 'date': '2026/04/16',
        'doc1': '315452',
        'doc2': '105430',
        'pdi_name': 'pAf', 'pdi_id': 'PDI20090908120040',
        'phc_name': 'RF ablation', 'phc_id': 'PHC20090907120009',
    },
    {
        'patno': '06575936', 'name': '許素質',
        'room': 'xa-CATH1', 'time': '0602', 'date': '2026/04/16',
        'doc1': '315452',
        'doc2': '105430',
        'pdi_name': 'PSVT', 'pdi_id': 'PDI20090908120033',
        'phc_name': 'RF ablation', 'phc_id': 'PHC20090907120009',
    },
]


def login(page):
    """Login to WEBCVIS"""
    # 1. Go to schedule page first
    page.goto(SCHEDULE_URL, timeout=15000)
    time.sleep(3)

    # 2. Check if session timeout → click 重新登入
    has_logout = page.evaluate('() => document.body.innerHTML.indexOf("logout.jsp") >= 0')
    if has_logout:
        page.evaluate('''() => { top.location.href = '../comm/logout.jsp'; }''')
        time.sleep(3)

    # 3. Check if on login page (has userid field)
    has_userid = page.evaluate('() => !!document.querySelector("input[name=userid]")')
    if not has_userid:
        page.goto(f"{BASE_URL}/comm/login.jsp", timeout=15000)
        time.sleep(2)

    # 4. Fill credentials and click loginButton
    page.evaluate(f'''() => {{
        document.querySelector('input[name="userid"]').value = '{ACCOUNT}';
        document.querySelector('input[name="password"]').value = '{PASSWORD}';
    }}''')
    time.sleep(0.5)
    page.evaluate('() => document.getElementById("loginButton").click()')
    time.sleep(5)

    # 5. Navigate to schedule page
    page.goto(SCHEDULE_URL, timeout=30000)
    time.sleep(8)  # Dojo needs time to render


def query_date(page, date_str):
    """Query schedule for a specific date"""
    page.evaluate(f'''() => {{
        var d1 = document.getElementById('daySelect1');
        var d2 = document.getElementById('daySelect2');
        if (d1) {{ d1.removeAttribute('readonly'); d1.value = '{date_str}'; }}
        if (d2) {{ d2.removeAttribute('readonly'); d2.value = '{date_str}'; }}
        document.getElementById('QueryButton').click();
    }}''')
    time.sleep(3)


def get_existing_patients(page):
    """Get list of existing patient chart numbers in current schedule"""
    result = page.evaluate('''() => {
        var allCells = document.querySelectorAll('td, th');
        var headerRow = null;
        for (var i = 0; i < allCells.length; i++) {
            if (allCells[i].innerText.trim() === '\u8853\u524d\u8a3a\u65b7') {
                headerRow = allCells[i].parentElement; break;
            }
        }
        if (!headerRow) return [];
        var dataTable = headerRow.closest('table');
        var rows = dataTable.querySelectorAll('tr');
        var patients = [];
        for (var i = 1; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll('td');
            if (cells.length < 11) continue;
            var pi = cells[8] ? cells[8].innerText.trim() : '';
            var diag = cells[9] ? cells[9].innerText.trim() : '';
            var proc = cells[10] ? cells[10].innerText.trim() : '';
            if (pi) {
                var lines = pi.split('\\n');
                patients.push({chart: lines[0], name: lines[1] || '', diag: diag, proc: proc});
            }
        }
        return patients;
    }''')
    return result


def add_patient(page, pt):
    """Add a single patient to the schedule"""
    # Install form.submit interceptor to strip prefix
    page.evaluate('''() => {
        var form = document.forms['HCO1WForm'];
        if (!form._hooked) {
            var realSubmit = form.submit.bind(form);
            form.submit = function() {
                var pdi = document.getElementById('pdijson');
                if (pdi && pdi.value && pdi.value.indexOf(' > ') >= 0) {
                    try {
                        var arr = JSON.parse(pdi.value);
                        for (var i = 0; i < arr.length; i++) {
                            if (arr[i].name && arr[i].name.indexOf(' > ') >= 0) {
                                arr[i].name = arr[i].name.split(' > ').pop();
                            }
                        }
                        pdi.value = JSON.stringify(arr);
                    } catch(e){}
                }
                return realSubmit();
            };
            form._hooked = true;
        }
    }''')

    # Fill form
    page.evaluate(f'''() => {{
        document.getElementById('patno2').value = '{pt["patno"]}';

        var room = document.getElementById('examroom');
        for (var i = 0; i < room.options.length; i++) {{
            if (room.options[i].value === '{pt["room"]}') {{ room.selectedIndex = i; break; }}
        }}

        var dateField = document.querySelector('input[name="inspectiondate"]');
        if (dateField) {{ dateField.removeAttribute('readonly'); dateField.value = '{pt["date"]}'; }}

        document.getElementById('inspectiontime').value = '{pt["time"]}';

        var doc1 = document.getElementById('attendingdoctor1');
        for (var i = 0; i < doc1.options.length; i++) {{
            if (doc1.options[i].value === '{pt["doc1"]}') {{ doc1.selectedIndex = i; break; }}
        }}

        var doc2 = document.getElementById('attendingdoctor2');
        for (var i = 0; i < doc2.options.length; i++) {{
            if (doc2.options[i].value === '{pt["doc2"]}') {{ doc2.selectedIndex = i; break; }}
        }}
    }}''')
    time.sleep(0.5)

    # Set pdijson and phcjson with child-only names
    pdi_json = json.dumps([{"name": pt["pdi_name"], "id": pt["pdi_id"]}])
    phc_json = json.dumps([{"name": pt["phc_name"], "id": pt["phc_id"]}])

    page.evaluate(f'''() => {{
        document.getElementById('pdijson').value = '{pdi_json}';
        document.getElementById('phcjson').value = '{phc_json}';
    }}''')
    time.sleep(0.3)

    # Click AddButton
    page.evaluate('''() => {
        document.getElementById('buttonName').value = '';
        document.getElementById('buttonName').name = 'ADD';
        document.getElementById('AddButton').click();
    }''')
    time.sleep(4)


def main():
    out = open('_cathlab_fix.txt', 'w', encoding='utf-8')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Login
        out.write('Logging in...\n')
        login(page)

        # Navigate to schedule page
        page.goto(SCHEDULE_URL, timeout=15000)
        time.sleep(3)

        # Debug: check what page we're on
        has_qb = page.evaluate('() => !!document.getElementById("QueryButton")')
        page_url = page.url
        out.write(f'After login URL: {page_url}\n')
        out.write(f'Has QueryButton: {has_qb}\n')

        if not has_qb:
            # Maybe it's a frameset - check for frames
            frames = page.frames
            out.write(f'Frames: {len(frames)}\n')
            for f in frames:
                out.write(f'  Frame: {f.name} URL: {f.url}\n')
            # Try clicking the 心導管排程作業 menu link
            page.evaluate('''() => {
                var links = document.querySelectorAll('a');
                for (var i = 0; i < links.length; i++) {
                    if (links[i].innerText.indexOf('排程') >= 0) {
                        return links[i].href;
                    }
                }
                return 'no schedule link';
            }''')
            # Try navigating to schedule URL again
            page.goto(SCHEDULE_URL, timeout=15000)
            time.sleep(3)
            has_qb = page.evaluate('() => !!document.getElementById("QueryButton")')
            out.write(f'After 2nd navigate - Has QueryButton: {has_qb}\n')

        # Query 4/16
        out.write('\nQuerying 2026/04/16...\n')
        query_date(page, '2026/04/16')

        # Check existing entries
        existing = get_existing_patients(page)
        existing_charts = {p['chart'] for p in existing}
        out.write(f'Existing patients: {len(existing)}\n')
        for ep in existing:
            out.write(f'  {ep["chart"]} {ep["name"]} | {ep["diag"]} | {ep["proc"]}\n')

        # Add new patients (skip if already exists)
        for pt in PATIENTS_0416:
            if pt['patno'] in existing_charts:
                out.write(f'\nSKIP {pt["patno"]} {pt["name"]} - already exists\n')
                continue

            out.write(f'\nADDING {pt["patno"]} {pt["name"]} diag={pt["pdi_name"]} proc={pt["phc_name"]}...\n')
            add_patient(page, pt)

            # Re-install interceptor (page reloads after ADD)
            time.sleep(1)

        # Final check
        out.write('\n=== Final state ===\n')
        query_date(page, '2026/04/16')
        final = get_existing_patients(page)
        for fp in final:
            out.write(f'  {fp["chart"]} {fp["name"]} | {fp["diag"]} | {fp["proc"]}\n')

        browser.close()

    out.close()
    with open('_cathlab_fix.txt', 'r', encoding='utf-8') as f:
        print(f.read())


if __name__ == '__main__':
    main()
