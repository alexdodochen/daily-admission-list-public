"""
驗證導管排程：比對入院序 (Sheet N-U) vs WEBCVIS 隔日排程
用法: python verify_cathlab.py 20260409
  → 讀取 20260409 入院序，查 20260410 WEBCVIS 排程，輸出比對結果
"""
import sys
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from gsheet_utils import get_worksheet, read_all_values

BASE_URL = "http://cardiopacs01.hosp.ncku:8080/WEBCVIS"
SCHEDULE_URL = f"{BASE_URL}/HCO/HCO1W001.do"
ACCOUNT = "107614"
PASSWORD = "107614"

SKIP_KEYWORDS = ["不排程", "檢查"]


def get_cathlab_date(admission_date_str):
    """入院日+1 = 導管日"""
    dt = datetime.strptime(admission_date_str, "%Y%m%d")
    cathlab_dt = dt + timedelta(days=1)
    return cathlab_dt.strftime("%Y/%m/%d"), cathlab_dt.strftime("%m%d")


def read_ordering(sheet_name):
    """讀取 N-U 入院序，回傳病人列表"""
    ws = get_worksheet(sheet_name)
    if not ws:
        raise ValueError(f"找不到工作表: {sheet_name}")

    data = read_all_values(ws)
    patients = []

    for row in data[1:]:  # skip header
        if len(row) > 13 and row[13]:  # col N (index 13) = 序號
            seq = row[13]
            doctor = row[14] if len(row) > 14 else ''
            name = row[15] if len(row) > 15 else ''
            note = row[16] if len(row) > 16 else ''
            chart = row[17] if len(row) > 17 else ''
            diag = row[18] if len(row) > 18 else ''
            cath = row[19] if len(row) > 19 else ''

            should_skip = any(kw in note for kw in SKIP_KEYWORDS)

            patients.append({
                'seq': seq,
                'doctor': doctor,
                'name': name,
                'note': note,
                'chart': chart,
                'diag': diag,
                'cath': cath,
                'skip': should_skip,
            })
        else:
            if not row[13] if len(row) > 13 else True:
                break

    return patients


def query_webcvis(cathlab_date):
    """連線 WEBCVIS 查詢指定日期排程，回傳已排程病歷號 set"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()

        # Login
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle", timeout=15000)
        page.fill('input[name="userid"]', ACCOUNT)
        page.fill('input[name="password"]', PASSWORD)
        page.click('input[type="submit"], button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=10000)

        # Query
        page.goto(SCHEDULE_URL)
        page.wait_for_load_state("networkidle", timeout=10000)
        time.sleep(1)
        page.evaluate(f'''() => {{
            let d1 = document.getElementById("daySelect1");
            let d2 = document.getElementById("daySelect2");
            d1.removeAttribute("readonly"); d2.removeAttribute("readonly");
            d1.value = "{cathlab_date}"; d2.value = "{cathlab_date}";
        }}''')
        time.sleep(0.3)
        page.evaluate('''() => {
            document.HCO1WForm.buttonName.name = "QRY";
            document.HCO1WForm.buttonName.value = "QRY";
            document.HCO1WForm.submit();
        }''')
        page.wait_for_load_state("networkidle", timeout=10000)
        time.sleep(1)

        # Get existing charts
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

        browser.close()
        return set(charts)


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_cathlab.py <admission_date>")
        print("Example: python verify_cathlab.py 20260409")
        sys.exit(1)

    admission_date = sys.argv[1]
    cathlab_date, cathlab_mmdd = get_cathlab_date(admission_date)

    output = []
    output.append(f"=== 導管排程驗證 ===")
    output.append(f"入院日: {admission_date}")
    output.append(f"導管日: {cathlab_date}")
    output.append("")

    # Step 1: Read ordering
    output.append("--- 讀取入院序 ---")
    patients = read_ordering(admission_date)
    output.append(f"入院序共 {len(patients)} 人")

    to_check = [p for p in patients if not p['skip']]
    skipped = [p for p in patients if p['skip']]
    output.append(f"應排導管: {len(to_check)} 人")
    output.append(f"預期不排: {len(skipped)} 人")
    output.append("")

    # Step 2: Query WEBCVIS
    output.append("--- 查詢 WEBCVIS ---")
    webcvis_charts = query_webcvis(cathlab_date)
    output.append(f"WEBCVIS 排程共 {len(webcvis_charts)} 筆")
    output.append("")

    # Step 3: Compare
    output.append("--- 比對結果 ---")
    found = []
    missing = []
    for p in to_check:
        if p['chart'] in webcvis_charts:
            found.append(p)
        else:
            missing.append(p)

    for p in found:
        output.append(f"  OK  {p['seq']:>2}. {p['doctor']} {p['name']} ({p['chart']}) {p['diag']}/{p['cath']}")

    for p in missing:
        output.append(f"  NG  {p['seq']:>2}. {p['doctor']} {p['name']} ({p['chart']}) {p['diag']}/{p['cath']} [{p['note']}]")

    if skipped:
        output.append("")
        output.append("--- 預期不排（備註含不排程/檢查）---")
        for p in skipped:
            in_webcvis = "竟然在排程中!" if p['chart'] in webcvis_charts else "確認不在"
            output.append(f"  SKIP {p['seq']:>2}. {p['doctor']} {p['name']} ({p['chart']}) [{p['note']}] → {in_webcvis}")

    output.append("")
    output.append(f"=== 結果: {len(found)} OK / {len(missing)} MISSING / {len(skipped)} SKIP ===")
    if not missing:
        output.append("ALL CLEAR - 所有應排導管的病人都已在排程中!")
    else:
        output.append("WARNING - 有病人尚未排入導管排程!")

    # Write output
    out_file = f"_verify_cathlab_{cathlab_mmdd}.txt"
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    # Also try to print (may fail on cp950)
    for line in output:
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode('ascii', 'replace').decode())


if __name__ == "__main__":
    main()
