---
name: workflow-docs
description: End-of-session review + workflow doc sync. 掃描本次對話的變更、更新 memory、評估 skills、修正工作流程 txt / CLAUDE.md，最後 commit + push 到專案 GitHub repo。Trigger on "/workflow-doc", "/workflow-docs", "更新工作流程", "同步說明文件", "產生操作說明", or 主動於 skill/memory/規則異動後觸發。
---

# 工作流程說明文件同步（含 session review）

## Overview
本 skill 將「每次對話結束的回顧」與「工作流程文件同步」合併為單一流程：
1. 盤點本次 session 的變更
2. 更新 memory
3. 評估 skills 是否需修正
4. 更新工作流程 txt / CLAUDE.md
5. Commit + push 到關聯的 GitHub repo（含 `.claude/skills/`）

## When to Use
- 使用者輸入 `/workflow-doc` 或 `/workflow-docs`
- 使用者說「更新工作流程」「同步說明」「產生操作說明」
- **主動觸發**：新增/修改 skill、更新 memory 規則、修正工作流程錯誤之後

---

## 流程

### Step 1: 盤點本次 session 變更

掃描整個對話，列出以下五類：

| 類別 | 要找什麼 |
|------|---------|
| A. 新能力 | 新腳本、新工作表、新自動化 |
| B. 使用者修正 | 被糾正的錯誤、「不要這樣」「改成那樣」 |
| C. 已驗證做法 | 使用者肯定的方法（「perfect」「OK」或未反對地接受） |
| D. 系統知識 | 欄位 ID、URL、編碼細節、API 行為 |
| E. 問題排除 | 遇到的錯誤與根因/修法 |

簡短列出後才進入 Step 2。

---

### Step 2: 更新 memory

對 Step 1 中**無法從 code / git 推導**的項目：

1. 先讀 `memory/MEMORY.md` 查是否已有相關條目
2. 若有 → 讀該檔 → **更新合併**（禁止重複）
3. 若無 → **新增** `.md`，frontmatter 格式：
   ```markdown
   ---
   name: descriptive-name
   description: one-line — 未來比對相關度用
   type: feedback | project | user | reference
   ---
   內容。feedback/project 類型須包含：
   **Why:** 原因
   **How to apply:** 何時/何處適用
   ```
4. 可從 code 推導的 → **不存**
5. 更新 `MEMORY.md` 索引（每條 < 150 字元）

**規則：**
- 絕不重複
- 相對日期轉絕對日期（「明天」→「2026-04-13」）
- 只存結論，不存除錯過程

---

### Step 3: 評估 skills

讀 `每日入院清單工作流程.txt` 的 Skills 章節，對每個 skill：
1. **描述是否準確** — 與當前行為相符？
2. **是否完整** — 今天手動做的流程有該被 skill cover？
3. **是否正確** — 規則是否與今天的修正衝突？

另檢查：今天有無手動做的事該變成**新 skill**？

**輸出格式：**
- `[OK]` skill-name — 無需變動
- `[FIX]` skill-name — 需更新：[具體問題]
- `[NEW]` suggested-name — [為何需要]

**修改 SKILL.md 本體需使用者授權。** 報告後等待。

---

### Step 4: 更新文件

#### 4a. `{專案}工作流程.txt`
比對 session 中的修正，修掉：
- 被使用者糾正的規則
- 錯誤的時間/代碼/技術細節
- 該記錄的新流程或指令
- 過時的描述

若檔案不存在，依下方格式新建：

```
============================================
  {專案名稱}工作流程
============================================

【準備】
  需要的檔案和工具

--------------------------------------------
步驟 N：{步驟名稱}
--------------------------------------------
  1. 使用者操作
  2. Claude 執行內容
  3. 確認事項

--------------------------------------------
快速指令
--------------------------------------------
  常用指令範例

--------------------------------------------
相關說明
--------------------------------------------
  補充資料、名詞解釋等
```

**只改真正錯的段落。** 每筆編輯展示 before/after。

#### 4b. `CLAUDE.md`
檢查是否需要更新：
- Key Files — 新增的重要檔案？
- Common Commands — 新的常用指令？
- 技術細節（URLs、編碼、欄位名）— 有無修正？

---

### Step 5: 同步 GitHub（雙向）

1. `git fetch origin main` 取得遠端狀態
2. 比對差異：
   - 本地新內容、遠端沒有 → push
   - 遠端新內容、本地沒有 → merge 下來
   - 兩邊都有改（衝突）→ **以較新/資訊更完整的為主**，不需問
3. Commit 訊息：`docs: sync workflow documentation`
4. 在 worktree 中 → `git push origin <branch>:main`
5. 推送範圍：工作流程 txt、CLAUDE.md、`memory/`、`.claude/skills/`
6. **專案 → GitHub repo 對照表**：

   | 專案資料夾 | GitHub Repo |
   |-----------|-------------|
   | 每日入院名單 | https://github.com/alexdodochen/daily-admission-list |
   | LINE提醒機器人 (行政總醫師) | https://github.com/alexdodochen/line-reminder-bot |
   | 排班 | https://github.com/alexdodochen/cv-scheduling |

7. 若專案不在對照表 → 問使用者 repo URL

---

## Step 6: 總結報告

完成後輸出結構化總結：

```
=== Workflow-Doc Review ===

Session Changes:
  - [簡要列表]

Memory Updates:
  - [created/updated] filename — description
  (or "No memory updates needed")

Skills Status:
  - [status] each skill
  (or "All skills up to date")

Docs Updated:
  - [file]: [變動內容, 行號]
  (or "No doc changes needed")

GitHub Sync:
  - [commit hash] pushed to origin/main
  (or "No push needed")

Pending Actions:
  - [需使用者決定的事項]
  (or "None")
```

---

## 撰寫原則

- **使用者視角**：操作手冊，非技術文件
- **具體指令**：每步驟附可直接對 Claude 說的範例
- **純文字**：用 `====` `----` 分隔，不用 markdown
- **中文為主**
- **簡潔明瞭**：清楚列出「使用者做什麼」「Claude 會做什麼」
- **附驗證資料**：正確名單、代碼對照表等放文末

## 主動觸發時機

以下情境**主動執行本 skill**（不需使用者要求）：
- 完成新 skill 建立後
- 修改既有 skill 流程後
- 更新 memory 中的操作規則後
- 修正工作流程錯誤後

主動同步時，簡短告知「工作流程已同步更新並推送到 GitHub」即可。
