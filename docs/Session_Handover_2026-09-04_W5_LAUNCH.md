# Session Handover — 2026-09-04 W5 (LAUNCH)

**Series:** W1 WEBSITE · W2 MOBILE · W3 REPO · W4 APP · **W5 LAUNCH (4 Sep, 14:15–18:10 UTC)** · W6 = WATCH.
Everything below is from output pasted back from the box, GA/Ads screenshots, and one real-actor submission. Treat it as this session's read, not ground truth. Recon at W6 open.

## 0. Recon — 13/14

All W4 standing facts held (porcelain 0, main `d1f4967`, `--check` 25/50/0, served == build, PM2 5, X-Robots 1, vhost `d01dec4b`/snippet `929c585f`, four controls 200). New measurements: apex `flo4paws.co.uk` = three Wix A records (`185.230.63.x`); TTL 3600 on both names. Miss: `publish.js` is at `scripts/intake-form/`, not under `src/` (memory location stale).

## 1. Outcome — BL-654 DONE

`https://www.flo4paws.co.uk/` live from `ubuntu-4gb-hel1-1` at 18:05 UTC. Cert `staging.flo4paws.co.uk` lineage expanded to `staging`, `www`, apex (expires 2026-12-03). Apex 301 → www on both ports (proven via `--resolve`, not the box resolver — see F-98). `X-Robots-Tag` gone from every response on www, staging and images. 301 map spot-checked: `/my-services`→`/how-it-works/`, `/healthform`→intake form, `/blog`→`/guides/`. `/.git/HEAD` 404. Sitemap 25 URLs (`/thank-you/` excluded by design). DNS: `www` CNAME→Wix replaced by A `204.168.132.118`; apex three A → one A `204.168.132.118`, both edited in the **Wix** DNS panel (nameservers are `ns10/ns11.wixdns.net`, delegated from **IONOS**, the registrar — see BL-661).

## 2. Stage A — GA4 + Consent Mode v2

**A1 finding that changed the plan.** The property `Flo4Paws – Reset 2025` (508446406) had one web stream (`Flo4Paws Website`, measurement ID `G-WZVF0MNWQF`). Google **refuses to serve a tag for that ID**: `gtag/js?id=G-WZVF0MNWQF` → 404 (1.5 kB error page) from the box with and without a browser UA, and the same 404 when the Ad Tag container chain-loads it as a destination (`&cx=c`). Controls: a fake ID returns 200/427 kB (so 200 proves nothing); ClientFlex's `G-J9CQ2WKRBT` 200/567 kB; container bytes self-mention their own IDs. The ID is destination-only inside the Ad Tag container (`AW-16900645722` / `GT-5D9KNJ93`), added 13/10/2025; March's "404, probably temporary" on `admin.html` was this — the admin tag has been dead five months. Wix feeds the old stream by its own integration. **Resolution (Ian ruled): new web stream `Flo4Paws Website 2026`, measurement ID `G-SSKB2MX887`, same property** — Ads link (since 14 Oct 2025, auto-tagging on) and history untouched. Old stream left in place for now (BL-662).

**A2 — site repo PR #7 (`4dd8f7e`, `56db9d2`, `06cc3b6` → squash `055a1fa`), #8 (`219bd57`).**
- `gen.py`: tag replaces the `HEAD_TAIL` placeholder — consent default (all four denied) pushed before `gtag.js` is requested; stored `f4p-consent === granted` replayed inline so no `wait_for_update` race; linker domains `flo4paws.co.uk`, `app.flo4paws.co.uk`; `debug_mode` only when hostname is `staging.`. Loader and config both `G-SSKB2MX887`. `@@ROBOTS@@` per page (default unchanged for the 25); `"sitemap": null` excludes a page.
- `site.js` (6→25 lines): consent bar (`localStorage f4p-consent`, Accept/Decline → `gtag('consent','update')`), `#consent-reset` re-asks, `intake_form_start` on the `/contact/` form link. `site.css` +5 lines.
- `/thank-you/`: noindex,nofollow, out of the sitemap, carries the claim-email instruction (copy from S218's in-page message, generic — no email address in a GA-tagged URL); drops the plan-and-diary claim (BL-657).
- Cookie policy rewritten: website section (what the tag does, `_ga` up to 2 years, cookieless pings when denied, change-choice button), platform section kept, note-box gone, "Last updated: September 2026".

**A3 — proven on staging (Chrome incognito).** `gtag/js?id=G-SSKB2MX887` 200; `collect` 204 with `tid=G-SSKB2MX887`; DebugView `page_view` after Accept (no device while denied — DebugView cannot attach an ID-less ping); `intake_form_start` ×2; cross-domain linker proven: app URL carried `_gl=…*_ga_SSKB2MX887*…` with `_gcl_au`. Domain rule "Contains flo4paws.co.uk" set on the new stream's tag (the GA4 stream's Google tag *is* the Ad Tag container — one domain list). Not read: the Consent tab on an event; step 5 (change-choice → Decline) — BL-667.

**A4 — API repo PR #131 (`ce27f78` → squash `92c2a58`).** Ian's rulings: (a) success redirects to `/thank-you/`, in-page message replaced by the page's copy; (ii) prove on Flo's live form, no staging alias (the staging tenant has **no** intake location on the clientflex-app vhost — only the generic deny). Design: optional `--success-url` on `generate.js` (https, `[A-Za-z0-9./_-]` only), emitted as `<meta name="cf-success-url">` with a `GENERATED-SUCCESS-URL` marker under the same count-of-one guard as the tenant slug; template redirects in the `out.ok` branch only (the 502 "saved, do not resubmit" message stays in-page and is not counted); `publish.js` passes it through and records `success_url`. No migration, no restart, no G-2. Preference changed mid-session from a `tenants` column to the CLI arg because a column means `deploy.sh` = production API restart for a URL. Dry runs ×2 against prod DB passed every publisher gate. Real publish 16:30 with `https://staging.flo4paws.co.uk/thank-you/`; **real-actor submission by Ian landed on the thank-you page**; test row `645759e0…` (email `ianberry-test100@fastmail.com`, unclaimed) deleted; the claim email bounced at Fastmail (alias not routed) — one SES bounce. Republished 18:08 with `https://www.flo4paws.co.uk/thank-you/` (`77b45495…`, record `live`). Publisher run from `/root/flo4paws-dev-api` at `main`; the connection string read from `/root/flo4paws-api/.env` (`GEN_DATABASE_URL` is not in the dev clone's `.env` — BL-671); prod checkout never pulled (still `9e34de6`).

**A5.** GA4: `intake_submitted` created from `page_view` where URL contains `/thank-you/`, on stream *2026*, key event, no value, once per session. Proven on the wire: `collect … en=intake_submitted&_c=1` 204 from `/thank-you/` (Google pushes the definition into the container; DebugView lagged). Ads: imported from GA4 as **Primary** under category *Contact* (Submit-lead-form category not offered in the wizard); the `/contact` page-visit suggestion declined. Wix actions (`Contacts` 7, `Submit lead forms` 2 over Jun 5–Sep 2) left in place — retire after ≥1 new conversion (BL-664).

## 3. Stage B/C — vhost, DNS, cert, index

- PR #9 (`0f9fcee`): apex in both `server_name`s; `if ($host = flo4paws.co.uk) { return 301 https://www.flo4paws.co.uk$request_uri; }` in both blocks. `nginx -t` proven on the candidate with live swapped in and restored (try/finally, both rc 0) before the PR existed. Installed 17:39:58, reload, controls 200×4/5 both sides.
- DNS edited in Wix by Ian ~17:56. Authoritative (`@ns10.wixdns.net`) showed 204 for both within two minutes; 1.1.1.1 followed; the box resolver held the Wix apex for its full hour.
- `certbot --nginx --expand --cert-name staging.flo4paws.co.uk -d staging -d www -d apex`: certificate issued and deployed; **rc 1** on the redirect-enhancement step (conflict with our apex `if`) — harmless; left three blank lines in the vhost, removed by the next install. SANs verified with `openssl` on the wire. Renewal lineage unchanged (BL-665 to dry-run).
- PR #10 (`4a8e4c7`): `X-Robots-Tag` line and its LAUNCH comment out of the headers snippet. Installed with the vhost 18:05:17, reload, controls 200×5/5 (www added as fifth). Headers on www: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, `Cache-Control: no-cache`.
- Search Console sitemap submit + indexing requests: Ian, after close (confirm at W6 open).

Invariants at close: site repo main `4a8e4c7`, one branch, porcelain 0, `--check` 26/51/0, served == build; `deploy/` == `/etc/nginx/` for both files (`7c8100ed`, `7b251ac9`); API dev clone main `92c2a58`, porcelain 0; PM2 5. Backups: `/root/incoming/flo4paws-site.{w5-pre-apex,pre-apex-HHMM,pre-certbot-HHMM,pre-index-HHMM}.bak`, `flo4paws-site-headers.pre-index-HHMM.bak`; `/root/publish-records/artefact-backups/flo4paws-2026-09-04T{15-18-20,16-30-08,18-08-18}*.html`.

## 4. Rulings given (Ian)

New GA4 stream rather than repairing the old ID · apex moves with www · both events: thank-you page_view as key event + `intake_form_start` secondary · (a) redirect with generic copy · (ii) prove on Flo's live form · Stage B/C tonight · Flo told once before the first reload (G-2 covered all three reloads + certbot's).

## 5. Errors — see F-92..F-99

Six count mispredictions labelled DERIVED without an instrument (F-93). `grep -r` on `sites-enabled/` false absence (F-92). `node --check` on `.candidate` (F-94). `gh pr checks --watch` merged ungated on "no checks reported" (F-95, fixed same session with `sleep` + `PIPESTATUS`). "Browser blocker" invented for a symptom the dead ID explained (F-97). Box resolver cache used as the instrument for the apex http test (F-98). `push rc=$?` after a pipe; `clean -n` before `add` (F-99). None reached the bytes. One paste of output back into the shell (Ian) — harmless, all "command not found".

## 6. Observed, not acted on

Paste tails from the S218 frontend/API session throughout (PR #111 merged, served `8f19cf2` ≠ main `94d3eea`; `deploy.sh` chmod list read; `/root/deploy-logs` absent). `flo4paws-dev-api` has 12 local branches. `admin.html` still carries the dead `G-WZVF0MNWQF` tag. `deleted_intake_archive` columns not read (my `created_at` guess errored). Enhanced-measurement `click` still fired on the app link after the domain rule was saved (may be container lag).

## 7. Still open from W4

BL-655 guides ruling · BL-656 double Cache-Control · BL-657 (partly addressed) · BL-658 docs/ gaps (W2–W5 handovers not in repo) · BL-659 Ads figure.

## 8. seo-audit.md coverage, read against the served site at close (Ian asked)

| audit § | state | basis |
|---|---|---|
| 1 six documents, h1, canonical/OG/robots meta, sitemap, robots.txt | done (W1/W3) | MEASURED tonight: 26 pages, HEAD template, sitemap 25, `robots.txt` 200 with `Allow: /` + Sitemap line |
| 3 per-page titles/descriptions | present per page; wording is `ia-v2`'s, not the audit table's | MEASURED (front-matter) |
| 4 301 map | 24 entries live; walks kept and international-canine → guide (rulings); `/healthform` → app form (Ian, W4) vs audit's `/contact/` | MEASURED (vhost, curl) |
| 5.1–5.3 IDs, cross-domain, consent, cookie policy | done W5 (see §2) | MEASURED |
| 5.4 GSC by DNS, sitemap, Business Profile, keep Wix 30 days | DNS TXT verified; sitemap Success/25; **Business Profile open** (BL-676); Wix held behind BL-661 | MEASURED / OPEN |
| 6 articles | nine guides are the pain-and-behaviour articles; cadence open (BL-677) | MEASURED (pages) |
| 6 verbatim Trustpilot / widget; no hand-authored review markup | widget 0 pages; `/reviews/` JSON-LD is BreadcrumbList + ListItem only — **nothing to strip**; verbatim reviews still owed by Flo (BL-675) | MEASURED |
| 6 Lincolnshire contradiction | **gone** — 0 served pages mention Lincolnshire; BL-649 is now "add it?" not "fix it" | MEASURED |
| 7.7 Google Business Profile | open | — |

## 9. Ads final URLs (Ian raised at close) — BL-674

The Flo4Paws campaign's ads, sitelinks and any keyword-level final URLs still carry Wix-era paths. The 301 map catches them but each is a wasted hop and an Ads destination-review risk. Review at W6 with the map in the entries; preference stated: lead ads land on `/contact/` (the page with the form button, so `intake_form_start` and the linker cookie both happen), not on the app form directly.

## 10. Next: W6 = WATCH. Brief in `W6_Opening_Brief.md`.
