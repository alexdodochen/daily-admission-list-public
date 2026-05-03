---
name: Public mirror sync — daily-admission-list-public
description: 私有 repo 推 commit 時自動 sync 到 public mirror（給其他行政總醫師 clone）；千萬不要從 public 拉回 local；public 用不同 Sheet ID
type: project
---

## 兩個 repo

| 角色 | URL | Sheet ID |
|---|---|---|
| **私有（我們的）** | https://github.com/alexdodochen/daily-admission-list | 見 `memory/_private_setup.md`（gitignored） |
| **公開 mirror** | https://github.com/alexdodochen/daily-admission-list-public | `1u2FZE6-Ldich_b2jI-i0gNnxu1ZsZtZ2Ra6ffCU2Er8` |

公開 mirror 給別的行政總醫師 clone 來用，他們可以自由改自己的 clone。

## Git remote 設定（已部署 2026-05-01）

`origin` 設定成 dual push URLs（fetch 只有私有那一個）：

```
origin  https://github.com/alexdodochen/daily-admission-list.git (fetch)
origin  https://github.com/alexdodochen/daily-admission-list.git (push)
origin  https://github.com/alexdodochen/daily-admission-list-public.git (push)
```

→ `git push origin main` 自動推兩邊（私有 + 公開）
→ `git fetch origin` / `git pull origin` 只動私有（fetch URL 唯一）
→ 沒有 `public` 這個 remote → `git pull public ...` 結構上不可能發生

## Why

- 使用者 2026-05-01 規則：「我們的 update 都同步到 public，但 public 的 update 千萬不要 pull 回來」
- Public 上其他人可能會 push 自己的改動 — 我們不關心、不合併
- 結構性禁止 pull 是最強防線（比靠記性可靠）

## How to apply

**每次 commit 完直接 `git push origin main`** — 兩邊都會更新。不用切 remote、不用做兩次 push。

**不要做的事：**
- ❌ 不要 `git remote add public <public_url>` — 只要 public 是 named remote 就有風險被 pull
- ❌ 不要 `git fetch <public_url>` — 即使 ad-hoc 也會在本地建 FETCH_HEAD
- ❌ 不要 force-push 到私有 origin — 會連帶 force-push public 蓋掉別人的 commit（如果 public 已經有別人的 commit）

**Public 已分歧（別人 push 過）的話：**
- 我們的下次 push 會在 public URL fail（non-fast-forward），私有 URL 會成功
- 處理方式：另開 ad-hoc 命令 `git push https://github.com/alexdodochen/daily-admission-list-public.git main --force` 強推（我們是 source of truth；別人 push 到 public 的內容由他們自己 fork 保留）
- 不要把 public 的歷史 merge 回私有

## Sheet ID 分歧（已實作 2026-05-01）

`gsheet_utils.py` 改成：

```python
try:
    from local_config import SHEET_ID
except ImportError:
    SHEET_ID = '1u2FZE6-Ldich_b2jI-i0gNnxu1ZsZtZ2Ra6ffCU2Er8'  # public default
```

- 我的本地有 `local_config.py`（gitignored，含私有 `SHEET_ID`）→ runtime 走私有 sheet
- Public clone 出去的人沒 `local_config.py` → 走 public demo sheet 預設值
- `local_config.py` 在 `.gitignore`，不會推到 public

公開 sheet `1u2FZE6...` 是大家共用的（user 2026-05-01 確認），不是每人各一份。

私有 SHEET_ID 已從所有 tracked 文件清掉（2026-05-03），集中保存在 `memory/_private_setup.md`（gitignored）。Public mirror 看不到任何私有值 → 結構上不可能寫到私有 sheet。

## 服務帳戶 JSON

`sigma-sector-492215-d2-0612bef3b39b.json` 已在 .gitignore，不會推到 public。
別的行政總醫師需要自備 service account（或共用一個由 user 透過私下管道提供），share 公開 sheet 給該帳戶。

歷史驗證（2026-05-03）：`git log -p -S "BEGIN PRIVATE KEY"` 0 命中 — JSON 內容**從沒**進入過任何 commit。public repo 歷史會看到的私有 metadata 是 service account email、project ID、舊私有 SHEET_ID 字串，但這些**不能**登入 Google API（沒 private key 一切免談）。User 2026-05-03 接受不做歷史 rewrite。

## LINE 推播功能：public 不存在（2026-05-03 規則）

LINE 推播 bot（`alexdodochen/line-reminder-bot`）讀的是**私有 sheet**，跟 public mirror 完全無關 — public sheet 沒被 share 給 bot 的 service account，bot 也不知道 public sheet ID 存在 → public sheet 永遠不會被推播。

但 **LINE bot infra metadata** (URL / endpoint / Bot ID / cron schedule) 已從所有 tracked 檔案撤除：
- 步驟五整段移到 `_step5_line_push.md`（gitignored）
- 三份 LINE 相關 reference memory 加 `_` 前綴 → gitignored：`_reference_line_reminder_bot.md` / `_reference_line_monthly_quota.md` / `_reference_cronjob_render_gotchas.md`
- 工作流程 txt 由 7 步縮為 6 步（步驟五 = cathlab keyin、步驟六 = 清暫存）
- CLAUDE.md overview 的「LINE notifications」字眼移除

**未來新增 LINE 規則 / bot 細節 → 一律寫到 `_*.md`（root 或 memory/）**，不要寫進 tracked 檔案。

## Push-time 護欄（2026-05-03 部署）

- `scripts/pre_push_check.py` — 掃 tracked 檔案禁忌字串：私有 SHEET_ID、bot URL、bot ID、`trigger-*` endpoint 路徑、PEM private key block（具體 regex 見該腳本的 `FORBIDDEN` list）
- `.githooks/pre-push` — git hook 自動跑 check
- 一次性 setup（每台 clone）：`git config core.hooksPath .githooks`
- 命中 → push 中止；不要用 `--no-verify` 繞，違規內容應搬到 `_*.md`
- 加新禁忌字串 → 改 `scripts/pre_push_check.py` 的 `FORBIDDEN` list（描述 + regex）
