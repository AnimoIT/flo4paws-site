# W6b FINDINGS entries - 2026-09-05
W-series register entry (ruling A, W6b, 5 Sep 2026: W register lives in `flo4paws-site/docs/`, not `animoit-infra`). Numbering continues from WF-105 (W6).

### WF-106 | W6b | MEASURED | `os.replace` ran inside the loop, before the assert it existed to gate
The rename block wrote all 14 files as it went, then asserted `applied + skipped == 207`. The assert fired (206) with the bytes already on disk. Recovery was `git checkout`, trivial - but the gate was decorative. Fixed in every later block: assert, then write.
★ A control that runs after the action it controls is not a control (F-73 shape). Assert before `os.replace`, always.
---
### WF-107 | W6b | MEASURED | the register collision was sixteen IDs, not five, and started at W3
Infra `BACKLOG.md` has headings BL-643 through BL-658, all S217-S219 API items with titles unrelated to W3/W4's. The W6 handover and the W6b intro said "W4's five (BL-655-659)". Measured by printing both registers' headings side by side.
★ The extent of a defect is measured on every register it touches, not inherited from the previous session's read of one of them.
---
### WF-108 | W6b | MEASURED | five predictions of my own output stated as DERIVED before an instrument printed them
Edits 13 (12); diff lines 154 (151); README rows 15 (14); PR #13 (#14); `git clean -n` 0 (1, the new file). None reached the bytes; all were counts I could have run first.
★ WF-102 again, one session later. A count of my own edit is INFERRED until a script prints it; label it so.
---
### WF-109 | W6b | MEASURED | W1's redirect census missed the Wix booking page
`/book-online` was the final URL of a live sitelink with 496 impressions. Zero hits for `book-online` in `ia-v2.md` or the vhost. The census walked the site's own navigation and sitemap; it never read the Ads account.
★ A redirect census for a relaunch must include every URL paid traffic is sent to: ad final URLs, sitelinks, and Google's auto-expanded landing pages.
---
### WF-110 | W6b | MEASURED | the Flo4Paws Ads campaign was Enabled, not paused, throughout W5-W6b
Campaign settings panel: status Enabled, "Limited by budget"; 8 impressions and 1 click on 5 Sep before 08:00. The W6 handover and the W6b intro both said "paused". Ads were serving into the dead `/book-online` sitelink for the whole of launch day and this morning until the sitelink edit. Flo told 5 Sep.
★ "Paused" is a status read off the Ads UI, not a memory of having paused it. Campaign status goes in the five-controls list for any session that touches Ads.
---
