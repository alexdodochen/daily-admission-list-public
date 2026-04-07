---
description: End-of-session review — save progress/corrections to memory, evaluate skills, update workflow documentation
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(cat:*), Bash(head:*), Bash(wc:*)
---

## Current Project State

- Memory index: !`cat memory/MEMORY.md 2>/dev/null || echo "No MEMORY.md"`
- Memory files: !`ls memory/*.md 2>/dev/null | grep -v MEMORY.md`
- Project files: !`ls *.py *.txt *.json 2>/dev/null`
- CLAUDE.md sections: !`grep "^#" CLAUDE.md 2>/dev/null`
- Skills referenced: !`grep -n "skill:" 每日入院清單工作流程.txt 2>/dev/null`

## Task: Comprehensive End-of-Session Review

Perform ALL 5 steps below. This is a structured review — do not skip any step.

---

### Step 1: Identify Session Changes

Scan the **entire conversation** and extract ALL of the following:

| Category | What to look for |
|----------|-----------------|
| **A. New capabilities** | Scripts created, worksheets added, new automation |
| **B. User corrections** | Mistakes corrected, rules clarified, "don't do X" / "do Y instead" |
| **C. Confirmed approaches** | Things that worked well and user approved (subtle — watch for "perfect", "OK", acceptance without pushback) |
| **D. System knowledge** | Form fields, IDs, URLs, encoding quirks, API behaviors discovered |
| **E. Issues resolved** | Errors encountered and their root cause / fix |

List each item concisely before proceeding to Step 2.

---

### Step 2: Update Memory

For each item from Step 1 that is **not derivable from code or git**:

1. Read `memory/MEMORY.md` — check if a related entry already exists
2. Read the related memory file if it exists
3. Decide:
   - **Related memory exists** → UPDATE the existing `.md` file (merge new info, don't duplicate)
   - **New topic** → CREATE a new `.md` file with proper frontmatter:
     ```markdown
     ---
     name: descriptive-name
     description: one-line — used for relevance matching
     type: feedback | project | user | reference
     ---
     Content. For feedback/project types:
     **Why:** reason
     **How to apply:** when/where this matters
     ```
   - **Derivable from code** → SKIP (don't save)
4. Update `memory/MEMORY.md` index — one line per entry, under 150 chars

**Rules:**
- Never duplicate. Always check existing entries first.
- Convert relative dates to absolute (e.g., "tomorrow" → "2026-04-05").
- Don't save debugging steps, only conclusions.

---

### Step 3: Evaluate Skills

Read `每日入院清單工作流程.txt` Skills section. For each skill:

1. **Check accuracy** — Does the description match current behavior?
2. **Check completeness** — Were any manual workflows done today that this skill should cover?
3. **Check correctness** — Do any rules in the doc contradict today's corrections?

Also check: Was anything done manually today that should be a **new skill**?

**Output format for each skill:**
- `[OK]` skill-name — up to date
- `[FIX]` skill-name — needs update: [specific issue]
- `[NEW]` suggested-skill-name — [why it's needed]

**Do not modify skill files without user confirmation.** Report recommendations and wait.

---

### Step 4: Update Documentation

#### 4a. `每日入院清單工作流程.txt`
Cross-reference today's corrections against the workflow doc. Fix:
- Rules that were corrected by the user in this session
- Times, codes, or technical details that are wrong
- New workflows or commands that should be documented
- Outdated descriptions that no longer match actual behavior

**Only edit sections that are genuinely wrong.** Show each edit with before/after context.

#### 4b. `CLAUDE.md`
Check if any of these need updating:
- Key Files section — new important files added?
- Common Commands — new patterns established?
- Technical details (URLs, encoding, field names) — any corrections?

---

### Step 5: Summary Report

After completing all steps, output this structured summary:

```
=== Workflow-Doc Review ===

Session Changes:
  - [concise list of changes]

Memory Updates:
  - [created/updated] filename — description
  (or "No memory updates needed")

Skills Status:
  - [status] each skill
  (or "All skills up to date")

Docs Updated:
  - [file]: [what changed, line numbers]
  (or "No doc changes needed")

Pending Actions:
  - [anything that needs user decision]
  (or "None")
```
