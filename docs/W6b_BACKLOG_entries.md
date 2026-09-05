# W6b BACKLOG entries - 2026-09-05
W-series register entry (ruling A, W6b, 5 Sep 2026: W register lives in `flo4paws-site/docs/`, not `animoit-infra`). Numbering continues from WBL-687 (W6). Census instrument: `grep -c '^### WBL-'`.

### WBL-688 | OPEN | W6b | MEASURED | SMALL | `/book-online` is a live sitelink target and 404s; batch its 301 with the trailing-slash variants at the next reload
state:    `curl` 404 on `/book-online`; zero mentions in `ia-v2.md` or the vhost (WF-109). The "Book a Free Call" sitelink carried 496 impressions / 18 clicks Jun-Sep into it. Sitelink repointed to `/contact/` in Ads on 5 Sep (both campaigns). `/my-services/` and `/blog/` with trailing slash also 404; the no-slash forms 301 correctly. Ruling b: no reload today.
remedy:   Add `location = /book-online { return 301 /contact/; }` and slash variants for `/my-services/` and `/blog/`; one reload with Flo told, five controls before and after, byte/sha guard (WBL-679).
Claim evidence: MEASURED.
---
### WBL-689 | OPEN | W6b | MEASURED | SMALL | Ads final URL expansion is on and chose `/my-services`, `/`, `/blog` on the old site by itself
state:    Landing pages report rows marked "Automatically selected". On the new site it will pick pages nobody chose. Ian's task in Ads: campaign settings, Final URL expansion off or exclusions; re-read Landing pages at Stage D.
remedy:   Ian, ten minutes in Ads. Box does nothing.
Claim evidence: MEASURED (screenshot 5 Sep).
---
### WBL-690 | DONE | W6b | RULED | SMALL | Ruling A executed: W register under WBL-/WF- in `docs/`, `W_REGISTER.md`, README table, manifest, `deploy/` comments
state:    PR #14 (`39fa6f7`): 69 headings renamed across 14 files, four historical lines kept infra IDs verbatim, `sha256sum -c` 0 failures. `deploy/` comments renamed and installed without reload, sha parity restored (`964a0ed`, this branch). Sitelink half of WBL-674 done in Ads (11 sitelinks, two campaigns); ad final URLs were already `/`.
remedy:   None. WBL-674 still needs Stage D read before any un-pause.
Claim evidence: MEASURED (census 69, manifest 0, three sha pairs equal).
---
