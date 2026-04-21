"""
驗證導管排程：比對子表格（統整資料）vs WEBCVIS 排程
用法: python verify_cathlab.py 20260409
  → 讀取 20260409 子表格病人清單，查對應 WEBCVIS 排程日，輸出比對結果

資料來源：子表格（主治醫師病人清單），欄位 A=姓名 B=病歷號 F=術前診斷 G=預計心導管 H=註記。
子表格位置：日期工作表中的「X人）」title 行以下、空白行為區塊界線。
不使用 N-V 入院序欄位（那是住服通知清單，是子表格的子集）。
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
ZHANG_BORROWED_BY = ["王思翰", "張倉惟"]


def get_cathlab_date_for_patient(admission_date_str, doctor, note):
    """回傳該 patient 的 cathlab 日期（Y/M/D 字串）。
    規則：
    - 週五入院 → 同日
    - 張獻元週二入院 + 註記無 王思翰/張倉惟 → 同日 PM（張獻元週二自己時段）
    - 張獻元週三入院 → 同日 PM（張獻元週三自己時段，無 borrow 例外）
    - 其他 → N+1
    """
    dt = datetime.strptime(admission_date_str, "%Y%m%d")
    wd = dt.weekday()

    if wd == 4:  # Friday
        cath = dt
    elif doctor == '張獻元' and wd == 2:
        cath = dt  # Wednesday same-day PM (all)
    elif doctor == '張獻元' and wd == 1 and not any(k in note for k in ZHANG_BORROWED_BY):
        cath = dt  # Tuesday same-day
    else:
        cath = dt + timedelta(days=1)
    return cath.strftime("%Y/%m/%d")


def read_rescheduled_charts(data):
    """從 N-V ordering 區塊讀取有 V 欄值的 row，回傳 {病歷號: V值}。
    row[15]=P 姓名、row[18]=S 病歷號、row[21]=V 改期。"""
    out = {}
    for row in data:
        if len(row) < 22:
            continue
        chart = (row[18] or '').strip()
        v = (row[21] or '').strip()
        if chart and v and v != '改期':
            out[chart] = v
    return out


def read_ordering(sheet_name):
    """讀取子表格（統整資料）病人清單，回傳病人列表。
    有 V 欄改期標記的病人會被標成 skip。"""
    ws = get_worksheet(sheet_name)
    if not ws:
        raise ValueError(f"找不到工作表: {sheet_name}")

    data = read_all_values(ws)
    rescheduled = read_rescheduled_charts(data)
    patients = []
    current_doctor = ''
    seq = 0

    for row in data:
        r = row[:8] + [''] * (8 - len(row[:8]))
        col_a = r[0].strip()

        # Doctor title row: col A 含 "人）"
        if '人）' in col_a:
            current_doctor = col_a.split('（')[0].strip()
            continue

        # Sub-header row
        if col_a == '姓名':
            continue

        # Patient row: A=name, B=chart, F=diag, G=cath, H=note
        if col_a and r[1].strip() and current_doctor:
            seq += 1
            name = col_a
            chart = r[1].strip()
            diag = r[5].strip()
            cath = r[6].strip()
            note = r[7].strip()
            v_mark = rescheduled.get(chart, '')
            should_skip = any(kw in note for kw in SKIP_KEYWORDS) or bool(v_mark)
            if v_mark:
                note = (note + f' [改期→{v_mark}]').strip()

            patients.append({
                'seq': seq,
                'doctor': current_doctor,
                'name': name,
                'note': note,
                'chart': chart,
                'diag': diag,
                'cath': cath,
                'skip': should_skip,
            })

    return patients


def query_webcvis(cathlab_dates):
    """連線 WEBCVIS 查詢多個日期排程，回傳 {date_str: set(charts)}。"""
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()

        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle", timeout=15000)
        page.fill('input[name="userid"]', ACCOUNT)
        page.fill('input[name="password"]', PASSWORD)
        page.click('input[type="submit"], button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=10000)

        for d in cathlab_dates:
            page.goto(SCHEDULE_URL)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(1)
            page.evaluate(f'''() => {{
                let d1 = document.getElementById("daySelect1");
                let d2 = document.getElementById("daySelect2");
                d1.removeAttribute("readonly"); d2.removeAttribute("readonly");
                d1.value = "{d}"; d2.value = "{d}";
            }}''')
            time.sleep(0.3)
            page.evaluate('''() => {
                document.HCO1WForm.buttonName.name = "QRY";
                document.HCO1WForm.buttonName.value = "QRY";
                document.HCO1WForm.submit();
            }''')
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(1)
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
            results[d] = set(charts)

        browser.close()
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_cathlab.py <admission_date>")
        print("Example: python verify_cathlab.py 20260409")
        sys.exit(1)

    admission_date = sys.argv[1]

    output = []
    output.append(f"=== 導管排程驗證 ===")
    output.append(f"入院日: {admission_date}")
    output.append("")

    # Step 1: Read ordering
    output.append("--- 讀取入院序 ---")
    patients = read_ordering(admission_date)
    output.append(f"入院序共 {len(patients)} 人")

    to_check = [p for p in patients if not p['skip']]
    skipped = [p for p in patients if p['skip']]

    # 每位 patient 的 cathlab date
    for p in to_check:
        p['cath_date'] = get_cathlab_date_for_patient(admission_date, p['doctor'], p['note'])

    unique_dates = sorted(set(p['cath_date'] for p in to_check))
    output.append(f"應排導管: {len(to_check)} 人 (涉及日期: {', '.join(unique_dates)})")
    output.append(f"預期不排: {len(skipped)} 人")
    output.append("")

    # Step 2: Query WEBCVIS
    output.append("--- 查詢 WEBCVIS ---")
    webcvis_map = query_webcvis(unique_dates)
    for d in unique_dates:
        output.append(f"  {d}: {len(webcvis_map[d])} 筆")
    output.append("")

    # Step 3: Compare
    output.append("--- 比對結果 ---")
    found = []
    missing = []
    for p in to_check:
        charts_that_day = webcvis_map.get(p['cath_date'], set())
        if p['chart'] in charts_that_day:
            found.append(p)
        else:
            missing.append(p)

    for p in found:
        output.append(f"  OK  {p['seq']:>2}. [{p['cath_date']}] {p['doctor']} {p['name']} ({p['chart']}) {p['diag']}/{p['cath']}")

    for p in missing:
        output.append(f"  NG  {p['seq']:>2}. [{p['cath_date']}] {p['doctor']} {p['name']} ({p['chart']}) {p['diag']}/{p['cath']} [{p['note']}]")

    if skipped:
        output.append("")
        output.append("--- 預期不排（備註含不排程/檢查/改期）---")
        all_charts = set()
        for s in webcvis_map.values():
            all_charts |= s
        for p in skipped:
            in_webcvis = "竟然在排程中!" if p['chart'] in all_charts else "確認不在"
            output.append(f"  SKIP {p['seq']:>2}. {p['doctor']} {p['name']} ({p['chart']}) [{p['note']}] → {in_webcvis}")

    output.append("")
    output.append(f"=== 結果: {len(found)} OK / {len(missing)} MISSING / {len(skipped)} SKIP ===")
    if not missing:
        output.append("ALL CLEAR - 所有應排導管的病人都已在排程中!")
    else:
        output.append("WARNING - 有病人尚未排入導管排程!")

    # Write output
    out_file = f"_verify_cathlab_{admission_date}.txt"
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
