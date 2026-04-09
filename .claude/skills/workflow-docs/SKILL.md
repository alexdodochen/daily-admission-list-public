---
name: workflow-docs
description: Use when a project workflow changes (new skill, updated process, corrected rules) to sync the workflow explanation txt file and push to GitHub. Also use when user asks to generate or update a workflow document for any project. Trigger on "更新工作流程", "產生操作說明", "同步說明文件".
---

# 工作流程說明文件同步

## Overview
當專案的 skill、memory、或操作流程有異動時，自動同步更新該專案資料夾中的工作流程 txt 說明檔，並推送到關聯的 GitHub repo。

## When to Use
- 新增或修改了專案相關的 skill
- 修改了操作規則（memory 更新）
- 使用者要求產生或更新工作流程文件
- 使用者說「更新工作流程」「同步說明」「產生操作說明」

## 流程

1. **找到工作流程檔**
   - 在專案資料夾中尋找 `*工作流程*.txt` 或 `*workflow*.txt`
   - 若不存在，新建一個，檔名格式：`{專案名稱}工作流程.txt`

2. **蒐集資訊來源**
   - 該專案相關的 skill（從 `~/.claude/skills/` 讀取相關 SKILL.md）
   - 該專案的 memory（從 MEMORY.md 索引找相關記憶）
   - 專案資料夾中的資料檔案結構

3. **撰寫/更新 txt 內容**
   - 格式：純文字，用 `====` 和 `----` 分隔章節
   - 結構：

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

4. **寫入檔案**
   - 用 Write tool 寫入專案資料夾
   - 確認檔案路徑正確

5. **比對本地與 GitHub（雙向同步）**
   - 先 `git fetch origin main` 取得 GitHub 最新狀態
   - 比對本地和 GitHub 的差異：
     - 本地有新內容、GitHub 沒有 → 以本地為主，push 上去
     - GitHub 有新內容、本地沒有 → 以 GitHub 為主，merge 下來
     - 兩邊都有改動（衝突）→ **以較新的為主**，不需詢問
   - 衝突解決原則：看哪一邊的改動包含更新的資訊（新規則、新修正），就用那邊的版本
   - 解決完後 commit + push

6. **推送到 GitHub（自動）**
   - 更新完工作流程檔後，自動 commit + push 到關聯的 GitHub repo
   - Commit 訊息格式：`docs: sync workflow documentation`
   - 如果在 worktree 中，push 到 main：`git push origin <branch>:main`
   - 推送範圍：工作流程 txt、CLAUDE.md、memory 目錄下的變更
   - **專案 → GitHub repo 對照表**：

     | 專案資料夾 | GitHub Repo |
     |-----------|-------------|
     | 每日入院名單 | https://github.com/alexdodochen/daily-admission-list |
     | LINE提醒機器人 (行政總醫師) | https://github.com/alexdodochen/line-reminder-bot |
     | 排班 | https://github.com/alexdodochen/cv-scheduling |

   - 若當前專案不在對照表中，詢問使用者是否要推送及 repo URL
   - skills 目錄 (`.claude/skills/`) 也隨 repo 一起推送，方便跨電腦同步

## 撰寫原則

- **使用者視角**：寫給使用者看的操作手冊，不是技術文件
- **具體指令**：每個步驟附上可以直接對 Claude 說的範例指令
- **純文字**：不用 markdown，用 `====` `----` 做視覺分隔
- **中文為主**：配合使用者習慣
- **簡潔明瞭**：每個步驟清楚列出「使用者做什麼」和「Claude 會做什麼」
- **包含驗證資料**：如有正確名單、代碼對照表等，附在文件末尾供參考

## 觸發時機

此 skill 應在以下情境**主動觸發**（不需使用者要求）：
- 完成一個新 skill 的建立後
- 修改了既有 skill 的流程後
- 更新了 memory 中的操作規則後
- 修正了工作流程中的錯誤後

主動同步時，簡短告知使用者「工作流程說明已同步更新並推送到 GitHub」即可。
