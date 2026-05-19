---
name: reference_qixiang_app_deliverable
description: 麒翔 distributable app — repo, PyInstaller build, deliverable zip, fast-path patch
metadata:
  type: reference
---

The "給麒翔" runnable app (3-card home) is a **separate sibling project** from the
admission-list scripts (cf. [[project_local_app_v2]] which is the older worktree app).

- **Working dir**: `C:\Users\dr\Downloads\Y\排班 Key班 DayList APP`
- **GitHub**: `alexdodochen/daily_admission_list_app` (push main → GitHub Action
  mirrors to public `public_daily_admission_app`). Push is NOT Claude-blocked
  (unlike line-reminder-bot).
- **Build**: `python -m PyInstaller packaging.spec --noconfirm` → onedir
  `dist/每日入院名單/` (`每日入院名單.exe` + `_internal/`). Spec bundles
  `app/bundled/service_account.json` (real SA key — gitignored, copied in
  pre-build **by design** so the colleague's exe works out-of-box) + Playwright
  Chromium → ~390 MB. `app/bundled/defaults.json` ships the **public** sheet id
  `1u2FZE6-...` (not private — safe).
- **Deliverable**: `C:\Users\dr\Downloads\Y\每日入院名單 for 麒翔.zip`
  (single root `每日入院名單/`). "更新給麒翔壓縮檔" = repackage this file.

**Fast-path vs full rebuild** (decides whether a PyInstaller rebuild is needed):
- Changed only `app/static/**` or `app/templates/**`? → those ship as **loose
  files** under `dist/每日入院名單/_internal/app/...`. Just copy the changed
  files in + re-zip. No rebuild.
- Changed any `.py` (e.g. `app/main.py`, `app/services/*.py`)? → frozen into the
  PYZ. **Full `pyinstaller packaging.spec` rebuild required** (rm -rf build dist
  first), then re-zip.

**Re-zip with Python `zipfile`**, NOT PowerShell. Windows PowerShell 5.1's
`.NET Framework ZipFile.CreateFromDirectory` writes **backslash** path
separators (violates the zip spec; original deliverable used forward slashes).
Python: walk `dist/每日入院名單`, arcname `每日入院名單/<relpath with '/'>`.

**Why:** done twice (2026-05-18/19); the rebuild-vs-fast-path call and the
PowerShell-zip backslash trap are easy to get wrong and the artifact ships to a
third party. Source is fully reproducible (git + spec + dist) → no .bak kept
(user's preference, confirmed 2026-05-19).
