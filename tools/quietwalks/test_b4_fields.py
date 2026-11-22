#!/usr/bin/env python3
"""S372 B4 end-to-end test: synthetic region, offline build, check the exported seasonal fields.

    python3 test_b4_fields.py [path/to/tools/quietwalks]
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
LAT0, LON0 = 46.4, 4.7
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110540.0


def ll(x, y):
    return round(LAT0 + y / KY, 6), round(LON0 + x / KX, 6)


def ring_lonlat(pts):
    r = [[ll(x, y)[1], ll(x, y)[0]] for x, y in pts]
    return r + [r[0]]


def box(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def way(wid, pts, tags):
    return {"type": "way", "id": wid, "tags": tags,
            "geometry": [{"lat": ll(x, y)[0], "lon": ll(x, y)[1]} for x, y in pts]}


def closed_way(wid, pts, tags):
    w = way(wid, pts + pts[:1], tags)
    w["nodes"] = list(range(len(pts))) + [0]
    return w


d = tempfile.mkdtemp(prefix="qwb4_")
try:
    for f in ("quietwalks.py",):
        shutil.copy(os.path.join(SRC, f), d)
    os.makedirs(os.path.join(d, "regions"))
    fr = json.load(open(os.path.join(SRC, "regions", "fr.json"), encoding="utf-8"))
    reg = {"id": "t", "place_name": "Test", "centre": [LAT0, LON0], "radius_m": 3000, "cache": "cache",
           "out": "out", "places": "communes", "crops": {"source": "none"},
           "attribution": "test", "layers": fr["layers"]}
    json.dump(reg, open(os.path.join(d, "regions", "t.json"), "w"))
    c = os.path.join(d, "cache")
    os.makedirs(c)
    # paths: A along y=0 x -1000..1000 (through wood with a 200 m clearing); B in the vineyard;
    # C at x=+1500 (dept 2, in ONF forest F2 for 100%); D crosses dept line at x=0 mostly in dept 1
    paths = [
        way(1, [(-1000, 0), (1000, 0)], {"highway": "track"}),
        way(2, [(-1000, 1200), (-200, 1200)], {"highway": "path"}),
        way(3, [(1300, -800), (1300, 800)], {"highway": "path"}),
        way(4, [(-900, -1500), (300, -1500)], {"highway": "footway"}),
    ]
    json.dump({"elements": paths}, open(os.path.join(c, "paths_0.json"), "w"))
    for q in ("features", "cycleroutes", "walkroutes", "bangs", "honeypots"):
        json.dump({"elements": []}, open(os.path.join(c, f"{q}_0.json"), "w"))
    # OSM landcover: the vineyard for path B (x -1000..-600 only, i.e. half of B)
    json.dump({"elements": [closed_way(90, box(-1050, 1100, -600, 1300), {"landuse": "vineyard"})]},
              open(os.path.join(c, "landcover_0.json"), "w"))
    # WFS wood: outer -500..500 x -200..200 with a hole -100..100  -> path A wood = 800/2000 = 40%
    wood = {"W1": {"props": {}, "polys": [[
        [(la, lo) for lo, la in ring_lonlat(box(-500, -200, 500, 200))],
        [(la, lo) for lo, la in ring_lonlat(box(-100, -200 + 50, 100, 200 - 50))]]]}}
    json.dump(wood, open(os.path.join(c, "wfs_wood_0.json"), "w"))
    # WFS vine (RPG): the other half of B (-600..-200) -> B vine = 100%
    vine = {"V1": {"props": {}, "polys": [[[(la, lo) for lo, la in ring_lonlat(box(-610, 1100, -150, 1300))]]]}}
    json.dump(vine, open(os.path.join(c, "wfs_vine_0.json"), "w"))
    json.dump({}, open(os.path.join(c, "wfs_grass_0.json"), "w"))
    forest = {"F2": {"props": {"llib_frt": "Forêt domaniale de Test", "cdom_frt": "OUI", "cinse_dep": "02"},
                     "polys": [[[(la, lo) for lo, la in ring_lonlat(box(1200, -900, 1400, 900))]]]},
              "F9": {"props": {"llib_frt": "Forêt communale du bout", "cdom_frt": "NON", "cinse_dep": "01"},
                     "polys": [[[(la, lo) for lo, la in ring_lonlat(box(-1000, -100, -900, 100))]]]}}
    json.dump(forest, open(os.path.join(c, "wfs_forest_0.json"), "w"))
    dept = {"01": {"props": {"nom_officiel": "Un"}, "polys": [[[(la, lo) for lo, la in ring_lonlat(box(-5000, -5000, 0, 5000))]]]},
            "02": {"props": {"nom_officiel": "Deux"}, "polys": [[[(la, lo) for lo, la in ring_lonlat(box(0, -5000, 5000, 5000))]]]}}
    json.dump(dept, open(os.path.join(c, "wfs_dept_0.json"), "w"))
    r = subprocess.run([sys.executable, "quietwalks.py", "--region", "t", "--offline", "--export", "out/finder"],
                       cwd=d, capture_output=True, text=True)
    print(r.stdout[-2500:], r.stderr[-2500:])
    assert r.returncode == 0, "build failed"
    idx = json.load(open(os.path.join(d, "out/finder/index.json")))
    assert idx["fields"][9:] == ["wood", "vine", "dept", "forest_id"], idx["fields"]
    assert idx.get("forests") == "forests.json"
    rows = {}
    for fn in os.listdir(os.path.join(d, "out/finder/chunks")):
        for row in json.load(open(os.path.join(d, "out/finder/chunks", fn))):
            rows[row[0]] = row
    fo = json.load(open(os.path.join(d, "out/finder/forests.json")))
    print("rows", {k: v[:8] + v[9:] for k, v in rows.items()})
    print("forests", fo)
    ok = True

    def expect(cond, msg):
        global ok
        print(("PASS " if cond else "FAIL ") + msg)
        ok = ok and cond
    a, b, cc, dd = rows[1], rows[2], rows[3], rows[4]
    expect(abs(a[9] - 40) <= 4, f"A wood ~40 (clearing excluded): {a[9]}")
    expect(a[10] == 0, f"A vine 0: {a[10]}")
    expect(b[10] >= 95, f"B vine ~100 (OSM half + RPG half): {b[10]}")
    expect(b[9] == 0, f"B wood 0: {b[9]}")
    expect(cc[11] == "02" and cc[12] == "F2", f"C dept 02, forest F2: {cc[11]} {cc[12]}")
    expect(dd[11] == "01", f"D dept 01 (3/4 of it): {dd[11]}")
    expect(a[12] == "", f"A forest '' (F9 covers < 25%): {a[12]!r}")
    expect(fo.get("F2") == ["Forêt domaniale de Test", True, "02"], f"forests.json F2: {fo.get('F2')}")
    expect(os.path.exists(os.path.join(d, "out/livestock_check.csv")), "livestock_check.csv written")
    expect(all(len(v) == 13 for v in rows.values()), "13 fields per row")
    print("E2E", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
finally:
    shutil.rmtree(d)
