# Service Account 金鑰權限

**檔名**：`sigma-sector-492215-d2-0612bef3b39b.json`

**Service Account 資訊：**
- 帳號：`admission-bot@sigma-sector-492215-d2.iam.gserviceaccount.com`
- 專案：`sigma-sector-492215-d2`
- Client ID：`109046374969194072927`

**授權範圍（Scopes）：**
- `https://www.googleapis.com/auth/spreadsheets` — Google Sheets 完整讀寫
- `https://www.googleapis.com/auth/drive` — Google Drive 完整存取

**實際能做什麼：**
- 讀寫該 service account 被共享的 Google Sheets
- 建立/刪除工作表
- 格式化、資料驗證、批次更新
- 存取被共享的 Drive 檔案

**限制：**
- 只能存取明確共享給 `admission-bot@...` 的文件，無法看到個人 Drive 的其他檔案
- 目前只共享了一份 Sheet（ID: `1DTIRNy10Tx3GfhuFq46Eu2_4J74Z3ZiIh7ymZtetZUI`）

**注意：**
- 此檔案已加入 `.gitignore`，不會被 commit 到 repo
- Claude Code 雲端環境的網路代理會擋 `sheets.googleapis.com`，需在本機執行相關腳本
