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

## Watch
- Three arithmetic mislabels of my own edit counts (WF-108) and one write-before-assert (WF-106). Both patterns are in the intro's warnings and recurred anyway. Next instance: assert before write; label own-edit counts INFERRED.
- `docs/MANIFEST.sha256` must be regenerated in the same PR as any docs edit; `sha256sum -c` printing 0 is the proof.

## Open block for the next W session
Same as the W6b intro's opening block, plus: `grep -hoE '^### (WBL|WF)-[0-9]+' docs/W*_entries.md | wc -l` (expect 76) and `cd docs && sha256sum -c MANIFEST.sha256 | grep -vc ': OK$'` (expect 0).
