# Session Handover - 2026-09-05 - W6b REGISTER + ADS

Written by the W6b instance at close. It is this instance's read; the box is canonical. Re-verify before relying on it.

## Rulings (Ian, 5 Sep)
- Register: **A** - W-series keeps its own register in `docs/`, prefixes `WBL-` / `WF-`, numbers kept. Infra `BL-657` and site `WBL-657` are different items.
- `deploy/` comment lines: **a** - renamed and copied to `/etc/nginx` without a reload.
- `/book-online` 404: **b** - no reload today; 301 batched into WBL-688.
- Contact sitelinks: **`/contact/`**, not the app intake form.

## Done (MEASURED at close)
- PR #14 `39fa6f7` on main: 69 headings renamed across 14 files; four historical lines kept infra IDs; `W_REGISTER.md` created; README table rewritten; manifest regenerated.
- Branch `w6b-close`: `964a0ed` deploy/ comments to WBL- (installed, no reload, three sha pairs equal, bytes 4955/705/385); `8ba9207` W6b entries WBL-688-690, WF-106-109; counters WBL-691 / WF-110; manifest 20 entries, 0 failures; census 76 headings.
- Ads (Ian, in the UI): all 11 Flo4Paws sitelinks across both campaigns repointed to new-site URLs per the table in WBL-690's session. Ad final URLs already `/`. Campaign status unchanged (paused stays paused).
- Collision extent measured: BL-643-658, sixteen IDs, S217-S219 vs W3-W4 (WF-107). The intro's "W4 five" was wrong.

## Not done / next
1. **Stage D read** (intro item 2) - GA4 Realtime on `G-SSKB2MX887`, Ads `intake_submitted`, GSC. Retire Wix Ads actions only at >=1 (WBL-664). Ian, off-box.
2. **Browser checks** (intro item 3) - cookie bar Decline (WBL-667); DebugView Consent tab; `click` beside `intake_form_start` (WBL-663). Three literal clicks; Ian.
3. **WBL-689** - Final URL expansion off or exclusions in Ads. Ian.
4. **WBL-688** - one reload adding `/book-online`, `/my-services/`, `/blog/` 301s. Flo told, five controls, byte guard. Any W session.
5. **W7 ASSETS** - unchanged; needs a staging root first (WBL-681). Badge artwork received from Ian on 5 Sep as WebP rasters (330x98, 500x149), not the vector originals; get the official SVGs from Apple/Google badge pages before use.
6. S220 note: infra `NEXT_ID` BL-659 / `NEXT_F` F-82 were untouched by this session. Nothing in `animoit-infra` was written. S220 allocates freely from BL-659.

## Addendum - Stage D and browser checks (Ian in browsers, 5 Sep 07:30-08:15 BST)
- GA4 tag live on the new site: Realtime showed `/` and `/contact/`. `intake_form_start` fires on form focus (count 2 for 2 focuses); no `click` event alongside it. Standard Events report empty for today (24-48 h lag), not a fault.
- `intake_submitted` is not sent by the site. It is a GA4 created event: `page_view` with URL containing `/thank-you/`, key event on stream "Flo4Paws Website 2026", imported into Ads as Primary under goal Contact. Proven by one manual visit to `/thank-you/` at ~07:55 BST: Realtime key events showed `intake_submitted` 1. **That one is a test, not a lead; exclude it from WBL-664's first-real reading.**
- Ads conversion actions: goal Contact held `click (1)` Active/Primary - GA4's generic outbound-click key event steering bidding. Set to Secondary 5 Sep (WBL-663 closes: no double-fire on the form, but `click` was polluting conversions from elsewhere). `Contact_Thank_You_2` and `Booking_thank_you_2` (Wix pages) and `generate_lead` sit on the old stream "Flo4Paws Website"; retire with WBL-664 / WBL-662.
- Campaign was **Enabled**, not paused (WF-110). Flo to be told.
- WBL-689 done: Final URL expansion off, DSA empty, no tracking template.
- Search Console: `sitemap.xml` Success, 25 discovered (matches the box). Pages report still pre-launch (20 indexed / 41 not, data to ~23 Aug); re-read in two weeks. Homepage re-index requested.
- WBL-667 closes: Decline hides the bar and it stays hidden on reload (incognito); "Change my cookie choice" is a button on `/cookie-policy/` (once in `build/cookie-policy/index.html`), reachable from the footer link.
- Sitelinks: all 11 across both campaigns repointed; `/book-online` no longer receives paid clicks. 301 still owed (WBL-688).

## Watch
- Three arithmetic mislabels of my own edit counts (WF-108) and one write-before-assert (WF-106). Both patterns are in the intro's warnings and recurred anyway. Next instance: assert before write; label own-edit counts INFERRED.
- `docs/MANIFEST.sha256` must be regenerated in the same PR as any docs edit; `sha256sum -c` printing 0 is the proof.

## Open block for the next W session
Same as the W6b intro's opening block, plus: `grep -hoE '^### (WBL|WF)-[0-9]+' docs/W*_entries.md | wc -l` (expect 76) and `cd docs && sha256sum -c MANIFEST.sha256 | grep -vc ': OK$'` (expect 0).
