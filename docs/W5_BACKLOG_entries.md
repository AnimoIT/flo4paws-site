# W5 BACKLOG entries — 2026-09-04

Append to `animoit-infra/claude/BACKLOG.md`. Numbering continues from BL-659 (W4). Census instrument: `grep -c '^### BL-'`.

## Closures (edit existing rows)

- **BL-654 → DONE (W5).** Website launched 2026-09-04 18:05 UTC. www + apex A records → 204.168.132.118 (edited at Wix DNS); cert expanded to three names; X-Robots-Tag removed; GA4 + Consent Mode v2 live on the new stream `G-SSKB2MX887`; `intake_submitted` key event proven on the wire and imported into Ads as Primary; intake form redirects to `/thank-you/`. Site PRs #7–#10, API PR #131. MEASURED throughout; real-actor submission by Ian.
- **BL-657 → PARTIAL (W5).** The plan-and-diary claim is gone from `/thank-you/`; still present on `/app/`. Screenshots still owed.
- **BL-649 → note (W5).** `grep -rl Lincolnshire /var/www/flo4paws-site` = 0 pages at close; the contradiction is gone. The ruling left is whether Flo wants Lincolnshire *added* to the footer/copy.
- **BL-651 → note.** Cross-domain GA4 + Consent Mode (the last cutover gate item) is done; the register closure itself is still owed here.

---

### BL-660 | OPEN | W5 | MEASURED | SMALL | staging.flo4paws.co.uk is now indexable

state:    The `X-Robots-Tag` line left the shared snippet for launch, so staging serves the same content as www with no noindex — a duplicate for Google.
remedy:   `if ($host = staging.flo4paws.co.uk) { add_header X-Robots-Tag "noindex, nofollow" always; }` cannot go inside `if` in nginx; use a `map $host $robots` in the http context emitted via the snippet, or serve a staging-only `robots.txt` (`location = /robots.txt { if ($host = staging…) { return 200 "User-agent: *\nDisallow: /\n"; } }`). `deploy/` PR + reload with controls. Do before Search Console has crawled staging.
Claim evidence: MEASURED — `curl -sI https://staging.flo4paws.co.uk/ | grep -ci x-robots` = 0.

---

### BL-661 | OPEN | W5 | MEASURED | MEDIUM | DNS zone lives on Wix nameservers; move it before any Wix downgrade

state:    Registrar is IONOS, delegating to `ns10/ns11.wixdns.net` (IONOS shows `ns14/ns15`). The Wix zone holds: apex/app/staging/www A; `_dmarc` CNAME → wixemails; DKIM CNAMEs for Fastmail (`fm1–3`), Wix (`x1`,`x2`), SES-style tokens (`64vcbq…`, `guqwe5…`, `x6j26p3…`), `sel1`; `sg` (SendGrid) CNAME; SPF TXT (`v=spf1 include:spf.messagi…`); MX not read. **Plus (W5, 18:2x): TXT `google-site-verification=CauJlIBagawlEeNLGoB1XBEDjaR0rg8WrHz8Xppc5Bw` for Search Console — must be carried across.** Cancelling the Wix plan risks the zone.
remedy:   Own session: export every record (`dig` each name/type, plus the Wix panel), recreate at Cloudflare (clientflex/finvault already there), switch nameservers at IONOS, verify mail + SES + SPF/DKIM, carry the Search Console TXT, then downgrade Wix (C4). Not before.
Claim evidence: MEASURED (dig NS/SOA; Wix DNS panel screenshot).

---

### BL-662 | OPEN | W5 | MEASURED | SMALL | Old GA4 stream and the dead measurement ID

state:    `Flo4Paws Website` (stream 12288878814, `G-WZVF0MNWQF`) is destination-only inside the Ad Tag container; Google 404s its script. It still receives Wix traffic and Realtime bots. `admin.html` (S-series, March) carries the dead tag — never worked.
remedy:   After a week of `G-SSKB2MX887` data: archive the old stream (Data streams → ⋯ → delete) and remove the destination from the Ad Tag; remove the `G-WZVF0MNWQF` block from `admin.html` (frontend PR) or replace with the new ID + consent default if staff analytics is wanted (ruling).
Claim evidence: MEASURED (curl 404 ×3 shapes; tag Admin screen).

---

### BL-663 | OPEN | W5 | MEASURED | SMALL | Enhanced-measurement `click` still fires on the app link

state:    After the "Contains flo4paws.co.uk" domain rule was saved, clicking the intake button still produced an outbound `click` alongside `intake_form_start`. May be container propagation lag.
remedy:   Re-test at W6 open; if it persists, set the domain rule as `Exactly matches app.flo4paws.co.uk` too, or turn off Outbound clicks in Enhanced measurement.
Claim evidence: MEASURED (DebugView 16:43).

---

### BL-664 | OPEN | W5 | RULED | SMALL | Retire the Wix Ads conversion actions after ≥1 `intake_submitted`

state:    `intake_submitted` imported as Primary (category Contact). Wix `Contacts` (7) and `Submit lead forms` (2) actions still Primary.
remedy:   When Ads shows ≥1 `intake_submitted`: set the Wix actions to Secondary, then remove. Also decline/dismiss the `/contact` page-visit suggestion permanently.
Claim evidence: RULED (brief A5).

---

### BL-665 | OPEN | W5 | MEASURED | SMALL | certbot redirect-enhancement conflict; renewal not dry-run

state:    `certbot --nginx --expand` issued the cert but rc 1 on "redirect enhancement" (its `if ($host = flo4paws.co.uk)` conflicts with ours). Left three blank lines (since overwritten by `deploy/`). Renewal config unchanged; renewals use `--nginx` installer and may retry the enhancement.
remedy:   `certbot renew --dry-run --cert-name staging.flo4paws.co.uk` at a quiet hour with controls; if the installer complains, switch the lineage to `--webroot` or `certonly` + a deploy-hook `nginx -s reload`. Consider renaming the lineage (`www.flo4paws.co.uk`) at first renewal.
Claim evidence: MEASURED (certbot output; `openssl` SANs).

---

### BL-666 | OPEN | W5 | RULED | SMALL | `--success-url` lives in the publish record only

state:    The intake success redirect is a CLI argument to `publish.js`, recorded in `/root/publish-records/flo4paws.json` (`success_url`). A republish without the flag silently reverts to the in-page message.
remedy:   Either a `tenants.intake_success_url` column read by `generate.js` (migration + deploy), or a `publish.js` guard that reads the previous record and refuses to drop a previously set URL without `--no-success-url`. Preference: the guard (no restart).
Claim evidence: RULED — Ian took the CLI arg for W5.

---

### BL-667 | OPEN | W5 | INFERRED | SMALL | A3 residue: consent reset path and Consent tab unread

state:    `/cookie-policy/` → "Change my cookie choice" → Decline never exercised by a real actor; DebugView Consent tab never read; `non_personalized_ads = 1` seen as a sticky user property from the first denied hit.
remedy:   Five-minute browser check at W6; if the reset button fails, `site.js` fix.
Claim evidence: INFERRED.

---

### BL-668 | OPEN | W5 | INHERITED | SMALL | Stage D watch

state:    Launch 18:05 UTC 4 Sep.
remedy:   GA4 Realtime over 24 h (new stream); Ads `intake_submitted` count; Search Console coverage after 3–7 days (sitemap submitted by Ian post-close — confirm); seo-audit §5.4: Google Business Profile refresh, GSC verification by DNS TXT.
Claim evidence: INHERITED (brief Stage D).

---

### BL-673 | OPEN | W5 | MEASURED | SMALL | Search Console ownership: add the HTML-tag meta to `gen.py` HEAD

state:    The property `https://www.flo4paws.co.uk/` was verified only by Wix's HTML tag (gone since launch). W5 added DNS TXT verification (verified 18:2x). The HTML-tag method will lapse at Google's next re-check; harmless with DNS in place, but a second method costs one line.
remedy:   Ian copies the `content="…"` value from Settings → Ownership verification → HTML tag; one `gen.py` HEAD line; PR; re-verify.
Claim evidence: MEASURED (ownership screen).

---

### BL-669 | OPEN | W5 | MEASURED | SMALL | Wix site stays up; nothing points at it

state:    www/apex moved; Wix still serves at its own IPs; Wix's `/healthform` link on the old site is dead-ended by our 301 map only for visitors on our host.
remedy:   Leave up a week; downgrade only after BL-661. Update Google Business Profile links to `/contact/`.
Claim evidence: MEASURED.

---

### BL-670 | OPEN | W5 | RULED | SMALL | Intake 502 branch is not counted as a conversion

state:    When SES fails after the row is written, the form shows the in-page "saved, do not resubmit" message and no redirect.
remedy:   Accept (ruled by design). Revisit only if the 502 rate is material.
Claim evidence: RULED.

---

### BL-671 | OPEN | W5 | MEASURED | SMALL | `flo4paws-dev-api/.env` lacks `GEN_DATABASE_URL`

state:    Publishing from the dev clone required reading the key from `/root/flo4paws-api/.env` by hand.
remedy:   Add `GEN_DATABASE_URL` to the dev clone's `.env` (read-only migrator/reader role) or document the read in DEPLOY.md.
Claim evidence: MEASURED (key list).

---

### BL-672 | OPEN | W5 | INHERITED | SMALL | Cookie policy wording review

state:    Website section written by Claude against what the tag does. Not reviewed by Ian/Flo; the ICO/PECR angle from seo-audit §5.3 is the reason it exists.
remedy:   Ian reads `/cookie-policy/`; one PR for wording.
Claim evidence: INHERITED.

---

### BL-674 | OPEN | W5 | RULED | MEDIUM | Google Ads final URLs still point at Wix-era paths

state:    Campaign `Flo4Paws` (paused) ads, sitelinks and possibly keyword-level final URLs were authored against the Wix site. The 301 map absorbs them; each is a wasted hop and a destination-review risk, and a final URL on `app.` bypasses the website tag entirely.
remedy:   W6: Campaigns → Flo4Paws → Ads and assets → Ads (Final URL column, URL suffix/tracking template under campaign URL options); Assets → Sitelinks; Keywords → Final URL column. Replace per the map: `/` → `https://www.flo4paws.co.uk/`; `/my-services*` → `/how-it-works/`; `/contact`, `/copy-of-contact-thank-you`, `/healthform` → `/contact/` (ads land on www, not the app form — preference stated, Ian to rule); `/blog` → `/guides/`; `/walkies` → `/walks/`; `/customer-testimonials` → `/reviews/`; `/code-of-ethics`, `/flos-friends` → same + trailing slash; `/general-4` → `/`; `/post/*` → the mapped guide/walk else `/guides/`. Then un-pause only when Flo says.
Claim evidence: RULED (Ian raised it; not yet read in the Ads UI).

---

### BL-675 | OPEN | W5 | MEASURED | SMALL | Reviews: verbatim Trustpilot text or the widget; no review markup to strip

state:    `/reviews/` has no Trustpilot widget and its JSON-LD is BreadcrumbList + ListItem only (audit §6: hand-authored `Review`/`AggregateRating` would be penalised — none present). Review text is W1's shortened/reworded versions.
remedy:   Flo supplies verbatim reviews (owed since W1) or rules for the Trustpilot widget (carries its own markup). One content PR.
Claim evidence: MEASURED (`@type` census).

---

### BL-676 | OPEN | W5 | INHERITED | SMALL | Google Business Profile refresh (audit §5.4/§7.7)

state:    Not touched in the W series. Website link may still be a Wix-era URL; category/service area per audit: Dog Trainer; Nottinghamshire, Leicestershire, Rutland; link to `/contact/`.
remedy:   Ian, in the Business Profile UI; then re-check the `Google Business Profile: 1 linked` row in Ads.
Claim evidence: INHERITED (audit).

---

### BL-677 | OPEN | W5 | INHERITED | SMALL | Article cadence on pain-and-behaviour topics (audit §6/§7.8)

state:    Nine guides exist (the audit's topics: pain-driven behaviour, decompression walks, chews, muzzle, harness, enrichment). Nothing new since W1.
remedy:   One guide a month from Flo's consult reports; each is one `src/pages/guides__*.html` PR with sitemap order appended. Flo's call on topics.
Claim evidence: INHERITED.
