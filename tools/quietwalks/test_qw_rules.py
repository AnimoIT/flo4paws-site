#!/usr/bin/env python3
"""Tests for qw_rules.py: the real file passes, each check can fail, and state_on matches the orders.

    python3 test_qw_rules.py
"""
import copy
import datetime as dt
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qw_rules as q  # noqa: E402

with open(os.path.join(HERE, "regions", "fr_rules.json"), encoding="utf-8") as _f:
    RULES = json.load(_f)
TODAY = dt.date(2026, 11, 22)


def errs(rules, today=TODAY, forests=None):
    return q.check(rules, today, forests)[0]


class Check(unittest.TestCase):
    def test_real_file_passes(self):
        self.assertEqual(errs(RULES), [])

    def mutate(self, fn, expect, **kw):
        r = copy.deepcopy(RULES)
        fn(r)
        e = errs(r, **kw)
        self.assertTrue(any(expect in x for x in e), f"expected {expect!r} in {e}")

    def test_bad_date(self):
        self.mutate(lambda r: r["hunting"]["71"]["2026-27"]["periods"][0].update({"from": "2026-02-30"}), "bad date")

    def test_from_after_to(self):
        def f(r):
            p = r["hunting"]["69"]["2026-27"]["periods"][0]
            p["to"] = (dt.date.fromisoformat(p["from"]) - dt.timedelta(days=1)).isoformat()
        self.mutate(f, "is after")

    def test_unknown_level(self):
        self.mutate(lambda r: r["hunting"]["01"]["2026-27"]["periods"][0].update({"level": "busy"}), "not allowed")

    def test_overlapping_seasons(self):
        def f(r):
            s = copy.deepcopy(r["hunting"]["71"]["2026-27"])
            s["periods"] = [{"level": "open", "from": "2027-05-01", "to": "2028-02-28", "what": "x"}]
            r["hunting"]["71"]["2027-28"] = s
        self.mutate(f, "overlap")

    def test_missing_dept(self):
        self.mutate(lambda r: r["hunting"].pop("69"), "hunting.69: no season in force")

    def test_stale_season(self):
        self.assertTrue(any("no season in force" in x for x in errs(RULES, today=dt.date(2027, 8, 1))))

    def test_bad_weekday(self):
        self.mutate(lambda r: r["hunting"]["01"]["2026-27"]["day_rules"][0].update({"weekdays": [0]}), "weekdays")

    def test_holiday_outside_season(self):
        self.mutate(lambda r: r["public_holidays"]["2026-27"].append("2027-12-25"), "outside")

    def test_missing_source_url(self):
        self.mutate(lambda r: r["hunting"]["71"]["2026-27"]["source"].pop("url"), "missing url")

    def test_onf_day_outside_season(self):
        def f(r):
            r["onf"]["forests"]["FTEST"] = {"dept": "71", "seasons": {"2026-27": {
                "days": ["2027-09-01"], "source": {"url": "https://www.onf.fr/"}}}}
        self.mutate(f, "outside the season")

    def test_onf_unknown_forest(self):
        def f(r):
            r["onf"]["forests"]["FTEST"] = {"dept": "71", "seasons": {}}
        self.mutate(f, "not in forests.json", forests={})

    def test_onf_day_unlisted_and_listed(self):
        f = lambda d: q.state_on(RULES, "71", dt.date.fromisoformat(d), "F22134H").get("onf_listed_day")  # noqa: E731
        self.assertEqual((f("2026-11-23"), f("2026-11-24")), (True, False))   # Cluny: Mondays
        self.assertIsNone(q.state_on(RULES, "71", dt.date(2026, 11, 23), "F22559Q").get("onf_listed_day"))  # Pezanin: no calendar

    def test_real_onf_days_inside_season(self):
        self.assertEqual(len(RULES["onf"]["forests"]), 3)

    def test_bad_lead_rule(self):
        self.mutate(lambda r: r["lead_rule"].update({"from": "04-31"}), "bad month-day")


class State(unittest.TestCase):
    def lv(self, dept, day):
        return q.state_on(RULES, dept, dt.date.fromisoformat(day))["level"]

    def test_71_every_day(self):
        for d in ("2026-11-23", "2026-11-24", "2026-11-27", "2026-11-29"):   # Mon, Tue, Fri, Sun
            self.assertEqual(self.lv("71", d), "battue", d)

    def test_71_boar_battue_before_opening(self):
        self.assertEqual(self.lv("71", "2026-08-01"), "battue")
        self.assertEqual(self.lv("71", "2026-07-31"), "stalk")

    def test_71_spring(self):
        self.assertEqual(self.lv("71", "2027-04-15"), "stalk")

    def test_01_tuesday_friday(self):
        self.assertEqual(self.lv("01", "2026-11-24"), "suspended")   # Tue
        self.assertEqual(self.lv("01", "2026-11-27"), "suspended")   # Fri
        self.assertEqual(self.lv("01", "2026-11-25"), "open")        # Wed

    def test_01_holiday_friday_is_hunted(self):
        self.assertEqual(self.lv("01", "2026-12-25"), "open")        # Christmas, a Friday

    def test_69_tuesday_still_battue(self):
        self.assertEqual(self.lv("69", "2026-11-24"), "battue")

    def test_69_assumed_summer_and_spring(self):
        self.assertEqual(self.lv("69", "2026-07-10"), "stalk")
        self.assertEqual(self.lv("69", "2027-04-20"), "stalk")
        assumed = [p for p in RULES["hunting"]["69"]["2026-27"]["periods"] if p.get("assumed")]
        self.assertEqual(len(assumed), 2)

    def test_stale(self):
        s = q.state_on(RULES, "71", dt.date(2027, 7, 1))
        self.assertTrue(s.get("stale"))
        self.assertEqual(s["level"], "battue")

    def test_lead_rule_window(self):
        f = lambda d: q.state_on(RULES, "71", dt.date.fromisoformat(d))["lead_rule"]  # noqa: E731
        self.assertEqual((f("2027-04-14"), f("2027-04-15"), f("2027-06-30")), (False, True, True))


if __name__ == "__main__":
    unittest.main()
