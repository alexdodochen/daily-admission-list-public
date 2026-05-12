---
name: emr-verify-divuserspec-race
description: divUserSpec refreshes async vs leftFrame after BTQuery click — must stamp divUserSpec itself, never trust leftFrame-only wait
metadata:
  type: feedback
---

**Rule**: When polling for EMR query completion to read `<span id="divUserSpec">`, **stamp divUserSpec.innerText with a per-query sentinel** before clicking BTQuery, then wait until divUserSpec.innerText no longer contains the sentinel AND contains '姓名'. Do NOT rely on leftFrame readiness as a proxy.

**Why**: divUserSpec lives in a different frame than leftFrame and refreshes asynchronously after BTQuery. If the wait poller only checks leftFrame, divUserSpec will still hold the **previous chart's** content when the read fires — an off-by-one corruption of every row. 5/12 incident: first iteration of `verify_main_emr.py` waited only on leftFrame sentinel-cleared; result was 9 cells silently overwritten with neighboring-row data (謝翠英→董相路, 顏舜煒→謝翠英, etc.) and had to be reverted manually.

**How to apply**:
- Any Playwright script that reads divUserSpec after a BTQuery click MUST stamp divUserSpec across all frames before the click. Example:
  ```js
  for (let i = 0; i < window.frames.length; i++) {
      try {
          let el = window.frames[i].document.querySelector('#divUserSpec');
          if (el) el.innerText = 'VERIFY-SENT-XXX';
      } catch(e) {}
  }
  ```
- Poll until divUserSpec.innerText doesn't contain sentinel AND has '姓名' marker — that confirms the new chart's data has loaded.
- Add a small (~0.4s) settle delay after readiness before the actual read — cross-frame DOM updates can still be mid-flight.
- Same applies to `fetch_emr.py`'s `_read_name` — currently it works because the script also waits for leftFrame visit-list reload, but if anyone reuses `_read_name` outside that context, they must add divUserSpec stamping first.

**Connected**: [[reference_post_main_emr_verify_hook.md]] (the verify hook this race-fix protects).
