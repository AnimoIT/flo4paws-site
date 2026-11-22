#!/usr/bin/env python3
"""Quiet Walks France: check regions/<id>_rules.json and work out a day's hunting state.

    python3 qw_rules.py --check [--region fr] [--today YYYY-MM-DD] [--forests forests.json]
    python3 qw_rules.py --state 71 2026-12-04 [--region fr]

--check fails (exit 1) on any error. The checks (spec S368 §6):
  - every date parses, and from <= to;
  - levels and weekdays are known values;
  - within a département, the spans of its seasons don't overlap;
  - every coverage département has a season in force on --today (default: today);
  - public holidays fall inside the season they're listed under;
  - ONF days fall inside the forest's département's season, and (with --forests) the forest exists.

state_on() is the reference for the page (B5): finder.js must give the same answers.
Standard library only.
"""
import datetime as dt
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = ("battue", "open", "stalk", "suspended", "closed")
RANK = {"closed": 0, "suspended": 1, "stalk": 2, "open": 3, "battue": 4}
SCOPES = ("all_shooting", "small_game")


def _date(s, where, errors):
    try:
        return dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        errors.append(f"{where}: bad date {s!r}")
        return None


def _mmdd(s, where, errors):
    try:
        m, d = (int(x) for x in s.split("-"))
        dt.date(2024, m, d)          # leap year, so 02-29 is allowed
        return m, d
    except (AttributeError, ValueError):
        errors.append(f"{where}: bad month-day {s!r}")
        return None


def season_span(season):
    ds = [(dt.date.fromisoformat(p["from"]), dt.date.fromisoformat(p["to"])) for p in season["periods"]]
    return min(a for a, _ in ds), max(b for _, b in ds)


def check(rules, today, forests=None):
    errors, warnings = [], []
    for k in ("format", "coverage_depts", "hunting", "levels", "weights", "lead_rule", "vineyards"):
        if k not in rules:
            errors.append(f"missing top-level key {k!r}")
    if errors:
        return errors, warnings
    for lv in LEVELS:
        if lv not in rules["weights"]["woodland"] or lv not in rules["weights"]["open_land"]:
            errors.append(f"weights: no value for level {lv!r}")
    hol = {}
    for skey, days in (rules.get("public_holidays") or {}).items():
        if skey == "note":
            continue
        hol[skey] = [x for x in (_date(s, f"public_holidays.{skey}", errors) for s in days) if x]
    spans = {}
    for dept, seasons in rules["hunting"].items():
        if dept not in rules["coverage_depts"]:
            warnings.append(f"hunting.{dept}: not a coverage département")
        for skey, s in seasons.items():
            w = f"hunting.{dept}.{skey}"
            src = s.get("source") or {}
            for k in ("ref", "date", "url"):
                if not src.get(k):
                    errors.append(f"{w}.source: missing {k}")
            if src.get("url") and not src["url"].startswith("https://"):
                errors.append(f"{w}.source.url: not https")
            if src.get("date"):
                _date(src["date"], f"{w}.source.date", errors)
            if not s.get("periods"):
                errors.append(f"{w}: no periods")
                continue
            ok = True
            for i, p in enumerate(s["periods"]):
                a = _date(p.get("from"), f"{w}.periods[{i}].from", errors)
                b = _date(p.get("to"), f"{w}.periods[{i}].to", errors)
                if p.get("level") not in LEVELS or p.get("level") in ("closed", "suspended"):
                    errors.append(f"{w}.periods[{i}]: level {p.get('level')!r} not allowed in a period")
                if a and b and a > b:
                    errors.append(f"{w}.periods[{i}]: from {a} is after to {b}")
                ok = ok and bool(a and b)
            for i, r in enumerate(s.get("day_rules") or []):
                if not r.get("weekdays") or any(d not in range(1, 8) for d in r["weekdays"]):
                    errors.append(f"{w}.day_rules[{i}]: weekdays must be 1-7")
                if r.get("scope") not in SCOPES:
                    errors.append(f"{w}.day_rules[{i}]: scope must be one of {SCOPES}")
                if r.get("except_public_holidays") and skey not in hol:
                    errors.append(f"{w}.day_rules[{i}]: needs public_holidays.{skey}")
            if ok:
                spans.setdefault(dept, []).append((season_span(s), skey))
    for dept, lst in spans.items():
        lst.sort()
        for (sp1, k1), (sp2, k2) in zip(lst, lst[1:]):
            if sp2[0] <= sp1[1]:
                errors.append(f"hunting.{dept}: seasons {k1} and {k2} overlap ({sp2[0]} <= {sp1[1]})")
    for skey, days in hol.items():
        a, b = dt.date(int(skey[:4]), 6, 1), dt.date(int(skey[:4]) + 1, 6, 30)
        for x in days:
            if not a <= x <= b:
                errors.append(f"public_holidays.{skey}: {x} is outside {a}..{b}")
    for dept in rules["coverage_depts"]:
        if not any(sp[0] <= today <= sp[1] for sp, _ in spans.get(dept, [])):
            errors.append(f"hunting.{dept}: no season in force on {today} (enter the new order)")
    onf = (rules.get("onf") or {}).get("forests") or {}
    for fid, f in onf.items():
        if forests is not None and fid not in forests:
            errors.append(f"onf.{fid}: not in forests.json")
        dept = f.get("dept")
        for skey, s in (f.get("seasons") or {}).items():
            if not rules["hunting"].get(dept, {}).get(skey):
                errors.append(f"onf.{fid}.{skey}: no hunting.{dept}.{skey} to sit inside")
                continue
            span = [sp for sp, k in spans.get(dept, []) if k == skey]
            if not span:
                continue        # that season's own dates are bad: already reported above
            a, b = span[0]
            for x in s.get("days") or []:
                d = _date(x, f"onf.{fid}.{skey}.days", errors)
                if d and not a <= d <= b:
                    errors.append(f"onf.{fid}.{skey}: day {d} is outside the season {a}..{b}")
            src = s.get("source") or {}
            if not src.get("url"):
                errors.append(f"onf.{fid}.{skey}: missing source.url")
    lr = rules["lead_rule"]
    _mmdd(lr.get("from"), "lead_rule.from", errors)
    _mmdd(lr.get("to"), "lead_rule.to", errors)
    if not lr.get("ref"):
        errors.append("lead_rule: missing ref")
    v = rules["vineyards"]
    _mmdd(v["harvest_default"]["from"], "vineyards.harvest_default.from", errors)
    _mmdd(v["harvest_default"]["to"], "vineyards.harvest_default.to", errors)
    for y, h in (v.get("harvest") or {}).items():
        a = _date(h.get("from"), f"vineyards.harvest.{y}.from", errors)
        b = _date(h.get("to"), f"vineyards.harvest.{y}.to", errors)
        if a and b and (a > b or a.year != int(y)):
            errors.append(f"vineyards.harvest.{y}: bad window {a}..{b}")
    if str(today.year) not in (v.get("harvest") or {}):
        warnings.append(f"vineyards.harvest: no entry for {today.year}; the default window applies")
    return errors, warnings


def _in_mmdd(day, a, b):
    m1, d1 = (int(x) for x in a.split("-"))
    m2, d2 = (int(x) for x in b.split("-"))
    return (m1, d1) <= (day.month, day.day) <= (m2, d2)


def state_on(rules, dept, day, forest_id=None):
    """Today's hunting state for one département: level, the period, notes. The page's reference."""
    v = rules["vineyards"]
    h = (v.get("harvest") or {}).get(str(day.year))
    common = {
        "lead_rule": _in_mmdd(day, rules["lead_rule"]["from"], rules["lead_rule"]["to"]),
        "harvest": (dt.date.fromisoformat(h["from"]) <= day <= dt.date.fromisoformat(h["to"])) if h else
        _in_mmdd(day, v["harvest_default"]["from"], v["harvest_default"]["to"]),
    }
    seasons = rules["hunting"].get(dept) or {}
    cur = None
    for skey, s in seasons.items():
        a, b = season_span(s)
        if a <= day <= b:
            cur = (skey, s)
    if not cur:
        return {"level": "battue", "stale": True, "notes": ["règles de chasse non mises à jour pour cette saison"],
                **common}
    skey, s = cur
    active = [p for p in s["periods"]
              if dt.date.fromisoformat(p["from"]) <= day <= dt.date.fromisoformat(p["to"])]
    level = max((p["level"] for p in active), key=RANK.get, default="closed")
    hol = {dt.date.fromisoformat(x) for x in (rules.get("public_holidays") or {}).get(skey, [])}
    notes = []
    for r in s.get("day_rules") or []:
        if day.isoweekday() in r["weekdays"] and not (r.get("except_public_holidays") and day in hol):
            if r["scope"] == "all_shooting" and level != "closed":
                level = "suspended"
            notes.append(r["what"])
    out = {"level": level, "season": skey, "periods": [p["what"] for p in active], "notes": notes,
           "source": s["source"]["ref"]}
    f = ((rules.get("onf") or {}).get("forests") or {}).get(forest_id) if forest_id else None
    if f and skey in (f.get("seasons") or {}):
        out["onf_listed_day"] = day.isoformat() in f["seasons"][skey].get("days", [])
    out.update(common)
    return out


def chasse_value(rules, st, wood, forest_id=None):
    """0-100 Chasse value of one path on the day described by st (from state_on).

    wood is the path's woodland share (0-100). In an ONF forest with a calendar for the
    season, the woodland part uses onf_listed_day / onf_other_day instead of the level.
    """
    w = rules["weights"]
    level = st["level"]
    wood_w = w["woodland"][level]
    if "onf_listed_day" in st and level not in ("closed", "suspended") and not st.get("stale"):
        wood_w = w["onf_listed_day"] if st["onf_listed_day"] else w["onf_other_day"]
    f = wood / 100.0
    return int(math.floor(100 * (f * wood_w + (1 - f) * w["open_land"][level]) + 0.5))   # half up, like Math.round


def main(argv):
    region = argv[argv.index("--region") + 1] if "--region" in argv else "fr"
    with open(os.path.join(HERE, "regions", f"{region}_rules.json"), encoding="utf-8") as f:
        rules = json.load(f)
    if "--state" in argv:
        i = argv.index("--state")
        print(json.dumps(state_on(rules, argv[i + 1], dt.date.fromisoformat(argv[i + 2])),
                         ensure_ascii=False, indent=1))
        return 0
    today = dt.date.fromisoformat(argv[argv.index("--today") + 1]) if "--today" in argv else dt.date.today()
    forests = None
    if "--forests" in argv:
        with open(argv[argv.index("--forests") + 1], encoding="utf-8") as f:
            forests = json.load(f)
    errors, warnings = check(rules, today, forests)
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"{region}_rules.json: {len(errors)} error(s), {len(warnings)} warning(s) (today {today})")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
