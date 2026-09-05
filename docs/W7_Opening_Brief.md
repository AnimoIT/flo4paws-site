# W7 Opening Brief — Flo4Paws website ASSETS

Read first: `Session_Handover_2026-09-04_W6_WATCH.md`, then W6 entries (provisional numbers). Re-verify every standing fact at the box.

**Standing facts (MEASURED at W6 close).** Site repo main `ba1b692` (+ the docs PR), porcelain 0, `--check` 26/51/0, served == build. `deploy/` == `/etc/nginx/`: vhost `7c8100ed`, snippet `88d31f5d`, `conf.d/flo4paws-robots-map.conf` `d322ec8c`. Staging X-Robots 1 / www 0. Cert 2026-12-03, dry-run passes. PM2 5. Staging and www share `/var/www/flo4paws-site` (WBL-681). Prod API checkout `9e34de6` — `deploy.sh` has not run since W5. Controls: `app.flo4paws.co.uk` · `app.lilyvetphysiotherapy.com` · `beerscope.co.uk` · `staging.flo4paws.co.uk` · `www.flo4paws.co.uk` 200, PM2 5. G-2 to Flo before any reload.

**Opening recon (REVIEW-ONLY) — predict, then run.** `cd /root/flo4paws-site` first (the API session shares the terminal). 1 porcelain 0 · 2 HEAD = origin (`rev-parse` one revision at a time) · 3 `python3 src/gen.py --check` 26/51/0 · 4 `diff -rq build/ /var/www/flo4paws-site` 0 · 5 three shas repo == live, **`wc -c` on all three ≥ 1** · 6 five controls, PM2 5 · 7 staging x-robots 1, www 0 · 8 placeholder sweep (WBL-686) = 0 · 9 `git branch -r` count after `fetch --prune` · 10 `ls /root/incoming/flo4paws-site-bundles` for Wix badge exports.

**W7 work, in order**
1. WBL-681 staging root — second document root + install path, so layout work can be seen before it is live. One reload (G-2, controls, byte guard WBL-679).
2. WBL-682 assets — badges (Ian scp's Apple/Google artwork + Scooby + any qualification images), `/about/` refactor, then the five alignment items on staging with screenshots, then promote.
3. WBL-684 maps if GPX has arrived.
4. Close-set: handover + entries into `docs/` **in the same PR**, `fetch --prune`, register merge status.

**Own session, not W7:** register merge (WBL-678, ruling A/B), Ads final URLs (WBL-674), Stage D read (GA Realtime, GSC, Ads `intake_submitted`), WBL-663/667 browser checks, WBL-661 DNS move.

**Do not.** Install anything to `/var/www/flo4paws-site` that Flo has not seen (WBL-681 exists for this). · Reload without `wc -c`/`diff` on the three site files first (WBL-679). · Allocate BL-/F- numbers until WBL-678 is ruled. · Trust `journalctl -u nginx` for reloads (WF-103). · Label a count of your own edit as anything but INFERRED until a script prints it (WF-102).
