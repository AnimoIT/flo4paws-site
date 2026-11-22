#!/usr/bin/env python3
"""Parity test: qwf-rules.js (the page) must give the same answers as qw_rules.py.

    python3 test_qwf_rules_js.py            # needs node

Every day 1 May 2026 - 31 Aug 2027, for 71, 69, 01 and a département with no rules (42),
with and without ONF forests (calendar and none), at several woodland shares.
"""
import datetime as dt
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qw_rules as q  # noqa: E402

JS = os.path.join(HERE, "..", "..", "src", "static", "walks", "finder", "qwf-rules.js")
RULES_PATH = os.path.join(HERE, "regions", "fr_rules.json")
rules = json.load(open(RULES_PATH, encoding="utf-8"))
KEYS = ("level", "stale", "season", "periods", "notes", "source", "onf_listed_day", "lead_rule", "harvest")

cases, expect = [], []
d, end = dt.date(2026, 5, 1), dt.date(2027, 8, 31)
while d <= end:
    for dept in ("71", "69", "01", "42"):
        for fid in (None, "F22134H", "F22303U", "F22488X", "F22559Q"):
            st = q.state_on(rules, dept, d, fid)
            vals = [q.chasse_value(rules, st, w, fid) for w in (0, 37, 50, 100)]
            cases.append([dept, d.isoformat(), fid])
            expect.append([{k: st[k] for k in KEYS if k in st}, vals])
    d += dt.timedelta(days=1)

node = r"""
const fs = require("fs"); const R = require(process.argv[1]);
const rules = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const cases = JSON.parse(fs.readFileSync(0, "utf8"));
const KEYS = %s;
const out = cases.map(([dept, day, fid]) => {
  const st = R.stateOn(rules, dept, day, fid);
  const o = {}; KEYS.forEach(k => { if (k in st) o[k] = st[k]; });
  return [o, [0, 37, 50, 100].map(w => R.chasseValue(rules, st, w, fid))];
});
process.stdout.write(JSON.stringify(out));
""" % json.dumps(KEYS)
try:
    r = subprocess.run(["node", "-e", node, os.path.abspath(JS), RULES_PATH], input=json.dumps(cases),
                       capture_output=True, text=True, check=True)
except FileNotFoundError:
    print("SKIP: node not installed")
    sys.exit(0)
got = json.loads(r.stdout)
# weekday numbering on its own: no current rule names Sunday, so the day grid alone can't catch it
days = [(dt.date(2026, 1, 1) + dt.timedelta(days=i)) for i in range(730)]
wk = subprocess.run(["node", "-e", "const R=require(process.argv[1]);"
                     "process.stdout.write(JSON.stringify(JSON.parse(require('fs').readFileSync(0,'utf8')).map(R.isoWeekday)))",
                     os.path.abspath(JS)], input=json.dumps([x.isoformat() for x in days]),
                    capture_output=True, text=True, check=True)
wk_bad = [x for x, w in zip(days, json.loads(wk.stdout)) if w != x.isoweekday()]
print(f"weekdays: {len(days)} days, {len(wk_bad)} mismatches")
bad = [(c, e, g) for c, e, g in zip(cases, expect, got) if json.loads(json.dumps(e)) != g]
for c, e, g in bad[:10]:
    print("MISMATCH", c, "\n  py", e, "\n  js", g)
levels = {}
for e in expect:
    levels[e[0]["level"]] = levels.get(e[0]["level"], 0) + 1
print(f"{len(cases)} cases, {len(bad)} mismatches; levels seen {dict(sorted(levels.items()))}")
ok = not bad and not wk_bad
print("PARITY", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
