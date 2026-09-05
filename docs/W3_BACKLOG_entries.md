# W3 BACKLOG entries — 2026-09-04

W-series register entry (ruling A, W6b, 5 Sep 2026: W register lives in `flo4paws-site/docs/`, not `animoit-infra`). Numbering continues from BL-642 (S216) under the WBL- prefix. Census instrument: `grep -c '^### WBL-'`.

---

### WBL-643 | DONE | W3 | MEASURED | MEDIUM | flo4paws-site had no source control and no generator

state:    The 23-page static site was generated in a Claude sandbox (W1); `gen.py`/`content.py` were never downloaded and no longer exist. W2 hand-edited the served tree. The served tree was the only copy of the site.
remedy:   Repo `AnimoIT/flo4paws-site` (public). Initial commit = served tree, tag `w2-live`. Generator reconstructed as `src/gen.py` + `src/pages/*.html` + `src/static/`; `gen.py --check` proves `build/` regenerates byte-for-byte (48/48) and runs in CI. PRs #1, #2 merged.
Claim evidence: MEASURED — `differences: 0` on sandbox, box and GitHub runner.

---

### WBL-644 | OPEN-PR | W3 | MEASURED | MEDIUM | /about/ page, About Flo in nav/footer, real store links, cache-busted assets

state:    PR #3 `w3-about`, CI green, **deployed to staging by rsync, not merged**. Content carried from the old Wix site (story, shelters, psychology, how she works, BCCS L4, IMDT ×3, Grisha Stewart Academy + CPD ×6, NICE/IICE/UK Dog Charter, Pet Remedy). Person schema linked to `#business`. Home: App Store `id6780405244`, Play `uk.co.flo4paws.app`, sign-in link. `?v=<sha[:8]>` on css/js.
remedy:   Flo reads `/about/`; Ian checks nav wrap on tablet widths; rule Lincolnshire (WBL-649); merge. If wrong: `git checkout main && rsync` restores.
Claim evidence: MEASURED — `/about/` 200 on staging; store hrefs present in served home.

---

### WBL-645 | OPEN | W3 | MEASURED | SMALL | HTML pages carry no Cache-Control; ruling on `no-cache`

state:    `curl -sI /` returns no `Cache-Control`/`Expires`; browsers apply heuristic freshness (~10 % of `Last-Modified` age — grows as pages age). css 7d, images 30d, js none. W2's "7-day cache on HTML" claim was wrong.
remedy:   Ruling: add `location ~ \.html$|location /` `add_header Cache-Control "no-cache"` (revalidate via ETag, 304 cost only). Vhost change → `deploy/` PR → `nginx -t` → reload with the app/Lily/beerscope controls. Preference: yes, bundle with the cutover vhost PR.
Claim evidence: MEASURED.

---

### WBL-646 | OPEN | W3 | RULED-PARTIAL | MEDIUM | /app/ page — marketing on the site, help in the tenant frontend

state:    Ian wants an app page that doubles as help. Home already links the stores and sign-in (WBL-644). Help content is per-tenant (Lily needs the same with her branding).
remedy:   Proposal: `/app/` on the website = marketing only (why, 2–3 screenshots, badges, sign-in). Help = `/help/` page served by the tenant frontend, written once, tenant-branded by the existing `/api/tenant/config`. Ruling owed; the frontend half is an API/frontend-repo BL, not a website one.
Claim evidence: RULED-PARTIAL (marketing page yes; help location open).

---

### WBL-647 | OPEN | W3 | MEASURED | SMALL | Newgrange Vets placeholder renders as client-facing text

state:    `grep -R -l 'One line to be confirmed' build/` → 1 file (`flos-friends`). Unchanged since W1.
remedy:   Flo supplies the line; edit `src/pages/flos-friends.html`; PR. Until then it ships as-is on any deploy.
Claim evidence: MEASURED.

---

### WBL-648 | OPEN | W3 | MEASURED | SMALL | No branch protection on flo4paws-site; merge can outrun CI

state:    PR #2 was squash-merged with `gh pr merge` before its check was seen (the `grep` filtered the status line). It happened to be green.
remedy:   `gh api -X PUT repos/AnimoIT/flo4paws-site/branches/main/protection` requiring `build-matches-source/check`; or at minimum never merge without `gh pr checks N` read unfiltered.
Claim evidence: MEASURED.

---

### WBL-649 | OPEN | W1→W3 | RULING | SMALL | Coverage counties — Lincolnshire in or out

state:    Old site: Notts, Leics, **Lincs**, Rutland (hero) and a different list in the footer. New site + JSON-LD `areaServed`: Notts, Leics, Rutland. `/about/` follows the new site. Inconsistency is a local-SEO signal.
remedy:   Ian/Flo rule once; apply to hero, footer, About, `areaServed` in one PR.
Claim evidence: MEASURED (both sites read).

---

### WBL-650 | OPEN | W3 | INHERITED | SMALL | Move W1 satellite docs into the repo and fix ia-v2 Ads figure

state:    `ia-v2.md`, `seo-audit.md`, the ChatGPT audit, and W1–W3 handovers live only in the Claude project. `ia-v2.md` §6 carries the wrong £634.93.
remedy:   `docs/` in `flo4paws-site`; correct the figure in the same PR.
Claim evidence: INHERITED.

---

### WBL-651 | OPEN | W3 | VERBAL | SMALL | Record BL-576 closure, real E2E submission, BL-566 parked — with evidence

state:    Ian stated all three in W3. None appear in S212–S216 registers. Without a row/PR reference they will resurface as open (as the staging-pull claim did).
remedy:   In the API-side BACKLOG.md: BL-576 → DONE with PR; E2E → which client row, date; BL-566 → PARKED with Ian's ruling text.
Claim evidence: VERBAL — Ian, W3.

---

### WBL-652 | OPEN | W3 | MEASURED | SMALL | Hygiene — r2dev.env, /tmp tarballs, second login, beerscope in controls

state:    `/root/incoming/r2dev.env` (600, 24 Aug) is a credential file in scratch. Seven site tarballs in `/tmp` (v7 preserved elsewhere). Two users logged in at W3 open; second not identified. `beerscope.co.uk` vhost not in any control list.
remedy:   Delete/move `r2dev.env`; `rm /tmp/flo4paws-site-build*.tar.gz`; add beerscope to the nginx-reload control set.
Claim evidence: MEASURED.

---

### WBL-653 | OPEN | W2→W3 | RULING | SMALL | Nav label "How it works" and site-wide width

state:    W2 proposed "Working with me"; if the URL changes, 2 redirect entries + ~7 internal links move. Width: 64rem site-wide vs centred narrow columns. Both untouched in W3.
remedy:   Ian rules before cutover or defers both to post-launch (URL change after launch costs a redirect hop).
Claim evidence: INHERITED from W2.

---

### WBL-654 | OPEN | W1→W3 | INHERITED | MEDIUM | Launch session: GA4 + Consent Mode v2, then cutover

state:    Last remaining gate item. Must land **before** the `www` A record moves: Ads bids on a Wix thank-you conversion that vanishes at cutover. Placeholder comment is in the `<head>` template (`gen.py` HEAD) — one edit, 24 pages.
remedy:   Ruling: single `intake_submitted` event on success state, no field content. Tag + Consent Mode into `gen.py` HEAD → staging → GA4 DebugView → tag into `publish.js` template (API repo) → republish both estates → GA4 admin (cross-domain list, conversion, GSC Domain property) → `/healthform` directive → `www` A record → remove `X-Robots-Tag` → sitemap submit.
Claim evidence: INHERITED (W1 §4/§5 + W3 discussion).
