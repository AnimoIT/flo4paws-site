#!/usr/bin/env python3
"""Box side of the Quiet Walks publish. Installed as /usr/local/bin/qw-swap and run
ONLY through a forced-command SSH key for the qwpush user:

  command="/usr/local/bin/qw-swap uk",restrict ssh-ed25519 AAAA... qw-swap-uk

The pipeline server has already rsync'd candidates (write-only rrsync key) into
INCOMING/<region>/, outside the web root. This script checks each candidate against
the live copy and swaps it in, keeping the previous copy as <name>.prev:

  v1.candidate/               -> <live>/v1            (index parses, every chunk file
                                                       present, paths/starts/chunks
                                                       down no more than 15%)
  postcodes.candidate/        -> <live>/postcodes     (postcode count down no more than 15%)
  basemap.pmtiles.candidate   -> <live>/basemap.pmtiles (PMTiles header, size down no
                                                       more than 15%)

Whatever the client asks to run is ignored: the region comes from this script's own
argument in authorized_keys. Exit codes: 0 swapped (or nothing to do), 1 failed,
2 a check refused a candidate. A refused candidate stays in INCOMING for inspection;
the live copy is never touched unless its check passed.
"""
import json
import os
import shutil
import sys
import time

INCOMING = "/var/lib/qwpush/incoming"
LIVE = {"uk": "/var/www/quietwalks-data"}     # add "fr" in B6
MAX_DROP = 0.15
LOG = "/var/lib/qwpush/qw-swap.log"


def log(region, msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + f"[{region}] " + msg
    print(line, flush=True)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def too_low(region, label, old, new):
    if old and new < old * (1 - MAX_DROP):
        log(region, f"REFUSED: {label} fell from {old} to {new}")
        return True
    log(region, f"check {label}: {old} -> {new} ok")
    return False


def check_v1(region, cand, live):
    with open(os.path.join(cand, "index.json")) as f:
        new = json.load(f)
    missing = [k for k in new.get("chunks", {}) if not os.path.isfile(os.path.join(cand, "chunks", k + ".json"))]
    if missing or not os.path.isfile(os.path.join(cand, "starts.json")):
        log(region, f"REFUSED: candidate incomplete (missing chunks {missing[:5]} or starts.json)")
        return False
    old = {}
    if os.path.exists(os.path.join(live, "index.json")):
        with open(os.path.join(live, "index.json")) as f:
            old = json.load(f)
    bad = (too_low(region, "paths", old.get("paths"), new.get("paths", 0))
           | too_low(region, "start points", old.get("starts"), new.get("starts", 0))
           | too_low(region, "chunks", len(old.get("chunks", {})), len(new.get("chunks", {}))))
    return not bad


def count_pc(d):
    n = 0
    for fn in os.listdir(d) if os.path.isdir(d) else []:
        with open(os.path.join(d, fn)) as f:
            n += len(json.load(f))
    return n


def check_postcodes(region, cand, live):
    return not too_low(region, "postcodes", count_pc(live), count_pc(cand))


def check_basemap(region, cand, live):
    with open(cand, "rb") as f:
        if f.read(7) != b"PMTiles":
            log(region, "REFUSED: basemap candidate has no PMTiles header")
            return False
    old = os.path.getsize(live) if os.path.exists(live) else 0
    return not too_low(region, "basemap bytes", old, os.path.getsize(cand))


def swap_in(cand, live):
    prev = live + ".prev"
    if os.path.isdir(prev) and not os.path.islink(prev):
        shutil.rmtree(prev)
    elif os.path.exists(prev):
        os.remove(prev)
    if os.path.exists(live):
        os.rename(live, prev)
    os.rename(cand, live)


def main():
    region = sys.argv[1] if len(sys.argv) == 2 else ""
    if region not in LIVE:
        print(f"qw-swap: unknown region {region!r}", file=sys.stderr)
        return 1
    inc, live = os.path.join(INCOMING, region), LIVE[region]
    plan = [("v1.candidate", "v1", check_v1),
            ("postcodes.candidate", "postcodes", check_postcodes),
            ("basemap.pmtiles.candidate", "basemap.pmtiles", check_basemap)]
    todo = [(os.path.join(inc, c), os.path.join(live, n), n, chk) for c, n, chk in plan
            if os.path.exists(os.path.join(inc, c))]
    if not todo:
        log(region, "nothing to swap")
        return 0
    for cand, dest, name, chk in todo:          # check everything before swapping anything
        try:
            ok = chk(region, cand, dest)
        except Exception as e:  # noqa: BLE001
            log(region, f"FAILED: check of {name} raised {e!r}")
            return 1
        if not ok:
            log(region, "live data untouched")
            return 2
    for cand, dest, name, _ in todo:
        try:
            swap_in(cand, dest)
        except OSError as e:
            log(region, f"FAILED: swap of {name}: {e!r}")
            return 1
        log(region, f"SWAPPED {name} (previous kept as {name}.prev)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
