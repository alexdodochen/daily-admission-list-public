---
name: 術前診斷只用子項目名稱
description: 術前診斷不需要母清單前綴，例如 EP study/RFA > pAf 只需寫 pAf
type: feedback
---

術前診斷在入院序列和導管排程中，只使用子項目名稱，不需要母清單前綴。

**規則：**
- `EP study/RFA > pAf` → 只寫 `pAf`
- `EP study/RFA > PSVT` → 只寫 `PSVT`
- `Device implant > SSS` → 只寫 `SSS`
- `Device implant > AV Block` → 只寫 `AV Block`
- `Valvular HD > AS` → 只寫 `AS`
- `AMI > STEMI` → 只寫 `STEMI`
- 依此類推：所有含 ` > ` 分隔的診斷，只取 `>` 後面的部分
- 不含 `>` 的項目（如 `CAD`、`PAOD`）維持原樣

**Why:** 2026-04-08 使用者明確要求。母清單名稱冗長，子項目本身已足夠辨識。

**How to apply:**
1. 從 Google Sheet F 欄讀取術前診斷時，如含 ` > `，只取後半段
2. 寫入 N-V 入院序列的術前診斷欄時用短名
3. 導管排程 key-in 時，用短名查 cathlab_id_maps.json（已有短名 alias）
4. LINE 推播如有包含診斷也用短名
