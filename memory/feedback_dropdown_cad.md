---
name: 術前診斷下拉清單必須包含 CAD
description: 入院名單術前診斷 dropdown (下拉選單!A2:A66) 必須有 CAD 選項，即使 CAD 是母分類
type: feedback
---

入院名單系統的 術前診斷 (subtable 欄位 F，使用 `'下拉選單'!$A$2:$A$66`) 必須包含 `CAD` 作為可選項。

**Why:** CAD 在分類學上是 STEMI/NSTEMI/Stable/Unstable/PCI 等子分類的母分類，但實際使用上 user 經常需要直接選 `CAD` 而不指定子型。User 已多次提醒這件事，表示之前曾被誤刪或漏加。

**How to apply:**
- 任何時候建立或重建 `下拉選單` 工作表的 A 欄（術前診斷清單），都要確保 `CAD` 在裡面。
- 任何時候 dropdown 範圍可能漏掉 CAD（例如把它刪到範圍外），要補回來。
- 不要因為 CAD 是「母清單」就移除——user 明確要求保留。
- 目前 CAD 位於 `下拉選單!A60`。
