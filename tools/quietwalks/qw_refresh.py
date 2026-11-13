#!/usr/bin/env python3
"""Scheduled refresh of the Quiet Walk Finder data (run monthly by cron as flo4paws).

Every run (monthly):
  1. Copy cache/ to cache.new/ and delete the OpenStreetMap files in the copy
     (paths, features, routes, honeypots, bangs). The crop map (CROME) is kept:
     it changes once a year and is refreshed by hand.
  2. Run quietwalks.py against cache.new/ (QW_CACHE), which re-downloads OSM and
     exports to v1.candidate/.
  3. Sanity check against the live v1/: paths, start points and chunks must not
     drop by more than MAX_DROP. If they do, nothing live changes; the candidate
     is kept for inspection and the run exits 2.
  4. Swap: v1 -> v1.prev, v1.candidate -> v1; cache -> cache.prev, cache.new -> cache.
Quarterly (Jan, Apr, Jul, Oct, or with --all):
  5. Postcodes (fresh OS Code-Point Open) and basemap (latest Protomaps build) into
     a staging folder, checked against the live copies the same way, then swapped.

  python3 qw_refresh.py              # monthly run (quarterly parts in Jan/Apr/Jul/Oct)
  python3 qw_refresh.py --all        # force the quarterly parts too
  python3 qw_refresh.py --no-fetch   # test: skip deleting OSM files (no downloads)

Exit codes: 0 ok, 1 failed (nothing live changed), 2 sanity check refused the
new data (nothing live changed). Everything is logged to refresh.log.
"""
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("QW_DATA", "/var/www/quietwalks-data")
CACHE = os.path.join(HERE, "cache")
LOG = os.path.join(HERE, "refresh.log")
MAX_DROP = 0.15
OSM_PREFIXES = ("paths_", "features_", "cycleroutes_", "walkroutes_", "honeypots_", "bangs_")
QUARTER_MONTHS = (1, 4, 7, 10)


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def run(args, env=None):
    log("run: " + " ".join(args))
    r = subprocess.run(args, cwd=HERE, env=env, capture_output=True, text=True)
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-6:])
    for ln in tail.splitlines():
        log("  | " + ln)
    return r.returncode


def rmtree(p):
    if os.path.islink(p) or os.path.isfile(p):
        os.remove(p)
    elif os.path.isdir(p):
        shutil.rmtree(p)


def move(src, dst):
    rmtree(dst)
    shutil.move(src, dst)


def dropped(old, new, label):
    """True (and logged) if new is more than MAX_DROP below old."""
    if old and new < old * (1 - MAX_DROP):
        log(f"REFUSED: {label} fell from {old} to {new} (more than {int(MAX_DROP * 100)}%)")
        return True
    log(f"check {label}: {old} -> {new} ok")
    return False


def refresh_paths(no_fetch):
    new_cache = CACHE + ".new"
    cand = os.path.join(DATA, "v1.candidate")
    rmtree(new_cache)
    shutil.copytree(CACHE, new_cache)
    if not no_fetch:
        gone = 0
        for fn in os.listdir(new_cache):
            if fn.startswith(OSM_PREFIXES) and fn.endswith(".json"):
                os.remove(os.path.join(new_cache, fn))
                gone += 1
        log(f"cleared {gone} OpenStreetMap files in the staging cache (crop map kept)")
    env = dict(os.environ, QW_CACHE=new_cache)
    if run([sys.executable, "quietwalks.py", "--export", cand], env) != 0:
        log("FAILED: quietwalks run failed; live data untouched")
        rmtree(new_cache)
        return 1
    try:
        with open(os.path.join(cand, "index.json")) as f:
            new = json.load(f)
        old = {}
        if os.path.exists(os.path.join(DATA, "v1", "index.json")):
            with open(os.path.join(DATA, "v1", "index.json")) as f:
                old = json.load(f)
    except Exception as e:  # noqa: BLE001
        log(f"FAILED: cannot read index.json ({e}); live data untouched")
        return 1
    bad = (dropped(old.get("paths"), new.get("paths", 0), "paths")
           | dropped(old.get("starts"), new.get("starts", 0), "start points")
           | dropped(len(old.get("chunks", {})), len(new.get("chunks", {})), "chunks"))
    if bad:
        log(f"live data untouched; candidate kept at {cand} and staging cache at {new_cache}")
        return 2
    move(os.path.join(DATA, "v1"), os.path.join(DATA, "v1.prev")) if os.path.exists(os.path.join(DATA, "v1")) else None
    shutil.move(cand, os.path.join(DATA, "v1"))
    move(CACHE, CACHE + ".prev")
    shutil.move(new_cache, CACHE)
    log(f"SWAPPED paths: {new.get('paths')} paths, {new.get('starts')} start points "
        f"(previous kept at v1.prev and cache.prev)")
    return 0


def refresh_site_data():
    stage = os.path.join(HERE, "site_stage")
    rmtree(stage)
    os.makedirs(stage)
    env = dict(os.environ, QW_CACHE=os.path.join(stage, "cache"))
    os.makedirs(env["QW_CACHE"])          # fresh Code-Point Open download goes here
    if run([sys.executable, "qw_site_data.py", "all", stage], env) != 0:
        log("FAILED: postcodes/basemap build failed; live copies untouched")
        return 1

    def count_pc(d):
        n = 0
        for fn in os.listdir(d) if os.path.isdir(d) else []:
            with open(os.path.join(d, fn)) as f:
                n += len(json.load(f))
        return n

    old_pc, new_pc = count_pc(os.path.join(DATA, "postcodes")), count_pc(os.path.join(stage, "postcodes"))
    old_bm = os.path.getsize(os.path.join(DATA, "basemap.pmtiles")) if os.path.exists(os.path.join(DATA, "basemap.pmtiles")) else 0
    new_bm = os.path.getsize(os.path.join(stage, "basemap.pmtiles"))
    if dropped(old_pc, new_pc, "postcodes") | dropped(old_bm, new_bm, "basemap bytes"):
        log(f"live postcodes/basemap untouched; new copies kept in {stage}")
        return 2
    move(os.path.join(DATA, "postcodes"), os.path.join(DATA, "postcodes.prev")) if os.path.exists(os.path.join(DATA, "postcodes")) else None
    shutil.move(os.path.join(stage, "postcodes"), os.path.join(DATA, "postcodes"))
    tmp = os.path.join(DATA, "basemap.pmtiles.new")
    shutil.copyfile(os.path.join(stage, "basemap.pmtiles"), tmp)
    os.replace(tmp, os.path.join(DATA, "basemap.pmtiles"))
    rmtree(stage)
    log(f"SWAPPED postcodes ({new_pc}) and basemap ({new_bm / 1e6:.1f} MB)")
    return 0


def main():
    no_fetch = "--no-fetch" in sys.argv
    quarterly = "--all" in sys.argv or time.localtime().tm_mon in QUARTER_MONTHS
    lock = open(os.path.join(HERE, ".refresh.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("another refresh is running; exiting")
        return 1
    t0 = time.time()
    log(f"=== quietwalks refresh start (quarterly parts: {'yes' if quarterly else 'no'})")
    rc = refresh_paths(no_fetch)
    if quarterly and rc == 0 and not no_fetch:
        rc = refresh_site_data()
    log(f"=== quietwalks refresh end rc={rc} in {time.time() - t0:.0f}s")
    return rc


if __name__ == "__main__":
    sys.exit(main())
