---
name: Public mirror sync — daily-admission-list-public
description: 私有 repo 推 commit 時自動 sync 到 public mirror（給其他行政總醫師 clone）；千萬不要從 public 拉回 local；public 用不同 Sheet ID
type: project
---

## 兩個 repo

| 角色 | URL | Sheet ID |
|---|---|---|
| **私有（我們的）** | https://github.com/alexdodochen/daily-admission-list | `1DTIRNy10Tx3GfhuFq46Eu2_4J74Z3ZiIh7ymZtetZUI` |
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

## 待處理：Sheet ID 分歧

`gsheet_utils.py` 目前 hardcode 私有 Sheet ID。Public clone 出去的人會打不到自己的 sheet。
解法待定（候選：`local_config.py` 覆寫 + 公開預設值；或 env var）。
其他 hardcode 位置：CLAUDE.md / 每日入院清單工作流程.txt / .claude/skills/admission-image-to-excel/SKILL.md / memory/feedback_all_data_to_google_sheet.md。

## 服務帳戶 JSON

`sigma-sector-492215-d2-0612bef3b39b.json` 已在 .gitignore，不會推到 public。
別的行政總醫師需要自備 service account + 自己 share 自己的 sheet 給該帳戶。
