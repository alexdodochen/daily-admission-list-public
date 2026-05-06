---
name: cathlab_patients JSON must be uniquely named (or recreated)
description: Avoid stale tracked JSON re-running prior session's cathlab keyin
type: feedback
---

`cathlab_patients_*.json` files must be **gitignored** AND uniquely named per run. Stale JSON in git can re-run with last session's data.

**Why:** 2026-05-06 incident — Claude's `Write cathlab_patients_reschedule.json` failed with "File has not been read yet" (file already tracked in git from 5/5 reschedule). Error went unnoticed; `python cathlab_keyin.py cathlab_patients_reschedule.json` then ran the **stale 5/5 JSON (10 patients)** instead of the intended 5/6 reschedule (1 patient: 譚翠翠). Phase 2 UPT touched 10 unrelated charts. Recovery: re-Read + re-Write + re-run.

**How to apply:**
1. `cathlab_patients_*.json` is in `.gitignore` — never commit. If tracked already, `git rm --cached`.
2. For reschedule: write to a unique name like `cathlab_patients_reschedule_<chart>_<date>.json`, OR `os.remove` the generic name first, OR Read-then-Write to surface the error.
3. After cathlab_keyin runs, delete the JSON (it's input, not output).
4. Skill `admission-reschedule` PHASE 4 references this rule.
