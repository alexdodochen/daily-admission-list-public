---
name: 入院清單本地 App v2（此 user 機器）+ 公開 repo
description: FastAPI + 三家 LLM 本地版 app/；公開 repo public_daily_admission_app；私→公自動同步 + 客戶端 auto-updater
type: project
originSessionId: db63619a-c7b1-4350-ba96-fa897a57c0d0
---
## Repo 與位置
- **私有 source**：`D:\心臟內科 總醫師\行政總醫師\每日入院名單\.claude\worktrees\friendly-solomon-026502\`
  branch `claude/friendly-solomon-026502`，latest commit a7d820b（已 push 到 origin，CI 跑中/綠）
- **公開 repo**：https://github.com/alexdodochen/public_daily_admission_app（最新同步 a7d820b）

## 狀態（2026-04-18 兩次 session 累積）

### app/ 已實作
- FastAPI 26 routes + Jinja2 + 無框架 vanilla JS
- **LLM 抽象層**：Anthropic / OpenAI / Gemini（`app/llm/` 各自 provider class）
- 設定頁 `/settings` + 測試連線（同時 ping LLM & Sheet）
- **6 步驟**：
  - Step 1 OCR 截圖 → LLM vision → A-L ✅
  - Step 2 抽籤 + round-robin → N-S ✅
  - Step 3 EMR Playwright + LLM 4 段摘要 ✅
  - Step 4 讀子表格 F/G → N-W 整合 ✅
  - Step 5 cathlab：**verify + plan + keyin 全部完成**（static data：`app/data/static/cathlab_id_maps.json` / `cathlab_schedule.json` / `doctor_codes.json`；Phase 1 ADD + Phase 2 UPT，非時段自動 2100+ 並加備註「本日無時段」）
  - Step 6 LINE 推播 N-Q 四欄到 group ✅

### 商用軟體式更新基礎建設
- **客戶端 auto-updater**（`app/services/updater.py`）：
  - 頁面載入時自動 `GET /api/update/check`（打 GitHub API）
  - 有新版 → topbar 黃色徽章 + 「更新」按鈕
  - 按更新 → `git pull --ff-only` → 選擇性 `os.execv` 重啟
  - 非 git checkout（下載 zip）會顯示提示改用 git clone
- **私→公 sync**：
  - `scripts/sync_to_public_app.py`：stage → clone public → mirror → commit → push
  - `.github/workflows/sync-public-app.yml`：push main 到 private repo 且 `app/**` 有動 → 觸發同步
  - 需在私 repo 設 `SYNC_TOKEN` secret（PAT with `repo` scope on public repo）
  - 每次同步寫 `app/VERSION`（JSON：sha + built_at）給非-git 使用者的 updater 比對

## 待做
- Step 5 實機 keyin 完整 end-to-end 演練（plan/verify 測過；ADD+UPT 尚未真實 WEBCVIS 驗證）
- 若需 CI 在公開 repo 也跑：用 `gh auth refresh -s workflow` 或在 SYNC_TOKEN 加 workflow scope，然後把 `.github/workflows/pytest.yml` 納入 sync 白名單
- （可選）Playwright-heavy 路徑 e2e 整合測試（cathlab._add_patient / _upt_patient 目前只覆蓋純邏輯）

## 已完成（2026-04-18 第二次擴充）
- Step 4 inline F/G 編輯：子表格 F/G 欄變 contenteditable，blur 直接寫入 Sheet
- Step 5 第二主治醫師：從備註抽 浩/寬/晨/嘉/軨，葉立浩優先
- Step 5 multi-slot：schedule 改成 list 結構，`compute_all_slots()`／`compute_slot(prefer_session=)`；備註 "下午/PM/晚" 自動選 PM，張獻元 Tue 同日自動選 PM
- pytest：**113 cases**（cathlab_service + cathlab_enrich_plan / lottery / ordering / line / updater / ocr / emr / llm extract_json / config / main endpoints with FastAPI TestClient），`python -m pytest tests/` 0.4s 全綠，0 gspread/Playwright/LLM 真實 call
- CI：`.github/workflows/pytest.yml`（push / PR on app|tests|pytest.ini），私有 repo 上 CI 綠
- 同步腳本補強：mirror tests/ + pytest.ini 到公開 repo；刻意排除 `.github/workflows/`（OAuth token 少 workflow scope）
- private branch `claude/friendly-solomon-026502` 已 push 到 origin（有 backup + CI）
- **bug fix**：`extract_json` 原本永遠偏好 `[` opener，遇到 `{"outer":{"inner":[1,2]}}` 會被誤切成 `[1,2]`；改成取最早出現的 opener
- **bug fix (latent)**：`.gitignore` 的 `_*.py` 會意外匹配 `__init__.py`（glob `*` 可包含下底線），所以 `app/__init__.py` / `app/llm/__init__.py` / `app/services/__init__.py` 一直沒被 git 追蹤。本地跑 ok 因為檔案存在；先前 CI 綠是 PEP 420 namespace package 巧合地能支援簡單 import。這次新增 endpoint 測試觸發 `from ..llm import get_llm` 才露餡。修法：加 `!__init__.py` / `!__main__.py` negation + force-add 三檔

## 設定 `SYNC_TOKEN`
1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained token
2. Repo access：only `public_daily_admission_app`
3. Permissions：Contents (Read+Write), Metadata (Read)
4. 複製 token → 私有 repo Settings → Secrets and variables → Actions → New → name=`SYNC_TOKEN`

## 跑起來
```bash
# clone 公開 repo（任一使用者都行）
git clone https://github.com/alexdodochen/public_daily_admission_app
cd public_daily_admission_app
pip install -r requirements.txt
playwright install chromium  # 只為 Step 3/5 需要
python -m app.run            # 自動開瀏覽器 127.0.0.1:8766
```

**Why:** 實作了真正商用軟體式流程：私有 source 開發 → 自動鏡像到公開 → 使用者端自動提示更新
**How to apply:** 下次 session 要繼續直接 `cd worktrees/friendly-solomon-026502 && python -m app.run`
