---
name: post-main-emr-verify-hook
description: PostToolUse hook auto-runs verify_main_emr.py after process_emr.py, cross-checks main A-L 姓名/性別/年齡 against EMR divUserSpec
metadata:
  type: reference
---

**What**: `scripts/post_main_emr_verify.py` is a PostToolUse Bash hook (registered in `.claude/settings.json`) that auto-runs `verify_main_emr.py YYYYMMDD` after any Bash command containing `process_emr.py` + a `20YYMMDD` token. It exists to guarantee every main A-L row gets EMR-verified, not only rows whose chart appears in `emr_data_<date>.json`.

**Why**: process_emr.py only corrects rows whose chart is in the fetched JSON. Existing rows (prior-session admissions, charts not re-fetched) get no name/age check — see 5/12 「董相路 vs 董相鉻」 where the image OCR disagreed and I asked the user to confirm visually instead of re-querying EMR. The user's response: 「主表做完後 都用EMR那個欄位確認姓名 年紀 性別」.

**Components**:
- `verify_main_emr.py YYYYMMDD [session_url]` — Playwright (headless) opens the saved session, queries each chart's divUserSpec, parses 「姓名 / 生日 / 性別」, computes age from DOB→today, applies F/G/H corrections via `batch_write_cells`. Reads session URL from `_emr_session.txt` (gitignored, auto-written by `fetch_emr.py`) if no arg given. Silent exit (rc=0) if no session file or session expired — verify is opportunistic.
- `scripts/post_main_emr_verify.py` — hook glue: parses Bash payload, matches `process_emr.py` + date, subprocesses `verify_main_emr.py`, emits hookSpecificOutput to transcript.
- `fetch_emr.py` — modified to write `sys.argv[1]` (session URL) to `_emr_session.txt` at startup so subsequent hook firings can re-use the session.

**divUserSpec stamping (race-fix, mandatory)**: divUserSpec lives in a different frame than leftFrame and refreshes asynchronously after BTQuery click. Naive wait-on-leftFrame returned the PREVIOUS chart's divUserSpec → off-by-one corruption across all rows. Fix: stamp divUserSpec.innerText with sentinel before each query; wait until divUserSpec text no longer contains sentinel AND contains '姓名'. See [[feedback_emr_verify_divuserspec_race.md]].

**Activation**: settings.json edits need next session or `/hooks` reload — script edits to the .py take effect immediately.
