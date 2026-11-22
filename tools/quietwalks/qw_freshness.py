#!/usr/bin/env python3
"""Freshness heartbeat for the Quiet Walk Finder (run weekly by cron on the pipeline server).

  python3 qw_freshness.py --region uk

Fetches the region's live index.json from the public site (regions/<id>.json ->
public_index) and pings the BetterStack heartbeat only if its "built" date is at most
max_age_days old. So BetterStack alerts by silence whenever any part of the chain has
stopped: the refresh failed or was refused, the push or swap failed, the pipeline
server or its cron is dead, or the site stopped serving the data.

The heartbeat URL is a secret and is not in the repo: one line in
~/.config/quietwalks/heartbeat-<id>.url (chmod 600).
Exit codes: 0 pinged, 1 stale or unreadable (no ping), 3 no heartbeat file.
"""
import datetime
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "quietwalks-freshness/1.0 (Flo4Paws)"}


def main():
    if "--region" not in sys.argv or sys.argv.index("--region") + 1 >= len(sys.argv):
        raise SystemExit("--region is required, e.g. python3 qw_freshness.py --region uk")
    rid = sys.argv[sys.argv.index("--region") + 1]
    with open(os.path.join(HERE, "regions", rid + ".json"), encoding="utf-8") as f:
        region = json.load(f)
    logdir = os.path.join(HERE, "logs")
    os.makedirs(logdir, exist_ok=True)

    def log(msg):
        line = time.strftime("%Y-%m-%d %H:%M:%S ") + f"[{rid}] " + msg
        print(line, flush=True)
        with open(os.path.join(logdir, f"freshness-{rid}.log"), "a") as fh:
            fh.write(line + "\n")

    hb_file = os.path.expanduser(f"~/.config/quietwalks/heartbeat-{rid}.url")
    if not os.path.exists(hb_file):
        log(f"no heartbeat file {hb_file}; nothing pinged")
        return 3
    try:
        req = urllib.request.Request(region["public_index"], headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            built = json.load(r)["built"]
        age = (datetime.date.today() - datetime.date.fromisoformat(built)).days
    except Exception as e:  # noqa: BLE001
        log(f"STALE: cannot read live index ({e!r}); no ping")
        return 1
    if age > region["max_age_days"]:
        log(f"STALE: live data built {built}, {age} days old (limit {region['max_age_days']}); no ping")
        return 1
    with open(hb_file) as f:
        url = f.read().strip()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            code = r.status
    except Exception as e:  # noqa: BLE001
        log(f"fresh (built {built}, {age} days) but the ping failed: {e!r}")
        return 1
    log(f"fresh: built {built}, {age} days old; heartbeat {code}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
