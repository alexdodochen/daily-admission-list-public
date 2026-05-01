---
name: Claude-Gemini-Dialogue 委派工具
description: 本機 ~/repos/Claude-Gemini-Dialogue/ 的 delegate.sh 可把長 context grunt work 丟給 Gemini CLI 跑省 Claude token；token 吃緊或處理大檔搜尋翻譯時使用
type: reference
---

## 位置與設定

- Repo: `~/repos/Claude-Gemini-Dialogue/`（已 clone 自 https://github.com/alexdodochen/Claude-Gemini-Dialogue）
- 主腳本: `~/repos/Claude-Gemini-Dialogue/scripts/delegate.sh`
- Prereq: Node.js、`@google/gemini-cli`（已裝；2026-05-01 完成 setup）+ Gemini CLI 已 OAuth 完成（user 親自跑過 `gemini`）

## 三種呼叫法

```bash
# 唯讀分析
bash ~/repos/Claude-Gemini-Dialogue/scripts/delegate.sh "Find 5 RCTs on Bayesian NMA in heart failure from the last 3 years"

# 允許寫檔（落地到 out/）
bash ~/repos/Claude-Gemini-Dialogue/scripts/delegate.sh -e "Convert this CSV to markdown table, save to out/table.md"

# 指定 model
bash ~/repos/Claude-Gemini-Dialogue/scripts/delegate.sh -m gemini-2.5-flash "Translate 20 medical terms to Traditional Chinese"
```

回傳格式：`DONE: <path>` 或 `NEEDS_REVIEW: <reason>` — 我看到 DONE 就讀那個 path 的結果，看到 NEEDS_REVIEW 就接手。

## 何時用（對 token 緊張時最有效）

- **長文搜尋/閱讀**：scan 一堆 PDF / 翻譯一大段 / 摘要長報告
- **高度結構化轉檔**：CSV → markdown table、JSON 清洗、批次 rename
- **獨立任務**：不需要 admission-list 上下文的 grunt work
- 一次性研究查詢（user 偏向丟大量論文搜尋給 Gemini）

## 何時 *不* 用

- 涉及 admission-list 業務邏輯（Gemini 沒有 memory / CLAUDE.md context）
- 需多輪判斷的複雜決策
- 寫進此 repo 的 production code（Claude 自己審）
- Token 還很充裕、任務量小（呼叫成本不划算）

## 安全限制（wrapper 已硬性禁止）

Gemini wrapper 有 sandbox：禁裝套件、禁 clone repo、禁從網路執行 shell script、禁讀 credential 檔。所以丟它做的事是純運算/翻譯/搜尋，不是要它動我的環境。
