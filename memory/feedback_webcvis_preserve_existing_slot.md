---
name: WEBCVIS 既有排程時間/檢查室/主刀維持不動
description: cathlab keyin 時若病歷號已在 WEBCVIS 存在（ADD SKIP），不要再另開 UPT 腳本去改時間/檢查室/主刀醫師，F/G 的 UPT 照舊可做
type: feedback
---

Cathlab keyin 跑完後若發現 ADD 全部 SKIP（病人已存在於 WEBCVIS），**不需要**另寫 UPT script 把 examroom/inspectiontime/attendingdoctor1/attendingdoctor2 改成 memory 規範的值（AM 0600+、PM 1800+、蘇奕嘉 2nd 等）。既有 slot 保持原狀即可。

**Why:** 既有排程可能是使用者或他人根據當下現場狀況手動調整過（例如房間借用、時段協調），Claude 不該用「規範」反向覆蓋現場決策。F/G 是臨床診斷資料，UPT 對齊是 OK 的；時間/房間/主刀屬於現場安排，要尊重。

**How to apply:**
- Phase 1 (ADD) 若全 SKIP，Phase 2 (UPT F/G) 跑完、Phase 3 (Verify) 通過就算完成，不要提議「再寫一個 UPT 腳本改時間/檢查室/主刀」。
- 只有在驗證階段發現 F/G 不符時才需追加 UPT F/G（原本流程就會做）。
- verify_cathlab.py 只檢查 name+F+G，這樣的驗證範圍已足夠。
