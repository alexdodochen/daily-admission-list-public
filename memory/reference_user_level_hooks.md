---
name: User-level SessionStart + SessionEnd hooks for handoff continuity
description: Hooks at ~/.claude/hooks/ inject HANDOFF/MEMORY into each session start and write a marker on session end so the next start can warn about unfinished /workflow-docs runs.
type: reference
originSessionId: 330aff12-7a2c-45d7-9870-70b184f5f581
---
Two user-level hooks (apply to ALL projects, not just this one):

**`C:/Users/user/.claude/hooks/session_start_handoff.py`** (SessionStart)
- Reads stdin JSON: `{cwd, session_id, ...}`
- If `<cwd>/memory/` exists, builds context string with:
  - HANDOFF.md content (cap 8KB)
  - MEMORY.md index (cap 12KB)
  - Git state: branch, ahead/behind origin, uncommitted file count
  - Stale-session warnings from `<cwd>/memory/.session_end_marker.json`
- Outputs `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}` to stdout
- Silently exits 0 if no `memory/` dir (non-managed project)

**`C:/Users/user/.claude/hooks/session_end_marker.py`** (SessionEnd)
- Writes `<cwd>/memory/.session_end_marker.json` with:
  - `ended_at`, `branch`, `dirty_count`, `ahead`, `last_commit_msg`, `workflow_docs_run`, `reason`
- `workflow_docs_run` heuristic: last commit msg contains 'docs:' OR 'sync workflow' AND tree clean AND not ahead of origin
- Silently exits 0 if no `memory/` or no git

**Registration:** `C:/Users/user/.claude/settings.json` `hooks.SessionStart[].hooks[]` and `hooks.SessionEnd[].hooks[]`, both with timeout 10000ms.

**Marker file gitignored** (per project): each project's `.gitignore` should add `memory/.session_end_marker.json` since it's per-machine state.

**Testing locally:**
```python
import json, subprocess
inp = json.dumps({"cwd": "D:/path/to/project", "session_id": "test"})
r = subprocess.run(["python", "C:/Users/user/.claude/hooks/session_start_handoff.py"],
                   input=inp, capture_output=True, text=True, encoding="utf-8")
# r.stdout should be valid JSON with hookSpecificOutput.additionalContext
```

**Why:**
- 2026-05-07: user requested SessionStart auto-runs /check-previous-progress and SessionEnd auto-runs /workflow-docs. SessionEnd hook can't invoke a slash command (Claude already exited), so design uses marker file + next SessionStart warning as the safety net.
- 3 user-confirmed "project end" signals when Claude is still active: (1) explicit phrases like 「結束」「就到這」「掰」「OK 這次到此」, (2) major task completion, (3) explicit /workflow-docs.

**How to apply:**
- If a SessionStart context shows the marker warned about unfinished workflow-docs → run /workflow-docs first thing in the new session.
- If editing the hook scripts, test with the snippet above before committing — silent stderr makes debugging tricky.
- Per-project `.gitignore` MUST include `memory/.session_end_marker.json` to keep marker per-machine.
