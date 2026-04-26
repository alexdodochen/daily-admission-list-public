"""Generic cathlab keyin driver — replaces per-date `cathlab_keyin_MMDD.py` scripts.

Usage:
  python cathlab_keyin.py cathlab_patients_YYYYMMDD.json

JSON schema (list of patient dicts):
  [
    {"cathlab_date": "2026/04/28", "name": "陳爽", "chart": "04668242",
     "doctor": "黃睦翔", "second": null, "room": "C2", "time": "1801",
     "diagnosis": "CAD", "procedure": "Left heart cath.", "note": ""},
    ...
  ]

Required fields: cathlab_date, name, chart, doctor, room, time
Optional: second, diagnosis, procedure, note (default empty)

Two-phase execution:
  Phase 1 — ADD: dedupe by chart against current WEBCVIS for each date.
  Phase 2 — UPT: fix pdijson/phcjson (some fields don't stick on first ADD).
  Verification: requery each date and report OK/MISSING per patient.

Logs go to `_cathlab_keyin_<input_basename>.log`.
"""
import sys, os, json, time
from playwright.sync_api import sync_playwright

BASE_URL = "http://cardiopacs01.hosp.ncku:8080/WEBCVIS"
SCHEDULE_URL = f"{BASE_URL}/HCO/HCO1W001.do"
ACCOUNT, PASSWORD = "107614", "107614"

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

# IDs are loaded from cathlab_id_maps.json (66 diag + 22 proc verified entries).
# Don't hardcode — wrong IDs would push wrong records into WEBCVIS.
DIAG_IDS, PROC_IDS = {}, {}
def _load_id_maps():
    p = os.path.join(os.path.dirname(__file__), 'cathlab_id_maps.json')
    if not os.path.exists(p):
        raise SystemExit("cathlab_id_maps.json missing — required for ID lookup")
    with open(p, 'r', encoding='utf-8') as f:
        m = json.load(f)
    DIAG_IDS.update(m.get('diag', {}))
    PROC_IDS.update(m.get('proc', {}))
_load_id_maps()

LOG = []
def log(m):
    try: print(m)
    except UnicodeEncodeError: print(m.encode('ascii','replace').decode())
    LOG.append(m)


def login(page):
    page.goto(f"{BASE_URL}/")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.fill('input[name="userid"]', ACCOUNT)
    page.fill('input[name="password"]', PASSWORD)
    page.click('input[type="submit"], button[type="submit"]')
    page.wait_for_load_state("networkidle", timeout=10000)


def query(page, d):
    page.goto(SCHEDULE_URL)
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(1)
    page.evaluate(f'''() => {{
        let d1=document.getElementById("daySelect1"), d2=document.getElementById("daySelect2");
        d1.removeAttribute("readonly"); d2.removeAttribute("readonly");
        d1.value="{d}"; d2.value="{d}";
    }}''')
    time.sleep(0.3)
    page.evaluate('''() => {
        document.HCO1WForm.buttonName.name="QRY";
        document.HCO1WForm.buttonName.value="QRY";
        document.HCO1WForm.submit();
    }''')
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(1)


def existing_charts(page):
    return set(page.evaluate('''() => {
        let c=[]; document.querySelectorAll("#row tr").forEach(r=>{
            let el=r.querySelector("#hes_patno"); if(el && el.value) c.push(el.value.trim());
        }); return c;
    }'''))


def _build_json(name, item_id):
    if not item_id: return ""
    return json.dumps([{"name": name, "id": item_id}], ensure_ascii=False)


def add_patient(page, p, existing):
    if p['chart'] in existing:
        log(f"  SKIP (exists): {p['name']} ({p['chart']}) on {p['cathlab_date']}")
        return 'skip'
    dcode = DOCTOR_CODES.get(p['doctor'], '')
    scode = DOCTOR_CODES.get(p.get('second')) if p.get('second') else ''
    rcode = ROOM_CODES.get(p['room'], '')
    diag = p.get('diagnosis', ''); proc = p.get('procedure', '')
    diag_json = _build_json(diag, DIAG_IDS.get(diag, ''))
    proc_json = _build_json(proc, PROC_IDS.get(proc, ''))
    note = p.get('note', '')
    if not dcode:
        log(f"  ERROR: 醫師代碼缺失 {p['doctor']} → {p['name']}"); return 'error'
    if not rcode:
        log(f"  ERROR: room 代碼缺失 {p['room']} → {p['name']}"); return 'error'

    log(f"  ADD: {p['name']} ({p['chart']}) {p['cathlab_date']} {p['room']} {p['time']} {p['doctor']}")
    try:
        page.click('input[name="patno2"]'); time.sleep(0.5)
        page.fill('input[name="patno2"]', p['chart']); time.sleep(0.3)
        page.press('input[name="patno2"]', 'Enter'); time.sleep(2)
        page.evaluate(f'() => {{ document.querySelector(\'input[name="inspectiondate"]\').value="{p["cathlab_date"]}"; }}')
        page.fill('input[name="inspectiontime"]', p['time'])
        page.select_option('select[name="examroom"]', value=rcode)
        page.select_option('select[name="attendingdoctor1"]', value=dcode)
        if scode:
            page.select_option('select[name="attendingdoctor2"]', value=scode)
        page.evaluate('''([dj,pj]) => {
            if(dj) document.querySelector('[name="pdijson"]').value=dj;
            if(pj) document.querySelector('[name="phcjson"]').value=pj;
        }''', [diag_json, proc_json])
        if note: page.fill('input[name="note"]', note)
        time.sleep(0.3)
        page.evaluate('''() => {
            document.HCO1WForm.buttonName.name="ADD";
            document.HCO1WForm.buttonName.value="ADD";
            document.HCO1WForm.submit();
        }''')
        page.wait_for_load_state("networkidle", timeout=15000); time.sleep(1)
        log(f"    ADD OK"); return 'ok'
    except Exception as e:
        log(f"    ERROR: {e}")
        page.screenshot(path=f"_cathlab_err_{p['chart']}.png"); return 'error'


def fix_diag(page, p):
    diag = p.get('diagnosis', ''); proc = p.get('procedure', '')
    if not diag and not proc: return
    diag_json = _build_json(diag, DIAG_IDS.get(diag, ''))
    proc_json = _build_json(proc, PROC_IDS.get(proc, ''))
    if not diag_json and not proc_json: return
    found = page.evaluate('''(c) => {
        let rows=document.querySelectorAll("#row tr");
        for(let r of rows){let el=r.querySelector("#hes_patno");
            if(el && el.value===c){r.click(); return true;}}
        return false;
    }''', p['chart'])
    if not found:
        log(f"    UPT: row not found {p['chart']}"); return
    time.sleep(0.5)
    page.evaluate('''([dj,pj,dt,pt]) => {
        if(dj){document.querySelector('[name="pdijson"]').value=dj;
            let f=document.querySelector('[name="prediagnosisitem"]'); if(f)f.value=dt;}
        if(pj){document.querySelector('[name="phcjson"]').value=pj;
            let f=document.querySelector('[name="preheartcatheter"]'); if(f)f.value=pt;}
    }''', [diag_json, proc_json, diag, proc])
    time.sleep(0.3)
    page.evaluate('''() => {
        document.HCO1WForm.buttonName.name="UPT";
        document.HCO1WForm.buttonName.value="UPT";
        document.HCO1WForm.submit();
    }''')
    page.wait_for_load_state("networkidle", timeout=15000); time.sleep(1)
    log(f"    UPT OK: {p['name']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python cathlab_keyin.py <patients.json>"); sys.exit(1)
    json_path = sys.argv[1]
    with open(json_path, 'r', encoding='utf-8') as f:
        patients = json.load(f)
    log(f"=== cathlab keyin: {len(patients)} patients from {json_path} ===")

    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=False, slow_mo=200)
        page = b.new_context(viewport={"width":1400,"height":900}).new_page()
        login(page)

        results = {'ok':0, 'skip':0, 'error':0}
        log("\n--- Phase 1: ADD ---")
        for p in patients:
            query(page, p['cathlab_date'])
            ex = existing_charts(page)
            results[add_patient(page, p, ex)] += 1

        log("\n--- Phase 2: UPT (fix diag/proc) ---")
        for p in patients:
            query(page, p['cathlab_date'])
            fix_diag(page, p)

        log("\n--- Verification ---")
        by_date = {}
        for p in patients:
            by_date.setdefault(p['cathlab_date'], []).append(p)
        for d, pts in by_date.items():
            query(page, d)
            final = existing_charts(page)
            log(f"[{d}] WEBCVIS total: {len(final)}")
            for p in pts:
                s = 'OK' if p['chart'] in final else 'MISSING'
                log(f"  {p['name']} ({p['chart']}): {s}")

        log(f"\nResults: {results['ok']} added, {results['skip']} skipped, {results['error']} errors")
        base = os.path.splitext(os.path.basename(json_path))[0]
        with open(f"_cathlab_keyin_{base}.log", "w", encoding="utf-8") as f:
            f.write("\n".join(LOG))
        time.sleep(2); b.close()


if __name__ == "__main__":
    main()
