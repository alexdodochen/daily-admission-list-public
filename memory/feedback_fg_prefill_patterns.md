---
name: F/G prefill 該照 plan 的 procedure intent，不是只看 Dx 字串
description: EMR auto-prefill F/G 時 user 的 ground-truth pattern：F 優先看 Plan 的 procedure intent（cath/CAG → CAD、CRT → CHF、ablation → arrhythmia 等），不是看 Dx#1；G 優先看 Plan 關鍵字而非 F→G default。整理自 5/3 5/4 sample 比對。
type: feedback
---

**整理：** EMR auto-prefill 給使用者前，**Claude 應主動比對 Plan section 的 procedure intent，而不是只機械式吃 Dx 字串**。下面是 user 在 5/3 5/4 sample（15 人）上手填 F/G 的 pattern，作為未來 prefill 的權威參考。

## F (術前診斷) 選擇優先序

1. **Plan 的 procedure intent 定義 F（最高優先）**
   | Plan 關鍵字 | F 應為 |
   |---|---|
   | cath study / CAG / cath on / Left heart cath | `CAD` |
   | PCI / primary PCI / plan PCI | `CAD`（不是 STEMI/NSTEMI 除非當下急性發作） |
   | TEER / M-TEER | `MR` 或對應 valve |
   | CRT / cardiac resynchronization | `CHF` |
   | RF ablation / RFA / EP study | `pAf` / `PSVT` / `VPC` / `Atrial flutter` 等 arrhythmia 子項 |
   | PPM / pacemaker | `Sinus nodal dysfunction` / `AV nodal dysfunction` / `Generator replacement` |
   | PTA | `PAOD` |
   | 無 plan keyword | 退回 Dx-based |

2. **Numbered Dx item #1 > ICD-10 description**
   - Dx 寫「1. CAD ... 2. ...」→ F=CAD，不要被 ICD code 描述（如 "Hypertensive heart and chronic kidney disease with heart failure"）拉去 CHF
   - 規則：先抓「* (Dx)」後第一個 numbered item 或第一句

3. **過去 s/p / 歷史不算當下 F**
   - "Inferior STEMI s/p DES (2023/11/03)" → 不要觸發 STEMI rule（這是 s/p 歷史）
   - "post PCI" / "s/p stent" 在 Dx → 看 plan 決定，多半是 CAD f/u
   - **規則**：DIAG_RULES 比對前先把 `s/p ...`、`post ...`、`(\d{4}/\d{1,2}/\d{1,2})` 之後的句子權重降低

4. **Negation 處理**
   - 「No syncope」「No chest pain」「No palpitation」不應觸發對應 rule
   - **規則**：rule keyword 前面有 `No `（含空白）→ skip

5. **angina / unstable / Angina pectoris 一律 → CAD**
   - 已在 `cathlab_keyin.py _normalize_diag()` 強制執行
   - sheet F 也應該 normalize（見 `feedback_diag_angina_false_positive.md`）

## G (預計心導管) 選擇優先序

1. **Plan 關鍵字 authoritative，先於 F→G default**
   - Plan 提到 "CAG" / "cath study" → G=`Left heart cath.`，不論 F 是什麼
   - Plan 提到 "CRT" / "CRT-D" / "cardiac resynchronization" → G=`CRT`
   - Plan 提到 "TEER" / "M-TEER" → G=`Both-sided cath.`（評估 + 同時做）

2. **`ablation` word boundary 檢查**
   - `rotaablation` / `rotational atherectomy` ≠ RF ablation → 不要觸發
   - 規則：用 `\bablation\b` 或前置 `RF |RFA |radiofrequency ` 才當 ablation

3. **valve disease G 留空（user 慣例）**
   - F=MR / AR / AS / TR 且 plan 沒明確寫 percutaneous procedure → G 留空（討論時決定）
   - 不要套 F_TO_G_DEFAULT 強塞 `Both-sided cath.`

4. **CRT 偵測強化**
   - F=CHF + Plan 有 LVEF < 35% + Plan 有 "CRT" / "biventricular pacing" → G=`CRT`
   - 不要被 "intervention" 誤導去 PCI

## 已知 5/3 5/4 sample 對照（15 人，10 case 有偏差）

| 病人 | 病歷號 | auto F→user F | auto G→user G | 主要學習點 |
|---|---|---|---|---|
| 陳薏安 | 18385859 | CHF→CAD | RF ablation→Left heart cath. | ICD desc 不蓋 Dx#1；rotaablation 誤吃 |
| 周明仁 | 22718712 | pAf→CAD | (同) | Plan="Cath study" 蓋多項 Dx |
| 謝添福 | 07085851 | Syncope→CAD | PCI→Left heart cath. | Dx#1 是 CAD/3VD，syncope 從別處吃到 |
| 吳峰欽 | 23312840 | Syncope→CAD | (同) | "No syncope" negation |
| 林怡昌 | 21295052 | STEMI→CAD | (同) | 過去 NSTEMI 病史不算 |
| 郭清波 | 20561025 | STEMI→CAD | (同) | s/p DES 是 s/p 歷史 |
| 黃茂盛 | 00398109 | VPC→CAD | (同) | "CAD with angina like symptoms" Dx 應該贏 |
| 李淑眞 | 08290843 | VPC→CAD | RF ablation→Left heart cath. | Dx#1 VPC 但 plan=CAG → 走 CAD/cath |
| 劉廖寶蓮 | 18750900 | (F對) | Both-sided cath.→空白 | valve disease G 留空 |
| 康李金春 | 15996269 | (F對) | PCI→CRT | F=CHF + 低 EF → CRT，不是 PCI |

## How to apply

1. **EMR auto-prefill 給 user 看之前**，Claude 跑這個檢查清單：
   - (a) Plan section 有沒有 procedure keyword？有就 override 對應 F
   - (b) Dx 是 numbered list？取 #1，並把 s/p / post / 含日期的歷史描述忽略
   - (c) Negation：keyword 前有 `No ` → skip
   - (d) angina/unstable → CAD（已在 code）
   - (e) G：先看 plan keyword，valve disease 留空，rotaablation 不算 RF
2. **不需要動 process_emr.py code**（除非使用者明示）— Claude 在 prefill 給 user 看的步驟做 normalize
3. **若 unsure**：列幾個候選給 user 選，不要自作聰明
