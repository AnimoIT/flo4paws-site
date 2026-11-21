# quietwalks — data pipeline for the Quiet Walk Finder

Builds the data behind `/walks/quiet-walk-finder/`. Pure Python standard library.
From S369 it runs on the **pipeline server** (zooscape-prod, user `quietwalks`, in
`~/quietwalks/`), not on the web box; only the finished data is pushed to the box.

Each coverage area is a **region**: `regions/<id>.json` holds its centre, radius,
place source (postcodes or communes), crop source, attribution, local data folder,
publish target and freshness limit. `uk` is Bingham + 30 km. Engine commands default
to `--region uk`; `qw_refresh.py` and `qw_freshness.py` have no default and require it.

| Command | What it does |
|---|---|
| `python3 quietwalks.py` | Fetch OSM (Overpass) + crop map (CROME 2024) into `cache/`, score paths, write `out/quietwalks_map.html` (Ian's personal map). |
| `python3 quietwalks.py --offline` | Same, from `cache/` only. |
| `python3 quietwalks.py --offline --export /var/www/quietwalks-data/v1` | Also write the public finder data: trigger values per path in 10 km chunks, start points, `index.json`. No personal ratings are exported. |
| `python3 qw_site_data.py postcodes /var/www/quietwalks-data` | OS Code-Point Open → one JSON per postcode district inside the coverage. |
| `python3 qw_site_data.py basemap /var/www/quietwalks-data` | Protomaps daily build → `basemap.pmtiles` for the coverage (pmtiles CLI fetched into `bin/`). |

nginx serves `/var/www/quietwalks-data/` at `/walks/finder-data/` (see
`deploy/nginx-flo4paws.conf`). It is outside the rsync'd site tree, so publishing the
site never deletes it.

Data licences: OpenStreetMap (ODbL; the exported path values are a derived database,
available under the ODbL on request), CROME and Code-Point Open (Open Government
Licence), Protomaps basemap (OSM data, ODbL). Attribution is on the finder page.

## Scheduled refresh, publish and alerting

Pipeline server crontab (`quietwalks`):

    17 3 * * 0 [ "$(date +\%d)" -le 07 ] && cd ~/quietwalks && nice -n 19 python3 qw_refresh.py --region uk >> logs/cron-uk.out 2>&1
    41 9 * * 1 cd ~/quietwalks && python3 qw_freshness.py --region uk >> logs/cron-uk.out 2>&1

- **Monthly** (first Sunday): re-download OpenStreetMap into a staged copy of the
  region cache (crop map kept), export to `data/<id>/v1.candidate`, and check it
  against `data/<id>/v1` (the copy of what was last published): paths, start points
  and chunks must not fall by more than 15%.
- **Publish**: rsync the candidate with a write-only `rrsync` key into
  `/var/lib/qwpush/incoming/<id>/` on the box (outside the web root), then call the
  swap key, whose only possible command is `/usr/local/bin/qw-swap <id>`
  (`qw_swap.py`). The swap repeats the checks (index parses, every chunk present,
  15% rule; PMTiles header for the basemap), checks everything before swapping
  anything, and keeps the previous copy as `.prev`. The local copy swaps only after
  the box has.
- **Quarterly** (Jan/Apr/Jul/Oct, regions with `quarterly_site_data`): postcodes and
  basemap, same checks, same publish.
- **Alerting**: `qw_freshness.py` reads the live `index.json` from the public site
  and pings the BetterStack heartbeat only while `built` is at most `max_age_days`
  (40) old. Any break in the chain (build, refusal, push, swap, server, cron, serving)
  shows up as a missed heartbeat. The heartbeat URL lives outside the repo in
  `~/.config/quietwalks/heartbeat-<id>.url` (chmod 600).
- The crop map (CROME) is refreshed by hand once a year: delete `cache/crome_*.json`
  and run a refresh.
- Logs: `logs/refresh-<id>.log`, `logs/freshness-<id>.log`, `logs/cron-<id>.out` on
  the pipeline server; `/var/lib/qwpush/qw-swap.log` on the box. Exit 2 = refused
  by a check, exit 1 = failed; in both cases the live site is unchanged.

Box side (`qwpush` user, `~qwpush/.ssh/authorized_keys`):

    command="/usr/bin/rrsync -wo /var/lib/qwpush/incoming/uk",restrict ssh-ed25519 AAAA... qw-push-uk
    command="/usr/local/bin/qw-swap uk",restrict ssh-ed25519 AAAA... qw-swap-uk

Roll back a bad month on the box: `mv /var/www/quietwalks-data/v1 /var/www/quietwalks-data/v1.bad && mv /var/www/quietwalks-data/v1.prev /var/www/quietwalks-data/v1`,
then do the same in `~/quietwalks/data/uk/` on the pipeline server so its next check
compares against what is live.
