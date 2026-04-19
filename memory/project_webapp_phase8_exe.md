---
name: Phase 8 — 本地 app 打包成年度交接 exe
description: 將 public_daily_admission_app 打包為雙擊 exe，供每年行政總醫師接手使用；預埋憑證 + 最小設定
type: project
---

## 決策（2026-04-19）

| 項目 | 決定 |
|---|---|
| 目標使用者 | 每年新任行政總醫師（~1 人），非工程背景 |
| Per-user 編輯紀錄 | **不需要**（Sheet 編輯者統一顯示 service account 即可） |
| 部署模式 | 各自電腦跑（不做中央 server） |
| 發行形式 | 雙擊 **PyInstaller `--onedir` exe**（不是 `--onefile`） |
| Chromium | **首次啟動下載**（不 bundle，exe 檔案小，每台機器各自抓） |
| Service account | **年度輪替** — 每年換新 JSON，舊的在 GCP 作廢 |
| Repo 策略 | **退休私有 source，`alexdodochen/public_daily_admission_app` 為唯一 repo** |

## 預埋 vs 使用者自填

**exe 內建預設（不用使用者知道）：**
- Service account JSON（包進 `app/data/`）
- Sheet ID（`1KR9fyszCFvoPmV9-9cGqSpf6kFNRC6je8BjUNaY2Pc0`）
- EMR base URL（`http://hisweb.hosp.ncku/Emrquery/`）
- WEBCVIS base URL
- LINE token（成醫-心內群組，交接時輪替）
- LLM provider 預設 Gemini（免費 tier）

**設定頁只留 3 格：**
- LLM API key（自己去 AI Studio 申請）
- WEBCVIS 帳密（院內帳號）
- LINE 覆寫（通常留空）

## 實作 TODO（執行順序）

1. **退休私有 source** — 到 OPD 關掉 `每日入院清單_本地化/` 的 sync 腳本（不然會覆蓋 public mirror 上的 Phase 8 commits）
2. **`config.py` 改支援 bundled defaults** — 偵測 exe 內建的 config 模板 → 複製到 `app/data/config.json`，首次啟動預填
3. **設定頁 UI** — 隱藏已預填欄位，只露 LLM key / WEBCVIS / LINE 覆寫
4. **Chromium 首次下載邏輯** — 啟動時檢查 `playwright install chromium` 是否跑過，沒跑過先跑
5. **PyInstaller spec** — `--onedir --windowed --add-data "app/data/static;..." --add-data "sigma-...json;app/data/"`
6. **交接手冊** — 一頁 PDF：申請 Gemini API key + 啟動 app

## 年度交接流程（admin 做的事）

每年 7 月新任行政總上任前：
1. GCP 建新 service account `admission-bot-fellow-2027`
2. 加進 `1KR9fy...` sheet 編輯者
3. 重新打包 exe（換掉預埋 JSON）
4. 舊 service account 在 GCP 作廢
5. LINE token 視需要輪替（如果換群組或換 channel owner）
6. 把 exe 資料夾 + 手冊 zip 給新任

**Why:** 年度交接 + 非技術使用者，需要零技術門檻的雙擊啟動體驗；預埋憑證避免每年要教新人 GCP / Sheet 共用；service account 輪替限制離職人員後續存取。

**How to apply:**
- 規劃本地 app 的 deployment、打包、交接流程時參考這份
- 討論 Phase 8 先做什麼、Phase 7 是否要先完成再打包時，以這份的 TODO 順序為準
- 若有人問「為什麼不用 OAuth」→ 決策記錄在此：per-user 編輯紀錄不需要，OAuth 對非技術醫師門檻太高
