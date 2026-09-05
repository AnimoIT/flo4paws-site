# W5 FINDINGS entries — 2026-09-04

W-series register entry (ruling A, W6b, 5 Sep 2026: W register lives in `flo4paws-site/docs/`, not `animoit-infra`). Numbering continues from WF-91 (W4).

---

### WF-92 | W5 | MEASURED | `grep -r` on `sites-enabled/` filed a false absence, and a hypothesis was built on it

`grep -rn 'intake-form' /etc/nginx/sites-enabled/` → 0; the next block's `grep -rn … /etc/nginx/sites-enabled/*` found the alias at once. The directory holds symlinks; `-r` given the directory does not follow them, the glob hands the links as arguments and does. The rule is verbatim in the memory summary. Two blocks were spent on "the page is not nginx-served".

★ WF-89's corollary again: before asserting an absence, test the behaviour. And when a grep over `sites-enabled` returns 0, that is the symlink trap until proven otherwise.

---

### WF-93 | W5 | MEASURED | six counts labelled DERIVED that were not derived

Predicted 9 changed lines (actual 11); +12/−2 (actual +10/−2, the rewritten lines counted twice); 4 body lines (5, `printf`'s trailing newline); 11 snippet lines (10); `add_header` 3 (5 — the string is in the comments); dev-api branches 1 (12, inferred from the site repo). None reached the bytes; each had the instrument beside it.

★ WF-90's rule was in the brief and still not applied. Stronger form: a number is DERIVED only when a script or command printed it before the prediction was written. "I added these up from the edit I just wrote" is INFERRED and should be labelled so.

---

### WF-94 | W5 | MEASURED | an instrument that could not read its input scored as a pass-in-waiting

`node --check src/static/site.js.candidate` was predicted "js parses"; Node refuses the `.candidate` extension and never parsed anything. Replaced with `vm.Script` over the file contents, which did.

★ Prove an instrument can read its input before predicting its verdict. Same class as F-01.

---

### WF-95 | W5 | MEASURED | `gh pr checks --watch` returned before any check existed and the merge went through ungated

PR #9: `--watch` printed "no checks reported on the 'w5-apex' branch" (rc 0) because the workflow had not registered yet; the block merged anyway. The run did exist and passed, read afterwards. Fixed the same session: `sleep 20; gh pr checks … --watch --fail-fast; CI=${PIPESTATUS[0]}; [ "$CI" = "0" ] && merge`.

★ A gate that passes when the instrument is absent is not a gate (F-73 shape). Wait for the check to exist, then for it to pass, and gate on the exit code, not on the text.

---

### WF-96 | W5 | MEASURED | a valid-looking measurement ID that Google refuses to serve, five months old

`G-WZVF0MNWQF` is the stream's measurement ID in the GA UI, yet `gtag/js?id=G-WZVF0MNWQF` is a 404 from any client, including when its own container chain-loads it. March's chat saw this 404 and called it temporary; the `admin.html` tag has therefore never sent a hit. The controls that separated states: a fake ID gets 200 (so 200 is not validity); a live container's bytes mention their own IDs (`G-J9CQ2WKRBT` 567 kB, 0 mentions of the Flo4Paws IDs; `GT-5D9KNJ93` 592 kB, 20 mentions of `G-WZVF0MNWQF`, 0 of `G-WG0EPNKBD2`). Resolution: a new stream in the same property.

★ "Data collection is active" on a stream is not evidence the page tag works — Wix fed it by another route. Curl the tag URL and count the ID inside the served container before putting an ID on a page.

---

### WF-97 | W5 | MEASURED | two symptoms, one cause; a second cause was invented

Chrome's `net::ERR_BLOCKED_BY_CLIENT` on the tag request was attributed to an ad blocker / privacy setting; the extensions list showed none; the same incognito window loaded the new ID at once. Chrome reports Google's refusal of a dead tag ID with that error. Time was spent on Edge and extension hunting.

★ When one measured cause (the 404 from the box) already explains a symptom, do not add a second cause to explain the same symptom in a different instrument.

---

### WF-98 | W5 | MEASURED | the box's resolver cache was the instrument for a post-DNS control

`curl http://flo4paws.co.uk/guides/` after the reload went to Wix's IP (resolver held the old apex for its full hour, 1669 s left when checked) and returned Wix's `https://$host` redirect; the prediction (`www`) was scored a miss and a symlink-replacement theory drafted. The `--resolve` form gave `www` both before and after.

★ A control whose input is resolved by a cache measures the cache (F-73's shape). For anything DNS-dependent in the hour after a change, `--resolve` to the IP or `dig @authoritative`, never the default resolver.

---

### WF-99 | W5 | MEASURED | two instruments measuring the wrong thing, in one block

`git push -q … | tail -2; echo "push rc=$?"` reports `tail`'s exit; `git clean -n` run before `git add` was predicted empty — it listed the untracked page by construction.

★ `PIPESTATUS[0]` for anything piped; and a prediction must be about the state at the moment the instrument runs, not at the end of the block.

---

### WF-100 | W5 | MEASURED | brief and memory carried three stale facts into the session

"`page_view` fires only after consent" (A3) — under Consent Mode advanced, denied-state pings are sent cookieless; what changes is DebugView's ability to show them. "Intake template in `publish.js` under `src/`" — it is `scripts/intake-form/template.html`. "Prove A4 from a real staging submission" — the staging tenant has no intake alias on any vhost. Each was found by reading, none by recall.

★ The cardinal rule held: every one of these would have produced a wrong block if executed from the brief.
