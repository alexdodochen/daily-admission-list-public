---
name: 張獻元週三入院 — lottery/ordering 視為非時段醫師
description: 張獻元週三入院特例：cathlab 走同日 PM C2，但 lottery/ordering 一律視為「非時段醫師」（看隔日 Thu 沒時段）；兩個系統判定獨立
type: feedback
---

## 規則

張獻元 Wed (週三) 入院病人：

| 系統 | 時段判定 | 排法 |
|---|---|---|
| **Cathlab keyin** | 時段（同日 Wed PM C2 自有時段）| `cathlab_date = 入院日 (Wed)`，PM C2 1800+，`feedback_zhang_xianyuan_wed_same_day.md` |
| **Lottery / Ordering** | **非時段**（看隔日 Thu 沒時段）| 兩段 RR 中歸**非時段組**，排在時段醫師之後 |

## Why

- Lottery 時段判定看「隔日抽籤池」（Wed 入院 → 看週四 col D）。
- 張獻元在週四 col D **沒時段** → 非時段醫師。
- 雖然他週三 cathlab same-day 有時段，那是 cathlab 排程的特例（為了不放 N+1 因週四他無時段），**不影響 lottery 兩段 RR**。
- 使用者 2026-04-29 主動糾正：「張獻元週三入院是無時段醫師!! 因為他隔日沒有導管時段!!」

## How to apply

- `admission-lottery`：張獻元週三入院 → 跑 col D (Thu) pool → 不在池 → 自動歸非時段（排主 RR 之後）
- `admission-ordering`：兩段 RR 中張獻元歸**非時段組**，跟陳柏偉/黃鼎鈞 等時段組分開算
- `cathlab_keyin`：張獻元 Wed 病人排同日 Wed PM C2（**全 PM**，不能 AM，因為當天才入院）
- 此為「兩個系統不同步」的個案，**不要**假設「cathlab 時段 = lottery 時段」

## 同類規則對照

| 醫師 | 入院日 | Lottery 時段 | Cathlab 排程 |
|---|---|---|---|
| 詹世鴻 | 週五 | 非時段（特例） | 非時段 H1 2100+ |
| 張獻元 | 週三 | **非時段（隔日無時段）** | **同日 Wed PM C2（特例）** |
| 張獻元 | 週二 | 看 col C (Wed) 池 | 看註記，無王思翰/張倉惟 → 同日 Tue PM |

詹週五是兩邊都非時段；張週三 lottery 非時段 / cathlab 時段 — 要分開判斷。

## 4/29 實例

8 人入院：
- 時段組：陳柏偉(2)、黃鼎鈞(2) → RR 取 4 人
- 非時段組：張獻元(4) → 接後

```
1 陳柏偉/呂宗修 (時段)
2 黃鼎鈞/林俊煌 (時段)
3 陳柏偉/陳信義 (時段, HF AE 不排導管)
4 黃鼎鈞/邱淑卿 (時段)
5 張獻元/陳麗花 (非時段)
6 張獻元/王得福 (非時段)
7 張獻元/陳中坤 (非時段)
8 張獻元/鄭恩賜 (非時段)
```
