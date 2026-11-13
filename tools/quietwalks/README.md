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
