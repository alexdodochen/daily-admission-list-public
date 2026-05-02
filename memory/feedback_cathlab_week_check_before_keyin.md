---
name: cathlab keyin 前必須檢查整週是否已有該病人排程
description: ADD 前必須掃描入院當週 WEBCVIS（週一~週五）每位病人 chart no，已存在於任何一天就 STOP 給使用者看，不要自動 ADD
type: feedback
---

**HARD RULE：cathlab_keyin.py ADD 前，每位病人都要掃當週 (Mon-Fri) WEBCVIS chart no。**

- 已在當週某一天 → **STOP**，列出「該病人 X 已排在 MM/DD ROOM TIME 醫師」給使用者看
- 使用者看了再決定：時間錯要改 / 重新排 / skip 該筆 / 其他
- **絕對不要自動 ADD** 到入院 N+1 那天

**Why（2026-05-02 踩過）：**
康李金春 5/4 入院，N+1 = 5/5 → 我自動 ADD 5/5 H1 2100 廖瑀。但她實際 CRT 是 **5/6** 已排好。我多 ADD 一筆，造成 5/5 多一筆假排程，使用者要手動清。

使用者：「你要注意喔 key導管時是檢查當周是否有那個病人的導管 若已經有了就提出來給我看看是時間弄錯還怎樣 不要自動key in」「例如康李是5/4住院 但他的CRT 5/6才要做 而且也已經安排了」

**How to apply：**
1. cathlab_keyin.py Phase 1 之前，先 query Mon-Fri 五次（或一次拉整週清單），build chart_to_(date, room, time, doctor) map
2. 對 JSON 中每筆病人：
   - chart 在 map → STOP，log 該筆「已存在於 MM/DD ROOM TIME」並 skip 該筆 ADD
   - chart 不在 map → 進 Phase 1 ADD
3. 使用者看 log/輸出 → 確認是否要改 day/room/time（手動 DEL+ADD）或 skip
4. Phase 2 UPT 對所有 JSON 病人仍然跑（更新 diag/proc/third）— 因為 UPT 不會誤增重複

**JSON 設計：** 病人 chart 已在當週其他日 → 該筆從 JSON 移除，避免 ADD。要 UPT 該筆 diag/proc → 用對的日期建一筆 JSON entry（cathlab_date 對應實際日）。

**已知例：**
- 康李金春 (15996269) — 5/4 入院、5/6 CRT、不可 ADD 5/5
- 5/3 入院劉廖寶蓮 — 5/5 MTEER（不是 5/4）
- 一般週五入院的「下週一/二」cathlab 也是同類問題