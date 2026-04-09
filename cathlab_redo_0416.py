"""Delete old 4/16 entries (no names) and re-ADD properly with Enter + UPT diag/proc"""
from playwright.sync_api import sync_playwright
import json, time

BASE_URL = "http://cardiopacs01.hosp.ncku:8080/WEBCVIS"
SCHEDULE_URL = f"{BASE_URL}/HCO/HCO1W001.do"

PATIENTS = [
    {"chart": "17496914", "room": "xa-CATH1", "time": "0600", "date": "2026/04/16",
     "doc1": "315452", "doc2": "105430",
     "diag": "pAf", "diag_id": "PDI20090908120040",
     "proc": "RF ablation", "proc_id": "PHC20090907120009"},
    {"chart": "06821833", "room": "xa-CATH1", "time": "0601", "date": "2026/04/16",
     "doc1": "315452", "doc2": "105430",
     "diag": "pAf", "diag_id": "PDI20090908120040",
     "proc": "RF ablation", "proc_id": "PHC20090907120009"},
    {"chart": "06575936", "room": "xa-CATH1", "time": "0602", "date": "2026/04/16",
     "doc1": "315452", "doc2": "105430",
     "diag": "PSVT", "diag_id": "PDI20090908120033",
     "proc": "RF ablation", "proc_id": "PHC20090907120009"},
]

out = open("_cathlab_0416_redo.txt", "w", encoding="utf-8")

def log(msg):
    out.write(msg + "\n")
    out.flush()

def login_and_goto(page):
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

def query_date(page):
    page.evaluate('''() => {
        var d1 = document.getElementById('daySelect1');
        var d2 = document.getElementById('daySelect2');
        d1.removeAttribute('readonly'); d2.removeAttribute('readonly');
        d1.value = '2026/04/16'; d2.value = '2026/04/16';
        document.getElementById('QueryButton').click();
    }''')
    time.sleep(4)

def delete_charts(page, charts):
    page.evaluate('''(charts) => {
        var rows = document.querySelectorAll('#row tr');
        for (var i = 0; i < rows.length; i++) {
            var el = rows[i].querySelector('#hes_patno');
            if (el && charts.indexOf(el.value) >= 0) {
                var cb = rows[i].querySelector('input[type="checkbox"][name="chk"]');
                if (cb) { cb.checked = true; }
            }
        }
        checkedShowButton(document.getElementById('deleteButton'), document.getElementsByName('chk'));
        document.getElementById('deleteButton').click();
    }''', charts)

def add_patient(page, pt):
    # Click patno2 field to clear form
    page.click('input[name="patno2"]')
    time.sleep(0.5)

    # Fill chart number
    page.fill('input[name="patno2"]', pt["chart"])
    time.sleep(0.3)

    # Press Enter to trigger AJAX patient info lookup
    page.press('input[name="patno2"]', 'Enter')
    time.sleep(3)

    # Read loaded name
    name = page.evaluate('() => { var el = document.querySelector("input[name=patname]"); return el ? el.value : ""; }')
    log(f"  Name loaded: {name}")

    # Set date
    page.evaluate(f'() => {{ var d = document.querySelector(\'input[name="inspectiondate"]\'); if(d){{ d.removeAttribute("readonly"); d.value="{pt["date"]}"; }} }}')

    # Set time
    page.fill("#inspectiontime", pt["time"])

    # Select room and doctors
    page.select_option("#examroom", pt["room"])
    page.select_option("#attendingdoctor1", pt["doc1"])
    page.select_option("#attendingdoctor2", pt["doc2"])
    time.sleep(0.3)

    # Submit ADD via form.submit (not AddButton to avoid handler issues)
    page.evaluate('''() => {
        document.HCO1WForm.buttonName.name = 'ADD';
        document.HCO1WForm.buttonName.value = 'ADD';
        document.HCO1WForm.submit();
    }''')
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)
    log(f"  ADD done: {pt['chart']}")

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
        log(f"  UPT: row not found for {pt['chart']}")
        return
    time.sleep(0.5)

    dj = json.dumps([{"name": pt["diag"], "id": pt["diag_id"]}])
    pj = json.dumps([{"name": pt["proc"], "id": pt["proc_id"]}])

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
    log(f"  UPT done: diag={pt['diag']} proc={pt['proc']}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=200)
    page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()
    page.on("dialog", lambda d: d.accept())

    log("=== Login ===")
    login_and_goto(page)

    # Step 1: Delete
    log("\n=== Step 1: Delete old entries ===")
    query_date(page)
    charts = [pt["chart"] for pt in PATIENTS]
    delete_charts(page, charts)
    time.sleep(5)
    log("Delete done")

    # Step 2: ADD with Enter
    log("\n=== Step 2: ADD with Enter ===")
    for i, pt in enumerate(PATIENTS):
        log(f"\nAdding {pt['chart']}...")
        if i > 0:
            query_date(page)
        add_patient(page, pt)

    # Step 3: UPT diag/proc
    log("\n=== Step 3: UPT diag/proc ===")
    for pt in PATIENTS:
        log(f"\nUPT {pt['chart']}...")
        query_date(page)
        upt_diag(page, pt)

    log("\n=== All done! ===")
    browser.close()

out.close()
with open("_cathlab_0416_redo.txt", "r", encoding="utf-8") as f:
    print(f.read())
