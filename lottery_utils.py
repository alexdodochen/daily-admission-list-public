"""Lottery utilities — read 主治醫師抽籤表 + weighted doctor shuffle.

The 抽籤表 grid uses `*N` suffix to mean N tickets:
  「許志新」      → 1 ticket
  「李柏增*2」   → 2 tickets
  「黃鼎鈞*3」   → 3 tickets (rare)

For doctor-order randomization, every ticket goes in the pool, shuffle,
then dedup keeping first occurrence. A *2 doctor lands earlier in the
final order more often than a *1 doctor, but each doctor still occupies
one slot in the RR.

Usage:
    from lottery_utils import read_lottery_tickets, weighted_doctor_shuffle
    tickets = read_lottery_tickets('星期一')          # [('陳柏升', 1), ('李柏增', 2), ...]
    order = weighted_doctor_shuffle(tickets)          # deduped, randomized

Use `filter_by_names(tickets, admitted_doctors)` to limit the pool to
doctors with admitted patients today.
"""
import random
import re

from gsheet_utils import get_worksheet

WEEKDAY_COL = {
    '星期一': 1, '星期二': 2, '星期三': 3, '星期四': 4, '星期五': 5,
    'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5,
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
}


def parse_ticket_cell(raw: str) -> tuple[str, int]:
    """`'李柏增*2'` -> `('李柏增', 2)`. `'許志新'` -> `('許志新', 1)`. Empty -> `('', 0)`."""
    s = (raw or '').strip()
    if not s:
        return ('', 0)
    m = re.match(r'^(.+?)\*(\d+)$', s)
    if m:
        return (m.group(1).strip(), int(m.group(2)))
    return (s, 1)


def read_lottery_tickets(weekday) -> list[tuple[str, int]]:
    """Read 主治醫師抽籤表 column for the given weekday.

    weekday: '星期一'/'Mon'/1, etc.
    Returns: list of (doctor_name, ticket_count), excluding empty cells.
    """
    if weekday not in WEEKDAY_COL:
        raise ValueError(f"Unknown weekday: {weekday}")
    col_idx = WEEKDAY_COL[weekday]
    ws = get_worksheet('主治醫師抽籤表')
    if not ws:
        raise RuntimeError("worksheet 主治醫師抽籤表 not found")
    col = ws.col_values(col_idx)
    # row 1 = '星期X' header; data starts row 2
    out = []
    for cell in col[1:]:
        name, count = parse_ticket_cell(cell)
        if name and count > 0:
            out.append((name, count))
    return out


def weighted_doctor_shuffle(doctors_with_tickets: list[tuple[str, int]]) -> list[str]:
    """Pool = each doctor expanded by ticket count, shuffle, dedup keeping first occurrence.

    Example: [('A', 2), ('B', 1), ('C', 1)] → pool=[A,A,B,C] → shuffle → e.g. [B,A,A,C]
             → dedup → [B, A, C]. So A's earliness is weighted by tickets but slot count = 1.
    """
    pool = []
    for name, count in doctors_with_tickets:
        pool.extend([name] * count)
    random.shuffle(pool)
    seen = set()
    out = []
    for name in pool:
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def filter_by_names(tickets: list[tuple[str, int]], names: list[str]) -> list[tuple[str, int]]:
    """Restrict ticket list to doctors whose name is in `names` (preserve their ticket counts).

    Use to limit the lottery pool to doctors with admitted patients on the target day.
    Doctors in `names` but not in the lottery sheet are silently dropped (warn upstream).
    """
    name_set = set(names)
    return [(n, c) for n, c in tickets if n in name_set]


if __name__ == '__main__':
    # Quick smoke test: print Mon tickets and a sample shuffle
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    tix = read_lottery_tickets('星期一')
    print('Mon tickets:', tix)
    print('Sample shuffle:', weighted_doctor_shuffle(tix))
