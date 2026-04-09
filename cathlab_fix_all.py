"""
Fix cathlab prefix for 4/13, 4/14, 4/17:
1. Scan for entries with ' > ' in diagnosis
2. Record their full data
3. Delete ONLY those entries
4. Re-ADD with Enter (load patient name)
5. UPT to set diag/proc with child-only name
"""
from playwright.sync_api import sync_playwright
import json, time

BASE_URL = "http://cardiopacs01.hosp.ncku:8080/WEBCVIS"
SCHEDULE_URL = f"{BASE_URL}/HCO/HCO1W001.do"

out = open("_cathlab_fix_all.txt", "w", encoding="utf-8")

def log(msg):
    out.write(msg + "\n")
    out.flush()

def login(page):
    page.goto(f"{BASE_URL}/comm/login.jsp", timeout=15000)
    time.sleep(2)
    page.evaluate('''() => {
        document.querySelector('input[name="userid"]').value = '107614';
        document.querySelector('input[name="password"]').value = '107614';
        document.getElementById('loginButton').click();
    }''')
    time.sleep(5)
    page.goto(SCHEDULE_URL, timeout=30000)
    time.sleep(8)

def query_date(page, date_str):
    page.evaluate(f'''() => {{
        var d1 = document.getElementById('daySelect1');
        var d2 = document.getElementById('daySelect2');
        d1.removeAttribute('readonly'); d2.removeAttribute('readonly');
        d1.value = '{date_str}'; d2.value = '{date_str}';
        document.getElementById('QueryButton').click();
    }}''')
    time.sleep(4)

def scan_prefix_entries(page):
    """Find all entries with ' > ' in diagnosis, return list with full data"""
    # Get all rows
    all_rows = page.evaluate('''() => {
        var rows = document.querySelectorAll('#row tr');
        var result = [];
        for (var i = 0; i < rows.length; i++) {
            var el = rows[i].querySelector('#hes_patno');
            if (!el) continue;
            var chart = el.value;
            var cells = rows[i].querySelectorAll('td');
            // Get displayed diag/proc from the visible table
            var allCells2 = document.querySelectorAll('td, th');
            var hr = null;
            for (var j = 0; j < allCells2.length; j++) {
                if (allCells2[j].innerText.trim() === '\u8853\u524d\u8a3a\u65b7') { hr = allCells2[j].parentElement; break; }
            }
            result.push(chart);
        }
        return result;
    }''')

    # For each chart, click to load form data
    entries = []
    for chart in all_rows:
        found = page.evaluate('''(chart) => {
            let rows = document.querySelectorAll('#row tr');
            for (let row of rows) {
                let el = row.querySelector('#hes_patno');
                if (el && el.value === chart) { row.click(); return true; }
            }
            return false;
        }''', chart)
        if not found:
            continue
        time.sleep(0.5)

        data = page.evaluate('''() => {
            return {
                patno: document.getElementById('patno2').value,
                room: document.getElementById('examroom').value,
                time: document.getElementById('inspectiontime').value,
                date: document.querySelector('input[name="inspectiondate"]') ?
                      document.querySelector('input[name="inspectiondate"]').value : '',
                doc1: document.getElementById('attendingdoctor1').value,
                doc2: document.getElementById('attendingdoctor2').value,
                pdi: document.getElementById('pdijson').value,
                phc: document.getElementById('phcjson').value,
                note: document.getElementById('note') ? document.getElementById('note').value : '',
                prediag: document.querySelector('[name="prediagnosisitem"]') ?
                         document.querySelector('[name="prediagnosisitem"]').value : '',
                precath: document.querySelector('[name="preheartcatheter"]') ?
                         document.querySelector('[name="preheartcatheter"]').value : '',
            };
        }''')

        # Check if diagnosis has prefix
        has_prefix = ' > ' in data.get('prediag', '') or ' > ' in data.get('precath', '')
        if has_prefix:
            # Parse IDs from json
            try:
                pdi_arr = json.loads(data['pdi'])
                pdi_id = pdi_arr[0]['id'] if pdi_arr else ''
            except:
                pdi_id = ''
            try:
                phc_arr = json.loads(data['phc'])
                phc_id = phc_arr[0]['id'] if phc_arr else ''
            except:
                phc_id = ''

            # Strip prefix from names
            diag_name = data['prediag']
            if ' > ' in diag_name:
                diag_name = diag_name.split(' > ')[-1].strip()
            proc_name = data['precath']
            if ' > ' in proc_name:
                proc_name = proc_name.split(' > ')[-1].strip()

            entries.append({
                'chart': data['patno'],
                'room': data['room'],
                'time': data['time'],
                'date': data['date'],
                'doc1': data['doc1'],
                'doc2': data['doc2'],
                'note': data['note'],
                'diag': diag_name,
                'diag_id': pdi_id,
                'proc': proc_name,
                'proc_id': phc_id,
                'orig_diag': data['prediag'],
            })

    return entries

def delete_charts(page, charts):
    """Delete only specific chart numbers"""
    page.evaluate('''(charts) => {
        var rows = document.querySelectorAll('#row tr');
        for (var i = 0; i < rows.length; i++) {
            var el = rows[i].querySelector('#hes_patno');
            if (el && charts.indexOf(el.value) >= 0) {
                var cb = rows[i].querySelector('input[type="checkbox"][name="chk"]');
                if (cb) cb.checked = true;
            }
        }
        checkedShowButton(document.getElementById('deleteButton'), document.getElementsByName('chk'));
        document.getElementById('deleteButton').click();
    }''', charts)
    time.sleep(5)

def add_patient(page, pt):
    page.click('input[name="patno2"]')
    time.sleep(0.5)
    page.fill('input[name="patno2"]', pt["chart"])
    time.sleep(0.3)
    page.press('input[name="patno2"]', 'Enter')
    time.sleep(3)

    name = page.evaluate('() => { var el = document.querySelector("input[name=patname]"); return el ? el.value : ""; }')
    log(f"    Name: {name}")

    page.evaluate(f'() => {{ var d = document.querySelector(\'input[name="inspectiondate"]\'); if(d){{ d.removeAttribute("readonly"); d.value="{pt["date"]}"; }} }}')
    page.fill("#inspectiontime", pt["time"])
    page.select_option("#examroom", pt["room"])
    page.select_option("#attendingdoctor1", pt["doc1"])
    if pt["doc2"]:
        page.select_option("#attendingdoctor2", pt["doc2"])
    if pt.get("note"):
        page.fill("#note", pt["note"])
    time.sleep(0.3)

    page.evaluate('''() => {
        document.HCO1WForm.buttonName.name = 'ADD';
        document.HCO1WForm.buttonName.value = 'ADD';
        document.HCO1WForm.submit();
    }''')
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)
    log(f"    ADD done")

def upt_diag(page, pt):
    found = page.evaluate('''(chart) => {
        let rows = document.querySelectorAll('#row tr');
        for (let row of rows) {
            let el = row.querySelector('#hes_patno');
            if (el && el.value === chart) { row.click(); return true; }
        }
        return false;
    }''', pt["chart"])
    if not found:
        log(f"    UPT: row not found")
        return
    time.sleep(0.5)

    if pt["diag_id"]:
        dj = json.dumps([{"name": pt["diag"], "id": pt["diag_id"]}])
    else:
        dj = ""
    if pt["proc_id"]:
        pj = json.dumps([{"name": pt["proc"], "id": pt["proc_id"]}])
    else:
        pj = ""

    page.evaluate('''([dj, pj, dt, pt]) => {
        if (dj) {
            document.querySelector('[name="pdijson"]').value = dj;
            let f = document.querySelector('[name="prediagnosisitem"]');
            if (f) f.value = dt;
        }
        if (pj) {
            document.querySelector('[name="phcjson"]').value = pj;
            let f = document.querySelector('[name="preheartcatheter"]');
            if (f) f.value = pt;
        }
    }''', [dj, pj, pt["diag"], pt["proc"]])
    time.sleep(0.3)

    page.evaluate('''() => {
        document.HCO1WForm.buttonName.name = 'UPT';
        document.HCO1WForm.buttonName.value = 'UPT';
        document.HCO1WForm.submit();
    }''')
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)
    log(f"    UPT done: {pt['diag']} / {pt['proc']}")


def process_date(page, date_str):
    log(f"\n{'='*50}")
    log(f"  Processing {date_str}")
    log(f"{'='*50}")

    # Scan
    query_date(page, date_str)
    entries = scan_prefix_entries(page)
    log(f"Found {len(entries)} entries with prefix:")
    for e in entries:
        log(f"  {e['chart']} | {e['orig_diag']} -> {e['diag']} | {e['proc']} | room={e['room']} time={e['time']}")

    if not entries:
        log("Nothing to fix!")
        return

    # Delete
    charts = [e["chart"] for e in entries]
    log(f"\nDeleting {len(charts)} entries: {charts}")
    query_date(page, date_str)
    delete_charts(page, charts)
    log("Delete done")

    # Re-ADD
    log("\nRe-adding with Enter...")
    for i, pt in enumerate(entries):
        log(f"\n  ADD {pt['chart']}...")
        if i > 0:
            query_date(page, date_str)
        add_patient(page, pt)

    # UPT diag/proc
    log("\nUPT diag/proc...")
    for pt in entries:
        log(f"\n  UPT {pt['chart']}...")
        query_date(page, date_str)
        upt_diag(page, pt)

    log(f"\n{date_str} done: {len(entries)} entries fixed")


# ============ MAIN ============
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=200)
    page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()
    page.on("dialog", lambda d: d.accept())

    log("=== Login ===")
    login(page)

    for date_str in ["2026/04/13", "2026/04/14", "2026/04/17"]:
        process_date(page, date_str)

    log("\n\n=== ALL DONE ===")
    browser.close()

out.close()
with open("_cathlab_fix_all.txt", "r", encoding="utf-8") as f:
    print(f.read())
