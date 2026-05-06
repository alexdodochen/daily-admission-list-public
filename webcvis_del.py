"""
WEBCVIS cathlab schedule DEL helper.

Usage:
  python webcvis_del.py CHART YYYYMMDD [CHART YYYYMMDD ...]
  python webcvis_del.py 01808613 20260507
  python webcvis_del.py 01808613 20260507 02742922 20260507

Each (chart, date) pair is one DEL operation.

DEL mechanism (verified 2026-05-06):
  Each result row's first cell has <input type=checkbox name=chk value=N>.
  onclick fires checkedShowButton(deleteButton, allChkBoxes) → enables #deleteButton.
  Click #deleteButton → confirm("您確定要刪除嗎？") → form submits with buttonName=DEL.
  hes_referno is OFTEN EMPTY for cathlab entries — don't rely on it; use chk.

Anti-patterns (don't re-attempt):
  - Direct buttonName="DEL" form submit without populating row data → silent fail
  - removeAttribute("disabled") on #deleteButton + naive click without checkbox → silent fail
"""
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://cardiopacs01.hosp.ncku:8080/WEBCVIS"
SCHEDULE_URL = f"{BASE_URL}/HCO/HCO1W001.do"
ACCOUNT = "107614"
PASSWORD = "107614"


def parse_args(argv):
    if len(argv) < 3 or len(argv) % 2 != 1:
        print(__doc__)
        sys.exit(1)
    pairs = []
    for i in range(1, len(argv), 2):
        chart = argv[i].strip()
        date = argv[i + 1].strip()
        if len(date) != 8 or not date.isdigit():
            print(f"Bad date {date} (expected YYYYMMDD)")
            sys.exit(1)
        pairs.append((chart, f"{date[:4]}/{date[4:6]}/{date[6:]}"))
    return pairs


def login(page):
    page.goto(f"{BASE_URL}/")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.fill('input[name="userid"]', ACCOUNT)
    page.fill('input[name="password"]', PASSWORD)
    page.click('input[type="submit"], button[type="submit"]')
    page.wait_for_load_state("networkidle", timeout=10000)


def query_date(page, fmt_date):
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
    time.sleep(2)


def del_chart(page, chart, fmt_date):
    """Returns (ok, message)."""
    query_date(page, fmt_date)

    # Check the chk checkbox in target row → fires onclick → enables deleteButton
    result = page.evaluate(f'''() => {{
        let rows = document.querySelectorAll("#row tr");
        for (let r of rows) {{
            let el = r.querySelector("#hes_patno");
            if (el && el.value && el.value.trim() === "{chart}") {{
                let chk = r.querySelector('input[type=checkbox][name=chk]');
                if (!chk) return {{found: false, error: "no chk checkbox"}};
                chk.checked = true;
                if (chk.onclick) chk.onclick();
                let delBtn = document.getElementById("deleteButton");
                return {{found: true, chkVal: chk.value, delBtnDisabled: delBtn.disabled}};
            }}
        }}
        return {{found: false, error: "row not found"}};
    }}''')

    if not result.get('found'):
        return False, f"row not found ({result.get('error')})"
    if result.get('delBtnDisabled'):
        return False, "deleteButton still disabled after check"

    time.sleep(0.5)
    page.click('#deleteButton')
    page.wait_for_load_state("networkidle", timeout=20000)
    time.sleep(2)

    # Verify
    query_date(page, fmt_date)
    still = page.evaluate(f'''() => {{
        let rows = document.querySelectorAll("#row tr");
        for (let r of rows) {{
            let el = r.querySelector("#hes_patno");
            if (el && el.value && el.value.trim() === "{chart}") return true;
        }}
        return false;
    }}''')
    if still:
        return False, "still present after DEL"
    return True, "removed"


def main():
    pairs = parse_args(sys.argv)
    print(f"DEL plan: {len(pairs)} entries")
    for c, d in pairs:
        print(f"  {c} on {d}")

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=80)
        page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()
        page.on("dialog", lambda d: (print(f"  [dialog] {d.message[:60]} -> accept"), d.accept()))

        login(page)
        print("Login OK")

        for chart, fmt_date in pairs:
            ok, msg = del_chart(page, chart, fmt_date)
            tag = "OK" if ok else "FAIL"
            print(f"  [{tag}] {chart} on {fmt_date}: {msg}")
            results.append((chart, fmt_date, ok, msg))

        time.sleep(1)
        browser.close()

    ok_count = sum(1 for _, _, ok, _ in results if ok)
    print(f"\nResults: {ok_count}/{len(results)} succeeded")
    if ok_count < len(results):
        sys.exit(2)


if __name__ == "__main__":
    main()
