---
name: Lottery doctor shuffle is WEIGHTED by ticket count (*2 = double weight)
description: When randomizing doctor order for lottery / N-V RR, use weighted shuffle — each ticket goes in the pool, random.shuffle, dedup keeping first occurrence. Uniform random.shuffle on names alone is wrong when any doctor has `*2` (or `*N`) on 主治醫師抽籤表.
type: feedback
---

Doctor order randomization (in the lottery skill AND in the N-V RR doctor order step) must respect the `*N` ticket count from `主治醫師抽籤表`.

**Why:** User confirmed (5/8): «*2 雙籤 = 加權抽順位 (最常見)». Pure `random.shuffle(names)` gives every doctor uniform probability, ignoring tickets. With *2 doctors, weighted shuffle gives them a higher probability of landing earlier in the order — which is the whole point of *2 in 抽籤表.

**Canonical implementation (dedup-after-shuffle):**
```python
def weighted_doctor_shuffle(doctors_with_tickets: list[tuple[str, int]]) -> list[str]:
    """Each entry is (doctor_name, ticket_count). Returns deduped ordered list."""
    pool = []
    for name, count in doctors_with_tickets:
        pool.extend([name] * count)
    random.shuffle(pool)
    seen = set()
    result = []
    for name in pool:
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result
```

Permanent helper: `lottery_utils.weighted_doctor_shuffle()` — use it everywhere instead of inline `random.shuffle`.

**How to apply:**
- Reading `主治醫師抽籤表` (cols A-E = Mon-Fri): `*2` suffix means 2 tickets, `*3` means 3, no suffix = 1 ticket. Strip suffix to get doctor name.
- Use `weighted_doctor_shuffle` whenever Claude needs to randomize doctor order — the skills `admission-lottery` and `admission-ordering` both do this. Don't fall back to plain `random.shuffle`.
- Each doctor still occupies **one** slot in the final RR (sub-tables, N-V rows). *2 only affects probability of being earlier in the order, not slot count.
- Two RR groups (時段組 vs 非時段組) are still independent — shuffle each separately.
- A user-pinned doctor («許志新順位第一») overrides — pin them at slot 1, weight-shuffle the rest.

**Real-world check (5/8 / 5/10 case):** Mon column A had only `李柏增*2` as a double-ticket doctor. None of the 5/10 admitted doctors (許志新, 詹世鴻, 陳昭佑, 廖瑀) had *2 — uniform shuffle accidentally gave the right distribution. Bug latent until a *2 doctor admits a patient.
