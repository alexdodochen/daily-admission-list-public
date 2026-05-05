---
name: feedback_cathlab_id_maps_only
description: cathlab_keyin 的 PDI/PHC ID 一定從 cathlab_id_maps.json 載入，絕不在 .py 內硬編，否則會 push 錯資料進 WEBCVIS
type: feedback
originSessionId: a237e859-cb18-4efd-8aa5-0e8ae104bf8e
---
cathlab keyin 流程的 `pdijson` / `phcjson` 必須帶 WEBCVIS 認得的精確 ID 字串（如 `PDI20090908120009`）。
這些 ID 由 `cathlab_id_maps.json`（66 diag + 22 proc 已驗證）統一管理。

**禁止在 `cathlab_keyin.py` 或任何 per-date script 內硬編 `DIAG_IDS = {...}`**，因為：
1. 我（Claude）不知道院方完整 ID 表，硬編就是猜，極易猜錯
2. 真實踩過的例子：第一版 `cathlab_keyin.py` 我把 SSS 寫成 `PDI20090908120038`（其實那是 Sinus nodal dysfunction 的舊代碼，SSS 真值 = `PDI20090908120026`）。同樣 PTA 我寫 `PHC20090907120010`（錯，真值 `PHC20090907120007`）

**Why:** 錯 ID 會 push 進 WEBCVIS 變成「對的病人 + 錯的診斷/術式」，比 missing 更難察覺，事後要逐筆 UPT 修。

**How to apply:**
- `cathlab_keyin.py` 的 `DIAG_IDS` / `PROC_IDS` 起始為 `{}`，啟動時從 `cathlab_id_maps.json` 載；檔案不存在直接 `SystemExit`，不要 fallback
- 新術式/診斷在 WEBCVIS 沒對應 ID → 報「ID 缺失」由使用者去 WEBCVIS 查，更新 cathlab_id_maps.json，不要自己猜
- 任何 per-date script（被 cathlab_keyin.py 取代後不該再寫）也適用同規則
