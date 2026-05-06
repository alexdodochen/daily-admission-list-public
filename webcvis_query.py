"""
WEBCVIS cathlab schedule generic query helper.

Usage:
  python webcvis_query.py YYYYMMDD [YYYYMMDD ...]
  python webcvis_query.py YYYYMMDD --chart 01808613      # filter to one chart
  python webcvis_query.py YYYYMMDD --json                 # JSON output
  python webcvis_query.py 20260511 20260512 20260513 20260514 20260515  # week-scan

Output columns per row:
  chart | name | room | time | doctor1 | doctor2 | doctor6 | pdi | phc

Importable:
  from webcvis_query import query_dates
  result = query_dates(["20260507", "20260508"])  # → {date: [{chart,name,room,...}, ...]}
"""
import sys
import json
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://cardiopacs01.hosp.ncku:8080/WEBCVIS"
SCHEDULE_URL = f"{BASE_URL}/HCO/HCO1W001.do"
ACCOUNT = "107614"
PASSWORD = "107614"


def login(page):
    page.goto(f"{BASE_URL}/")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.fill('input[name="userid"]', ACCOUNT)
    page.fill('input[name="password"]', PASSWORD)
    page.click('input[type="submit"], button[type="submit"]')
    page.wait_for_load_state("networkidle", timeout=10000)


def query_one(page, fmt_date):
    """Return list of dicts."""
    page.goto(SCHEDULE_URL)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1)
    page.evaluate(f'''() => {{
        let d1 = document.getElementById("daySelect1");
        let d2 = document.getElementById("daySelect2");
        d1.removeAttribute("readonly"); d2.removeAttribute("readonly");
        d1.value = "{fmt_date}"; d2.value = "{fmt_date}";
    }}''')
    time.sleep(0.3)
    page.evaluate('''() => {
        document.HCO1WForm.buttonName.name = "QRY";
        document.HCO1WForm.buttonName.value = "QRY";
        document.HCO1WForm.submit();
    }''')
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1.5)
    return page.evaluate('''() => {
        let result = [];
        document.querySelectorAll("#row tr").forEach(r => {
            let chartEl = r.querySelector("#hes_patno");
            if (!chartEl || !chartEl.value) return;
            let getVal = (id) => {
                let el = r.querySelector("#" + id);
                return el ? (el.value || "").trim() : "";
            };
            result.push({
                chart: getVal("hes_patno"),
                name: getVal("hes_patname"),
                room: getVal("hes_mcrid"),
                date: getVal("hes_schdate"),
                time: getVal("hes_schtime"),
                doctor1: getVal("hes_doctor1"),
                doctor2: getVal("hes_doctor2"),
                doctor6: getVal("hes_doctor6"),
                pdi: getVal("hes_pdi"),
                phc: getVal("hes_phc"),
                note: getVal("hes_note"),
                referno: getVal("hes_referno"),
            });
        });
        return result;
    }''')


def query_dates(dates, chart_filter=None):
    """Query multiple dates. dates = list of YYYYMMDD. Returns {date_yyyymmdd: [rows]}."""
    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=60)
        page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()
        login(page)
        for d in dates:
            fmt = f"{d[:4]}/{d[4:6]}/{d[6:]}"
            rows = query_one(page, fmt)
            if chart_filter:
                rows = [r for r in rows if r['chart'] == chart_filter]
            out[d] = rows
        browser.close()
    return out


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    json_out = "--json" in args
    if json_out:
        args.remove("--json")
    chart_filter = None
    if "--chart" in args:
        i = args.index("--chart")
        chart_filter = args[i + 1]
        args = args[:i] + args[i + 2:]

    dates = args
    for d in dates:
        if len(d) != 8 or not d.isdigit():
            print(f"Bad date {d} (expected YYYYMMDD)")
            sys.exit(1)

    result = query_dates(dates, chart_filter=chart_filter)

    if json_out:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    for d, rows in result.items():
        print(f"=== {d} ({len(rows)} entries) ===")
        for r in rows:
            print(f"  {r['chart']} | {r['name']} | {r['room']} | {r['time']} | "
                  f"d1={r['doctor1']} d2={r['doctor2']} d6={r['doctor6']} | "
                  f"pdi={r['pdi'][:25]} | phc={r['phc'][:25]}")
        print()


if __name__ == "__main__":
    main()
