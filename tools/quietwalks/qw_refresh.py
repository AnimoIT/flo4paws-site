#!/usr/bin/env python3
"""Scheduled refresh of the Quiet Walk Finder data for one region (run monthly by cron
on the pipeline server, not on the web box).

  python3 qw_refresh.py --region uk               # monthly run (quarterly parts in Jan/Apr/Jul/Oct)
  python3 qw_refresh.py --region uk --all         # force the quarterly parts too
  python3 qw_refresh.py --region uk --no-fetch    # test: keep the cached OSM files (no downloads)
  python3 qw_refresh.py --region uk --no-publish  # build and check locally; publish nothing

--region is required: there is no default, so a job can never build one region and
publish it as another. Everything about the region comes from regions/<id>.json.

Every run (monthly):
  1. Copy the region's cache to <cache>.new and delete the OpenStreetMap files in the
     copy. The crop map is kept (refreshed by hand once a year).
  2. Run quietwalks.py --region <id> against the staged cache (QW_CACHE), exporting
     to <local_data>/v1.candidate.
  3. Sanity check against <local_data>/v1, the copy of what was last published:
     paths, start points and chunks must not drop by more than MAX_DROP. If they do,
     nothing is published; the candidate is kept for inspection and the run exits 2.
  4. Publish: rsync the candidate to the web box (restricted key, write-only, into a
     staging folder outside the web root), then run the box's swap (a second key that
     can only run the swap script, which repeats the checks before it swaps).
  5. Only when the box swap succeeds: swap locally too (v1 -> v1.prev, candidate -> v1;
     cache -> cache.prev, cache.new -> cache).
Quarterly (Jan, Apr, Jul, Oct, or with --all), when the region has quarterly_site_data:
  6. Postcodes (fresh OS Code-Point Open) and basemap (latest Protomaps build) into a
     staging folder, checked against the local copies the same way, published and
     swapped the same way.

Exit codes: 0 ok, 1 failed, 2 sanity check refused the new data. In every non-zero
case the live site is unchanged. Everything is logged to logs/refresh-<id>.log.
Alerting is separate: qw_freshness.py pings a heartbeat only while the live data is fresh.
"""
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_DROP = 0.15
OSM_PREFIXES = ("paths_", "features_", "cycleroutes_", "walkroutes_", "honeypots_", "bangs_")
QUARTER_MONTHS = (1, 4, 7, 10)


def arg_value(flag):
    if flag not in sys.argv:
        return None
    i = sys.argv.index(flag)
    if i + 1 >= len(sys.argv) or sys.argv[i + 1].startswith("-"):
        raise SystemExit(f"{flag} needs a value")
    return sys.argv[i + 1]


REGION_ID = arg_value("--region")
if not REGION_ID:
    raise SystemExit("--region is required, e.g. python3 qw_refresh.py --region uk")
with open(os.path.join(HERE, "regions", REGION_ID + ".json"), encoding="utf-8") as _f:
    REGION = json.load(_f)
CACHE = os.path.join(HERE, REGION["cache"])
DATA = os.environ.get("QW_DATA") or os.path.join(HERE, REGION["local_data"])
LOGDIR = os.path.join(HERE, "logs")
LOG = os.path.join(LOGDIR, f"refresh-{REGION_ID}.log")
PUB = REGION.get("publish")


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + f"[{REGION_ID}] " + msg
    print(line, flush=True)
    os.makedirs(LOGDIR, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def run(args, env=None):
    log("run: " + " ".join(args))
    r = subprocess.run(args, cwd=HERE, env=env, capture_output=True, text=True)
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-8:])
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


def ssh_opts(key):
    return ["ssh", "-i", os.path.expanduser(key), "-o", "BatchMode=yes",
            "-o", "IdentitiesOnly=yes", "-o", "ConnectTimeout=30"]


def publish(items):
    """items: list of (local path, remote name). rsync each into the box's staging
    folder, then run the swap. Returns 0 when the box swapped, else non-zero."""
    if "--no-publish" in sys.argv or not PUB:
        log("publish skipped (--no-publish or no publish block)")
        return 0
    rsh = " ".join(ssh_opts(PUB["push_key"]))
    for local, name in items:
        src = local.rstrip("/") + ("/" if os.path.isdir(local) else "")
        rc = run(["rsync", "-rt", "--delete", "--chmod=D755,F644", "-e", rsh,
                  src, f"{PUB['ssh']}:{name}" + ("/" if os.path.isdir(local) else "")])
        if rc != 0:
            log(f"FAILED: push of {name} exited {rc}; live site untouched")
            return 1
    rc = run(ssh_opts(PUB["swap_key"]) + [PUB["ssh"], "swap"])
    if rc != 0:
        log(f"FAILED: box swap exited {rc} (2 = its own check refused); live site unchanged")
    return rc


def refresh_paths(no_fetch):
    new_cache = CACHE + ".new"
    cand = os.path.join(DATA, "v1.candidate")
    os.makedirs(DATA, exist_ok=True)
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
    if run([sys.executable, "quietwalks.py", "--region", REGION_ID, "--export", cand], env) != 0:
        log("FAILED: quietwalks run failed; nothing published")
        rmtree(new_cache)
        return 1
    try:
        with open(os.path.join(cand, "index.json")) as f:
            new = json.load(f)
        old = {}
        if os.path.exists(os.path.join(DATA, "v1", "index.json")):
            with open(os.path.join(DATA, "v1", "index.json")) as f:
                old = json.load(f)
        else:
            log("no local v1 to compare against: this candidate sets the baseline")
    except Exception as e:  # noqa: BLE001
        log(f"FAILED: cannot read index.json ({e}); nothing published")
        return 1
    bad = (dropped(old.get("paths"), new.get("paths", 0), "paths")
           | dropped(old.get("starts"), new.get("starts", 0), "start points")
           | dropped(len(old.get("chunks", {})), len(new.get("chunks", {})), "chunks"))
    if bad:
        log(f"nothing published; candidate kept at {cand} and staging cache at {new_cache}")
        return 2
    rc = publish([(cand, "v1.candidate")])
    if rc != 0:
        log(f"local copies not swapped; candidate kept at {cand}")
        return rc
    if os.path.exists(os.path.join(DATA, "v1")):
        move(os.path.join(DATA, "v1"), os.path.join(DATA, "v1.prev"))
    shutil.move(cand, os.path.join(DATA, "v1"))
    move(CACHE, CACHE + ".prev")
    shutil.move(new_cache, CACHE)
    log(f"SWAPPED paths: {new.get('paths')} paths, {new.get('starts')} start points "
        f"(previous kept at v1.prev and {os.path.basename(CACHE)}.prev)")
    return 0


def count_pc(d):
    n = 0
    for fn in os.listdir(d) if os.path.isdir(d) else []:
        with open(os.path.join(d, fn)) as f:
            n += len(json.load(f))
    return n


def refresh_site_data():
    stage = os.path.join(HERE, f"site_stage_{REGION_ID}")
    rmtree(stage)
    os.makedirs(stage)
    env = dict(os.environ, QW_CACHE=os.path.join(stage, "cache"))
    os.makedirs(env["QW_CACHE"])          # fresh Code-Point Open download goes here
    if run([sys.executable, "qw_site_data.py", "--region", REGION_ID, "all", stage], env) != 0:
        log("FAILED: postcodes/basemap build failed; nothing published")
        return 1
    old_pc, new_pc = count_pc(os.path.join(DATA, "postcodes")), count_pc(os.path.join(stage, "postcodes"))
    bm = os.path.join(DATA, "basemap.pmtiles")
    old_bm = os.path.getsize(bm) if os.path.exists(bm) else 0
    new_bm = os.path.getsize(os.path.join(stage, "basemap.pmtiles"))
    if dropped(old_pc, new_pc, "postcodes") | dropped(old_bm, new_bm, "basemap bytes"):
        log(f"nothing published; new copies kept in {stage}")
        return 2
    rc = publish([(os.path.join(stage, "postcodes"), "postcodes.candidate"),
                  (os.path.join(stage, "basemap.pmtiles"), "basemap.pmtiles.candidate")])
    if rc != 0:
        log(f"local copies not swapped; new copies kept in {stage}")
        return rc
    if os.path.exists(os.path.join(DATA, "postcodes")):
        move(os.path.join(DATA, "postcodes"), os.path.join(DATA, "postcodes.prev"))
    shutil.move(os.path.join(stage, "postcodes"), os.path.join(DATA, "postcodes"))
    os.replace(os.path.join(stage, "basemap.pmtiles"), bm)
    rmtree(stage)
    log(f"SWAPPED postcodes ({new_pc}) and basemap ({new_bm / 1e6:.1f} MB)")
    return 0


def main():
    no_fetch = "--no-fetch" in sys.argv
    quarterly = REGION.get("quarterly_site_data") and (
        "--all" in sys.argv or time.localtime().tm_mon in QUARTER_MONTHS)
    lock = open(os.path.join(HERE, f".refresh-{REGION_ID}.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("another refresh of this region is running; exiting")
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
