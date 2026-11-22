/* Quiet Walk Finder (France): today's hunting, lead-rule and harvest state from rules.json.
   A line-for-line port of state_on() and chasse_value() in tools/quietwalks/qw_rules.py;
   tools/quietwalks/test_qwf_rules_js.py checks the two agree on every day of the season.
   Dates are "YYYY-MM-DD" strings (French local date); no time zone arithmetic. */
(function (root) {
  "use strict";
  var RANK = { closed: 0, suspended: 1, stalk: 2, open: 3, battue: 4 };

  function isoWeekday(day) {   // 1 = Monday .. 7 = Sunday
    var p = day.split("-");
    var d = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])).getUTCDay();
    return d === 0 ? 7 : d;
  }

  function inMmdd(day, a, b) {   // "MM-DD" window, inclusive
    var md = day.slice(5);
    return a <= md && md <= b;
  }

  function seasonSpan(season) {
    var a = null, b = null;
    season.periods.forEach(function (p) {
      if (a === null || p.from < a) a = p.from;
      if (b === null || p.to > b) b = p.to;
    });
    return [a, b];
  }

  function stateOn(rules, dept, day, forestId) {
    var v = rules.vineyards;
    var h = (v.harvest || {})[day.slice(0, 4)];
    var common = {
      lead_rule: inMmdd(day, rules.lead_rule.from, rules.lead_rule.to),
      harvest: h ? (h.from <= day && day <= h.to) : inMmdd(day, v.harvest_default.from, v.harvest_default.to)
    };
    var seasons = rules.hunting[dept] || {};
    var cur = null;
    Object.keys(seasons).forEach(function (k) {
      var sp = seasonSpan(seasons[k]);
      if (sp[0] <= day && day <= sp[1]) cur = k;
    });
    var out;
    if (!cur) {
      out = { level: "battue", stale: true, notes: ["règles de chasse non mises à jour pour cette saison"] };
    } else {
      var s = seasons[cur];
      var active = s.periods.filter(function (p) { return p.from <= day && day <= p.to; });
      var level = "closed";
      active.forEach(function (p) { if (RANK[p.level] > RANK[level]) level = p.level; });
      var hol = (rules.public_holidays || {})[cur] || [];
      var notes = [];
      (s.day_rules || []).forEach(function (r) {
        if (r.weekdays.indexOf(isoWeekday(day)) >= 0 && !(r.except_public_holidays && hol.indexOf(day) >= 0)) {
          if (r.scope === "all_shooting" && level !== "closed") level = "suspended";
          notes.push(r.what);
        }
      });
      out = { level: level, season: cur, periods: active.map(function (p) { return p.what; }), notes: notes,
              source: s.source.ref, from: seasonSpan(s)[0], to: seasonSpan(s)[1] };
      var f = forestId ? ((rules.onf || {}).forests || {})[forestId] : null;
      if (f && f.seasons && f.seasons[cur]) out.onf_listed_day = f.seasons[cur].days.indexOf(day) >= 0;
    }
    out.lead_rule = common.lead_rule;
    out.harvest = common.harvest;
    return out;
  }

  function chasseValue(rules, st, wood, forestId) {
    var w = rules.weights, level = st.level;
    var woodW = w.woodland[level];
    if ("onf_listed_day" in st && level !== "closed" && level !== "suspended" && !st.stale)
      woodW = st.onf_listed_day ? w.onf_listed_day : w.onf_other_day;
    var f = wood / 100;
    return Math.round(100 * (f * woodW + (1 - f) * w.open_land[level]));
  }

  var api = { stateOn: stateOn, chasseValue: chasseValue, isoWeekday: isoWeekday, seasonSpan: seasonSpan };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.QWFRules = api;
})(this);
