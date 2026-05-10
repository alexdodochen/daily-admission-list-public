---
name: Sub-table E col (manual order) must be read fresh from Sheet before N-V ordering
description: User keys patient order into sub-table E col (手動設定入院序) directly in Google Sheet. N-V ordering MUST read E fresh from the live Sheet — never rely on dialogue memory, JSON files, or prior session state. If E has values, use them; only ask the user when E is blank.
type: feedback
---

**Rule:** Before computing or writing N-V round-robin ordering, do a fresh `ws.get_all_values()` read of the date sheet and parse each sub-table's column E (col index 4 in 8-col A-H layout) as the patient's manual_order. If all patients in a multi-patient doctor block have non-empty E values, that's the answer — sort by int(E). Only ask the user when E is missing/blank.

**Why:** 5/10 — I asked the user "陳昭佑/陳儒逸 內部順序怎麼排?" when they had already keyed 1/2 and 1/2/3 into the E column. User correction: 「我都有 key 在 手動設定入院序 2 1 3 E欄 你怎麼最近常常沒看到? 你是不是只讀自己的 json 檔案 沒有讀 google sheet」. The user's workflow is: open the sheet, type numbers into E, then say "排住院序" — they don't dictate the order back to me in chat. If I don't read E, I waste a turn asking what the sheet already says.

**How to apply:**

1. **Step 1 of admission-ordering** must include parsing sub-table E along with F/G/H — never F/G/H alone. The skill's "讀取資料" section now has the canonical loop.
2. When iterating multi-patient doctor blocks:
   ```python
   if all(r['manual_order'] for r in rows):
       rows.sort(key=lambda r: int(r['manual_order']))
   else:
       # only THEN ask user
       ...
   ```
3. **Don't trust** prior session JSON snapshots, dialogue memory of "we discussed this earlier", or your own assumed defaults. The Sheet is the single source of truth — re-read every time. Same principle as CLAUDE.md rule #18 for F/G/H, now extended to E.
4. **Don't trust** sub-table doctor visual order alone — that's the lottery RR order, separate from per-doctor patient order which lives in E.

**Edge cases:**
- E partially filled (some rows have order, some don't) → still ask user; partial is ambiguous (could be in-progress edit).
- E filled with non-integer (e.g. "後") → treat as not set, ask user.
- E filled but duplicates (two patients both `1`) → ask user to resolve, don't guess.

**Related rules:**
- CLAUDE.md rule #18 — N-V write must re-read sub-table F/G/H now. This memory adds E to that list.
- `feedback_no_reconfirm_workflow.md` — don't re-confirm what's already in the sheet. Reading E satisfies this.
