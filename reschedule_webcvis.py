"""
改期 WEBCVIS 同步 — 刪除來源日已改期病人的導管排程

用法:
  python reschedule_webcvis.py <source_date>           # 正式執行
  python reschedule_webcvis.py <source_date> --dry-run # 只 print 不 DEL
  python reschedule_webcvis.py <source_date> --first   # 只處理第一筆 (測 DEL)

流程:
  1. 讀來源日 sheet 的 W 欄, 找「已改期至 YYYYMMDD」標記
     (表示 reschedule_patients.py 已經跑完 Sheet 搬遷)
  2. 取出這些病人的 chart_no
  3. 登入 WEBCVIS, 查詢來源日
  4. 對每位病人:
     - click 該 row 載入
     - 讀當前欄位 (room/time/doctor/diag/proc) 給 user 看
     - 等 user 按 Enter 確認 → buttonName.name="DEL" submit
     - --dry-run 不按下送出
  5. ADD 到目標日 → 不處理, 請 user 在 cathlab_keyin_MMDD.py 的 PATIENTS 加入,
     再跑 ADD+UPT 流程 (現有 skill)

注意:
  - 這是第一次在此 codebase 做 DEL, 第一次請務必先用 --first 或 --dry-run 驗證
  - 每個病人 DEL 前都會 pause 等手動按 Enter, 無法一次跑完全部
"""
import sys
import time
import traceback
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

import gsheet_utils as gu

BASE_URL = "http://cardiopacs01.hosp.ncku:8080/WEBCVIS"
SCHEDULE_URL = f"{BASE_URL}/HCO/HCO1W001.do"
ACCOUNT = "107614"
PASSWORD = "107614"

LOG = []
DONE_PREFIX = '已改期至'


def log(msg):
    LOG.append(msg)
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode())


def save_log(source_date):
    with open(f'_reschedule_webcvis_{source_date}.log', 'w', encoding='utf-8') as f:
        f.write('\n'.join(LOG))


def collect_already_migrated(source_date):
    """Read source sheet W col, return list of {chart_no, name, target_date}."""
    src = gu.get_worksheet(source_date)
    if src is None:
        log(f'ERROR: source sheet "{source_date}" not found')
        return []
    vals = src.get_all_values()
    out = []
    for i in range(1, len(vals)):
        row = vals[i]
        w = (row[22] if len(row) > 22 else '').strip()
        if not w.startswith(DONE_PREFIX):
            continue
        target = w.replace(DONE_PREFIX, '').strip()
        chart_no = (row[18] if len(row) > 18 else '').strip()
        name = (row[15] if len(row) > 15 else '').strip()
        if not chart_no:
            log(f'  WARN row {i+1}: marked but no chart_no')
            continue
        out.append({'chart_no': chart_no, 'name': name, 'target': target, 'row': i + 1})
    return out


def login(page):
    page.goto(f"{BASE_URL}/")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.fill('input[name="userid"]', ACCOUNT)
    page.fill('input[name="password"]', PASSWORD)
    page.click('input[type="submit"], button[type="submit"]')
    page.wait_for_load_state("networkidle", timeout=10000)
    log('WEBCVIS login OK')


def set_date_and_query(page, date_yyyy_mm_dd):
    page.goto(SCHEDULE_URL)
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(1)
    page.evaluate(f'''() => {{
        let d1 = document.getElementById("daySelect1");
        let d2 = document.getElementById("daySelect2");
        d1.removeAttribute("readonly"); d2.removeAttribute("readonly");
        d1.value = "{date_yyyy_mm_dd}"; d2.value = "{date_yyyy_mm_dd}";
    }}''')
    time.sleep(0.3)
    page.evaluate('''() => {
        document.HCO1WForm.buttonName.name = "QRY";
        document.HCO1WForm.buttonName.value = "QRY";
        document.HCO1WForm.submit();
    }''')
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(1)


def click_row_by_chart(page, chart_no):
    """Click the row matching chart_no (to load fields into form for display)."""
    found = page.evaluate('''(chart) => {
        let rows = document.querySelectorAll("#row tr");
        for (let r of rows) {
            let el = r.querySelector("#hes_patno");
            if (el && el.value.trim() === chart) { r.click(); return true; }
        }
        return false;
    }''', chart_no)
    if found:
        time.sleep(0.8)
    return found


def check_row_checkbox(page, chart_no):
    """Tick the chk checkbox in the row matching chart_no. Required before DEL."""
    return page.evaluate('''(chart) => {
        let rows = document.querySelectorAll("#row tr");
        for (let r of rows) {
            let el = r.querySelector("#hes_patno");
            if (el && el.value.trim() === chart) {
                let cb = r.querySelector('input[name="chk"]');
                if (!cb) return false;
                cb.checked = true;
                // fire onclick so checkedShowButton enables #deleteButton
                if (typeof cb.onclick === "function") cb.onclick();
                return true;
            }
        }
        return false;
    }''', chart_no)


def read_current_fields(page):
    """Read the loaded form's current values for display."""
    return page.evaluate('''() => {
        const g = (n) => {
            let el = document.querySelector(`[name="${n}"]`);
            if (!el) return '';
            if (el.tagName === 'SELECT') {
                return el.options[el.selectedIndex] ?
                       el.options[el.selectedIndex].text : '';
            }
            return el.value || '';
        };
        return {
            patno: g('patno2'),
            date: g('inspectiondate'),
            time: g('inspectiontime'),
            room: g('examroom'),
            doctor1: g('attendingdoctor1'),
            doctor2: g('attendingdoctor2'),
            diag: g('prediagnosisitem'),
            proc: g('preheartcatheter'),
            note: g('note'),
        };
    }''')


def submit_del(page):
    """Click #deleteButton — relies on checkbox being pre-ticked and a dialog handler."""
    page.evaluate('''() => {
        let btn = document.getElementById("deleteButton");
        if (btn) btn.disabled = false;
    }''')
    page.click('#deleteButton')
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1)


def yyyymmdd_to_slash(d):
    return f'{d[:4]}/{d[4:6]}/{d[6:8]}'


def cathlab_date_for(admission_yyyymmdd):
    """
    Admission day N → cathlab day:
      - Friday admission → same day (no Saturday schedule)
      - Otherwise → N+1
    """
    dt = datetime.strptime(admission_yyyymmdd, '%Y%m%d')
    if dt.weekday() == 4:  # Friday
        return admission_yyyymmdd
    return (dt + timedelta(days=1)).strftime('%Y%m%d')


def main():
    args = sys.argv[1:]
    if not args:
        print('Usage: python reschedule_webcvis.py <source_date> [--dry-run] [--first]')
        sys.exit(1)
    source_date = args[0]
    dry_run = '--dry-run' in args
    only_first = '--first' in args
    auto_yes = '--yes' in args

    log(f'=== WEBCVIS reschedule DEL: source={source_date} '
        f'{"[DRY-RUN]" if dry_run else ""} {"[FIRST-ONLY]" if only_first else ""}'
        f'{" [AUTO-YES]" if auto_yes else ""} ===')

    records = collect_already_migrated(source_date)
    if not records:
        log('No "已改期至..." markers in source sheet W col. Nothing to delete.')
        log('Hint: run reschedule_patients.py first to migrate sheets and mark source.')
        save_log(source_date)
        return

    log(f'Found {len(records)} migrated records:')
    for r in records:
        log(f'  {r["name"]} ({r["chart_no"]}) row {r["row"]} → {r["target"]}')

    if only_first:
        records = records[:1]
        log(f'\n[FIRST-ONLY] Processing only: {records[0]["name"]}')

    src_cathlab = cathlab_date_for(source_date)
    src_slash = yyyymmdd_to_slash(src_cathlab)
    log(f'Cathlab date for admission {source_date}: {src_cathlab} ({src_slash})')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()
        page.on("dialog", lambda d: d.accept())

        try:
            login(page)

            results = {'deleted': 0, 'skipped': 0, 'not_found': 0, 'error': 0}
            for idx, rec in enumerate(records):
                log(f'\n--- [{idx+1}/{len(records)}] {rec["name"]} ({rec["chart_no"]}) ---')
                set_date_and_query(page, src_slash)

                if not click_row_by_chart(page, rec['chart_no']):
                    log(f'  NOT FOUND in {src_slash} schedule')
                    results['not_found'] += 1
                    continue

                fields = read_current_fields(page)
                log(f'  Current: date={fields["date"]} time={fields["time"]} '
                    f'room={fields["room"]} doctor1={fields["doctor1"]}')
                log(f'           diag="{fields["diag"]}" proc="{fields["proc"]}" '
                    f'note="{fields["note"]}"')
                log(f'  → Will DEL from {src_slash} (target {rec["target"]} '
                    f'needs manual ADD via cathlab_keyin)')

                if dry_run:
                    log('  [DRY-RUN] skipped submit')
                    results['skipped'] += 1
                    continue

                if auto_yes:
                    ans = ''
                    log('  [AUTO-YES]')
                else:
                    try:
                        ans = input('  Confirm DEL? [Enter=yes / s=skip / q=quit]: ').strip().lower()
                    except EOFError:
                        ans = 'q'

                if ans == 'q':
                    log('  QUIT by user')
                    break
                if ans == 's':
                    log('  SKIPPED by user')
                    results['skipped'] += 1
                    continue

                try:
                    if not check_row_checkbox(page, rec['chart_no']):
                        log('  ERROR: could not find chk checkbox in row')
                        results['error'] += 1
                        continue
                    submit_del(page)
                    log('  DEL submitted')
                    time.sleep(1)
                    # Verify by re-querying
                    set_date_and_query(page, src_slash)
                    still = page.evaluate('''(chart) => {
                        let rows = document.querySelectorAll("#row tr");
                        for (let r of rows) {
                            let el = r.querySelector("#hes_patno");
                            if (el && el.value.trim() === chart) return true;
                        }
                        return false;
                    }''', rec['chart_no'])
                    if still:
                        log('  WARNING: still present after DEL — check manually')
                        results['error'] += 1
                    else:
                        log('  Verified: gone from source date')
                        results['deleted'] += 1
                except Exception as e:
                    log(f'  ERROR: {e}')
                    page.screenshot(path=f'_reschedule_webcvis_error_{rec["chart_no"]}.png')
                    results['error'] += 1

            log(f'\n=== Results: {results} ===')
            log('Next: edit the target date\'s cathlab_keyin_MMDD.py PATIENTS list '
                'to include these patients, then run it to ADD on target date.')
        finally:
            save_log(source_date)
            time.sleep(2)
            browser.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        log(traceback.format_exc())
        save_log(sys.argv[1] if len(sys.argv) > 1 else 'unknown')
        raise
