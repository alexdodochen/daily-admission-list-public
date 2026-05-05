---
name: 張獻元週三入院 — cathlab 同日 PM, lottery 視為非時段
description: 張獻元 Wed 入院特例：cathlab 同日（Wed PM C2）keyin，但 lottery/ordering 一律視為「非時段醫師」（看隔日 Thu 沒時段）
type: feedback
originSessionId: 89177871-fbbd-4bbc-904f-9c44fb514d35
---
## 規則

張獻元週三 (Wed) 入院的病人：

1. **Cathlab keyin** → **同日** Wed PM C2（張獻元週三 AM C2 + PM C2 兩個時段都他自己）。
   不走 N+1 因為週四他無時段。`verify_cathlab.py` 已有對應規則。

2. **Lottery / Ordering 時段判定** → **非時段醫師**。
   理由：lottery 時段判定看「隔日抽籤池」（一般 N+1，週三入院看週四 col D）。
   張獻元在週四 col D **沒時段** → 非時段醫師。
   雖然他週三 cathlab same-day 有時段，那是 cathlab 排程的特例，**不影響 lottery 兩段 RR 的時段歸屬**。

## Why

- 使用者 2026-04-29 主動糾正：「張獻元週三入院是無時段醫師!! 因為他隔日沒有導管時段!!」
- Cathlab 同日例外是為「不能放 N+1（週四他沒時段）」而開的折衷，不能反推說他「就是時段醫師」。
- 兩個系統判定邏輯獨立：cathlab 看「該病人實際做的那天」，lottery/ordering 看「N+1 抽籤池」。

## How to apply

- `admission-lottery`：張獻元週三入院 → 跑 col D (Thu) pool → 不在池 → 自動歸非時段醫師（排在主 RR 之後）
- `admission-ordering`：兩段 RR 中張獻元歸**非時段組**，跟陳柏偉/黃鼎鈞/etc 時段組分開算
- `cathlab_keyin`：張獻元 Wed 病人排同日 Wed AM/PM C2（不走 H1 2100+ 非時段格式）
- 這是「兩個系統不同步」的個案，**不要**假設「cathlab 時段 = lottery 時段」

## 同類規則對照

| 醫師 | 入院日 | Lottery 時段 | Cathlab 排程 |
|---|---|---|---|
| 詹世鴻 | 週五 | 非時段（特例） | 非時段 H1 2100+ |
| 張獻元 | 週三 | 非時段（隔日無時段） | 同日 Wed PM C2（特例）|
| 張獻元 | 週二 | 看 col C (Wed) 池 | 看註記，無王思翰/張倉惟 → 同日 Tue PM |

詹週五是兩邊都非時段；**張週三是 lottery 非時段 / cathlab 時段**，要分開判斷。
