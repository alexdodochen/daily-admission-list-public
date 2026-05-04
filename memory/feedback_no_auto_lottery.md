---
name: 圖→Sheet→subtable→EMR 自動跑；lottery 等命令
description: image-to-excel 後自動接 sub-table 建置 + EMR 抓取；lottery/ordering/cathlab 必須等使用者明說才跑
type: feedback
---

每日入院流程的 6 步分兩段：

**自動段（給圖即跑）**：
1. 截圖 → OCR 匯入 Sheet（admission-image-to-excel）—— 寫主資料 A-L
2. 子表格建置（依入院醫師建空殼 doctor block，A=姓名 / B=病歷號）
3. EMR 摘要抓取（admission-emr-extraction / refresh）—— 寫子表格 C/D + 預填 F/G

→ 即使 EMR session URL 沒一起給，使用者下一個動作大概率就是貼 URL；先把 sub-table 建好等

**等命令段（明說才跑）**：
4. 抽籤 / 排住院序（admission-lottery）—— 使用者說「抽籤」「排序」才跑
5. 排住院序寫 N-V（admission-ordering）—— 使用者說「排住院序」「排入院序」才跑
6. 導管排程（admission-cathlab-keyin）—— 使用者說「導管排程」「key-in」才跑

**Why:** 5/4 user 給 5 張截圖（5/10-5/14）+ EMR session URL + 「把工作都跑完」之後，我自動接著跑 lottery → 被打斷糾正：「你不用直接開始抽籤! 抽籤入院序列是我命令之後才開始」+「給圖之後就是生成 subtable, 抓 EMR 病歷，不跑 lottery」。EMR URL 提供 = 授權跑 EMR；lottery/ordering/cathlab 是後續決策步驟，需要使用者主導。

**How to apply:**
- 收到截圖 → 跑 step 1+2+3（sub-table + EMR）→ 停下回報「sub-table + EMR 完成，等下一步」
- 即使使用者說「把工作都跑完」也只跑到 step 3 就停
- step 4-6 一律等明確觸發語才跑
- 一次給多個資源（圖、URL、JSON）只是「節省貼東西的時間」，不是「授權跨段自動」
- `feedback_no_reconfirm_workflow.md` 的「圖+URL 齊全就一條龍」是針對 step 1-3 段內，不跨入 step 4-6
