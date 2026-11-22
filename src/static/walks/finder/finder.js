/* Flo 4 Paws Quiet Walk Finder: shared core (UK and France).
   Data: <data>/index.json, chunks/<k>.json, starts.json, built by the quietwalks pipeline;
   UK places: /walks/finder-data/postcodes/<OUTWARD>.json.
   Everything a visitor types stays in the browser: only the postcode district
   file (e.g. NG13.json) or the region's place file is requested.
   Analytics (14 Nov 2026): four GA events say only that something happened --
   qwf_search {method}, qwf_not_covered {method}, qwf_results {count}, qwf_directions.
   No postcode, location, area or slider answer is ever sent. gtag and the visitor's
   consent choice are set up by the page head (Consent Mode), not here; pages without
   gtag (soutenirmonchien.fr) send nothing.
   Regions (S373): a page may set window.QWF before this script to change data paths,
   units, text, sliders, place search and popups. With no window.QWF this is the UK
   finder, unchanged. See qwf-fr.js for the French region. */
(function () {
  "use strict";
  var CFG = window.QWF || {};
  var DATA = CFG.data || "/walks/finder-data/v1/";
  var PC = "/walks/finder-data/postcodes/";
  var BASEMAP = CFG.basemap || "/walks/finder-data/basemap.pmtiles";
  var ASSETS = CFG.assets || "/walks/finder/";
  var GREEN = 75, AMBER = 55;
  var NEAR_KM = 20;          // look for start points within this distance
  var MIN_QUIET_KM = 3;      // a start point needs this much quieter path around it
  var SHOW = 8;              // start points listed
  var COLS = { pd: 1, lv: 2, bk: 3, bg: 4, tr: 5 };   // built-in trigger -> row column
  var OWN = CFG.own || {};   // built-in triggers a region computes itself (CFG.value)

  // UK English text. A region's CFG.text replaces any of these.
  var T = {
    levels: ["Not bothered", "A little", "Worried", "Very worried"],
    triggers: { pd: "Other dogs and people", lv: "Livestock (sheep, cattle, horses)", bk: "Bikes",
                bg: "Bangs (shooting, bird scarers)", tr: "Traffic noise" },
    short: { pd: "Dogs/people", lv: "Livestock", bk: "Bikes", bg: "Bangs", tr: "Traffic" },
    flags: { big: "Large or busy car park", reserve: "Nature reserve nearby: check dog rules" },
    pathWords: /^(footway|path|track|bridleway|cycleway|steps|public footpath|public bridleway)$/i,
    path: "Path",
    you: "You",
    notPostcode: "That doesn't look like a UK postcode. Try something like NG13 8AB.",
    lookingUp: function (s) { return "Looking up " + s + "…"; },
    noPostcode: "I couldn't find that postcode. Check it, or use your location instead.",
    lookupFailed: "Sorry, the postcode lookup didn't load. Please try again.",
    notCovered: function (idx) {
      return "Sorry, the finder doesn't cover that area yet. It currently covers about " +
        Math.round(idx.radius_m / 1609) + " miles around Bingham, Nottinghamshire.";
    },
    noGeo: "Your browser can't share a location. Please enter a postcode.",
    finding: "Finding your location…",
    yourLocation: "your location",
    geoRefused: "Location wasn't shared. Please enter your postcode instead.",
    loadingNear: function (l) { return "Loading paths near " + l + "…"; },
    dataFailed: "Sorry, the walk data didn't load. Please try again in a moment.",
    showing: function (l) { return "Showing quieter paths and start points near " + l + "."; },
    noneNear: function (km, l) {
      return "No start points with enough quieter path within " + km + " km of " + l + ". Try easing a slider.";
    },
    listLine: function (dKm, quietKm, mean) {
      return (dKm * 0.6214).toFixed(1) + " miles away · " + (quietKm * 0.6214).toFixed(1) +
        " miles of quieter path within a mile · average score " + Math.round(mean);
    },
    showOnMap: "Show on map",
    directions: "Directions",
    quietNearby: function (quietKm) { return (quietKm * 0.6214).toFixed(1) + " miles of quieter path nearby"; },
    popupLine: function (s, lenM) { return "Score " + s + " · " + (lenM / 1609).toFixed(2) + " miles"; },
    noMap: "The map couldn't load in this browser.",
    unavailable: "Sorry, the walk finder isn't available right now. Please try again later.",
    updated: function (built) { return " Data updated " + built + "."; }
  };
  Object.keys(CFG.text || {}).forEach(function (k) { T[k] = CFG.text[k]; });

  // Trigger sliders: 0 not bothered .. 3 very worried
  var TRIGGERS = (CFG.triggers || [
    { key: "pd", def: 3 }, { key: "lv", def: 2 }, { key: "bk", def: 2 }, { key: "bg", def: 2 }, { key: "tr", def: 1 }
  ]).map(function (t) { return { key: t.key, label: t.label || T.triggers[t.key], def: t.def }; });
  var LEVELS = T.levels;
  var SEV = [0, 0.35, 0.7, 1.0];

  var $ = function (id) { return document.getElementById(id); };
  var state = { index: null, chunks: {}, rows: [], starts: null, point: null, map: null,
                markers: [], levels: {} };

  function track(name, params) {
    try { if (typeof window.gtag === "function") window.gtag("event", name, params || {}); } catch (e) { /* never break the finder */ }
  }

  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  var KEY = CFG.storagePrefix || "qwf-";

  function status(msg, isErr) {
    var s = $("qwf-status");
    s.textContent = msg || "";
    s.className = "qwf-status" + (isErr ? " err" : "");
  }

  function km(a, b) {   // [lat, lon] pairs
    var R = 6371, dLat = (b[0] - a[0]) * Math.PI / 180, dLon = (b[1] - a[1]) * Math.PI / 180;
    var la1 = a[0] * Math.PI / 180, la2 = b[0] * Math.PI / 180;
    var h = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  // ---------------------------------------------------------------- scoring
  function value(row, key) {   // 0-1
    return COLS[key] && !OWN[key] ? row[COLS[key]] / 100 : CFG.value(key, row) / 100;
  }

  function score(row) {
    // row: [id, pd, lv, bk, bg, tr, len, name, geom, ...region fields]; values 0-100
    var wsum = 0, mean = 0, worst = 0;
    TRIGGERS.forEach(function (t) {
      var s = SEV[state.levels[t.key]], f = value(row, t.key);
      wsum += s; mean += s * f;
      worst = Math.max(worst, s * f);
    });
    if (wsum === 0) return 100;
    return Math.round(100 * (1 - (0.5 * worst + 0.5 * mean / wsum)));
  }

  // ---------------------------------------------------------------- sliders
  function buildSliders() {
    var box = $("qwf-sliders");
    TRIGGERS.forEach(function (t) {
      var saved = parseInt(load(KEY + t.key), 10);
      state.levels[t.key] = isNaN(saved) ? t.def : Math.max(0, Math.min(3, saved));
      var id = "qwf-s-" + t.key;
      var wrap = document.createElement("div");
      wrap.className = "qwf-slider";
      wrap.innerHTML = '<label for="' + id + '">' + t.label + '</label>' +
        '<input type="range" min="0" max="3" step="1" id="' + id + '" value="' + state.levels[t.key] + '">' +
        '<span class="qwf-lvl" id="' + id + '-v"></span>';
      box.appendChild(wrap);
      var input = wrap.querySelector("input"), out = wrap.querySelector(".qwf-lvl");
      var show = function () {
        out.textContent = LEVELS[state.levels[t.key]];
        input.setAttribute("aria-valuetext", LEVELS[state.levels[t.key]]);
      };
      show();
      input.addEventListener("input", function () {
        state.levels[t.key] = parseInt(input.value, 10);
        store(KEY + t.key, input.value);
        show();
        refresh();
      });
    });
  }

  // ---------------------------------------------------------------- data
  function getJSON(url) {
    return fetch(url, { credentials: "omit" }).then(function (r) {
      if (!r.ok) { var e = new Error("HTTP " + r.status); e.status = r.status; throw e; }
      return r.json();
    });
  }

  function chunksNear(pt, radiusKm) {
    var keys = [];
    Object.keys(state.index.chunks).forEach(function (k) {
      var b = state.index.chunks[k].bbox;   // [minLon, minLat, maxLon, maxLat]
      var lat = Math.max(b[1], Math.min(pt[0], b[3])), lon = Math.max(b[0], Math.min(pt[1], b[2]));
      if (km(pt, [lat, lon]) <= radiusKm) keys.push(k);
    });
    return keys;
  }

  function loadChunks(keys) {
    var todo = keys.filter(function (k) { return !state.chunks[k]; });
    return Promise.all(todo.map(function (k) {
      return getJSON(DATA + "chunks/" + k + ".json").then(function (rows) {
        state.chunks[k] = rows;
        var base = state.index.chunks[k].base;
        rows.forEach(function (r, i) { state.rows[base + i] = r; });
      });
    }));
  }

  // ---------------------------------------------------------------- location
  function normalisePostcode(v) {
    var s = (v || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
    return /^[A-Z]{1,2}[0-9][A-Z0-9]?[0-9][A-Z]{2}$/.test(s) ? s : null;
  }

  function findPostcode(raw) {
    var pc = normalisePostcode(raw);
    if (!pc) { status(T.notPostcode, true); return; }
    var outward = pc.slice(0, -3);
    status(T.lookingUp(outward + " " + pc.slice(-3)));
    getJSON(PC + outward + ".json").then(function (book) {
      var p = book[pc];
      if (!p) { status(T.noPostcode, true); return; }
      setPoint([p[0], p[1]], outward + " " + pc.slice(-3), "postcode");
    }).catch(function (e) {
      if (e.status === 404) { track("qwf_not_covered", { method: "postcode" }); status(notCovered(), true); }
      else status(T.lookupFailed, true);
    });
  }

  function notCovered() { return T.notCovered(state.index); }

  function useLocation() {
    if (!navigator.geolocation) { status(T.noGeo, true); return; }
    status(T.finding);
    navigator.geolocation.getCurrentPosition(function (pos) {
      setPoint([pos.coords.latitude, pos.coords.longitude], T.yourLocation, "location");
    }, function () {
      status(T.geoRefused, true);
    }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 600000 });
  }

  function setPoint(pt, label, method) {
    var c = state.index.centre;
    if (km(pt, c) > state.index.radius_m / 1000 + 5) { track("qwf_not_covered", { method: method }); status(notCovered(), true); return; }
    track("qwf_search", { method: method });
    state.point = pt; state.label = label;
    status(T.loadingNear(label));
    var keys = chunksNear(pt, NEAR_KM + state.index.start_radius_m / 1000 + 1);
    Promise.all([loadChunks(keys), state.starts ? null : getJSON(DATA + "starts.json").then(function (s) {
      state.starts = s.map(function (st) {   // decode path-number gaps once
        var n = 0, nums = st[4].map(function (d) { n += d; return n; });
        return { lat: st[0], lon: st[1], name: st[2], flags: st[3], nums: nums };
      });
    })]).then(function () {
      refresh(true);
    }).catch(function () {
      status(T.dataFailed, true);
    });
  }

  // ---------------------------------------------------------------- render
  function refresh(fit) {
    if (!state.point || !state.map || !state.map.isStyleLoaded()) return;
    var quietOnly = $("qwf-quietonly").checked;
    var feats = [];
    var scores = {};
    Object.keys(state.chunks).forEach(function (k) {
      var base = state.index.chunks[k].base;
      state.chunks[k].forEach(function (r, i) {
        var s = score(r);
        scores[base + i] = s;
        if (quietOnly && s < GREEN) return;
        feats.push({ type: "Feature", properties: { s: s, n: base + i },
                     geometry: { type: "LineString", coordinates: r[8] } });
      });
    });
    state.map.getSource("qwf-paths").setData({ type: "FeatureCollection", features: feats });

    // rank start points near the visitor
    var ranked = [];
    state.starts.forEach(function (st) {
      var d = km(state.point, [st.lat, st.lon]);
      if (d > NEAR_KM) return;
      var tot = 0, w = 0, quiet = 0;
      st.nums.forEach(function (n) {
        var r = state.rows[n];
        if (!r) return;
        var s = scores[n] !== undefined ? scores[n] : score(r);
        tot += r[6]; w += r[6] * s;
        if (s >= GREEN) quiet += r[6];
      });
      if (!tot || quiet / 1000 < MIN_QUIET_KM) return;
      var mean = w / tot;
      ranked.push({ st: st, d: d, mean: mean, quietKm: quiet / 1000,
                    rank: mean - 1.0 * d - (st.flags.indexOf("big") >= 0 ? 8 : 0) });
    });
    ranked.sort(function (a, b) { return b.rank - a.rank; });
    var keep = [];
    ranked.forEach(function (r) {   // one start per walk area
      if (keep.length < SHOW && keep.every(function (k) { return km([k.st.lat, k.st.lon], [r.st.lat, r.st.lon]) > 1; }))
        keep.push(r);
    });
    renderList(keep);
    renderMarkers(keep, fit);
    if (fit) track("qwf_results", { count: keep.length });   // a new search, not a slider change
    status(keep.length ? T.showing(state.label) : T.noneNear(NEAR_KM, state.label), !keep.length);
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function startName(st) { return CFG.startName ? CFG.startName(st) : st.name; }

  function renderList(keep) {
    var ol = $("qwf-list");
    ol.innerHTML = "";
    keep.forEach(function (r, i) {
      var li = document.createElement("li");
      var flags = r.st.flags.map(function (f) { return T.flags[f] ? '<span class="qwf-flag">' + T.flags[f] + "</span>" : ""; }).join("");
      var dir = "https://www.google.com/maps/dir/?api=1&destination=" + r.st.lat + "," + r.st.lon;
      li.innerHTML = '<div class="qwf-li-h"><span class="qwf-num">' + (i + 1) + '</span><b>' + esc(startName(r.st)) + "</b></div>" +
        '<p>' + T.listLine(r.d, r.quietKm, r.mean) + "</p>" + flags +
        '<p class="qwf-acts"><button type="button" class="qwf-link" data-i="' + i + '">' + T.showOnMap + '</button>' +
        ' <a class="qwf-link" href="' + dir + '" target="_blank" rel="noopener">' + T.directions + '</a></p>';
      ol.appendChild(li);
    });
    ol.querySelectorAll("button[data-i]").forEach(function (b) {
      b.addEventListener("click", function () {
        var r = keep[+b.getAttribute("data-i")];
        state.map.flyTo({ center: [r.st.lon, r.st.lat], zoom: 14 });
        $("qwf-map").scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
    $("qwf-results").hidden = !keep.length;
  }

  function renderMarkers(keep, fit) {
    state.markers.forEach(function (m) { m.remove(); });
    state.markers = [];
    var bounds = new maplibregl.LngLatBounds([state.point[1], state.point[0]], [state.point[1], state.point[0]]);
    if (!state.home) {
      var h = document.createElement("div"); h.className = "qwf-home"; h.title = T.you;
      state.home = new maplibregl.Marker({ element: h }).setLngLat([state.point[1], state.point[0]]).addTo(state.map);
    } else {
      state.home.setLngLat([state.point[1], state.point[0]]);
    }
    keep.forEach(function (r, i) {
      var el = document.createElement("div");
      el.className = "qwf-marker"; el.textContent = i + 1;
      var pop = new maplibregl.Popup({ offset: 14 }).setHTML(
        "<b>" + esc(startName(r.st)) + "</b><br>" + T.quietNearby(r.quietKm) + "<br>" +
        '<a href="https://www.google.com/maps/dir/?api=1&destination=' + r.st.lat + "," + r.st.lon +
        '" target="_blank" rel="noopener">' + T.directions + '</a>');
      state.markers.push(new maplibregl.Marker({ element: el }).setLngLat([r.st.lon, r.st.lat]).setPopup(pop).addTo(state.map));
      bounds.extend([r.st.lon, r.st.lat]);
    });
    if (fit) state.map.fitBounds(bounds, { padding: 50, maxZoom: 13, duration: 600 });
  }

  // ---------------------------------------------------------------- map
  function pathPopup(e) {
    var f = e.features[0], r = state.rows[f.properties.n];
    if (!r) return;
    var nm = T.pathWords.test(r[7]) || !r[7] ? T.path : r[7];
    var bars = TRIGGERS.map(function (t) {
      return '<div class="qwf-bar"><span>' + (T.short[t.key] || t.label) + '</span><i style="width:' +
        (COLS[t.key] && !OWN[t.key] ? r[COLS[t.key]] : Math.round(CFG.value(t.key, r))) + '%"></i></div>';
    }).join("");
    new maplibregl.Popup().setLngLat(e.lngLat).setHTML(
      "<b>" + esc(nm) + "</b><br>" + T.popupLine(f.properties.s, r[6]) + bars + (CFG.popupExtra ? CFG.popupExtra(r) : "")
    ).addTo(state.map);
  }

  function initMap() {
    var protocol = new pmtiles.Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);
    var abs = function (u) { return new URL(u, location.href).href; };   // "/x/" or a relative path
    return getJSON(ASSETS + "basemap-style.json").then(function (style) {
      style.glyphs = abs(ASSETS) + "fonts/{fontstack}/{range}.pbf";
      style.sprite = abs(ASSETS) + "sprites/light";
      style.sources.protomaps.url = "pmtiles://" + abs(BASEMAP);
      var c = state.index.centre;
      var map = new maplibregl.Map({ container: "qwf-map", style: style, center: [c[1], c[0]], zoom: 9.5,
                                     attributionControl: { compact: true }, cooperativeGestures: true });
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
      map.on("load", function () {
        map.addSource("qwf-paths", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
        // draw paths beneath the basemap's labels so place names stay readable
        var firstLabel = (map.getStyle().layers.filter(function (l) { return l.type === "symbol"; })[0] || {}).id;
        map.addLayer({ id: "qwf-paths-casing", type: "line", source: "qwf-paths",
          paint: { "line-color": "#ffffff", "line-width": ["interpolate", ["linear"], ["zoom"], 10, 2, 15, 6], "line-opacity": 0.8 } }, firstLabel);
        map.addLayer({ id: "qwf-paths", type: "line", source: "qwf-paths",
          layout: { "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": ["step", ["get", "s"], "#c0392b", AMBER, "#e69500", GREEN, "#1e8a4c"],
            "line-width": ["interpolate", ["linear"], ["zoom"], 10, 1.2, 15, 4]
          } }, firstLabel);
        map.on("click", "qwf-paths", pathPopup);
        map.on("mouseenter", "qwf-paths", function () { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", "qwf-paths", function () { map.getCanvas().style.cursor = ""; });
        refresh(true);
      });
      state.map = map;
    });
  }

  // ---------------------------------------------------------------- start
  var api = { setPoint: function (pt, label, method) { setPoint(pt, label, method); }, status: status,
              track: track, getJSON: getJSON, refresh: function () { refresh(false); } };

  function begin() {
    buildSliders();
    var find = CFG.findPlace ? function (raw) { CFG.findPlace(raw, api); } : findPostcode;
    $("qwf-form").addEventListener("submit", function (e) { e.preventDefault(); find($(CFG.searchInput || "qwf-postcode").value); });
    $("qwf-locate").addEventListener("click", useLocation);
    $("qwf-quietonly").addEventListener("change", function () { refresh(false); });
    // Directions links live in the list and in map popups; one listener catches both
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest('a[href^="https://www.google.com/maps/dir/"]');
      if (a) track("qwf_directions");
    });
    getJSON(DATA + "index.json").then(function (idx) {
      state.index = idx;
      $("qwf-attrib").insertAdjacentText("beforeend", T.updated(idx.built));
      return initMap();
    }).catch(function () {
      status(T.unavailable, true);
    });
  }

  function start() {
    if (!window.maplibregl || !window.pmtiles) { status(T.noMap, true); return; }
    if (CFG.ready) CFG.ready.then(begin, function () { status(T.unavailable, true); });
    else begin();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
