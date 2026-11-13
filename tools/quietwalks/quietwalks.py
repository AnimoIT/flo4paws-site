#!/usr/bin/env python3
"""
quietwalks.py - find quiet footpaths for a nervous dog (Gatsby edition).

Personal, non-commercial tool. Pure Python standard library: nothing to install.

What it does
  1. Downloads OpenStreetMap data around a centre point (Overpass API), in tiles,
     cached in ./cache so re-runs are instant.
  2. Builds 50 m distance rasters for each trigger source (car parks, parks,
     playgrounds, kennels, housing, pasture, stiles/farmyards, main roads).
  3. Scores every footpath/bridleway/track 0-100 (100 = quietest) from
     Gatsby's trigger weights below.
  4. Ranks parking spots by how much quiet path lies within 1.5 km.
  5. Writes out/quietwalks_map.html (open in any browser) and out/top_starts.csv.

Your own verdicts: put rows in my_ratings.csv  ->  way_id,stars,note
  (stars 1-5; the way_id is shown in each path's popup). Rated paths use your
  stars instead of the model score on the next run.

Usage
  python3 quietwalks.py              # fetch (or reuse cache) and build
  python3 quietwalks.py --offline    # cache only, no network
  python3 quietwalks.py --refresh    # ignore cache, re-download

Data (c) OpenStreetMap contributors, ODbL.
"""
import array
import csv
import json
import math
import re
import os
import sys
import time
import urllib.parse
import urllib.request

# ---------------------------------------------------------------- settings
CENTRE_LAT, CENTRE_LON = 52.9520, -0.9530      # Bingham
RADIUS_M = 30000
CELL_M = 50                                    # raster resolution
TILES = 3                                      # TILES x TILES Overpass requests

# Gatsby's trigger weights (sum need not be 1; normalised below)
WEIGHTS = {
    "people_dogs": 0.40,   # other dogs, people, crowds
    "livestock":   0.20,   # sheep, cattle, horses
    "bikes":       0.15,   # cyclists
    "bangs":       0.15,   # shooting grounds/ranges, crop bird-scarers (gas guns)
    "traffic":     0.10,   # road noise (not a main trigger, small weight)
}
# How bad each trigger is on its own at full strength (0-1). Half the final
# risk is the single worst trigger, so one strong trigger (a sheep field, a
# busy car park) can't be averaged away by the others being fine.
SEVERITY = {
    "people_dogs": 1.0,
    "livestock":   0.8,
    "bikes":       0.6,
    "bangs":       0.8,    # Gatsby: bad, but less than dogs approaching
    "traffic":     0.3,
}
GREEN, AMBER = 75, 55       # map colour bands
START_RADIUS_M = 1500       # path catchment around a parking spot

VERSION = "4"
# Bangs. Shooting grounds carry ~2 km. Bird scarers are used on oilseed rape,
# beans/peas and at maize drilling; the crop map is from 2024 and crops rotate,
# so it marks likely scarer farms, not this year's fields - kept modest.
SHOOT_FULL_M, SHOOT_FADE_M = 1000, 1500   # full strength to 1 km, fading out by 2.5 km
SCARER_RADIUS_M = 500
SCARER_MAX = 0.7            # crop-map scarer risk never exceeds this
CROME_BASE = "https://environment.data.gov.uk/spatialdata/crop-map-of-england-2024/ogc/features/v1"
CROME_COUNTIES = ("Nottinghamshire", "Leicestershire", "Lincolnshire", "Derbyshire")
CROME_HIGH = ("AC67", "LG03", "LG07", "LG11", "LG14", "LG20")  # winter OSR + legumes
CROME_MID = ("AC17",)                                            # maize
CROME_MIN_PROB = 0.4
QUIET_SHOOTING_WORDS = ("laser", "airsoft", "archery", "paintball", "nerf")
RANGE_WORD = re.compile(r"\brange\b")     # "Rifle Range" yes, "Sherwood Rangers" no
DISUSED_WORDS = ("disused", "dissused", "former", "abandoned", "dismantled")
GAME_FADE_M, GAME_MAX = 500, 0.6   # woods tagged for shooting: seasonal game shoots
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
]
# Path density: km of path in a ~1 km square. Countryside is typically 3-6;
# forest parks and country parks 10-20. Risk ramps from DENS_LO to DENS_HI.
DENS_LO, DENS_HI = 6.0, 14.0
START_MIN_GREEN_KM = 4.0    # a start point needs this much quiet path within 1.5 km
DIST_PENALTY = 0.5          # rank points lost per km from the centre
HONEYPOT_WORDS = ("country park", "forest park", "visitor centre", "go ape", "adventure",
                  "castle", "abbey", "priory", "arboretum")
BIG_PARK_PENALTY = 8        # rank points lost if the start car park itself is large/busy
DEDUPE_M = 1000             # one start point per walk area
BIKE_WORDS = ("cycle", "bike", "mtb", "berm", "singletrack", "pump track", "bmx")
CHECK_DOGS_WORDS = ("rspb", "rsbp", "nature reserve", "wildlife trust", "nnr")
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
OUT = os.path.join(HERE, "out")
RATINGS = os.path.join(HERE, "my_ratings.csv")

# ---------------------------------------------------------------- geometry
KX = 111320.0 * math.cos(math.radians(CENTRE_LAT))
KY = 110540.0


def to_xy(lat, lon):
    return (lon - CENTRE_LON) * KX, (lat - CENTRE_LAT) * KY


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


# ---------------------------------------------------------------- overpass
def bbox_tiles():
    dlat = (RADIUS_M + 1500) / KY
    dlon = (RADIUS_M + 1500) / KX
    s, n = CENTRE_LAT - dlat, CENTRE_LAT + dlat
    w, e = CENTRE_LON - dlon, CENTRE_LON + dlon
    out = []
    for i in range(TILES):
        for j in range(TILES):
            ts = s + (n - s) * i / TILES
            tn = s + (n - s) * (i + 1) / TILES
            tw = w + (e - w) * j / TILES
            te = w + (e - w) * (j + 1) / TILES
            out.append((round(ts, 5), round(tw, 5), round(tn, 5), round(te, 5)))
    return out


QUERIES = {
    "paths": """
(
  way["highway"~"^(footway|path|bridleway|track|cycleway|steps|byway)$"]({b});
  way["highway"]["designation"~"public_footpath|public_bridleway|restricted_byway|byway_open_to_all_traffic"]({b});
);
out tags geom;""",
    "features": """
(
  nwr["amenity"="parking"]({b});
  nwr["leisure"~"^(park|playground|dog_park|picnic_site|pitch|recreation_ground)$"]({b});
  nwr["tourism"~"^(attraction|picnic_site|viewpoint|visitor_centre|camp_site|caravan_site)$"]({b});
  nwr["amenity"~"^(cafe|pub|school|dog_toilet|animal_boarding|animal_shelter)$"]({b});
  nwr["landuse"~"^(residential|meadow|farmyard)$"]({b});
  nwr["leisure"="horse_riding"]({b});
  nwr["building"="stable"]({b});
  node["barrier"~"^(stile|cattle_grid)$"]({b});
  way["highway"~"^(motorway|trunk|primary|secondary|motorway_link|trunk_link|primary_link)$"]({b});
);
out tags geom;""",
    "cycleroutes": """
relation["route"~"^(bicycle|mtb)$"]({b});
way(r)({b});
out ids;""",
    "walkroutes": """
relation["route"~"^(hiking|foot|walking)$"]({b});
way(r)({b});
out ids;""",
    "bangs": """
(
  nwr["sport"~"shooting|clay_pigeon|target_shooting",i]({b});
  nwr["leisure"~"^(shooting_ground|shooting_range)$"]({b});
  nwr["military"~"^(range|danger_area)$"]({b});
  nwr["landuse"="military"]({b});
);
out tags geom;""",
    "honeypots": """
(
  nwr["leisure"="nature_reserve"]({b});
  nwr["historic"~"^(castle|manor|stately_home)$"]({b});
  nwr["leisure"="park"]["name"~"Country Park|Forest Park",i]({b});
  node["place"~"^(town|village|hamlet|suburb)$"]({b});
);
out tags geom;""",
}


def overpass(query):
    body = "[out:json][timeout:300][maxsize:536870912];" + query
    data = urllib.parse.urlencode({"data": body}).encode()
    last = None
    for attempt in range(6):
        url = ENDPOINTS[attempt % len(ENDPOINTS)]
        try:
            req = urllib.request.Request(url, data=data, headers={
                "User-Agent": "quietwalks/1.0 (personal dog-walk planner)"})
            with urllib.request.urlopen(req, timeout=360) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last = e
            wait = 20 * (attempt + 1)
            log(f"  overpass error ({url}): {e}; retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Overpass failed after retries: {last}")


def bng_to_latlon(E, N):
    """OSGB36 National Grid -> lat/lon (Airy 1830, no datum shift; ~100 m error, fine here)."""
    a, b = 6377563.396, 6356256.909
    F0, lat0, lon0 = 0.9996012717, math.radians(49), math.radians(-2)
    N0, E0 = -100000, 400000
    e2 = 1 - (b * b) / (a * a)
    n = (a - b) / (a + b)
    lat, M = lat0, 0
    while N - N0 - M >= 0.00001:
        lat = (N - N0 - M) / (a * F0) + lat
        Ma = (1 + n + 1.25 * n ** 2 + 1.25 * n ** 3) * (lat - lat0)
        Mb = (3 * n + 3 * n ** 2 + 2.625 * n ** 3) * math.sin(lat - lat0) * math.cos(lat + lat0)
        Mc = (1.875 * n ** 2 + 1.875 * n ** 3) * math.sin(2 * (lat - lat0)) * math.cos(2 * (lat + lat0))
        Md = (35 / 24) * n ** 3 * math.sin(3 * (lat - lat0)) * math.cos(3 * (lat + lat0))
        M = b * F0 * (Ma - Mb + Mc - Md)
    c, sn, t = math.cos(lat), math.sin(lat), math.tan(lat)
    nu = a * F0 / math.sqrt(1 - e2 * sn * sn)
    rho = a * F0 * (1 - e2) * (1 - e2 * sn * sn) ** -1.5
    eta2 = nu / rho - 1
    VII = t / (2 * rho * nu)
    VIII = t / (24 * rho * nu ** 3) * (5 + 3 * t * t + eta2 - 9 * t * t * eta2)
    IX = t / (720 * rho * nu ** 5) * (61 + 90 * t * t + 45 * t ** 4)
    X = 1 / (c * nu)
    XI = 1 / (c * 6 * nu ** 3) * (nu / rho + 2 * t * t)
    XII = 1 / (c * 120 * nu ** 5) * (5 + 28 * t * t + 24 * t ** 4)
    XIIA = 1 / (c * 5040 * nu ** 7) * (61 + 662 * t * t + 1320 * t ** 4 + 720 * t ** 6)
    dE = E - E0
    la = lat - VII * dE ** 2 + VIII * dE ** 4 - IX * dE ** 6
    lo = lon0 + X * dE - XI * dE ** 3 + XII * dE ** 5 - XIIA * dE ** 7
    return math.degrees(la), math.degrees(lo)


def crome_centroid(feat):
    """Centre of a crop hexagon: from its cromeid (RPA + 6-digit easting + 6-digit northing)."""
    cid = (feat.get("properties") or {}).get("cromeid", "")
    if len(cid) == 15 and cid[3:].isdigit():
        return bng_to_latlon(int(cid[3:9]), int(cid[9:15]))
    g = feat.get("geometry") or {}
    ring = (g.get("coordinates") or [[]])[0]
    if ring and abs(ring[0][0]) < 180:
        return (sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring))
    return None


def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "quietwalks/1.0 (personal)",
                                               "Accept": "application/geo+json, application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_crome(offline, refresh):
    """Crop-map hexes for scarer-prone crops, as [lat, lon] centroids, cached per county+code."""
    dlat = (RADIUS_M + 1000) / KY
    dlon = (RADIUS_M + 1000) / KX
    bbox = f"{CENTRE_LON - dlon:.4f},{CENTRE_LAT - dlat:.4f},{CENTRE_LON + dlon:.4f},{CENTRE_LAT + dlat:.4f}"
    out = {"high": [], "mid": []}
    for county in CROME_COUNTIES:
        coll = f"Crop_Map_of_England_2024_{county}"
        for code in CROME_HIGH + CROME_MID:
            fn = os.path.join(CACHE, f"crome_{county}_{code}.json")
            pts = None
            if os.path.exists(fn) and not refresh:
                with open(fn) as f:
                    pts = json.load(f)
            elif offline:
                continue
            else:
                flt = urllib.parse.quote(f"lucode='{code}'")
                url = (f"{CROME_BASE}/collections/{coll}/items?f=json&limit=5000&bbox={bbox}"
                       f"&filter={flt}&filter-lang=cql2-text")
                pts, pages, failed = [], 0, False
                while url and pages < 200:
                    js = None
                    for attempt in range(4):
                        try:
                            js = http_json(url)
                            break
                        except urllib.error.HTTPError as e:
                            if e.code == 404:
                                log(f"  crop map: no collection {coll} - skipped")
                                url = None
                                break
                            log(f"  crop map error {e.code}; retry")
                            time.sleep(10 * (attempt + 1))
                        except Exception as e:  # noqa: BLE001
                            log(f"  crop map error {e}; retry")
                            time.sleep(10 * (attempt + 1))
                    if js is None:
                        failed = url is not None
                        break
                    for ft in js.get("features", []):
                        pr = (ft.get("properties") or {}).get("prob")
                        if pr is not None and pr < CROME_MIN_PROB:
                            continue
                        if (ft.get("properties") or {}).get("lucode") != code:
                            continue   # guard: server ignored the filter
                        c = crome_centroid(ft)
                        if c:
                            pts.append([round(c[0], 5), round(c[1], 5)])
                    pages += 1
                    url = next((l["href"] for l in js.get("links", []) if l.get("rel") == "next"), None)
                if failed:
                    log(f"  crop map {county} {code}: download failed - not cached, rerun later")
                    continue
                if js is None:
                    continue
                with open(fn, "w") as f:
                    json.dump(pts, f)
                log(f"crop map {county} {code}: {len(pts)} hexes ({pages} pages)")
                time.sleep(1)
            out["high" if code in CROME_HIGH else "mid"].extend(pts or [])
    return out


def fetch_all(offline, refresh):
    os.makedirs(CACHE, exist_ok=True)
    merged = {k: {} for k in QUERIES}
    tiles = bbox_tiles()
    for ti, (s, w, n, e) in enumerate(tiles):
        b = f"{s},{w},{n},{e}"
        for name, q in QUERIES.items():
            fn = os.path.join(CACHE, f"{name}_{ti}.json")
            if os.path.exists(fn) and not refresh:
                with open(fn) as f:
                    js = json.load(f)
            elif offline:
                log(f"  missing cache {fn} (offline) - skipped")
                continue
            else:
                log(f"fetch {name} tile {ti + 1}/{len(tiles)}")
                js = overpass(q.format(b=b))
                with open(fn, "w") as f:
                    json.dump(js, f)
                time.sleep(5)
            for el in js.get("elements", []):
                merged[name][(el["type"], el["id"])] = el
    return merged


# ---------------------------------------------------------------- rasters
NX = NY = int(math.ceil(2 * (RADIUS_M + 2000) / CELL_M))
OX = OY = -(RADIUS_M + 2000)
INF = 1e9


def cell_of(x, y):
    return int((x - OX) // CELL_M), int((y - OY) // CELL_M)


class Layer:
    def __init__(self, name):
        self.name = name
        self.src = bytearray(NX * NY)
        self.dist = None

    def mark_xy(self, x, y):
        cx, cy = cell_of(x, y)
        if 0 <= cx < NX and 0 <= cy < NY:
            self.src[cy * NX + cx] = 1

    def mark_line(self, pts):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            seg = math.hypot(x2 - x1, y2 - y1)
            n = max(1, int(seg // (CELL_M / 2)))
            for k in range(n + 1):
                t = k / n
                self.mark_xy(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

    def fill_polygon(self, pts):
        """Scanline fill (even-odd) of a closed ring, plus its outline."""
        if len(pts) < 3:
            return
        self.mark_line(pts)
        ys = [p[1] for p in pts]
        cy0, cy1 = cell_of(0, min(ys))[1], cell_of(0, max(ys))[1]
        cy0, cy1 = max(cy0, 0), min(cy1, NY - 1)
        edges = list(zip(pts, pts[1:] + pts[:1]))
        for cy in range(cy0, cy1 + 1):
            yc = OY + (cy + 0.5) * CELL_M
            xs = []
            for (x1, y1), (x2, y2) in edges:
                if (y1 <= yc < y2) or (y2 <= yc < y1):
                    xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for a, b in zip(xs[0::2], xs[1::2]):
                ca = max(0, int(math.ceil((a - OX) / CELL_M - 0.5)))
                cb = min(NX - 1, int(math.floor((b - OX) / CELL_M - 0.5)))
                row = cy * NX
                for cx in range(ca, cb + 1):
                    self.src[row + cx] = 1

    def transform(self):
        """Two-pass chamfer distance transform -> metres to nearest source."""
        d = array.array("f", [INF]) * (NX * NY)
        src = self.src
        for i in range(NX * NY):
            if src[i]:
                d[i] = 0.0
        a, b = 1.0, 1.41421356
        for y in range(NY):
            row = y * NX
            up = row - NX
            for x in range(NX):
                i = row + x
                v = d[i]
                if x > 0 and d[i - 1] + a < v:
                    v = d[i - 1] + a
                if y > 0:
                    if d[up + x] + a < v:
                        v = d[up + x] + a
                    if x > 0 and d[up + x - 1] + b < v:
                        v = d[up + x - 1] + b
                    if x < NX - 1 and d[up + x + 1] + b < v:
                        v = d[up + x + 1] + b
                d[i] = v
        for y in range(NY - 1, -1, -1):
            row = y * NX
            dn = row + NX
            for x in range(NX - 1, -1, -1):
                i = row + x
                v = d[i]
                if x < NX - 1 and d[i + 1] + a < v:
                    v = d[i + 1] + a
                if y < NY - 1:
                    if d[dn + x] + a < v:
                        v = d[dn + x] + a
                    if x < NX - 1 and d[dn + x + 1] + b < v:
                        v = d[dn + x + 1] + b
                    if x > 0 and d[dn + x - 1] + b < v:
                        v = d[dn + x - 1] + b
                d[i] = v
        self.dist = d
        self.src = None

    def at(self, x, y):
        cx, cy = cell_of(x, y)
        if 0 <= cx < NX and 0 <= cy < NY:
            return self.dist[cy * NX + cx] * CELL_M
        return INF


# ---------------------------------------------------------------- features
def element_points(el):
    """Return (kind, data): ('pt', (x,y)) or ('ring', [...]) or ('line', [...])."""
    if el["type"] == "node":
        return "pt", to_xy(el["lat"], el["lon"])
    if el["type"] == "way" and "geometry" in el:
        pts = [to_xy(g["lat"], g["lon"]) for g in el["geometry"] if g]
        if len(pts) >= 4 and el.get("nodes", [0])[0] == el.get("nodes", [1])[-1]:
            return "ring", pts[:-1]
        if len(pts) >= 4 and pts[0] == pts[-1]:
            return "ring", pts[:-1]
        return "line", pts
    if el["type"] == "relation":
        parts = []
        for m in el.get("members", []):
            if m.get("type") == "way" and m.get("role") in ("outer", "") and m.get("geometry"):
                parts.append([to_xy(g["lat"], g["lon"]) for g in m["geometry"] if g])
        rings = join_rings(parts)
        if rings:
            return "rings", rings
        c = el.get("center") or el.get("bounds")
        if c and "lat" in c:
            return "pt", to_xy(c["lat"], c["lon"])
    return None, None


def join_rings(parts):
    """Stitch multipolygon member ways end-to-end into closed rings."""
    parts = [p for p in parts if len(p) >= 2]
    rings = []
    while parts:
        cur = parts.pop(0)
        changed = True
        while cur[0] != cur[-1] and changed:
            changed = False
            for i, p in enumerate(parts):
                if p[0] == cur[-1]:
                    cur = cur + p[1:]
                elif p[-1] == cur[-1]:
                    cur = cur + p[::-1][1:]
                elif p[-1] == cur[0]:
                    cur = p[:-1] + cur
                elif p[0] == cur[0]:
                    cur = p[::-1][:-1] + cur
                else:
                    continue
                parts.pop(i)
                changed = True
                break
        if len(cur) >= 4 and cur[0] == cur[-1]:
            rings.append(cur)
    return rings


def centroid(kind, data):
    if kind == "pt":
        return data
    pts = data if kind in ("ring", "line") else [p for r in data for p in r]
    if not pts:
        return None
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def add_area(layer, kind, data):
    if kind == "ring":
        layer.fill_polygon(data)
    elif kind == "rings":
        for r in data:
            if len(r) >= 3:
                layer.fill_polygon(r[:-1] if r[0] == r[-1] else r)
    elif kind == "line":
        layer.mark_line(data)
    elif kind == "pt":
        layer.mark_xy(*data)


def add_point(layer, kind, data):
    c = centroid(kind, data)
    if c:
        layer.mark_xy(*c)


def low(t, *keys):
    return " ".join(t.get(k, "") for k in keys).lower()


def is_bike_trail(t, wid, cycle_ids):
    """Paths that bring cyclists: routes, cycleways, MTB trails (not plain bridleways)."""
    if wid in cycle_ids or t.get("highway") == "cycleway":
        return True
    if t.get("bicycle") == "designated" or t.get("mtb") in ("yes", "designated") or "mtb:scale" in t:
        return True
    return any(w in low(t, "name", "description") for w in BIKE_WORDS)


def path_ok(t):
    return not (t.get("footway") in ("sidewalk", "crossing")
                or t.get("access") in ("private", "no")
                or t.get("foot") in ("no", "private")
                or t.get("dog") in ("no",))


def density_grid(paths):
    """km of path within a ~1 km square around each cell (summed-area table)."""
    per = array.array("f", [0.0]) * (NX * NY)
    for el in paths.values():
        t = el.get("tags", {})
        if el["type"] != "way" or t.get("footway") in ("sidewalk", "crossing"):
            continue
        g = [to_xy(p["lat"], p["lon"]) for p in el.get("geometry", []) if p]
        for (x1, y1), (x2, y2) in zip(g, g[1:]):
            cx, cy = cell_of((x1 + x2) / 2, (y1 + y2) / 2)
            if 0 <= cx < NX and 0 <= cy < NY:
                per[cy * NX + cx] += math.hypot(x2 - x1, y2 - y1)
    W = NX + 1
    sat = array.array("d", [0.0]) * (W * (NY + 1))
    for y in range(NY):
        run = 0.0
        row, prev = (y + 1) * W, y * W
        for x in range(NX):
            run += per[y * NX + x]
            sat[row + x + 1] = sat[prev + x + 1] + run
    r = 10  # 10 cells each way = 1.05 km square
    out = array.array("f", [0.0]) * (NX * NY)
    for y in range(NY):
        y0, y1 = max(0, y - r), min(NY, y + r + 1)
        for x in range(NX):
            x0, x1 = max(0, x - r), min(NX, x + r + 1)
            out[y * NX + x] = (sat[y1 * W + x1] - sat[y0 * W + x1] - sat[y1 * W + x0]
                               + sat[y0 * W + x0]) / 1000.0
    return out


def shooting_kind(t):
    """'range' for gun clubs and firing ranges, 'game' for woods used for (seasonal)
    game shoots, None for everything quiet, indoor or disused."""
    nm = low(t, "name", "description")
    if any(w in nm for w in QUIET_SHOOTING_WORDS + DISUSED_WORDS) or t.get("military") == "abandoned":
        return None
    if t.get("leisure") == "sports_centre":
        return None                                  # indoor range
    shooting = "shoot" in t.get("sport", "") or "clay" in t.get("sport", "")
    if shooting and (any(w in nm for w in ("shooting ground", "clay", "club", "pigeon")) or RANGE_WORD.search(nm)):
        return "range"                               # a named gun club or ground, even in a wood
    if shooting and (t.get("landuse") in ("forest", "wood") or t.get("natural") == "wood"
                     or (" wood" in " " + nm or "plantation" in nm or "forest" in nm)
                     and t.get("leisure") not in ("shooting_ground", "pitch")):
        return "game"
    if t.get("military") in ("range", "danger_area"):
        return "range"
    if t.get("landuse") == "military":
        return "range" if RANGE_WORD.search(nm) else None
    if shooting or t.get("leisure") in ("shooting_ground", "shooting_range"):
        return "range"
    return None


def build_layers(feats, honey, paths, cycle_ids, bangs=None, crome=None):
    L = {n: Layer(n) for n in (
        "park_small", "park_large", "attractor", "dog", "residential",
        "meadow", "farm", "road", "honeypot", "bike", "shoot", "game", "scarer_hi", "scarer_mid")}
    found = {"range": set(), "game": set()}
    seen = set()
    for el in list((bangs or {}).values()) + list(feats.values()):
        if (el["type"], el["id"]) in seen:
            continue
        seen.add((el["type"], el["id"]))
        t = el.get("tags", {})
        sk = shooting_kind(t)
        if not sk:
            continue
        kind, data = element_points(el)
        if not kind:
            continue
        lay = L["shoot" if sk == "range" else "game"]
        if kind in ("ring", "rings") and _area(data, kind) < 4e6:
            add_area(lay, kind, data)
        else:
            add_point(lay, kind, data)
        found[sk].add(t.get("name", f"unnamed {el['type']}/{el['id']}"))
    log(f"shooting ranges/grounds: {len(found['range'])} ({', '.join(sorted(found['range']))})")
    log(f"game-shoot woods: {len(found['game'])} ({', '.join(sorted(found['game']))})")
    for key, lay in (("high", "scarer_hi"), ("mid", "scarer_mid")):
        for la, lo in (crome or {}).get(key, []):
            L[lay].mark_xy(*to_xy(la, lo))
    log(f"crop-map scarer hexes: high {len((crome or {}).get('high', []))}, "
        f"mid {len((crome or {}).get('mid', []))}")
    parking, places, reserves = [], [], []
    # honeypots: estates, country/forest parks, attractions, visitor centres
    for el in list(honey.values()) + list(feats.values()):
        t = el.get("tags", {})
        kind, data = element_points(el)
        if not kind:
            continue
        nm = low(t, "name", "operator")
        if t.get("place"):
            c = centroid(kind, data)
            if c and t.get("name"):
                places.append((c[0], c[1], t["name"], t["place"]))
            continue
        if t.get("leisure") == "nature_reserve" or any(w in nm for w in CHECK_DOGS_WORDS):
            c = centroid(kind, data)
            if c:
                reserves.append((c[0], c[1], t.get("name", "nature reserve")))
            continue
        hp = (t.get("historic") in ("castle", "manor", "stately_home")
              or t.get("tourism") in ("attraction", "visitor_centre", "theme_park", "zoo")
              or (t.get("leisure") == "park" and any(w in nm for w in HONEYPOT_WORDS))
              or (t.get("amenity") != "parking" and any(w in nm for w in HONEYPOT_WORDS[2:])))
        if hp:
            if kind in ("ring", "rings") and _area(data, kind) < 4e6:
                add_area(L["honeypot"], kind, data)
            else:
                add_point(L["honeypot"], kind, data)
    for el in paths.values():
        t = el.get("tags", {})
        if el["type"] == "way" and is_bike_trail(t, el["id"], cycle_ids):
            L["bike"].mark_line([to_xy(p["lat"], p["lon"]) for p in el.get("geometry", []) if p])
    log("distance transform: honeypot")
    L["honeypot"].transform()
    for el in feats.values():
        t = el.get("tags", {})
        kind, data = element_points(el)
        if not kind:
            continue
        am, le, lu, to = t.get("amenity"), t.get("leisure"), t.get("landuse"), t.get("tourism")
        if am == "parking":
            if t.get("access") in ("private", "customers", "no", "permit") or \
                    t.get("parking") in ("street_side", "lane", "multi-storey", "underground", "layby") or \
                    any(w in low(t, "name") for w in ("rest area", "lay-by", "layby", "services", "hgv", "lorry",
                                                       "truck", "park and ride", "park & ride")) or \
                    t.get("hgv") == "designated":
                continue
            cap = t.get("capacity", "")
            cap = int(cap) if cap.isdigit() else 0
            c = centroid(kind, data)
            if not c:
                continue
            area = _area(data, kind) if kind in ("ring", "rings") else 0
            near_hp = L["honeypot"].at(*c) < 400
            big = (cap >= 50 or area > 1500 or t.get("fee") == "yes" or near_hp
                   or any(w in low(t, "name", "operator") for w in HONEYPOT_WORDS))
            add_point(L["park_large" if big else "park_small"], kind, data)
            parking.append({"x": c[0], "y": c[1], "cap": cap, "big": big,
                            "name": t.get("name", ""), "id": f"{el['type']}/{el['id']}",
                            "op": low(t, "name", "operator")})
        elif am in ("dog_toilet", "animal_boarding", "animal_shelter") or le == "dog_park":
            add_point(L["dog"], kind, data)
        elif le in ("park", "playground", "picnic_site", "pitch", "recreation_ground") or \
                to in ("attraction", "picnic_site", "viewpoint", "visitor_centre",
                       "camp_site", "caravan_site") or am in ("cafe", "pub", "school"):
            add_point(L["attractor"], kind, data)
            if le in ("park", "recreation_ground") and kind in ("ring", "rings"):
                add_area(L["attractor"], kind, data)
        elif lu == "residential":
            add_area(L["residential"], kind, data)
        elif lu == "meadow":
            add_area(L["meadow"], kind, data)
        elif lu == "farmyard" or le == "horse_riding" or t.get("building") == "stable" or \
                t.get("barrier") in ("stile", "cattle_grid"):
            add_point(L["farm"], kind, data)
        elif "highway" in t:
            add_area(L["road"], "line" if kind == "ring" else kind,
                     data + data[:1] if kind == "ring" else data)
    for n, layer in L.items():
        if layer.dist is None:
            log(f"distance transform: {n}")
            layer.transform()
    log("path density grid")
    dens = density_grid(paths)
    return L, parking, dens, places, reserves


def _area(data, kind):
    ring = data if kind == "ring" else max(data, key=len)
    s = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


# ---------------------------------------------------------------- scoring
def decay(d, r):
    return 0.0 if d >= r else 1.0 - d / r


def sample_line(pts, step=25.0):
    out = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        seg = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(seg // step))
        for k in range(n):
            t = k / n
            out.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
    if pts:
        out.append(pts[-1])
    return out


def line_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def is_bikey(t, wid, cycle_ids):
    hw = t.get("highway")
    if wid in cycle_ids:
        return 1.0
    if hw in ("cycleway", "bridleway", "byway"):
        return 1.0
    if t.get("bicycle") == "designated" or t.get("designation") in (
            "public_bridleway", "byway_open_to_all_traffic", "restricted_byway"):
        return 1.0
    if t.get("mtb") == "yes" or "mtb:scale" in t:
        return 1.0
    if t.get("bicycle") == "yes" and hw in ("track", "path"):
        return 0.5
    return 0.0


def dens_at(dens, x, y):
    cx, cy = cell_of(x, y)
    if 0 <= cx < NX and 0 <= cy < NY:
        return dens[cy * NX + cx]
    return 0.0


def score_paths(paths, L, dens, cycle_ids, walk_ids, ratings):
    wsum = sum(WEIGHTS.values())
    out = []
    r2 = RADIUS_M * RADIUS_M
    for el in paths.values():
        if el["type"] != "way" or "geometry" not in el:
            continue
        t = el.get("tags", {})
        if not path_ok(t):
            continue
        geo = [(g["lat"], g["lon"]) for g in el["geometry"] if g]
        if len(geo) < 2:
            continue
        pts = [to_xy(a, b) for a, b in geo]
        if not any(x * x + y * y <= r2 for x, y in pts):
            continue
        length = line_len(pts)
        if length < 20:
            continue
        sm = sample_line(pts)
        n = len(sm)
        pd = lv = tr = bkn = busy = bg = 0.0
        for x, y in sm:
            dr = min(1.0, max(0.0, (dens_at(dens, x, y) - DENS_LO) / (DENS_HI - DENS_LO)))
            hp = decay(L["honeypot"].at(x, y), 1200)
            busy += max(dr, hp)
            p = max(
                0.6 * decay(L["park_small"].at(x, y), 500),
                1.0 * decay(L["park_large"].at(x, y), 900),
                0.8 * decay(L["attractor"].at(x, y), 500),
                1.0 * decay(L["dog"].at(x, y), 400),
                1.0 * decay(L["residential"].at(x, y), 700),
                0.9 * dr,
                1.0 * hp,
            )
            bkn += 0.7 * decay(L["bike"].at(x, y), 120)
            bg += max(1.0 * decay(max(0.0, L["shoot"].at(x, y) - SHOOT_FULL_M), SHOOT_FADE_M),
                      GAME_MAX * decay(L["game"].at(x, y), GAME_FADE_M),
                      SCARER_MAX * decay(L["scarer_hi"].at(x, y), SCARER_RADIUS_M),
                      0.6 * SCARER_MAX * decay(L["scarer_mid"].at(x, y), SCARER_RADIUS_M))
            pd += p
            inside = 1.0 if L["meadow"].at(x, y) <= 1 else 0.6 * decay(L["meadow"].at(x, y), 60)
            lv += max(inside, 0.7 * decay(L["farm"].at(x, y), 150))
            tr += decay(L["road"].at(x, y), 250)
        pd = min(1.0, pd / n + (0.15 if el["id"] in walk_ids else 0.0))
        lv /= n
        tr /= n
        bk = max(is_bikey(t, el["id"], cycle_ids), bkn / n)
        busy /= n
        bg /= n
        f = {"people_dogs": pd, "livestock": lv, "bikes": bk, "bangs": bg, "traffic": tr}
        mean = sum(WEIGHTS[k] * f[k] for k in f) / wsum
        worst = max(SEVERITY[k] * f[k] for k in f)
        risk = 0.5 * worst + 0.5 * mean
        score = round(100 * (1 - risk))
        note = ""
        rated = 0
        if el["id"] in ratings:
            stars, note = ratings[el["id"]]
            score = int(stars) * 20
            rated = 1
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        out.append({
            "id": el["id"], "score": score, "len": length, "pts": pts, "geo": geo,
            "bb": (min(xs), min(ys), max(xs), max(ys)),
            "pd": round(pd * 100), "lv": round(lv * 100), "bk": round(bk * 100),
            "tr": round(tr * 100), "busy": round(busy * 100), "bg": round(bg * 100),
            "rated": rated, "note": note,
            "name": t.get("name") or t.get("prow_ref") or t.get("designation", "").replace("_", " ")
                    or t.get("highway", ""),
            "hw": t.get("highway", ""),
        })
    return out


def rank_starts(parking, scored, places=(), reserves=()):
    # bucket path samples by 500 m grid for catchment lookups
    bucket = {}
    for i, p in enumerate(scored):
        for x, y in p["pts"][::1]:
            key = (int(x // 500), int(y // 500))
            bucket.setdefault(key, set()).add(i)
    r2 = START_RADIUS_M ** 2
    res = []
    for pk in parking:
        x0, y0 = pk["x"], pk["y"]
        if x0 * x0 + y0 * y0 > RADIUS_M ** 2:
            continue
        cand = set()
        kx, ky = int(x0 // 500), int(y0 // 500)
        rr = START_RADIUS_M // 500 + 1
        for dx in range(-rr, rr + 1):
            for dy in range(-rr, rr + 1):
                cand |= bucket.get((kx + dx, ky + dy), set())
        tot = green = wsum = 0.0
        R = START_RADIUS_M
        for i in cand:
            p = scored[i]
            bx0, by0, bx1, by1 = p["bb"]
            if bx0 > x0 + R or bx1 < x0 - R or by0 > y0 + R or by1 < y0 - R:
                continue
            if any((x - x0) ** 2 + (y - y0) ** 2 <= r2 for x, y in p["pts"]):
                tot += p["len"]
                wsum += p["len"] * p["score"]
                if p["score"] >= GREEN:
                    green += p["len"]
        if tot == 0 or green / 1000 < START_MIN_GREEN_KM:
            continue
        lat = CENTRE_LAT + y0 / KY
        lon = CENTRE_LON + x0 / KX
        dist_km = math.hypot(x0, y0) / 1000
        near = min(places, key=lambda q: (q[0] - x0) ** 2 + (q[1] - y0) ** 2, default=None)
        if near and (near[0] - x0) ** 2 + (near[1] - y0) ** 2 > 3000 ** 2:
            near = None
        label = pk["name"] or (f"Parking near {near[2]}" if near else "Parking")
        flag = ""
        if any((q[0] - x0) ** 2 + (q[1] - y0) ** 2 < 1000 ** 2 for q in reserves) or \
                any(w in pk.get("op", "") for w in CHECK_DOGS_WORDS):
            flag = "Nature reserve nearby: check dog rules"
        if pk["big"]:
            flag = (flag + "; " if flag else "") + "Large/busy car park"
        res.append({**pk, "name": label, "flag": flag, "lat": lat, "lon": lon,
                    "total_km": tot / 1000, "green_km": green / 1000, "mean": wsum / tot,
                    "dist_km": dist_km,
                    "rank": wsum / tot - DIST_PENALTY * dist_km - (BIG_PARK_PENALTY if pk["big"] else 0)})
    res.sort(key=lambda r: r["rank"], reverse=True)
    kept = []
    for r in res:  # one start per walk area: drop starts near a better one
        if all((r["x"] - k["x"]) ** 2 + (r["y"] - k["y"]) ** 2 > DEDUPE_M ** 2 for k in kept):
            kept.append(r)
    return kept[:40]


# ---------------------------------------------------------------- output
def simplify(geo, tol=0.00004):
    if len(geo) <= 2:
        return geo
    (a0, b0), (a1, b1) = geo[0], geo[-1]
    dmax, idx = 0.0, 0
    for i in range(1, len(geo) - 1):
        a, b = geo[i]
        num = abs((a1 - a0) * (b0 - b) - (a0 - a) * (b1 - b0))
        den = math.hypot(a1 - a0, b1 - b0) or 1e-12
        d = num / den
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return simplify(geo[:idx + 1], tol)[:-1] + simplify(geo[idx:], tol)
    return [geo[0], geo[-1]]


HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quiet walks for Gatsby (v4)</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
 html,body,#map{height:100%;margin:0;font-family:system-ui,sans-serif}
 .panel{position:absolute;z-index:1000;top:10px;right:10px;background:#fff;padding:10px 12px;
  border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.25);font-size:13px;max-width:260px}
 .panel h3{margin:0 0 6px;font-size:15px}
 .sw{display:inline-block;width:14px;height:4px;margin-right:6px;vertical-align:middle}
 .starts{max-height:40vh;overflow:auto;margin-top:8px;border-top:1px solid #ddd;padding-top:6px}
 .starts div{cursor:pointer;padding:2px 0}.starts div:hover{text-decoration:underline}
 .num{background:#1d4ed8;color:#fff;border-radius:50%;width:22px;height:22px;line-height:22px;
  text-align:center;font-size:11px;font-weight:600;border:2px solid #fff;box-shadow:0 1px 3px #0006}
</style></head><body><div id="map"></div>
<div class="panel"><h3>Quiet walks for Gatsby</h3>
<div><span class="sw" style="background:#16a34a"></span>Quiet (score &ge; __G__)</div>
<div><span class="sw" style="background:#f59e0b"></span>Mixed (__A__&ndash;__G1__)</div>
<div><span class="sw" style="background:#dc2626"></span>Busy / triggers (&lt; __A__)</div>
<div style="margin-top:6px">Show paths scoring at least <b id="mv">0</b><br>
<input id="min" type="range" min="0" max="100" step="5" value="0" style="width:100%"></div>
<label><input id="hideBikes" type="checkbox"> Hide bike routes &amp; bridleways</label>
<div class="starts" id="starts"><b>Best start points</b></div>
<div style="margin-top:6px;color:#666;font-size:11px">Built __BUILT__. Model estimate from map data:
check livestock and loose dogs on the ground. Click a path for details.</div></div>
<script>
const P=__PATHS__;const S=__STARTS__;
const map=L.map('map',{preferCanvas:true}).setView([__LAT__,__LON__],12);
const esri=(svc,max)=>L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/'+svc+'/MapServer/tile/{z}/{y}/{x}',
 {maxZoom:max,attribution:'Tiles &copy; Esri &mdash; Esri, HERE, Garmin, OpenStreetMap contributors, and the GIS user community'});
const street=esri('World_Street_Map',19).addTo(map);
const topo=esri('World_Topo_Map',19);
const sat=esri('World_Imagery',19);
L.control.layers({'Street':street,'Topo':topo,'Satellite':sat},null,{position:'bottomleft'}).addTo(map);
L.circle([__LAT__,__LON__],{radius:__R__,color:'#555',weight:1,fill:false,dashArray:'4 6'}).addTo(map);
function col(s){return s>=__G__?'#16a34a':(s>=__A__?'#f59e0b':'#dc2626')}
let layer=L.layerGroup().addTo(map);
function draw(){layer.clearLayers();const m=+document.getElementById('min').value;
 const hb=document.getElementById('hideBikes').checked;document.getElementById('mv').textContent=m;
 for(const p of P){const [id,s,pd,lv,bk,tr,rated,name,note,len,g,busy,bg]=p;if(s<m)continue;if(hb&&bk>=50)continue;
  const pl=L.polyline(g,{color:col(s),weight:rated?6:3,opacity:.85});
  pl.bindPopup(`<b>${name||'Path'}</b><br>Quiet score <b>${s}</b>${rated?' (your rating)':''}`+
   `<br>Dogs/people risk ${pd} (busy-site ${busy}) &middot; Livestock ${lv} &middot; Bikes ${bk} &middot; Bangs ${bg} &middot; Traffic ${tr}`+
   `<br>Length ${len} m${note?'<br><i>'+note+'</i>':''}`+
   `<br>way_id <code>${id}</code> &middot; <a target=_blank href="https://www.openstreetmap.org/way/${id}">OSM</a>`);
  layer.addLayer(pl);}}
document.getElementById('min').oninput=draw;document.getElementById('hideBikes').onchange=draw;draw();
const sl=document.getElementById('starts');
S.forEach((s,i)=>{const [lat,lon,name,gkm,tkm,mean,dkm,flag]=s;
 const icon=L.divIcon({className:'',html:`<div class="num">${i+1}</div>`,iconSize:[22,22]});
 const mk=L.marker([lat,lon],{icon}).addTo(map).bindPopup(`<b>#${i+1} ${name||'Parking'}</b>`+
  `<br>${gkm.toFixed(1)} km of quiet path within 1.5 km (of ${tkm.toFixed(1)} km)`+
  `<br>Average score ${mean.toFixed(0)} &middot; ${dkm.toFixed(1)} km from Bingham`+
  (flag?`<br><b style="color:#b45309">${flag}</b>`:'')+
  `<br><a target=_blank href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}">Directions</a>`);
 const d=document.createElement('div');d.textContent=`${i+1}. ${name||'Parking'} - ${gkm.toFixed(1)} km quiet`;
 d.onclick=()=>{map.setView([lat,lon],15);mk.openPopup()};sl.appendChild(d);});
</script></body></html>"""


# ---------------------------------------------------------------- website export
EXPORT_CHUNK_M = 10000       # data split into 10 km squares (by distance from the centre)
EXPORT_MIN_KM = 3.0          # a start point needs this much path within START_RADIUS_M
EXPORT_DEDUPE_M = 300


def export_finder(out_dir, scored, parking, places, reserves):
    """Write the public finder data: trigger values per path (no scores, no personal
    ratings) and every usable start point with the ids of the paths around it.
    The page combines the values with each visitor's own trigger sliders."""
    import shutil
    tmp = out_dir.rstrip("/") + ".tmp"
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(os.path.join(tmp, "chunks"))
    chunks = {}
    for p in scored:
        xs = [q[0] for q in p["pts"]]
        ys = [q[1] for q in p["pts"]]
        cx = int(((sum(xs) / len(xs)) + RADIUS_M + 2000) // EXPORT_CHUNK_M)
        cy = int(((sum(ys) / len(ys)) + RADIUS_M + 2000) // EXPORT_CHUNK_M)
        g = [[round(b, 5), round(a, 5)] for a, b in simplify(p["geo"])]   # [lon, lat]
        chunks.setdefault(f"{cx}_{cy}", []).append(
            [p["id"], p["pd"], p["lv"], p["bk"], p["bg"], p["tr"], round(p["len"]), p["name"][:60], g])
    bbox, gidx, base = {}, {}, 0
    for key in sorted(chunks):
        rows = chunks[key]
        lons = [c[0] for r in rows for c in r[8]]
        lats = [c[1] for r in rows for c in r[8]]
        bbox[key] = {"bbox": [min(lons), min(lats), max(lons), max(lats)], "base": base,
                     "count": len(rows)}
        for i, r in enumerate(rows):
            gidx[r[0]] = base + i          # global path number = chunk base + row position
        base += len(rows)
        with open(os.path.join(tmp, "chunks", key + ".json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, separators=(",", ":"), ensure_ascii=False)
    # start points: every public parking spot with enough path around it
    bucket = {}
    for i, p in enumerate(scored):
        for x, y in p["pts"]:
            bucket.setdefault((int(x // 500), int(y // 500)), set()).add(i)
    R = START_RADIUS_M
    starts, kept = [], []
    for pk in sorted(parking, key=lambda q: q["big"]):
        x0, y0 = pk["x"], pk["y"]
        if x0 * x0 + y0 * y0 > RADIUS_M ** 2:
            continue
        if any((x0 - k[0]) ** 2 + (y0 - k[1]) ** 2 < EXPORT_DEDUPE_M ** 2 for k in kept):
            continue
        kx, ky, rr = int(x0 // 500), int(y0 // 500), R // 500 + 1
        cand = set()
        for dx in range(-rr, rr + 1):
            for dy in range(-rr, rr + 1):
                cand |= bucket.get((kx + dx, ky + dy), set())
        ids, tot = [], 0.0
        for i in cand:
            p = scored[i]
            bx0, by0, bx1, by1 = p["bb"]
            if bx0 > x0 + R or bx1 < x0 - R or by0 > y0 + R or by1 < y0 - R:
                continue
            if any((x - x0) ** 2 + (y - y0) ** 2 <= R * R for x, y in p["pts"]):
                ids.append(p["id"])
                tot += p["len"]
        if tot / 1000 < EXPORT_MIN_KM:
            continue
        kept.append((x0, y0))
        near = min(places, key=lambda q: (q[0] - x0) ** 2 + (q[1] - y0) ** 2, default=None)
        if near and (near[0] - x0) ** 2 + (near[1] - y0) ** 2 > 3000 ** 2:
            near = None
        name = pk["name"] or (f"Parking near {near[2]}" if near else "Parking")
        flags = []
        if pk["big"]:
            flags.append("big")
        if any((q[0] - x0) ** 2 + (q[1] - y0) ** 2 < 1000 ** 2 for q in reserves) or \
                any(w in pk.get("op", "") for w in CHECK_DOGS_WORDS):
            flags.append("reserve")
        nums = sorted(gidx[i] for i in ids)
        deltas = [b - a for a, b in zip([0] + nums, nums)]   # first is absolute, rest are gaps
        starts.append([round(CENTRE_LAT + y0 / KY, 5), round(CENTRE_LON + x0 / KX, 5),
                       name[:60], flags, deltas])
    with open(os.path.join(tmp, "starts.json"), "w", encoding="utf-8") as f:
        json.dump(starts, f, separators=(",", ":"), ensure_ascii=False)
    index = {
        "format": 1,
        "built": time.strftime("%Y-%m-%d"),
        "centre": [CENTRE_LAT, CENTRE_LON],
        "radius_m": RADIUS_M,
        "start_radius_m": START_RADIUS_M,
        "fields": ["id", "people_dogs", "livestock", "bikes", "bangs", "traffic", "len_m", "name",
                   "geometry_lonlat"],
        "start_fields": ["lat", "lon", "name", "flags", "path_numbers_delta"],
        "chunks": bbox,
        "paths": len(scored),
        "starts": len(starts),
        "attribution": "Map data \u00a9 OpenStreetMap contributors (ODbL). Crop data: Rural Payments "
                       "Agency CROME 2024, Open Government Licence.",
    }
    with open(os.path.join(tmp, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1)
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.replace(tmp, out_dir)
    size = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fns in os.walk(out_dir) for fn in fns)
    log(f"exported finder data to {out_dir}: {len(bbox)} chunks, {len(starts)} start points, "
        f"{size / 1e6:.1f} MB")


def write_outputs(scored, starts):
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for p in scored:
        g = [[round(a, 5), round(b, 5)] for a, b in simplify(p["geo"])]
        rows.append([p["id"], p["score"], p["pd"], p["lv"], p["bk"], p["tr"], p["rated"],
                     p["name"][:60], p["note"][:120], round(p["len"]), g, p["busy"], p["bg"]])
    st = [[round(s["lat"], 5), round(s["lon"], 5), s["name"][:60], round(s["green_km"], 2),
           round(s["total_km"], 2), round(s["mean"], 1), round(s["dist_km"], 1), s["flag"]]
          for s in starts]
    html = (HTML.replace("__PATHS__", json.dumps(rows, separators=(",", ":")))
            .replace("__STARTS__", json.dumps(st, separators=(",", ":")))
            .replace("__LAT__", str(CENTRE_LAT)).replace("__LON__", str(CENTRE_LON))
            .replace("__R__", str(RADIUS_M)).replace("__G1__", str(GREEN - 1))
            .replace("__G__", str(GREEN)).replace("__A__", str(AMBER))
            .replace("__BUILT__", time.strftime("%d %b %Y")))
    fn = os.path.join(OUT, "quietwalks_map.html")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(OUT, "top_starts.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "name", "quiet_km_within_1.5km", "total_km", "mean_score",
                    "km_from_centre", "flags", "lat", "lon", "directions"])
        for i, s in enumerate(starts, 1):
            w.writerow([i, s["name"], f"{s['green_km']:.2f}", f"{s['total_km']:.2f}",
                        f"{s['mean']:.0f}", f"{s['dist_km']:.1f}", s["flag"], f"{s['lat']:.5f}",
                        f"{s['lon']:.5f}",
                        f"https://www.google.com/maps/dir/?api=1&destination={s['lat']:.5f},{s['lon']:.5f}"])
    return fn, os.path.getsize(fn)


def load_ratings():
    r = {}
    if os.path.exists(RATINGS):
        with open(RATINGS, newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[0].strip().isdigit() and row[1].strip().isdigit():
                    stars = max(1, min(5, int(row[1])))
                    r[int(row[0])] = (stars, row[2].strip() if len(row) > 2 else "")
    return r


def main():
    offline = "--offline" in sys.argv
    refresh = "--refresh" in sys.argv
    t0 = time.time()
    log(f"quietwalks: centre {CENTRE_LAT},{CENTRE_LON} radius {RADIUS_M / 1000:.0f} km, "
        f"grid {NX}x{NY} @ {CELL_M} m")
    data = fetch_all(offline, refresh)
    cycle_ids = {k[1] for k in data["cycleroutes"] if k[0] == "way"}
    walk_ids = {k[1] for k in data["walkroutes"] if k[0] == "way"}
    log(f"paths {len(data['paths'])}, features {len(data['features'])}, "
        f"cycle-route ways {len(cycle_ids)}, walk-route ways {len(walk_ids)}")
    crome = fetch_crome(offline, refresh)
    L, parking, dens, places, reserves = build_layers(
        data["features"], data["honeypots"], data["paths"], cycle_ids, data["bangs"], crome)
    log(f"places {len(places)}, nature reserves {len(reserves)}")
    ratings = load_ratings()
    log(f"scoring paths (your ratings: {len(ratings)})")
    scored = score_paths(data["paths"], L, dens, cycle_ids, walk_ids, ratings)
    km = sum(p["len"] for p in scored) / 1000
    gk = sum(p["len"] for p in scored if p["score"] >= GREEN) / 1000
    log(f"scored {len(scored)} paths, {km:.0f} km total, {gk:.0f} km quiet (>= {GREEN})")
    starts = rank_starts(parking, scored, places, reserves)
    if "--export" in sys.argv:
        export_finder(sys.argv[sys.argv.index("--export") + 1], scored, parking, places, reserves)
    fn, size = write_outputs(scored, starts)
    log(f"wrote {fn} ({size / 1e6:.1f} MB) and top_starts.csv ({len(starts)} start points)")
    for i, s in enumerate(starts[:10], 1):
        log(f"  #{i} {s['name']} {s['lat']:.4f},{s['lon']:.4f} quiet {s['green_km']:.1f} km, "
            f"mean {s['mean']:.0f}, {s['dist_km']:.0f} km away {('[' + s['flag'] + ']') if s['flag'] else ''}")
    log(f"DONE in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
