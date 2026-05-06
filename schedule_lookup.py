"""
主治醫師導管時段表 lookup helper.

Usage:
  python schedule_lookup.py 黃鼎鈞 Thu
  python schedule_lookup.py 黃鼎鈞 Thu --json
  python schedule_lookup.py --weekday Thu      # all doctors that day

Importable:
  from schedule_lookup import lookup
  slots = lookup("黃鼎鈞", "Thu")
  # → [{"session":"AM","room":"C1","second":"葉立浩","third":"洪晨惠","tags":[],"raw":"黃鼎鈞(浩、晨)"},
  #    {"session":"PM","room":"C1","second":"葉立浩","third":"洪晨惠","tags":[],"raw":"黃鼎鈞(浩、晨)"}]

Schedule grid (主治醫師導管時段表):
  Cols B=room (H1/H2/C1/C2), C=Mon, D=Tue, E=Wed, F=Thu, G=Fri
  Rows 2-7  = AM (上午):  H1 spans 2-4, H2 r5, C1 r6, C2 r7
  Rows 8-12 = PM (下午):  H1 spans 8-9, H2 r10, C1 r11, C2 r12

Cell parsing:
  "陳柏升"           → name=陳柏升, tags=[]
  "劉嚴文(寬)"        → name=劉嚴文, tags=[寬]    → 寬→葉建寬 (2nd)
  "黃鼎鈞(浩、晨)"     → name=黃鼎鈞, tags=[浩,晨]  → 2nd=葉立浩, 3rd=洪晨惠
  "EP(李柏增)(晨)"    → name=EP,    tags=[李柏增,晨] → main treated as study type
  "(陳則瑋)"          → continuation/secondary on row above

Per CLAUDE.md rule 15: 1st paren → attendingdoctor2; 2nd paren → recommendationDoctor (third).
"""
import sys
import re
import json

sys.stdout.reconfigure(encoding='utf-8')

# Map abbreviation → full doctor name (resolved against DOCTOR_CODES in cathlab_keyin.py)
ABBREV_MAP = {
    "浩": "葉立浩",
    "晨": "洪晨惠",
    "寬": "葉建寬",
    "嘉": "蘇奕嘉",
}

# Tags that are NOT doctor references (procedure / patient-type tags)
NON_DOCTOR_TAGS = {"齡", "結構"}

WEEKDAY_COL = {"Mon": 3, "Tue": 4, "Wed": 5, "Thu": 6, "Fri": 7}  # 1-indexed in gspread

# Layout: (row, session, room) for primary slots
SLOTS = [
    (2, "AM", "H1"), (5, "AM", "H2"), (6, "AM", "C1"), (7, "AM", "C2"),
    (8, "PM", "H1"), (10, "PM", "H2"), (11, "PM", "C1"), (12, "PM", "C2"),
]
# Continuation rows that belong to the slot above (for secondary listings in same room)
CONT_ROWS = {3: 2, 4: 2, 9: 8}  # row → primary row


def _doctor_codes():
    """Lazy import of DOCTOR_CODES from cathlab_keyin.py."""
    from cathlab_keyin import DOCTOR_CODES
    return DOCTOR_CODES


def parse_cell(text):
    """Parse a schedule cell.
    Returns {"name": str, "tags": [str], "raw": str} or None if empty.
    """
    if not text or not text.strip():
        return None
    raw = text.strip()
    # Match leading name (everything before the first '(') and all (...) groups
    m = re.match(r'^([^()]+)?(.*)$', raw)
    name = (m.group(1) or '').strip() if m else raw
    rest = m.group(2) if m else ''
    tags = []
    for t in re.findall(r'\(([^()]+)\)', rest):
        # Split multi-tag like "浩、晨" or "浩,晨"
        for sub in re.split(r'[、,，]', t):
            sub = sub.strip()
            if sub:
                tags.append(sub)
    return {"name": name, "tags": tags, "raw": raw}


def resolve_tag(tag):
    """Map tag → doctor name, or None if not a doctor."""
    if tag in NON_DOCTOR_TAGS:
        return None
    if tag in ABBREV_MAP:
        return ABBREV_MAP[tag]
    # Tag is a full doctor name?
    codes = _doctor_codes()
    if tag in codes:
        return tag
    return None  # unresolved


def _read_grid():
    """Read 主治醫師導管時段表 cells once. Returns 2D list (1-indexed row, 1-indexed col)."""
    from gsheet_utils import get_worksheet
    ws = get_worksheet('主治醫師導管時段表')
    return ws.get('A1:G15')


def _cell_at(grid, row, col):
    """1-indexed access with bounds-safe."""
    if row - 1 >= len(grid):
        return ''
    r = grid[row - 1]
    if col - 1 >= len(r):
        return ''
    return r[col - 1] or ''


def lookup(doctor, weekday, grid=None):
    """Find all slots where `doctor` is the primary attending on `weekday`.

    Returns list of dicts: {"session", "room", "second", "third", "tags", "raw"}.
    Empty list if doctor has no slot that day.
    """
    if grid is None:
        grid = _read_grid()
    col = WEEKDAY_COL.get(weekday)
    if not col:
        raise ValueError(f"weekday must be Mon/Tue/Wed/Thu/Fri, got {weekday}")

    results = []
    for row, session, room in SLOTS:
        # Collect cells from the primary row + any continuation rows in same slot
        rows_to_scan = [row] + [r for r, p in CONT_ROWS.items() if p == row]
        for r in rows_to_scan:
            text = _cell_at(grid, r, col)
            cell = parse_cell(text)
            if not cell:
                continue
            if cell['name'] != doctor:
                continue
            second = None
            third = None
            doctor_tags = [resolve_tag(t) for t in cell['tags']]
            doctor_tags = [d for d in doctor_tags if d]
            if len(doctor_tags) >= 1:
                second = doctor_tags[0]
            if len(doctor_tags) >= 2:
                third = doctor_tags[1]
            results.append({
                "session": session,
                "room": room,
                "second": second,
                "third": third,
                "tags": cell['tags'],
                "raw": cell['raw'],
            })
    return results


def list_day(weekday, grid=None):
    """List all primary doctors for a weekday."""
    if grid is None:
        grid = _read_grid()
    col = WEEKDAY_COL.get(weekday)
    if not col:
        raise ValueError(f"bad weekday {weekday}")
    out = []
    for row, session, room in SLOTS:
        for r in [row] + [rr for rr, p in CONT_ROWS.items() if p == row]:
            text = _cell_at(grid, r, col)
            cell = parse_cell(text)
            if not cell:
                continue
            out.append({
                "session": session,
                "room": room,
                "row": r,
                "name": cell['name'],
                "tags": cell['tags'],
                "raw": cell['raw'],
            })
    return out


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    json_out = "--json" in args
    if json_out:
        args.remove("--json")

    if args[0] == "--weekday" and len(args) >= 2:
        weekday = args[1]
        result = list_day(weekday)
        if json_out:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"=== {weekday} all slots ===")
            for s in result:
                print(f"  {s['session']} {s['room']:3} | {s['name']} {s['tags']}")
        return

    if len(args) < 2:
        print("Usage: python schedule_lookup.py DOCTOR WEEKDAY")
        sys.exit(1)
    doctor, weekday = args[0], args[1]
    result = lookup(doctor, weekday)
    if json_out:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if not result:
        print(f"{doctor} has no slot on {weekday}")
        return
    for s in result:
        print(f"  {s['session']} {s['room']} | second={s['second']} third={s['third']} | raw={s['raw']}")


if __name__ == "__main__":
    main()
