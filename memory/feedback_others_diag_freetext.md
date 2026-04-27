---
name: 術前診斷「Others:XXX」走 Others 母項 + 全字串 freetext
description: 子表格 F 欄寫「Others:DVT」之類自定 Others 子項時，cathlab keyin 用 Others 母 PDI (PDI20090908120008) + name 帶全字串「Others:DVT」。不用為每個 Others 子項在 cathlab_id_maps.json 加新 ID。
type: feedback
---

**規則：** 使用者在子表格 F 欄（術前診斷）寫 `Others:XXX`（XXX 為任意自訂內容，如 `Others:DVT`、`Others:Aortic dissection`），cathlab keyin 時：

1. **PDI ID** = `PDI20090908120008`（WEBCVIS 的「Others」母項 / 通用 Others）
2. **name 欄** = 使用者寫的完整字串（如 `"Others:DVT"`），WEBCVIS UI 顯示為 Others 選中 + freetext 為使用者寫的內容

**Why:**
- WEBCVIS PDI tree 對「Others」母項提供一個固定 ID + freetext 子項輸入欄位
- 過去 `cathlab_id_maps.json` 為每個常見 Others 子項手動建獨立 mapping（如 `Others:recent MI` → PDI...11），但對少見的子項（如 `Others:DVT`）會缺漏 → keyin 時 F 欄空 → WEBCVIS entry 沒診斷
- 使用者明示：「以後若我在術前診斷寫 Others:DVT 你就幫我選 Others 那個選單，自己 key 我寫的項目」(2026-04-27)
- 使用 PDI20090908120008 作 fallback 的依據：cathlab_id_maps 內 `Others:opd` 和 `Others:s/p HTx` 兩條歷史紀錄都對應此 ID，推測為通用 Others 母項

**How to apply:**
1. `cathlab_keyin.py` 已加 `OTHERS_PDI = 'PDI20090908120008'` + `_resolve_diag_id()` helper：F 字串開頭為 `Others:` 且不在 DIAG_IDS map 時，自動 fallback
2. `_build_json` 帶入 name = 完整 F 字串（`Others:DVT`），不要拆掉前綴
3. 不要為每個 `Others:XXX` 在 `cathlab_id_maps.json` 內新增條目 — fallback 已涵蓋
4. 如果 fallback 後 WEBCVIS 顯示異常（例如 freetext 沒 stick），把實際觀察到的 ID 寫回 memory 修正

**已知實例：**
- 2026-04-27 張連財 (11750894, 4/28 入院) — F=`Others:DVT` 第一次 keyin 時 fallback 規則尚未實作，WEBCVIS entry F 欄空。code 修補後此 case 規則生效，未來自動處理
