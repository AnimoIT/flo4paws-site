# W6 BACKLOG entries — W-register numbering WBL-678–687 (ruling A, W6b, 5 Sep 2026); formerly provisional W6-BL1–10

### WBL-678 | OPEN | W6 | MEASURED | MEDIUM | W-series entries never landed in animoit-infra; BL-655–659 and F-82+ collide with the S-series

state:    `docs/` holds W1+W3 only; W4/W5 entries exist only in the Claude project (now in this PR). Infra `NEXT_ID` BL-659 / `NEXT_F` F-82; S218 used BL-655–658; W4 used BL-655–659; W5 used BL-660–677 and F-92–100; W3 used F-82–87. Ruling owed: (A) separate W register in `docs/` with its own prefix, or (B) one register — apply W3–W6 into infra, renumber W4's five, fix references, bump `NEXT_`. Preference B, own session.
Claim evidence: MEASURED — `grep -l 'BL-660\|F-98'` across infra and docs/ = nothing; `NEXT_` lines read.

---

### WBL-679 | OPEN | W6 | MEASURED | SMALL | `nginx -t` passes an empty vhost; reload gates need a byte/sha guard

state:    Proven at W6 open ("test is successful" with `sites-available/flo4paws-site` at 0 bytes). Applies to `deploy.sh`'s reload and to the W-series install block.
remedy:   Before any reload: `wc -c` ≥ known minimum and `diff deploy/<f> /etc/nginx/<f>` rc 0 for each of the three site files (and the app vhost/snippets for `deploy.sh`); abort on mismatch.
Claim evidence: MEASURED.

---

### WBL-680 | OPEN | W6 | RULED | SMALL | W5 vhost zeroing — cause unknown

state:    mtime 18:07:20 UTC 4 Sep; no history line redirects to the path; certbot and the 18:08 republish do not touch the file. Ian may recall the block.
remedy:   If the cause surfaces, record it; otherwise WBL-679 is the control and this closes as UNRESOLVED-GUARDED.
Claim evidence: RULED.

---

### WBL-681 | OPEN | W6 | MEASURED | MEDIUM | staging and www share one document root — no preview

state:    vhost `root /var/www/flo4paws-site` for all three names. Every install is live on www immediately; Flo reviewed tonight's copy from the diff, not a page.
remedy:   Second root (`/var/www/flo4paws-site-staging`) + `map`/second server block, install to staging first, promote by rsync. Do with the W7 layout batch, which is the first change that needs a visual review.
Claim evidence: MEASURED (vhost line 12).

---

### WBL-682 | OPEN | W6 | RULED | MEDIUM | W7 assets + layout batch (Flo's read-through, screens 2–13)

state:    App Store / Google Play official badges (Ian downloads from Apple/Google brand pages; not fetchable from the box); qualification badges — BCCS L4, IMDT courses, Pet Remedy partner, Grisha Stewart Academy courses, Galen Myotherapy Postural Analyst (check `/root/incoming/flo4paws-site-bundles` for the Wix exports first); `/about/` refactor against the original Wix page; alignment: about-section columns, pain-section right gap, app-section columns, pricing-card rule lines, lozenge header wrap + more lozenges. Layout = `site.css`/templates; needs WBL-681 first for a visual review.
Claim evidence: RULED (screenshots in W6 chat).

---

### WBL-683 | PAUSED | W6 | RULED | SMALL | rescue-dogs section (Scooby)

state:    Flo is sending rescue dogs and their stories. Becomes a section under "Behaviour problems I help with", not a photo in the pain-section gap. Scooby.jpg received (not yet on the box).
Claim evidence: RULED.

---

### WBL-684 | PAUSED | W6 | RULED | SMALL | walk maps from GPX on OSM tiles

state:    Rufford and Gunthorpe screenshots were Mapbox/Strava and Apple Maps — not licensable. Ian exporting GPX; render all three walks the same way with OSM attribution.
Claim evidence: RULED.

---

### WBL-685 | OPEN | W6 | MEASURED | SMALL | prune stale remote refs in flo4paws-site

state:    13 remote refs; `w3-*`, `w4-*`, `w5-*`, `w6-noindex`, `w6-copy` all merged. `gh pr merge --delete-branch` removes the branch on GitHub; the local remote-tracking ref stays until `fetch --prune`.
remedy:   `git fetch --prune` at every close.
Claim evidence: MEASURED.

---

### WBL-686 | OPEN | W6 | MEASURED | SMALL | "Review needed" / "to be confirmed" placeholders — sweep

state:    Two internal callouts and one "One line to be confirmed" were live on public pages from W1 until tonight. Removed. No sweep has been done for others.
remedy:   `grep -rniE 'review needed|to be confirmed|TODO|lorem' src/pages build/` at W7 open; 0 expected.
Claim evidence: MEASURED.

---

### WBL-687 | OPEN | W6 | RULED | SMALL | W2 MOBILE has no handover

state:    W5's series line names W2; no file exists in `docs/`, infra, or the project. Ian to say whether W2 produced anything that needs recording, or mark it "no artefacts".
Claim evidence: RULED.

## Amendments

- **WBL-660** DONE (W6, MEASURED — header on the wire, staging only).
- **WBL-665** DONE (W6, MEASURED — dry-run rc 0, no config change). Lineage rename at first real renewal.
- **WBL-647** DONE (W6 — Newgrange placeholder → Nicholson Vets line, PR #12). Eurotunnel guide keeps Newgrange as history (Ian ruled).
- **WBL-658** DONE (this PR) — W4/W5/W6 handovers + entries + W7 brief in `docs/`. Rule from W6: handover into `docs/` same session.
- **WBL-672** partly: `/about/`, `/app/`, `/thank-you/`, cookie policy read by Flo; `/app/` "What it is not" fixed; `/about/` refactor → WBL-682.
- **WBL-653 nav**: label "My approach" (W6). URL unchanged.
- **WBL-649 Lincolnshire**, **WBL-655 guides ruling**, **WBL-656 double Cache-Control** (vhost lines 33/37: `expires` + `add_header`): unchanged.
- **WBL-663 / WBL-667 / WBL-674 / Stage D (WBL-664)**: tomorrow, Ian in the browser.
