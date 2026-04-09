"""
20260407 入院 → 20260408 心導管排程 key-in
使用 Playwright 自動化 WEBCVIS 系統
"""
import time
import json
import os
from playwright.sync_api import sync_playwright

BASE_URL = "http://cardiopacs01.hosp.ncku:8080/WEBCVIS"
SCHEDULE_URL = f"{BASE_URL}/HCO/HCO1W001.do"
DIAG_POPUP_URL = f"{BASE_URL}/HCO/HCO1N002.do?pageid=HCO1N002&pdijson="
PROC_POPUP_URL = f"{BASE_URL}/HCO/HCO1N004.do?pageid=HCO1N004&phcjson="
ACCOUNT = "107614"
PASSWORD = "107614"
CATHLAB_DATE = "2026/04/08"
LOG_FILE = "cathlab_keyin_log.txt"

# 醫師代碼
DOCTOR_CODES = {
    "詹世鴻": "023835", "許志新": "032894", "陳儒逸": "033047", "劉嚴文": "036030",
    "陳柏升": "044547", "黃睦翔": "046226", "柯呈諭": "049499", "李文煌": "053120",
    "李柏增": "053146", "林佳凌": "054143", "陳則瑋": "054185", "廖瑀": "054193",
    "陳昭佑": "100922", "鄭朝允": "101056", "王思翰": "102720", "張倉惟": "104031",
    "陳柏偉": "315444", "黃鼎鈞": "315452", "張獻元": "315460", "劉秉彥": "626105",
    # 第二主刀
    "葉建寬": "105234", "葉立浩": "105430", "洪晨惠": "636042",
    "許毓軨": "101696", "蘇奕嘉": "102180",
}

ROOM_CODES = {
    "H1": "xa-Hybrid1", "H2": "xa-Hybrid2",
    "C1": "xa-CATH1",   "C2": "xa-CATH2",
}

# 需要新增的病人 (按 AM → PM → 非時段 順序)
PATIENTS = [
    # AM
    {"name": "施焱騰", "chart": "17131818", "doctor": "詹世鴻", "room": "H1",
     "time": "0600", "second": "許毓軨",
     "diagnosis": "CAD", "procedure": "Left heart cath."},
    {"name": "蔡尚辰", "chart": "17196515", "doctor": "林佳凌", "room": "H2",
     "time": "0600", "second": None,
     "diagnosis": "AMI > Others:NSTEMI", "procedure": "Left heart cath."},
    {"name": "陳銀如", "chart": "05569348", "doctor": "陳儒逸", "room": "C1",
     "time": "0600", "second": "葉建寬",
     "diagnosis": "CAD", "procedure": "Left heart cath."},
    # PM
    {"name": "陳玉靜", "chart": "16227744", "doctor": "詹世鴻", "room": "H1",
     "time": "1730", "second": "許毓軨",
     "diagnosis": "EP study/RFA > Sinus nodal dysfunction", "procedure": "PPM"},
    {"name": "吳苾芳", "chart": "05449248", "doctor": "廖瑀", "room": "C1",
     "time": "1730", "second": None,
     "diagnosis": "EP study/RFA > pAf", "procedure": "RF ablation"},
    {"name": "周振豪", "chart": "07420217", "doctor": "廖瑀", "room": "C1",
     "time": "1731", "second": None,
     "diagnosis": "CAD", "procedure": "Left heart cath."},
    # 非時段
    {"name": "王劉愛雪", "chart": "01637432", "doctor": "黃鼎鈞", "room": "H1",
     "time": "1800", "second": None,
     "diagnosis": "EP study/RFA > pAf", "procedure": "Cardioversion"},
]

log_lines = []

def log(msg):
    log_lines.append(msg)
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode())


def save_log():
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))


def login(page):
    page.goto(f"{BASE_URL}/")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.fill('input[name="userid"]', ACCOUNT)
    page.fill('input[name="password"]', PASSWORD)
    page.click('input[type="submit"], button[type="submit"]')
    page.wait_for_load_state("networkidle", timeout=10000)
    log("Login OK")


def set_date_and_query(page):
    """Set date fields and click Query"""
    page.goto(SCHEDULE_URL)
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(1)

    # daySelect1/daySelect2 are readonly — remove readonly via JS
    page.evaluate(f'''() => {{
        let d1 = document.getElementById("daySelect1");
        let d2 = document.getElementById("daySelect2");
        d1.removeAttribute("readonly");
        d2.removeAttribute("readonly");
        d1.value = "{CATHLAB_DATE}";
        d2.value = "{CATHLAB_DATE}";
    }}''')
    time.sleep(0.3)

    # Click QueryButton (it's a <button>, not <input>)
    page.evaluate('''() => {
        document.HCO1WForm.buttonName.name = "QRY";
        document.HCO1WForm.buttonName.value = "QRY";
        document.HCO1WForm.submit();
    }''')
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(1)
    log(f"Query date: {CATHLAB_DATE}")


def get_existing_charts(page):
    """Read existing chart numbers from the schedule table"""
    charts = page.evaluate('''() => {
        let charts = [];
        let rows = document.querySelectorAll("#row tr");
        rows.forEach(row => {
            let patnoEl = row.querySelector("[id='hes_patno']") ||
                          row.querySelector("input[id='hes_patno']");
            if (patnoEl) {
                let v = patnoEl.value || patnoEl.textContent;
                if (v) charts.push(v.trim());
            }
        });
        // Also try reading from visible text
        if (charts.length === 0) {
            let tds = document.querySelectorAll("#row td");
            tds.forEach(td => {
                let text = td.textContent.trim();
                if (/^\\d{7,8}$/.test(text)) {
                    charts.push(text);
                }
            });
        }
        return charts;
    }''')
    existing = set(charts)
    log(f"Existing charts: {existing}")
    return existing


def scrape_popup_ids(page, popup_url, field_type):
    """
    Navigate to diagnosis/procedure popup page and scrape option IDs.
    Returns {name: id} mapping.
    """
    page.goto(popup_url)
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(1)

    # The popup pages have tree structures with checkboxes
    # Each option has an id and name attribute
    mapping = page.evaluate('''() => {
        let result = {};
        // Try various selectors for tree items
        // Common patterns: <input type="checkbox" name="..." value="...">
        // Or <span onclick="..."> with data attributes
        // Or <li> with data attributes

        // Method 1: Look for all checkbox/radio inputs
        document.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach(el => {
            let label = el.parentElement ? el.parentElement.textContent.trim() : '';
            let id = el.value || el.id || '';
            if (label && id) result[label] = id;
        });

        // Method 2: Look for clickable tree items with IDs
        document.querySelectorAll('[id*="PDI"], [id*="PHC"]').forEach(el => {
            let text = el.textContent.trim();
            let id = el.id;
            if (text && id) result[text] = id;
        });

        // Method 3: Look for spans/links in the tree
        document.querySelectorAll('span.dynatree-title, a.dynatree-title, .tree-label').forEach(el => {
            let text = el.textContent.trim();
            let node = el.closest('[data-key]') || el.closest('[id]');
            if (node) {
                let id = node.getAttribute('data-key') || node.id;
                if (text && id) result[text] = id;
            }
        });

        // Method 4: Check if there's a global tree data structure
        if (typeof treeData !== 'undefined') {
            result['__treeData'] = JSON.stringify(treeData).substring(0, 500);
        }

        // Method 5: Dump page info for debugging
        result['__bodyLength'] = document.body.innerHTML.length;
        result['__title'] = document.title;

        return result;
    }''')

    log(f"Scraped {field_type}: {len(mapping)} entries (title: {mapping.get('__title', '?')})")

    # Save raw scrape for debugging
    with open(f'_scraped_{field_type}.json', 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    return mapping


def scrape_popup_full(page, popup_url, field_type):
    """More thorough popup scraping - save HTML and extract all possible IDs"""
    page.goto(popup_url)
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(2)

    # Save the popup page HTML for analysis
    html = page.content()
    with open(f'_popup_{field_type}.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # Try to extract IDs from the HTML
    import re
    mapping = {}

    # Pattern: items with PDI or PHC IDs
    # e.g., PDI20090908120009 or PHC20090908120009
    prefix = 'PDI' if field_type == 'diag' else 'PHC'
    id_pattern = rf'{prefix}\d+'
    ids_found = set(re.findall(id_pattern, html))

    # Try to find name-id pairs
    # Common pattern: {"name":"CAD","id":"PDI..."}
    json_pairs = re.findall(r'"name"\s*:\s*"([^"]+)"\s*,\s*"id"\s*:\s*"(' + prefix + r'\d+)"', html)
    for name, pid in json_pairs:
        mapping[name] = pid

    # Also look for tree nodes: text followed by ID
    # Pattern: >text</span>...PDI_ID or similar
    tree_items = re.findall(r'>([^<]+)</(?:span|a|td|div)[^>]*>[^<]*(' + prefix + r'\d+)', html)
    for text, pid in tree_items:
        text = text.strip()
        if text and len(text) < 100:
            mapping[text] = pid

    # Check if items are in checkbox values
    checkbox_items = re.findall(r'value="(' + prefix + r'\d+)"[^>]*>([^<]+)', html)
    for pid, text in checkbox_items:
        mapping[text.strip()] = pid

    log(f"Full scrape {field_type}: {len(mapping)} name-id pairs, {len(ids_found)} total IDs found")
    return mapping, ids_found


def build_json_value(name, item_id):
    """Build the JSON string for pdijson/phcjson"""
    return json.dumps([{"name": name, "id": item_id}], ensure_ascii=False)


def find_best_match(target_name, mapping):
    """Find the best matching ID for a diagnosis/procedure name"""
    # Exact match
    if target_name in mapping:
        return mapping[target_name]

    # Case-insensitive match
    for key, val in mapping.items():
        if key.lower() == target_name.lower():
            return val

    # Partial match (target contained in key or vice versa)
    for key, val in mapping.items():
        if target_name in key or key in target_name:
            return val

    # Strip leading spaces and try again
    stripped_target = target_name.strip().lstrip()
    for key, val in mapping.items():
        stripped_key = key.strip().lstrip()
        if stripped_target == stripped_key:
            return val
        if stripped_target in stripped_key or stripped_key in stripped_target:
            return val

    return None


def add_patient(page, patient, diag_map, proc_map, existing_charts):
    """Add a single patient to the schedule"""
    chart = patient["chart"]
    name = patient["name"]

    if chart in existing_charts:
        log(f"  SKIP (already exists): {name} ({chart})")
        return "skip"

    doctor_code = DOCTOR_CODES.get(patient["doctor"], "")
    second_code = DOCTOR_CODES.get(patient["second"]) if patient["second"] else ""
    room_code = ROOM_CODES.get(patient["room"], "")

    if not doctor_code:
        log(f"  ERROR: No doctor code for {patient['doctor']}")
        return "error"

    log(f"\n  Adding: {name} ({chart})")
    log(f"    Doctor: {patient['doctor']}({doctor_code}), Room: {patient['room']}({room_code})")
    log(f"    Time: {patient['time']}, Diag: {patient['diagnosis']}, Proc: {patient['procedure']}")

    # Find diagnosis and procedure IDs
    diag_id = find_best_match(patient["diagnosis"], diag_map) if patient["diagnosis"] else None
    proc_id = find_best_match(patient["procedure"], proc_map) if patient["procedure"] else None

    diag_json = build_json_value(patient["diagnosis"], diag_id) if diag_id else '[]'
    proc_json = build_json_value(patient["procedure"], proc_id) if proc_id else '[]'

    if patient["diagnosis"] and not diag_id:
        log(f"    WARNING: No ID found for diagnosis '{patient['diagnosis']}'")
    if patient["procedure"] and not proc_id:
        log(f"    WARNING: No ID found for procedure '{patient['procedure']}'")

    log(f"    pdijson: {diag_json}")
    log(f"    phcjson: {proc_json}")

    try:
        # Step 1: Click patno2 to clear form
        page.click('input[name="patno2"]')
        time.sleep(0.5)

        # Step 2: Fill chart number
        page.fill('input[name="patno2"]', chart)
        time.sleep(0.3)

        # Step 3: Press Enter to trigger AJAX patient lookup
        page.press('input[name="patno2"]', 'Enter')
        time.sleep(2)  # Wait for AJAX response

        # Step 4: Fill inspection date
        page.evaluate(f'''() => {{
            document.querySelector('input[name="inspectiondate"]').value = "{CATHLAB_DATE}";
        }}''')

        # Step 5: Fill inspection time
        page.fill('input[name="inspectiontime"]', patient["time"])

        # Step 6: Select exam room
        page.select_option('select[name="examroom"]', value=room_code)

        # Step 7: Select attending doctor 1
        page.select_option('select[name="attendingdoctor1"]', value=doctor_code)

        # Step 8: Select attending doctor 2 (if applicable)
        if second_code:
            page.select_option('select[name="attendingdoctor2"]', value=second_code)

        # Step 9: Set pdijson and phcjson via JS (use evaluate with args for safe escaping)
        page.evaluate('''([dj, pj]) => {
            document.querySelector('[name="pdijson"]').value = dj;
            document.querySelector('[name="phcjson"]').value = pj;
        }''', [diag_json, proc_json])

        time.sleep(0.5)

        # Screenshot before adding
        page.screenshot(path=f"cathlab_pre_add_{chart}.png")

        # Step 10: Click Add button via JS (same as the jQuery handler)
        page.evaluate('''() => {
            document.HCO1WForm.buttonName.name = "ADD";
            document.HCO1WForm.buttonName.value = "ADD";
            document.HCO1WForm.submit();
        }''')

        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(1)

        # Check for error messages
        msg = page.evaluate('''() => {
            let msgEl = document.querySelector('.message, #message, [class*="error"], [class*="alert"]');
            return msgEl ? msgEl.textContent.trim() : '';
        }''')

        if msg:
            log(f"    Server message: {msg}")

        # Screenshot after adding
        page.screenshot(path=f"cathlab_post_add_{chart}.png")
        log(f"    ADD submitted for {name}")

        return "ok"

    except Exception as e:
        log(f"    ERROR adding {name}: {e}")
        page.screenshot(path=f"cathlab_error_{chart}.png")
        return "error"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        log("=" * 60)
        log(f"  Cathlab Key-in: {CATHLAB_DATE}")
        log(f"  Patients: {len(PATIENTS)}")
        log("=" * 60)

        # Step 1: Login
        log("\n[1] Login...")
        login(page)

        # Step 2: Navigate and query
        log("\n[2] Set date and query...")
        set_date_and_query(page)
        page.screenshot(path="cathlab_initial_query.png")

        # Step 3: Get existing charts
        log("\n[3] Check existing entries...")
        existing_charts = get_existing_charts(page)

        # Step 4: Scrape diagnosis IDs from popup
        log("\n[4] Scraping diagnosis IDs...")
        diag_map, diag_ids = scrape_popup_full(page, DIAG_POPUP_URL, "diag")
        log(f"    Diagnosis mapping: {json.dumps(diag_map, ensure_ascii=False)[:500]}")

        # Step 5: Scrape procedure IDs from popup
        log("\n[5] Scraping procedure IDs...")
        proc_map, proc_ids = scrape_popup_full(page, PROC_POPUP_URL, "proc")
        log(f"    Procedure mapping: {json.dumps(proc_map, ensure_ascii=False)[:500]}")

        # Step 6: Go back to schedule page and add patients
        log("\n[6] Adding patients...")
        set_date_and_query(page)

        results = {"ok": 0, "skip": 0, "error": 0}
        for i, patient in enumerate(PATIENTS):
            log(f"\n--- Patient {i+1}/{len(PATIENTS)} ---")

            # Re-query to ensure we're on the right page with fresh data
            if i > 0:
                # After each ADD, the page reloads. Re-set date and query.
                set_date_and_query(page)
                existing_charts = get_existing_charts(page)

            result = add_patient(page, patient, diag_map, proc_map, existing_charts)
            results[result] = results.get(result, 0) + 1

        # Step 7: Final verification
        log("\n[7] Final verification...")
        set_date_and_query(page)
        final_charts = get_existing_charts(page)
        page.screenshot(path="cathlab_final.png")

        # Check all patients are in the final list
        log("\nVerification:")
        for patient in PATIENTS:
            status = "OK" if patient["chart"] in final_charts else "MISSING"
            log(f"  {patient['name']} ({patient['chart']}): {status}")

        log(f"\n{'=' * 60}")
        log(f"  Results: {results['ok']} added, {results['skip']} skipped, {results['error']} errors")
        log(f"  Total entries now: {len(final_charts)}")
        log(f"{'=' * 60}")

        save_log()

        log("Screenshots and log saved. Auto-closing in 5 seconds...")
        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    main()
