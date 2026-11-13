# quietwalks — data pipeline for the Quiet Walk Finder

Builds the data behind `/walks/quiet-walk-finder/`. Runs on the box as `flo4paws`
in `/home/flo4paws/quietwalks/` (its `cache/` holds the downloaded OpenStreetMap and
crop-map data). Pure Python standard library.

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

## Scheduled refresh

`qw_refresh.py` runs from the `flo4paws` crontab at 03:17 on the first Sunday of
each month:

    17 3 * * 0 [ "$(date +\%d)" -le 07 ] && cd /home/flo4paws/quietwalks && nice -n 19 python3 qw_refresh.py >/dev/null 2>&1

- Monthly: re-downloads OpenStreetMap into a staged copy of `cache/` (the crop map
  is kept) and exports to `v1.candidate/`. It swaps in only if paths, start points
  and chunks each fell by no more than 15%; the previous data stays in `v1.prev/`
  and `cache.prev/`.
- Quarterly (Jan/Apr/Jul/Oct): fresh postcodes and basemap, same check, then swap.
- The crop map (CROME) is refreshed by hand once a year when RPA publishes it:
  delete `cache/crome_*.json` and run `python3 quietwalks.py --export ...`.
- Log: `/home/flo4paws/quietwalks/refresh.log`. Exit 2 = refused by the check
  (nothing live changed); exit 1 = failed (nothing live changed).

Roll back a bad month: `mv /var/www/quietwalks-data/v1 /var/www/quietwalks-data/v1.bad && mv /var/www/quietwalks-data/v1.prev /var/www/quietwalks-data/v1`.
