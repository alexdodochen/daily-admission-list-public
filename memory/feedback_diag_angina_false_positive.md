---
name: DIAG_RULES 'angina' 對 TET 報告誤判
description: process_emr.py DIAG_RULES 的 bare 'angina' 關鍵字會吃到 TET 報告裡的 "Angina Index" 字串，把該病人 F 欄誤判為 Angina pectoris；實際 Dx 通常是 r/o CAD
type: feedback
---

**規則：** EMR 含 TET (treadmill exercise test) 報告且病人實際 Dx 是「r/o CAD」時，`detect_fg()` 會回傳 `('Angina pectoris', 'Left heart cath.')`，因為 DIAG_RULES 第 55 行的 `(['angina pectoris', 'angina'], 'Angina pectoris')` 規則的 bare 'angina' 子字串會匹配到 TET 報告裡的「Angina Index:0.No angina during exercise」這一行。

**典型誤判場景：**
- 病人 Dx：`* (Dx)r/o CAD`、`Chronic ischemic heart disease`、`chest pain`
- 同時 EMR 含 TET 報告（運動心電圖）
- 預填 F 欄：誤寫 `Angina pectoris`，正解應為 `CAD`

**已知實例：**
- 2026-04-23 沈益川 (15015060) — Dx 是 r/o CAD + TET 報告，預填變 Angina pectoris，使用者手動改 CAD

**Why:** DIAG_RULES 規則順序是 angina 在 CAD 之前（CAD 是 broadest 故放最後），但 'angina' 沒做 word boundary，TET 報告裡的「Angina Index」這個 metric 名稱會被誤吃。
**How to apply:**
1. EMR auto-prefill 後若 F=Angina pectoris，檢查 EMR 是否含 TET 報告（搜尋 `Angina Index`）；若 Dx 主訴其實是 r/o CAD/chest pain，列出讓使用者確認改 CAD
2. 改 F 欄後同步：(a) 子表格 F 欄、(b) WEBCVIS 已 keyin 的 entry（UPT 修術前診斷）、(c) 入院序 N-V 的 T 欄（如已寫入）
3. 長期解法：考慮把 DIAG_RULES 第 55 行改成 `'angina pectoris'` 單一關鍵字，移除 bare 'angina'；目前未動 code 因為怕影響其他病人
