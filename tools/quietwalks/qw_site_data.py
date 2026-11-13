#!/usr/bin/env python3
"""Build the Quiet Walk Finder's non-path data for the website.

  python3 qw_site_data.py postcodes OUT_DIR   # OS Code-Point Open -> OUT_DIR/postcodes/<OUTWARD>.json
  python3 qw_site_data.py basemap OUT_DIR     # Protomaps daily build -> OUT_DIR/basemap.pmtiles
  python3 qw_site_data.py all OUT_DIR

Uses the coverage (centre and radius) from quietwalks.py in the same folder.
Pure standard library, plus the pmtiles CLI binary it downloads into ./bin.
Postcodes: Contains OS data (c) Crown copyright and database right; Royal Mail data
(c) Royal Mail copyright and database right; National Statistics data (c) Crown
copyright and database right. Open Government Licence.
"""
import csv
import datetime
import io
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import quietwalks as qw  # noqa: E402

UA = {"User-Agent": "quietwalks-site/1.0 (personal/Flo4Paws)"}
CPO_URL = "https://api.os.uk/downloads/v1/products/CodePointOpen/downloads?area=GB&format=CSV&redirect"
EXTRA_KM = 5            # postcodes this far beyond the path coverage still resolve
BASEMAP_EXTRA_KM = 10   # basemap a little wider than the paths
BASEMAP_MAXZOOM = 15


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def fetch(url, timeout=600):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def latlon_to_bng_approx(lat, lon):
    """Rough inverse for the centre only (used to pre-filter by metres)."""
    best, step = None, 2000.0
    E, N = 470000.0, 340000.0
    for _ in range(60):
        la, lo = qw.bng_to_latlon(E, N)
        dE = (lon - lo) * 111320 * math.cos(math.radians(lat))
        dN = (lat - la) * 110540
        E, N = E + dE, N + dN
        if abs(dE) < 0.5 and abs(dN) < 0.5:
            break
    return E, N


def build_postcodes(out_dir):
    cache = os.path.join(HERE, "cache", "codepo_gb.zip")
    if not os.path.exists(cache):
        log("downloading Code-Point Open (CSV, about 20 MB)")
        data = fetch(CPO_URL)
        with open(cache + ".tmp", "wb") as f:
            f.write(data)
        os.replace(cache + ".tmp", cache)
    E0, N0 = latlon_to_bng_approx(qw.CENTRE_LAT, qw.CENTRE_LON)
    lim = qw.RADIUS_M + EXTRA_KM * 1000
    log(f"coverage centre BNG {E0:.0f},{N0:.0f}; keeping postcodes within {lim / 1000:.0f} km")
    books, rows = {}, 0
    with zipfile.ZipFile(cache) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv") and "/data/csv/" in "/" + n.lower()]
        if not names:
            raise SystemExit("no Data/CSV files found in the Code-Point Open zip: " + ", ".join(z.namelist()[:10]))
        for name in names:
            with z.open(name) as fh:
                for r in csv.reader(io.TextIOWrapper(fh, encoding="utf-8", errors="replace")):
                    rows += 1
                    if len(r) < 4 or not r[2].strip().isdigit():
                        continue                      # header line or no coordinates
                    E, N = int(r[2]), int(r[3])
                    if E == 0 or (E - E0) ** 2 + (N - N0) ** 2 > lim * lim:
                        continue
                    pc = r[0].replace(" ", "").upper()
                    if len(pc) < 5:
                        continue
                    la, lo = qw.bng_to_latlon(E, N)
                    books.setdefault(pc[:-3], {})[pc] = [round(la, 5), round(lo, 5)]
    tmp = os.path.join(out_dir, "postcodes.tmp")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    for outward, book in books.items():
        with open(os.path.join(tmp, outward + ".json"), "w") as f:
            json.dump(book, f, separators=(",", ":"))
    dest = os.path.join(out_dir, "postcodes")
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.replace(tmp, dest)
    n = sum(len(b) for b in books.values())
    log(f"postcodes: read {rows} rows, wrote {n} postcodes in {len(books)} district files")


def pmtiles_bin():
    bindir = os.path.join(HERE, "bin")
    exe = os.path.join(bindir, "pmtiles")
    if os.path.exists(exe):
        return exe
    os.makedirs(bindir, exist_ok=True)
    rel = json.loads(fetch("https://api.github.com/repos/protomaps/go-pmtiles/releases/latest"))
    ver = rel["tag_name"].lstrip("v")
    arch = {"x86_64": "x86_64", "aarch64": "arm64"}.get(platform.machine(), platform.machine())
    want = f"go-pmtiles_{ver}_Linux_{arch}.tar.gz"
    asset = next((a for a in rel["assets"] if a["name"] == want), None)
    if not asset:
        raise SystemExit(f"pmtiles release asset {want} not found")
    log(f"downloading pmtiles CLI {ver}")
    with tarfile.open(fileobj=io.BytesIO(fetch(asset["browser_download_url"])), mode="r:gz") as t:
        member = next(m for m in t.getmembers() if os.path.basename(m.name) == "pmtiles" and m.isfile())
        with t.extractfile(member) as src, open(exe, "wb") as dst:
            shutil.copyfileobj(src, dst)
    os.chmod(exe, 0o755)
    return exe


def latest_build():
    today = datetime.datetime.now(datetime.timezone.utc).date()
    for i in range(10):
        d = (today - datetime.timedelta(days=i)).strftime("%Y%m%d")
        url = f"https://build.protomaps.com/{d}.pmtiles"
        try:
            req = urllib.request.Request(url, method="HEAD", headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    return url
        except Exception:  # noqa: BLE001
            continue
    raise SystemExit("no Protomaps daily build found in the last 10 days")


def build_basemap(out_dir):
    exe = pmtiles_bin()
    src = latest_build()
    r = qw.RADIUS_M + BASEMAP_EXTRA_KM * 1000
    dlat, dlon = r / qw.KY, r / qw.KX
    bbox = (f"{qw.CENTRE_LON - dlon:.4f},{qw.CENTRE_LAT - dlat:.4f},"
            f"{qw.CENTRE_LON + dlon:.4f},{qw.CENTRE_LAT + dlat:.4f}")
    tmp = os.path.join(out_dir, "basemap.pmtiles.tmp")
    log(f"extracting {src} bbox {bbox} maxzoom {BASEMAP_MAXZOOM}")
    subprocess.run([exe, "extract", src, tmp, f"--bbox={bbox}", f"--maxzoom={BASEMAP_MAXZOOM}",
                    "--download-threads=4"], check=True)
    subprocess.run([exe, "verify", tmp], check=True)
    os.replace(tmp, os.path.join(out_dir, "basemap.pmtiles"))
    log(f"basemap: {os.path.getsize(os.path.join(out_dir, 'basemap.pmtiles')) / 1e6:.1f} MB from {src}")


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("postcodes", "basemap", "all"):
        raise SystemExit(__doc__)
    what, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    if what in ("postcodes", "all"):
        build_postcodes(out_dir)
    if what in ("basemap", "all"):
        build_basemap(out_dir)
    log("SITE DATA DONE")


if __name__ == "__main__":
    main()
