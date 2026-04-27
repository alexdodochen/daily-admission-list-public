---
name: Angina 族群 F 欄一律 key CAD
description: 凡 EMR 讀到 angina / unstable angina / Angina pectoris，F 欄統一寫 CAD（不寫 Angina pectoris / Unstable）。原因之一：DIAG_RULES 'angina' 會被 TET 報告的 Angina Index 誤觸。
type: feedback
---

**通用規則（2026-04-24 使用者明訂）：**
EMR auto-prefill 出現下列任一字串時，F 欄一律改 `CAD`，**不要**保留 auto-detect 的 `Angina pectoris` 或 `Unstable`：
- `Angina pectoris`
- `Angina` (含 Angina Index false positive)
- `Unstable` / `Unstable angina`

**Why:**
- `process_emr.py` 的 DIAG_RULES 第 55 行 `(['angina pectoris', 'angina'], 'Angina pectoris')` 的 bare 'angina' 會吃到 TET 報告中的「Angina Index」字串，把 r/o CAD 病人誤判。
- 另外 'Unstable' 會吃到 EMR 中「unstable angina」這類片語，但臨床上 F 欄只需要寫根診斷 CAD。
- 使用者的慣例是在 cathlab/住院系統 F 欄一律用 **CAD** 當大項，不細分 stable/unstable/angina，下拉選單也是這樣設計。

**How to apply:**
1. EMR auto-prefill 結果給使用者前，自動把 `Angina pectoris` / `Unstable` → `CAD`（不要再問）
2. 若整串 F 只剩 "CAD"，寫入 (a) 子表格 F 欄、(b) N-V 入院序 T 欄、(c) WEBCVIS 已 keyin 的 entry 用 UPT 修術前診斷
3. **`cathlab_keyin.py` 已加 `_normalize_diag()` (2026-04-27)**：傳給 add/UPT 的 diag 字串若含 angina/unstable，code 自動轉 CAD（pdijson 名稱 + prediagnosisitem 顯示欄一致）→ 即使 sheet F 漏改、Claude 漏 normalize，cathlab WEBCVIS 不會再吃到 Angina pectoris
4. 長期解法（已部分落實）：cathlab_keyin 強制 normalize，process_emr.py DIAG_RULES 仍未動，下次 prefill 仍可能跑出 Angina pectoris 給 sheet — 至少 cathlab 那邊不會錯

**已知實例：**
- 2026-04-23 沈益川 (15015060) — TET 報告 Angina Index false positive，使用者手動改 CAD
- 2026-04-24 王仕由 (20945333, 4/28 入院) — 20251204 門診「Angina++」被 detect，使用者改 CAD
- 2026-04-24 陳中坤 (20444550, 4/28 入院) — EMR 中 "Unstable" 被吃到（ICD 41401=Unstable angina），使用者改 CAD
