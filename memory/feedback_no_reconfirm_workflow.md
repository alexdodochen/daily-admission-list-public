---
name: 工作流步驟不要反覆確認
description: User 已經給明確指令 + 完整資料（圖、session URL、病歷號）時，直接一口氣跑完整個工作流，不要停下來問「要執行嗎？」「要繼續嗎？」。工作流含: image-to-excel → lottery → EMR → ordering → cathlab。
type: feedback
originSessionId: 726bb693-3593-4f39-838b-e29a5122e8cb
---
# 工作流步驟不要反覆確認

**Rule：** 當 user 的指令是完整的（提供圖片 + EMR session URL + 工作項目名稱），Claude 應該從頭到尾跑完該指令涵蓋的所有 workflow steps，**不要在每個 phase 結束後停下問 "要繼續嗎？"**。

**Why：** User 2026-04-21 明說「每次都直接跑 不用問」。之前 Claude 在 Phase A 完成後、EMR 前、lottery 前都停下問一次，user 覺得多餘。指令本身已是授權，不需要分段確認。

**How to apply:**
- 收到「更新 X 日入院清單 + session URL」→ 直接 image-diff → 子表格 surgery → 格式驗證 → EMR extraction → 寫回 F/G → ordering（如需要）一條龍跑完
- **已有成文規則的場景直接套用，不要額外確認**：例如非時段醫師 cathlab = H1 2100+ / note="本日無時段" 是 CLAUDE.md rule #7 + `feedback_cathlab_times.md`，不需要再問「要排哪間」。2026-04-23 session 誤問「詹週五 PM 要排哪間」被糾正「routine key H1 2100 嗎 還問」。
- 例外（才要停）：
  - 出現錯誤/rate limit 無法自動解
  - 需要 user 手動補資料（例如 EMR session 過期要重貼、F/G 下拉選單沒有對應項要手選）
  - user 明確在本次 session 中臨時 pause
  - 規則明顯衝突需要 user 裁決（e.g. CLAUDE.md vs 現場 Sheet 對不上）
- 格式檢查依然必跑（`admission-format-check` skill / CLAUDE.md rule 17），只是不用先問 user
- 過程中每個 phase 給 1 行 status 更新就好，不要問允許
