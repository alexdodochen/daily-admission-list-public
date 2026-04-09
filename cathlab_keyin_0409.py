"""
20260408 入院 → 20260409 (Thu) 心導管排程 key-in
完整流程：ADD 新增 + UPT 補 pdijson/phcjson
跳過：沈桂英(非導管床/檢查)、陳郭明珠(HF AE)、王劉愛雪(Cardioversion不排)、黃鉦傑(不在排序)
"""
import time
import json
from playwright.sync_api import sync_playwright

BASE_URL = "http://cardiopacs01.hosp.ncku:8080/WEBCVIS"
SCHEDULE_URL = f"{BASE_URL}/HCO/HCO1W001.do"
ACCOUNT = "107614"
PASSWORD = "107614"
CATHLAB_DATE = "2026/04/09"

DOCTOR_CODES = {
    "詹世鴻": "023835", "許志新": "032894", "陳儒逸": "033047", "劉嚴文": "036030",
    "陳柏升": "044547", "黃睦翔": "046226", "柯呈諭": "049499", "李文煌": "053120",
    "李柏增": "053146", "林佳凌": "054143", "陳則瑋": "054185", "廖瑀": "054193",
    "陳昭佑": "100922", "鄭朝允": "101056", "王思翰": "102720", "張倉惟": "104031",
    "陳柏偉": "315444", "黃鼎鈞": "315452", "張獻元": "315460", "劉秉彥": "626105",
    "葉建寬": "105234", "葉立浩": "105430", "洪晨惠": "636042",
    "許毓軨": "101696", "蘇奕嘉": "102180",
}

ROOM_CODES = {"H1": "xa-Hybrid1", "H2": "xa-Hybrid2", "C1": "xa-CATH1", "C2": "xa-CATH2"}

DIAG_IDS = {
    "CAD": "PDI20090908120009",
    "CHF": "PDI20090908120050",
    "PAOD": "PDI20110104080726",
    "Carotid stenting": "PDI20110104080741",
    "Angina pectoris": "PDI20090908120002",
    "EP study/RFA > Sinus nodal dysfunction": "PDI20090908120038",
    "EP study/RFA > pAf": "PDI20090908120040",
    "EP study/RFA > PSVT": "PDI20090908120033",
    "EP study/RFA > AV nodal dysfunction": "PDI20090908120039",
    "AMI > Others:NSTEMI": "PDI20090908120011",
}
PROC_IDS = {
    "Left heart cath.": "PHC20090907120001",
    "PCI": "PHC20090907120004",
    "PPM": "PHC20170406095748",
    "RF ablation": "PHC20090907120009",
    "CRT": "PHC20170406100014",
    "PTA": "PHC20090907120007",
    "Both-sided cath.": "PHC20090907120003",
    "Carotid angiography + stenting": "PHC20090907120013",
}

# Thu schedule:
# AM C2=柯呈諭  C1=黃鼎鈞(浩、晨)  H2=陳柏偉
# PM H2=黃睦翔(結構)  C1=黃鼎鈞(浩、晨)
# 跳過: 沈桂英(非導管床), 陳郭明珠(HF AE), 王劉愛雪(Cardioversion), 黃鉦傑(不在排序)

PATIENTS = [
    # AM - 柯呈諭 C2 (2 patients)
    {"name": "施金士", "chart": "13531746", "doctor": "柯呈諭", "room": "C2",
     "time": "0600", "second": None,
     "diagnosis": "Carotid stenting", "procedure": "Carotid angiography + stenting"},
    {"name": "郭惠蘭", "chart": "13940053", "doctor": "柯呈諭", "room": "C2",
     "time": "0601", "second": None,
     "diagnosis": "CHF", "procedure": "Left heart cath."},
    # AM - 陳柏偉 H2 (1 patient)
    {"name": "陳秀玲", "chart": "07575235", "doctor": "陳柏偉", "room": "H2",
     "time": "0600", "second": None,
     "diagnosis": "PAOD", "procedure": "PTA"},
    # AM - 黃鼎鈞 C1 (2nd=葉立浩, note=晨, 3 patients)
    {"name": "邱調水", "chart": "19990690", "doctor": "黃鼎鈞", "room": "C1",
     "time": "0600", "second": "葉立浩",
     "diagnosis": "CHF", "procedure": "CRT", "note": "晨"},
    {"name": "傅榮珂", "chart": "00050212", "doctor": "黃鼎鈞", "room": "C1",
     "time": "0601", "second": "葉立浩",
     "diagnosis": "EP study/RFA > Sinus nodal dysfunction", "procedure": "PPM", "note": "晨"},
    {"name": "林素珍", "chart": "02050962", "doctor": "黃鼎鈞", "room": "C1",
     "time": "0602", "second": "葉立浩",
     "diagnosis": "EP study/RFA > PSVT", "procedure": "RF ablation", "note": "晨"},
    # PM - 黃睦翔 H2 (1 patient)
    {"name": "楊明樂", "chart": "08863646", "doctor": "黃睦翔", "room": "H2",
     "time": "1730", "second": None,
     "diagnosis": "CAD", "procedure": "Left heart cath.", "note": "CAD3VD, Syntax 33"},
    # PM - 黃鼎鈞 C1 (2nd=葉立浩, note=晨, 2 patients, 續等)
    {"name": "張皓傑", "chart": "14650529", "doctor": "黃鼎鈞", "room": "C1",
     "time": "1730", "second": "葉立浩",
     "diagnosis": "Angina pectoris", "procedure": "Left heart cath.", "note": "晨"},
    {"name": "曾松棋", "chart": "04852274", "doctor": "黃鼎鈞", "room": "C1",
     "time": "1731", "second": "葉立浩",
     "diagnosis": "EP study/RFA > AV nodal dysfunction", "procedure": "PPM", "note": "晨"},
]

LOG = []

def log(msg):
    LOG.append(msg)
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode())


def login(page):
    page.goto(f"{BASE_URL}/")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.fill('input[name="userid"]', ACCOUNT)
    page.fill('input[name="password"]', PASSWORD)
    page.click('input[type="submit"], button[type="submit"]')
    page.wait_for_load_state("networkidle", timeout=10000)
    log("Login OK")


def set_date_and_query(page):
    page.goto(SCHEDULE_URL)
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(1)
    page.evaluate(f'''() => {{
        let d1 = document.getElementById("daySelect1");
        let d2 = document.getElementById("daySelect2");
        d1.removeAttribute("readonly"); d2.removeAttribute("readonly");
        d1.value = "{CATHLAB_DATE}"; d2.value = "{CATHLAB_DATE}";
    }}''')
    time.sleep(0.3)
    page.evaluate('''() => {
        document.HCO1WForm.buttonName.name = "QRY";
        document.HCO1WForm.buttonName.value = "QRY";
        document.HCO1WForm.submit();
    }''')
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(1)


def get_existing_charts(page):
    charts = page.evaluate('''() => {
        let c = [];
        document.querySelectorAll("#row tr").forEach(r => {
            let el = r.querySelector("#hes_patno");
            if (el && el.value) c.push(el.value.trim());
        });
        if (c.length === 0) {
            document.querySelectorAll("#row td").forEach(td => {
                let t = td.textContent.trim();
                if (/^\\d{7,8}$/.test(t)) c.push(t);
            });
        }
        return c;
    }''')
    return set(charts)


def build_json(name, item_id):
    if not item_id:
        return ""
    return json.dumps([{"name": name, "id": item_id}], ensure_ascii=False)


def add_patient(page, patient, existing_charts):
    chart = patient["chart"]
    if chart in existing_charts:
        log(f"  SKIP (exists): {patient['name']} ({chart})")
        return "skip"

    doctor_code = DOCTOR_CODES.get(patient["doctor"], "")
    second_code = DOCTOR_CODES.get(patient["second"]) if patient["second"] else ""
    room_code = ROOM_CODES.get(patient["room"], "")

    diag = patient["diagnosis"]
    proc = patient["procedure"]
    diag_id = DIAG_IDS.get(diag, "")
    proc_id = PROC_IDS.get(proc, "")
    diag_json = build_json(diag, diag_id) if diag_id else ""
    proc_json = build_json(proc, proc_id) if proc_id else ""
    note = patient.get("note", "")

    if proc and not proc_id:
        note = (note + " " + proc).strip() if note else proc

    log(f"  ADD: {patient['name']} ({chart}) {patient['room']} {patient['time']} {patient['doctor']}")

    try:
        page.click('input[name="patno2"]')
        time.sleep(0.5)

        page.fill('input[name="patno2"]', chart)
        time.sleep(0.3)
        page.press('input[name="patno2"]', 'Enter')
        time.sleep(2)

        page.evaluate(f'() => {{ document.querySelector(\'input[name="inspectiondate"]\').value = "{CATHLAB_DATE}"; }}')
        page.fill('input[name="inspectiontime"]', patient["time"])
        page.select_option('select[name="examroom"]', value=room_code)
        page.select_option('select[name="attendingdoctor1"]', value=doctor_code)
        if second_code:
            page.select_option('select[name="attendingdoctor2"]', value=second_code)

        page.evaluate('''([dj, pj]) => {
            if (dj) document.querySelector('[name="pdijson"]').value = dj;
            if (pj) document.querySelector('[name="phcjson"]').value = pj;
        }''', [diag_json, proc_json])

        if note:
            page.fill('input[name="note"]', note)

        time.sleep(0.3)

        page.evaluate('''() => {
            document.HCO1WForm.buttonName.name = "ADD";
            document.HCO1WForm.buttonName.value = "ADD";
            document.HCO1WForm.submit();
        }''')
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(1)

        log(f"    ADD OK")
        return "ok"

    except Exception as e:
        log(f"    ERROR: {e}")
        page.screenshot(path=f"cathlab_0409_error_{chart}.png")
        return "error"


def fix_diag(page, patient):
    chart = patient["chart"]
    diag = patient["diagnosis"]
    proc = patient["procedure"]
    diag_id = DIAG_IDS.get(diag, "")
    proc_id = PROC_IDS.get(proc, "")

    if not diag_id and not proc_id:
        return

    diag_json = build_json(diag, diag_id) if diag_id else ""
    proc_json = build_json(proc, proc_id) if proc_id else ""

    found = page.evaluate('''(chart) => {
        let rows = document.querySelectorAll("#row tr");
        for (let row of rows) {
            let el = row.querySelector("#hes_patno");
            if (el && el.value === chart) { row.click(); return true; }
        }
        return false;
    }''', chart)

    if not found:
        log(f"    UPT: Row not found for {chart}")
        return

    time.sleep(0.5)

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
    }''', [diag_json, proc_json, diag, proc])

    time.sleep(0.3)

    page.evaluate('''() => {
        document.HCO1WForm.buttonName.name = "UPT";
        document.HCO1WForm.buttonName.value = "UPT";
        document.HCO1WForm.submit();
    }''')
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1)
    log(f"    UPT OK: {patient['name']}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()

        log(f"=== Cathlab Key-in: {CATHLAB_DATE} ({len(PATIENTS)} patients) ===")

        login(page)
        set_date_and_query(page)
        existing = get_existing_charts(page)
        log(f"Existing: {existing}")

        # Phase 1: ADD all patients
        log("\n--- Phase 1: ADD ---")
        results = {"ok": 0, "skip": 0, "error": 0}
        for i, pt in enumerate(PATIENTS):
            if i > 0:
                set_date_and_query(page)
                existing = get_existing_charts(page)
            r = add_patient(page, pt, existing)
            results[r] += 1

        # Phase 2: UPT to fix pdijson/phcjson
        log("\n--- Phase 2: UPT (fix diag/proc) ---")
        for i, pt in enumerate(PATIENTS):
            if pt["diagnosis"] or pt["procedure"]:
                set_date_and_query(page)
                fix_diag(page, pt)

        # Final verification
        log("\n--- Verification ---")
        set_date_and_query(page)
        final = get_existing_charts(page)
        page.screenshot(path="cathlab_0409_final.png")

        for pt in PATIENTS:
            s = "OK" if pt["chart"] in final else "MISSING"
            log(f"  {pt['name']} ({pt['chart']}): {s}")

        log(f"\nResults: {results['ok']} added, {results['skip']} skipped, {results['error']} errors")
        log(f"Total entries: {len(final)}")

        with open("cathlab_0409_log.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(LOG))

        time.sleep(3)
        browser.close()


if __name__ == "__main__":
    main()
