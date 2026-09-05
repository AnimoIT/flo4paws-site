# flo4paws-site - docs
Satellite documents for the website rebuild, moved here from the Claude project in W4 (4 Sep 2026, WBL-650). Session handovers describe what the previous session *believed*; the box and this repo are canonical. Anything in a handover that the W3 addendum corrects is superseded by the addendum.

Register: the W-series keeps its own register in this directory (ruling A, W6b, 5 Sep 2026). See `W_REGISTER.md` for prefixes, ranges and the `NEXT_` counters. `animoit-infra` holds the S-series only.

| File | What it is |
|---|---|
| `W_REGISTER.md` | W-series register index: WBL-/WF- prefixes, per-session ranges, `NEXT_WBL` / `NEXT_WF`, census instruments. |
| `ia-v2.md` | Information architecture v2 - the page map, redirects, and the 90-day baseline. Ads figures corrected in W4 (see the table notes). |
| `seo-audit.md` | The pre-rebuild SEO audit. Section 5.3 is the GA4 + Consent Mode requirement for launch (WBL-654). |
| `Session_Handover_2026-09-02_W1_WEBSITE.md` | W1: generated the 23-page site. Read with its addendum. |
| `Session_Handover_2026-09-02_W1_WEBSITE_Addendum_W3.md` | W3's corrections to W1 - eight claims, each with the measurement that falsified it. |
| `W3_BACKLOG_entries.md`, `W3_FINDINGS_entries.md` | W3 register entries (WBL-643-654, WF-82-87). |
| `Session_Handover_2026-09-04_W4_APP.md` | W4: `/app/` page, docs moved into the repo, manifest introduced. |
| `W4_BACKLOG_entries.md`, `W4_FINDINGS_entries.md` | W4 register entries (WBL-655-659, WF-88-91). |
| `Session_Handover_2026-09-04_W5_LAUNCH.md` | W5: launch - GA4 + Consent Mode v2, apex on the vhost, 301 map, Ads paused. |
| `W5_BACKLOG_entries.md`, `W5_FINDINGS_entries.md` | W5 register entries (WBL-660-677, WF-92-100). |
| `Session_Handover_2026-09-04_W6_WATCH.md` | W6: staging noindex, cert lineage, Flo's read-through text batch, the register collision as then understood. |
| `W6_BACKLOG_entries.md`, `W6_FINDINGS_entries.md` | W6 register entries (WBL-678-687, WF-101-105); formerly provisional W6-BLn / W6-Fn. |
| `W7_Opening_Brief.md` | Brief for W7 ASSETS (badges, qualifications, `/about/` refactor). Needs a staging root first (WBL-681). |
| `MANIFEST.sha256` | `sha256sum` of every `.md` in this directory. Verify with `cd docs && sha256sum -c MANIFEST.sha256`. Regenerate in the same PR as any docs edit. |

Still not here: the W2 (mobile) handover and the ChatGPT screenshot audit. Add them if found.
