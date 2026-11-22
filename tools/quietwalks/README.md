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

## France (`regions/fr.json`), in development

Mâcon + Cluny, 30 km round 46.371 N, 4.744 E. Built on zooscape-prod in
`~quietwalks/quietwalks-fr-dev/` (not published yet; publishing comes with the
French pages, build step B6 of the France spec).

- **Crops:** `crops.source = "rpg"` reads IGN RPG parcels from the Géoplateforme
  WFS (`RPG.LATEST:parcelles_graphiques`), filtered on the server by `code_group`:
  high 5 colza, 6 tournesol, 8 protéagineux, 15 légumineuses à grains; mid 2 maïs.
  Fields are marked along their outline. Licence Ouverte 2.0 ("IGN – RPG").
- **Place search:** `places = "communes"`; `python3 qw_site_data.py --region fr communes OUT`
  writes `communes.json` (name, INSEE, postcodes, centre, population) from
  geo.api.gouv.fr for `communes_depts` 71, 69, 01. Licence Ouverte 2.0.
- **Extra starts:** `extra_starts` adds village centres and `highway=trailhead`
  as starts, after every car park, flagged `noparking`, 1 km from any kept start.
- **First counts (22 Nov 2026):** 28,903 paths, 8,671 km; 640 starts (587 car
  parks + 53 villages; 0 trailheads mapped); 318 communes; RPG 8,599 parcels.
- **UK is unaffected:** with the same cache, the UK `v1/` is byte-identical apart
  from `built` (S370).
- **Seasonal layers (B4, S372):** `layers` in `fr.json` adds four fields after index 8 in
  every path row: `wood` and `vine` (0-100, share of the path's 25 m samples), `dept`
  (INSEE code covering most of the path) and `forest_id` (ONF id covering at least 25%),
  plus `forests.json` (id -> name, forêt domaniale yes/no, dept). Sources: OSM + IGN
  masque forêt 2021-2023; OSM + RPG group 21; IGN Admin Express; ONF forêts publiques.
  RPG permanent grassland goes only to `out/livestock_check.csv` (not exported).
  Regions without `layers` (the UK) get no new query and no new field.
- **Rules:** `regions/fr_rules.json` holds the hunting orders (71, 69, 01), ONF hunt days,
  the lead rule (15 Apr-30 Jun) and the harvest window. `python3 qw_rules.py --check`
  validates it; `qw_rules.py --state 71 2026-12-04` shows a day's state. **Every August or
  September**, enter the new orders and ONF days, or the check fails and the page treats
  every day as a hunting day.
- **Tests:** `python3 test_qw_rules.py`, `python3 test_b4_fields.py` (offline, synthetic).
- **Livestock check:** `python3 qw_livestock_map.py <dir holding out/> map.html` makes the
  map Flo uses to say whether the red livestock paths round Cluny really have stock.
