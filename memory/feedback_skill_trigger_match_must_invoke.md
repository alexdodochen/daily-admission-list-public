---
name: User message matches skill trigger phrase → MUST invoke skill, no inline shortcut
description: When the user's message contains a literal trigger phrase from any skill description, Claude MUST invoke that skill via the Skill tool — never inline-reimplement the logic. Inline shortcuts skip skill rules and reproduce bugs the skill already solved.
type: feedback
---

If the user's message contains a literal trigger phrase listed in any skill's description, Claude **must** invoke that skill via the `Skill` tool. No inline `python -c` reimplementation, no «I'll just do it manually because it's only N items», no shortcut.

**Why:** User instruction (5/8): «請你檢討為甚麼你會自作聰明 我規則都寫好了 你為何沒有遵守??». Concrete incident: user said «生成5/10入院序列» (literal trigger of `admission-ordering` skill). Claude bypassed the skill and inline-wrote the N-V logic, missing the weighted-by-tickets shuffle, asking redundant questions, and contradicting a feedback rule the user had given hours earlier the same session. The bug was a routing failure, not an algorithm failure — the skill already had the correct weighted algorithm at lines 137–163.

**Skill description = procedural truth; CLAUDE.md = high-level reminder.** When CLAUDE.md and skill disagree, skill wins. When CLAUDE.md uses shorthand like `random.shuffle()`, that's a reminder pointer to the skill — not a complete algorithm to copy verbatim.

**How to apply:**
- Before starting any work, scan the user's message for literal trigger phrases against the skill list (it's loaded into context every turn).
- Trigger phrases for current skills include (non-exhaustive): «匯入入院名單», «讀取圖片匯入», «抽籤», «排住院序», «排入院序», «生成入院序列», «排導管», «key-in導管», «導管排程», «提取EMR», «做摘要», «改期», «改 MM/DD 住院», «重啟改期功能», «重抓 EMR», «refresh EMR», «重建 sheet», «重新建立 [date]».
- If a literal match exists → **first action is `Skill <name>`**, not Bash or Edit. The skill loads its own procedural detail; trust it.
- Tool inertia is a real failure mode — if previous turns used `Bash python -c ...`, switching to `Skill` for the next request takes deliberate intent.
- «It's only N items» is not a valid reason to skip the skill. The skill embeds rules (`*2` weighting, R col from sub-table H, post-write format check, etc) the inline path will likely miss.
- If the skill is wrong/incomplete → fix the skill, then run it. Don't bypass.

**Self-check before any inline write:** «is the user's exact phrasing in any skill's trigger list?» If yes, stop, invoke skill instead.
