---
name: WEBCVIS DEL — list candidates → wait for user approval → run automated DEL flow
description: For cathlab DEL (especially reschedule), the correct sequence is (1) list DEL candidates with chart/name/date/room/time, (2) wait for user explicit approval, (3) run Playwright DEL flow automatically. Don't punt to "user does it manually", don't auto-DEL without confirmation.
type: feedback
---

When user invokes a workflow that needs cathlab DEL (e.g. reschedule: DEL old + ADD new):

1. **List DEL candidates** — chart no, name, date, room, time, source (e.g. from sub-table)
2. **Wait for user explicit "OK" / "del" / "go" / similar** — destructive op needs authorization
3. **After approval → run Playwright DEL automatically** — don't output "請手動刪除" as the answer
4. **Verify** — re-query the date in WEBCVIS; row absent = success
5. **If automation fails** → report exact failure (DOM state / server response), then ask user to handle manually as fallback

**Why:**
- User correction 2026-05-05 (two-step): first "我叫你刪除的時候 你就幫我刪除", then clarification "list and ask -> 我同意後自動跑del flow 這樣才對"
- Confirmation gate prevents accidental destructive ops on cross-day cathlab data
- After confirmation, automation is the value — manual deletion of N rows defeats the point

**How to apply:**
- Reschedule full-move flow: after building DEL list (from V-marked rows), present it to user. After user says go → run DEL flow. Then ADD via cathlab_keyin.py.
- Standalone DEL request ("刪掉 5/7 王小明 的導管"): list the matched row(s), confirm chart/date, run DEL after user approves.
- Only escalate to "please do it manually" if a fresh automation attempt provably fails AND a re-test confirms server-side rejection (not a UI/timing bug).

**Approaches already tried that failed (don't repeat verbatim):**
- v1: direct form submit `document.HCO1WForm.buttonName.name="DEL"; HCO1WForm.submit()` — server returned 200 but row remained on re-query
- v2: force-enable `#deleteButton` via `removeAttribute("disabled")` then click + Playwright dialog accept — same result, row remained

**New approaches to try:**
- Row-click first to select (mimics UPT-enable flow), then trigger DEL via the page's actual jQuery click handler if one exists; inspect `cathlab_page.html` / live DOM for the DEL handler binding
- Check whether DEL needs a separate confirm dialog (`window.confirm`) — accept via Playwright's `page.on("dialog", ...)`
- If `#deleteButton` truly has no handler, look for a context-menu DEL or a different action endpoint
- If server-side perm is genuinely missing for 107614, document the exact server response (status, body) so it's clear what's blocking

**Verify after DEL attempt:**
- Re-query the date in WEBCVIS; row absent = success
- If row still present → fail; report exact attempt + DOM state, then ask user to handle manually
