---
name: 各機器 python 路徑與跨機器 setup
description: 不同機器 python 安裝位置、WindowsApps stub 陷阱、新機器的最小 setup 步驟
type: reference
---

# 各機器 Python 路徑

| 機器 | Python 路徑 | 備註 |
|------|------------|------|
| 這台 (user@Win11) | `C:\Users\user\AppData\Local\Programs\Python\Python314\python.exe` | winget 安裝，**不在 PATH** |
| 其他機器 | (補充) | |

## WindowsApps stub 陷阱

`C:\Users\user\AppData\Local\Microsoft\WindowsApps\python.exe` 是 0-byte stub，跑下去 silent fail（exit code 49，無 stderr）。`where.exe python` 看到的是這個 stub，不是真 python。

**繞過：用絕對路徑呼叫**：
```bash
PY="/c/Users/user/AppData/Local/Programs/Python/Python314/python.exe"
PYTHONIOENCODING=utf-8 "$PY" script.py
```

或加 PATH（永久）：
```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Users\user\AppData\Local\Programs\Python\Python314", "User")
```

## 新機器 setup（從乾淨 clone 開始）

1. `winget install Python.Python.3.14` （或從 python.org 下載）
2. `pip install gspread google-auth playwright`
3. `playwright install chromium`
4. **複製 service account JSON** `sigma-sector-492215-d2-0612bef3b39b.json` 到 repo 根目錄（gitignored，不從 git 來）
5. 私有 sheet → 在 repo 根目錄建 `local_config.py`：私有 `SHEET_ID` 從別台機器 `scp` 過來，或從 `memory/_private_setup.md`（gitignored）拿。

## hookify plugin Windows 不兼容

`~/.claude/plugins/cache/claude-plugins-official/hookify/unknown/hooks/hooks.json` 用 `python3` command，但 Windows 只有 `python.exe`，沒 `python3`。後果：每次 Stop / PreToolUse / PostToolUse / UserPromptSubmit event 都會吐 `Failed with non-blocking status code: No stderr output`。

**解法**：
- A) `claude plugin disable hookify@claude-plugins-official`（沒在用 hookify 規則時）
- B) 建 hard link：`New-Item -ItemType HardLink -Path "...Python314\python3.exe" -Target "...Python314\python.exe"`
