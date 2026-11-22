/* Quiet Walk Finder: the French region (Mâcon–Cluny), FR and EN.
   Load order: the page sets window.QWF_PAGE = {lang, data, rules, communes, basemap, assets},
   then qwf-rules.js, this file, finder.js. This file sets window.QWF for finder.js.
   Adds: commune search, km, a sixth "Chasse" slider worked out from today's rules
   (prefectoral orders + ONF calendars), seasonal banners and popup notes, the harvest
   bump to "dogs and people" in vineyards. Nothing the visitor types leaves the browser;
   there is no analytics on soutenirmonchien.fr. */
(function () {
  "use strict";
  var P = window.QWF_PAGE || {};
  var LANG = P.lang === "en" ? "en" : "fr";
  var R = window.QWFRules;
  var DEPT_NAMES = { "71": "Saône-et-Loire", "69": "Rhône", "01": "Ain" };
  // Each préfecture's hunting page: the yearly orders are posted there, same address
  // every season. Linked from the hunting banner (S376).
  var HUNT_URLS = {
    "71": "https://www.saone-et-loire.gouv.fr/Actions-de-l-Etat/Environnement-risques-naturels-et-technologiques/Chasse-et-gestion-de-la-faune-sauvage-chassable/Gestion-de-la-faune-sauvage-chassable",
    "69": "https://www.rhone.gouv.fr/Actions-de-l-Etat/Environnement-transition-ecologique-risques-naturels-et-technologiques/Chasse-peche/Chasse/Arretes-prefectoraux/Ouverture-et-fermeture-de-la-chasse",
    "01": "https://www.ain.gouv.fr/Actions-de-l-Etat/Environnement-risques-naturels-et-technologiques/Chasse-Faune-sauvage"
  };

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  var now = new Date();
  var TODAY = P.today || (now.getFullYear() + "-" + pad(now.getMonth() + 1) + "-" + pad(now.getDate()));

  function num(x, d) { var s = x.toFixed(d); return LANG === "fr" ? s.replace(".", ",") : s; }
  function dmy(iso) {   // "2026-09-20" -> "20 sept. 2026" / "20 Sep 2026"
    var p = iso.split("-"), m = +p[1] - 1;
    var M = LANG === "fr" ? ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
                          : ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return (+p[2]) + " " + M[m] + " " + p[0];
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }

  var TXT = {
    fr: {
      levels: ["Pas gêné", "Un peu", "Inquiet", "Très inquiet"],
      triggers: { pd: "Autres chiens et promeneurs", lv: "Bétail (vaches, moutons, chevaux)", bk: "Vélos",
                  bg: "Détonations (tir, effaroucheurs)", tr: "Bruit de la circulation", ch: "Chasse" },
      short: { pd: "Chiens/gens", lv: "Bétail", bk: "Vélos", bg: "Détonations", tr: "Circulation", ch: "Chasse" },
      flags: { big: "Grand parking ou très fréquenté", reserve: "Réserve naturelle à proximité : vérifiez les règles pour les chiens",
               noparking: "Pas de parking cartographié" },
      pathWords: /^(footway|path|track|bridleway|cycleway|steps|chemin|sentier)$/i,
      path: "Chemin", you: "Vous",
      lookingUp: function (s) { return "Recherche de " + s + "…"; },
      notCovered: function () { return "Désolé, l'outil ne couvre pas encore ce secteur. Il couvre environ 30 km autour de Mâcon et Cluny."; },
      noGeo: "Votre navigateur ne peut pas partager votre position. Saisissez une commune ou un code postal.",
      finding: "Recherche de votre position…", yourLocation: "votre position",
      geoRefused: "Position non partagée. Saisissez plutôt une commune ou un code postal.",
      loadingNear: function (l) { return "Chargement des chemins près de " + l + "…"; },
      dataFailed: "Désolé, les données n'ont pas pu être chargées. Réessayez dans un instant.",
      showing: function (l) { return "Chemins plus calmes et points de départ près de " + l + "."; },
      noneNear: function (k, l) { return "Aucun point de départ avec assez de chemins calmes à moins de " + k + " km de " + l + ". Essayez d'assouplir un curseur."; },
      listLine: function (d, q, m) { return num(d, 1) + " km · " + num(q, 1) + " km de chemins plus calmes à moins de 1,5 km · note moyenne " + Math.round(m); },
      showOnMap: "Voir sur la carte", directions: "Itinéraire",
      quietNearby: function (q) { return num(q, 1) + " km de chemins plus calmes à proximité"; },
      popupLine: function (s, len) { return "Note " + s + " · " + num(len / 1000, 2) + " km"; },
      noMap: "La carte ne peut pas s'afficher dans ce navigateur.",
      unavailable: "Désolé, l'outil n'est pas disponible pour le moment. Réessayez plus tard.",
      updated: function (b) { return " Données mises à jour le " + dmy(b) + "."; },
      // France only
      notFound: "Je ne trouve pas cette commune. Vérifiez l'orthographe ou essayez le code postal.",
      choose: "Plusieurs communes correspondent : choisissez la vôtre.",
      empty: "Saisissez une commune ou un code postal.",
      parkingNear: "Parking près de ", parking: "Parking",
      seasonOpen: "Saison de chasse en cours.",
      seasonLines: function (n, st) {
        if (st.stale) return n + " : règles de chasse non mises à jour pour cette saison, prudence tous les jours";
        var lv = { battue: "battues possibles aujourd'hui", open: "chasse ouverte aujourd'hui", stalk: "chasse à l'affût ou à l'approche seulement",
                   suspended: "chasse à tir suspendue aujourd'hui (sauf exceptions)", closed: "pas de chasse aujourd'hui" }[st.level];
        return n + " : " + lv;
      },
      seasonAdvice: "En forêt et en lisière, cherchez les panneaux jaunes « Chasse en cours » ou « Battue en cours » et changez d'itinéraire.",
      rulesHint: "Cliquez sur un département pour lire les règles de chasse de la préfecture.",
      leadBanner: "Du 15 avril au 30 juin, en bois et forêts, les chiens doivent être tenus en laisse en dehors des allées forestières (arrêté du 16 mars 1955).",
      harvestBanner: "Vendanges : plus de monde, de machines et de tracteurs dans les vignes.",
      forest: function (name, dom) { return (dom ? "Forêt domaniale (ONF)" : "Forêt publique (ONF)") + " : " + esc(name); },
      onfToday: "Chasse prévue aujourd'hui dans cette forêt (calendrier ONF).",
      onfNot: "Pas de chasse ONF prévue aujourd'hui ici, mais prudence en lisière.",
      leadNote: "Laisse obligatoire hors des allées forestières jusqu'au 30 juin.",
      sprayNote: "Traitements possibles dans les vignes : évitez que votre chien broute l'herbe des rangs.",
      harvestNote: "Vendanges en cours dans les vignes proches."
    },
    en: {
      levels: ["Not bothered", "A little", "Worried", "Very worried"],
      triggers: { pd: "Other dogs and people", lv: "Livestock (cattle, sheep, horses)", bk: "Bikes",
                  bg: "Bangs (shooting, bird scarers)", tr: "Traffic noise", ch: "Hunting" },
      short: { pd: "Dogs/people", lv: "Livestock", bk: "Bikes", bg: "Bangs", tr: "Traffic", ch: "Hunting" },
      flags: { big: "Large or busy car park", reserve: "Nature reserve nearby: check the dog rules",
               noparking: "No mapped car park" },
      pathWords: /^(footway|path|track|bridleway|cycleway|steps|chemin|sentier)$/i,
      path: "Path", you: "You",
      lookingUp: function (s) { return "Looking up " + s + "…"; },
      notCovered: function () { return "Sorry, the finder doesn't cover that area yet. It covers about 30 km around Mâcon and Cluny."; },
      noGeo: "Your browser can't share a location. Please enter a town or postcode.",
      finding: "Finding your location…", yourLocation: "your location",
      geoRefused: "Location wasn't shared. Please enter a town or postcode instead.",
      loadingNear: function (l) { return "Loading paths near " + l + "…"; },
      dataFailed: "Sorry, the walk data didn't load. Please try again in a moment.",
      showing: function (l) { return "Showing quieter paths and start points near " + l + "."; },
      noneNear: function (k, l) { return "No start points with enough quieter path within " + k + " km of " + l + ". Try easing a slider."; },
      listLine: function (d, q, m) { return num(d, 1) + " km away · " + num(q, 1) + " km of quieter path within 1.5 km · average score " + Math.round(m); },
      showOnMap: "Show on map", directions: "Directions",
      quietNearby: function (q) { return num(q, 1) + " km of quieter path nearby"; },
      popupLine: function (s, len) { return "Score " + s + " · " + num(len / 1000, 2) + " km"; },
      noMap: "The map couldn't load in this browser.",
      unavailable: "Sorry, the walk finder isn't available right now. Please try again later.",
      updated: function (b) { return " Data updated " + dmy(b) + "."; },
      notFound: "I can't find that town. Check the spelling or try the postcode.",
      choose: "Several towns match: pick yours.",
      empty: "Please enter a town or a postcode.",
      parkingNear: "Parking near ", parking: "Parking",
      seasonOpen: "Hunting season is open.",
      seasonLines: function (n, st) {
        if (st.stale) return n + ": hunting rules not updated for this season, take care every day";
        var lv = { battue: "drive hunts possible today", open: "hunting open today", stalk: "stalking from hides only",
                   suspended: "shooting suspended today (with exceptions)", closed: "no hunting today" }[st.level];
        return n + ": " + lv;
      },
      seasonAdvice: "In and near woods, look out for yellow \"Chasse en cours\" or \"Battue en cours\" signs and change your route.",
      rulesHint: "Click a département to read the préfecture's hunting rules (in French).",
      leadBanner: "From 15 April to 30 June, dogs in woods and forests must be on a lead away from forest tracks (French law, 1955).",
      harvestBanner: "Grape harvest: more people, machines and tractors in the vineyards.",
      forest: function (name, dom) { return (dom ? "State forest (ONF)" : "Public forest (ONF)") + ": " + esc(name); },
      onfToday: "A hunt is planned in this forest today (ONF calendar).",
      onfNot: "No ONF hunt planned here today, but take care near the edges.",
      leadNote: "Dogs on a lead off the forest tracks until 30 June.",
      sprayNote: "Vines may have been sprayed: don't let your dog graze the grass between the rows.",
      harvestNote: "Grape harvest under way in nearby vineyards."
    }
  }[LANG];

  var rules = null, forests = {}, communes = [], states = {}, harvest = false;

  function stateFor(dept, forestId) {
    var k = dept + "|" + (forestId || "");
    if (!(k in states)) states[k] = R.stateOn(rules, dept || "71", TODAY, forestId || null);
    return states[k];
  }

  function chasse(row) {   // 0-100
    var st = stateFor(row[11], row[12]);
    return R.chasseValue(rules, st, row[9] || 0, row[12] || null);
  }

  // ---------------------------------------------------------------- places
  function norm(s) {
    return String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
      .replace(/\bst(e?)\b\.?/g, "saint$1").replace(/[-'’]/g, " ").replace(/\s+/g, " ").trim();
  }

  function findPlace(raw, api) {
    var q = String(raw || "").trim(), box = document.getElementById("qwf-choices");
    box.innerHTML = "";
    if (!q) { api.status(TXT.empty, true); return; }
    var hits;
    if (/^\d{5}$/.test(q)) {
      hits = communes.filter(function (c) { return c[2].indexOf(q) >= 0; });
    } else {
      var n = norm(q);
      hits = communes.filter(function (c) { return c.n === n; });
      if (!hits.length) hits = communes.filter(function (c) { return c.n.indexOf(n) === 0; });
      if (!hits.length && n.length >= 3) hits = communes.filter(function (c) { return c.n.indexOf(n) >= 0; });
    }
    hits.sort(function (a, b) { return b[5] - a[5]; });
    if (!hits.length) { api.status(TXT.notFound, true); return; }
    if (hits.length === 1) { go(hits[0], api); return; }
    api.status(TXT.choose);
    hits.slice(0, 8).forEach(function (c) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "qwf-choice";
      b.textContent = c[0] + " (" + c[2][0] + ")";
      b.addEventListener("click", function () { box.innerHTML = ""; go(c, api); });
      box.appendChild(b);
    });
  }

  function go(c, api) {
    api.setPoint([c[3], c[4]], c[0], "commune");   // setPoint reports the search itself
  }

  function nearestCommune(lat, lon, maxKm) {
    var best = null, bd = maxKm * maxKm;
    communes.forEach(function (c) {
      var dy = (c[3] - lat) * 110.54, dx = (c[4] - lon) * 76.8, d = dx * dx + dy * dy;
      if (d < bd) { bd = d; best = c; }
    });
    return best;
  }

  function near(place) {   // "Parking près de" + place, with French de + le/les -> du/des
    if (LANG === "fr") {
      if (/^Le /.test(place)) return "Parking près du " + place.slice(3);
      if (/^Les /.test(place)) return "Parking près des " + place.slice(4);
    }
    return TXT.parkingNear + place;
  }

  function startName(st) {
    var nm = st.name || "";
    var m = /^Parking near (.+)$/.exec(nm);
    var place = m ? m[1] : null;
    if (place && /^(le )?bourg$/i.test(place) || /^(le )?bourg$/i.test(nm)) {   // "Le Bourg" says nothing
      var c = nearestCommune(st.lat, st.lon, 3);
      if (c) { if (place) place = c[0]; else nm = c[0]; }
    }
    if (place) return near(place);
    return nm === "Parking" ? TXT.parking : nm;
  }

  // ---------------------------------------------------------------- notes
  function popupExtra(r) {
    var out = [];
    if (r[12] && forests[r[12]]) {
      var f = forests[r[12]];
      out.push(TXT.forest(f[0], f[1]));
      var st = stateFor(r[11], r[12]);
      if ("onf_listed_day" in st) out.push(st.onf_listed_day ? TXT.onfToday : TXT.onfNot);
    }
    var lr = stateFor(r[11], null);
    if (lr.lead_rule && r[9] > 0) out.push(TXT.leadNote);
    if (r[10] > 0) {
      var sp = rules.vineyards.spraying;
      var md = TODAY.slice(5);
      if (sp && sp.from <= md && md <= sp.to) out.push(TXT.sprayNote);
      if (harvest) out.push(TXT.harvestNote);
    }
    return out.length ? '<p class="qwf-notes">' + out.join("<br>") + "</p>" : "";
  }

  function value(key, row) {
    if (key === "ch") return chasse(row);
    if (key === "pd") {   // grape harvest: vine x 0.6 adds to people (spec §4.3)
      var v = row[1] + (harvest ? rules.vineyards.harvest_people_weight * (row[10] || 0) : 0);
      return Math.min(100, v);
    }
    return 0;
  }

  // ---------------------------------------------------------------- banners
  function deptLink(d) {   // new tab, so the visitor keeps their map and sliders
    return '<a href="' + esc(HUNT_URLS[d]) + '" target="_blank" rel="noopener noreferrer">' +
      esc(DEPT_NAMES[d] + " (" + d + ")") + "</a>";
  }

  function banners() {
    var box = document.getElementById("qwf-banners");
    if (!box) return;
    var html = [];
    var lines = ["71", "69", "01"].map(function (d) { return [d, stateFor(d, null)]; });
    var hunting = lines.some(function (x) { return x[1].stale || x[1].level !== "closed"; });
    if (hunting) {
      html.push('<div class="qwf-banner qwf-banner-hunt"><b>' + TXT.seasonOpen + "</b><ul>" +
        lines.map(function (x) {   // seasonLines("") gives just the separator and the level
          return "<li>" + deptLink(x[0]) + esc(TXT.seasonLines("", x[1])) + "</li>";
        }).join("") +
        "</ul><p>" + esc(TXT.seasonAdvice) + "</p><p>" + esc(TXT.rulesHint) + "</p></div>");
    }
    if (lines[0][1].lead_rule) html.push('<div class="qwf-banner qwf-banner-lead">' + esc(TXT.leadBanner) + "</div>");
    if (harvest) html.push('<div class="qwf-banner qwf-banner-harvest">' + esc(TXT.harvestBanner) + "</div>");
    box.innerHTML = html.join("");
  }

  // ---------------------------------------------------------------- config
  var ready = Promise.all([
    fetch(P.rules, { credentials: "omit" }).then(function (r) { if (!r.ok) throw new Error("rules"); return r.json(); }),
    fetch(P.communes, { credentials: "omit" }).then(function (r) { if (!r.ok) throw new Error("communes"); return r.json(); }),
    fetch(P.data + "forests.json", { credentials: "omit" }).then(function (r) { return r.ok ? r.json() : {}; })
  ]).then(function (res) {
    rules = res[0];
    communes = res[1].communes.map(function (c) { c.n = norm(c[0]); return c; });
    forests = res[2] || {};
    harvest = stateFor("71", null).harvest;
    banners();
  });

  window.QWF = {
    data: P.data, basemap: P.basemap, assets: P.assets, storagePrefix: "qwf-fr-",
    searchInput: "qwf-place",
    text: TXT,
    triggers: [{ key: "pd", def: 3 }, { key: "lv", def: 2 }, { key: "bk", def: 2 }, { key: "bg", def: 2 },
               { key: "tr", def: 1 }, { key: "ch", def: 3 }],
    own: { pd: true },
    value: value,
    findPlace: findPlace,
    startName: startName,
    popupExtra: popupExtra,
    ready: ready
  };
})();
