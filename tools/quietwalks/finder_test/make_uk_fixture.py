#!/usr/bin/env python3
"""Synthetic UK-shaped finder data (9-field rows) for the identity test. Deterministic."""
import json
import math
import random
import sys

rnd = random.Random(373)
C = [52.958, -0.951]                      # Bingham
KX, KY = 111320 * math.cos(math.radians(C[0])), 110540
chunks, rows_all, files = {}, [], {}
n = 0
for cx in range(5, 8):
    for cy in range(5, 8):
        key = f"{cx}_{cy}"
        rows = []
        for _ in range(60):
            x = (cx - 6) * 10000 + rnd.uniform(-5000, 5000)
            y = (cy - 6) * 10000 + rnd.uniform(-5000, 5000)
            geo = [[round(C[1] + (x + k * 60) / KX, 5), round(C[0] + (y + k * 25) / KY, 5)] for k in range(6)]
            vals = [rnd.choice([0, 5, 20, 40, 60, 80, 100]) for _ in range(5)]
            name = rnd.choice(["footway", "track", "Public Footpath", "Trent Valley Way", "", "path"])
            rows.append([1000 + n, *vals, rnd.randint(150, 1600), name, geo])
            n += 1
        chunks[key] = rows
index = {"format": 1, "built": "2026-11-13", "centre": C, "radius_m": 30000, "start_radius_m": 1500,
         "fields": ["id", "people_dogs", "livestock", "bikes", "bangs", "traffic", "len_m", "name", "geometry_lonlat"],
         "chunks": {}, "paths": n, "starts": 0, "attribution": "test"}
base = 0
for k in sorted(chunks):
    rs = chunks[k]
    lons = [c[0] for r in rs for c in r[8]]
    lats = [c[1] for r in rs for c in r[8]]
    index["chunks"][k] = {"bbox": [min(lons), min(lats), max(lons), max(lats)], "base": base, "count": len(rs)}
    files[f"/walks/finder-data/v1/chunks/{k}.json"] = rs
    base += len(rs)
starts = []
allrows = [r for k in sorted(chunks) for r in chunks[k]]
for i in range(40):
    lat = C[0] + rnd.uniform(-0.12, 0.12)
    lon = C[1] + rnd.uniform(-0.18, 0.18)
    nums = sorted(rnd.sample(range(len(allrows)), 25))
    deltas = [b - a for a, b in zip([0] + nums, nums)]
    flags = rnd.choice([[], ["big"], ["reserve"], ["big", "reserve"]])
    starts.append([round(lat, 5), round(lon, 5), rnd.choice(["Bingham Car Park", "", "Parking near Car Colston", "Wiverton Lane"]), flags, deltas])
index["starts"] = len(starts)
files["/walks/finder-data/v1/index.json"] = index
files["/walks/finder-data/v1/starts.json"] = starts
files["/walks/finder-data/postcodes/NG13.json"] = {"NG138AB": [52.951, -0.948], "NG138ZZ": [52.97, -0.9]}
files["/walks/finder-data/postcodes/DE1.json"] = {"DE11AA": [52.92, -1.48]}
files["/walks/finder/basemap-style.json"] = {"version": 8, "sources": {"protomaps": {"type": "vector", "url": "x"}}, "layers": []}
scenario = [["search", "ng13 8ab"], ["slider", "pd", 0], ["slider", "bg", 3], ["quietonly", True], ["show", 1],
            ["pathclick", 7], ["quietonly", False], ["search", "XX1"], ["search", "NG13 1QQ"], ["search", "DE1 1AA"],
            ["search", "SW1A 1AA"], ["locate"], ["slider", "tr", 0], ["slider", "lv", 3], ["pathclick", 3]]
json.dump({"files": files, "scenario": scenario, "geo": [52.96, -0.93]}, open(sys.argv[1], "w"))
print(n, "paths,", len(starts), "starts")
