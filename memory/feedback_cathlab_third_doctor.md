---
name: 兩位 second 醫師 → 第二位填「推薦醫師」欄位 + 黃鼎鈞 Mon 強制 second 洪晨惠
description: cathlab keyin 時「黃鼎鈞(浩、晨)」這類兩位 second 寫法 → 第一位 attendingdoctor2、第二位 recommendationDoctor（取代舊「放 note」）。另外黃鼎鈞 Mon cathlab 強制 second=洪晨惠。
type: feedback
---

## 規則 1：兩位 second 醫師 → 第二位 recommendationDoctor

時段表寫法如「黃鼎鈞(浩、晨)」、「陳儒逸(寬、嘉)」表示**兩位 second 醫師**：

- 第一位 → `attendingdoctor2` 欄位 (`select[name="attendingdoctor2"]`)
- 第二位 → **`推薦醫師` 欄位** (`select[name="recommendationDoctor"]`)

舊規則（已廢）：第二位放 note 欄位。**不要再用 note**。

## 規則 2：黃鼎鈞 Mon cathlab → second=洪晨惠

即使時段表 col 2 (Mon) 沒寫黃鼎鈞，凡是黃鼎鈞 Mon cathlab 一律 second=洪晨惠（晨）。
（Mon 入院 → Tue cathlab 走 Tue 池規則；Sun 入院 → Mon cathlab 才適用此 Mon 規則）

## Why

- 使用者 2026-04-29 新規定：「黃鼎鈞周一的導管都 second 洪晨惠 / 若導管排程表上有兩位 second 第二位 key 在推薦醫師欄位 (新規定 請記住)」
- 之前 CLAUDE.md rule 15 寫「葉立浩優先，其餘放備註」 — 已過時。
- WEBCVIS 介面有獨立「推薦醫師」select 欄位（`recommendationDoctor`），語意上比 note 自由文字更精準。

## How to apply

`cathlab_keyin.py` 已支援 `third` 欄位（2026-04-29 加入）：

```python
# JSON schema
{"doctor": "黃鼎鈞", "second": "葉立浩", "third": "洪晨惠", ...}
```

- ADD phase：select recommendationDoctor with tcode
- UPT phase：fix_diag 也會處理 third（即 doctor 變更後可重跑修補）

時段表 → JSON 轉換對照：

| 時段表寫法 | second | third |
|---|---|---|
| `黃鼎鈞(浩、晨)` | 葉立浩 | 洪晨惠 |
| `陳儒逸(寬、嘉)` | 葉建寬 | 蘇奕嘉 |
| `黃鼎鈞(浩)` | 葉立浩 | null |
| `廖瑀(晨)` | 洪晨惠 | null |
| `陳儒逸(寬)` | 葉建寬 | null |
| `EP(李柏增)(晨)` | 李柏增 (但 2026/08 前 skip) → 改 second=洪晨惠 | null |

## 已知實例

- 2026-05-07 cathlab (5/6 入院) 黃鼎鈞 5 人 (陳忻妤/譚翠翠/黃綉文/王睿鍾/黃秀琴) Thu AM/PM C1 (浩、晨) → second=葉立浩 + third=洪晨惠（4/29 修正版）
- 2026-05-04 cathlab (5/3 入院) 黃鼎鈞 2 人 (徐豐淇/吳宇豪) Mon → second=洪晨惠（規則 2，無 third）
