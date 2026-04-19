---
name: 入院清單 Web App 改造計畫
description: 每日入院清單本地化 Web App（FastAPI+PyQt5），Phase 1-4 已完成，專案在 每日入院清單_本地化/
type: project
---

## 專案位置
`C:\Users\OPD\Desktop\Fellow 資料夾\每日入院清單_本地化\`

## 已完成（2026-04-08）

### Phase 1: 骨架 + 認證 + 設定
- FastAPI + PyQt5 QWebEngineView（port 8766）
- JWT + bcrypt 認證（從 NCKUH_Scheduler 移植）
- LLM 設定頁（Anthropic Claude API / OpenAI）
- 6 步驟 stepper 主畫面
- WebSocket 即時通訊

### Phase 2: Step 1 — OCR 匯入
- `services/ocr_service.py`：LLM vision OCR + 醫師名校正 + 病歷號驗證
- 前端：圖片拖曳/貼上上傳 → AI 辨識 → 表格預覽（可編輯病歷號）→ 確認寫入 Sheet
- API：`POST /api/step1/ocr` + `POST /api/step1/confirm`

### Phase 3: Step 2 — 抽籤排序
- `services/lottery_service.py`：讀取抽籤表 + 隨機抽籤（*2雙籤）+ Round-Robin
- 前端：載入醫師 → 執行抽籤 → 顯示結果 → 寫入 Sheet N-P 欄
- API：`GET /api/step2/schedule/{date}` + `POST /api/step2/lottery`

### Phase 4: Step 4 — 下拉選單 + 入院序整合
- `services/ordering_service.py`：讀取醫師子表格 + F/G inline 編輯 + N-U 整合
- 前端：醫師病人表格含 F/G 下拉選單（即時同步 Sheet）→ 整合入院序按鈕
- API：`GET /api/step4/dropdowns` + `GET /api/step4/doctors/{date}` + `POST /api/step4/cell` + `POST /api/step4/ordering`

## 待實作
- **Phase 5**: Step 3 — EMR 擷取（Playwright + LLM 摘要）
- **Phase 6**: Steps 5+6 — LINE 推播觸發 + 導管排程自動化（Playwright WEBCVIS）
- **Phase 7**: ✅ 2026-04-20 完成 — `format_check_service` + `finalize_service`（定案檢查清單），含前端 UI + 32 tests
- **Phase 8**: 進行中 — bundled defaults / packaging.spec / BUILD.md / HANDOFF.md 已就位；**pending: 實跑 pyinstaller + Chromium 首次下載邏輯**（詳見 `project_webapp_phase8_exe.md`）

## 技術筆記
- Starlette 1.0: 用 `_render()` helper 包裝 TemplateResponse keyword args
- gsheet 同步函數用 `asyncio.to_thread()` 包裝
- cathlab keyin 改為資料驅動（不再一天一個腳本）
- Port 8766 避免與 NCKUH_Scheduler 8765 衝突

**Why:** 所有人都能用入院清單系統，各人登入自己的 LLM
**How to apply:** 下次說「繼續本地化 Phase 5」開始 EMR 擷取
