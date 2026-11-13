/* Flo 4 Paws Quiet Walk Finder.
   Data: /walks/finder-data/v1/ (index.json, chunks/<k>.json, starts.json) and
   /walks/finder-data/postcodes/<OUTWARD>.json, built by the quietwalks pipeline.
   Everything a visitor types stays in the browser: only the postcode district
   file (e.g. NG13.json) is requested. */
(function () {
  "use strict";
  var DATA = "/walks/finder-data/v1/";
  var PC = "/walks/finder-data/postcodes/";
  var BASEMAP = "/walks/finder-data/basemap.pmtiles";
  var GREEN = 75, AMBER = 55;
  var NEAR_KM = 20;          // look for start points within this distance
  var MIN_QUIET_KM = 3;      // a start point needs this much quieter path around it
  var SHOW = 8;              // start points listed

  // Trigger sliders: 0 not bothered .. 3 very worried
  var TRIGGERS = [
    { key: "pd", label: "Other dogs and people", def: 3 },
    { key: "lv", label: "Livestock (sheep, cattle, horses)", def: 2 },
    { key: "bk", label: "Bikes", def: 2 },
    { key: "bg", label: "Bangs (shooting, bird scarers)", def: 2 },
    { key: "tr", label: "Traffic noise", def: 1 }
  ];
  var LEVELS = ["Not bothered", "A little", "Worried", "Very worried"];
  var SEV = [0, 0.35, 0.7, 1.0];

  var $ = function (id) { return document.getElementById(id); };
  var state = { index: null, chunks: {}, rows: [], starts: null, point: null, map: null,
                markers: [], levels: {} };

  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

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
  function score(row) {
    // row: [id, pd, lv, bk, bg, tr, len, name, geom]; values 0-100
    var f = { pd: row[1] / 100, lv: row[2] / 100, bk: row[3] / 100, bg: row[4] / 100, tr: row[5] / 100 };
    var wsum = 0, mean = 0, worst = 0;
    TRIGGERS.forEach(function (t) {
      var s = SEV[state.levels[t.key]];
      wsum += s; mean += s * f[t.key];
      worst = Math.max(worst, s * f[t.key]);
    });
    if (wsum === 0) return 100;
    return Math.round(100 * (1 - (0.5 * worst + 0.5 * mean / wsum)));
  }

  // ---------------------------------------------------------------- sliders
  function buildSliders() {
    var box = $("qwf-sliders");
    TRIGGERS.forEach(function (t) {
      var saved = parseInt(load("qwf-" + t.key), 10);
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
        store("qwf-" + t.key, input.value);
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
    if (!pc) { status("That doesn't look like a UK postcode. Try something like NG13 8AB.", true); return; }
    var outward = pc.slice(0, -3);
    status("Looking up " + outward + " " + pc.slice(-3) + "…");
    getJSON(PC + outward + ".json").then(function (book) {
      var p = book[pc];
      if (!p) { status("I couldn't find that postcode. Check it, or use your location instead.", true); return; }
      setPoint([p[0], p[1]], outward + " " + pc.slice(-3));
    }).catch(function (e) {
      if (e.status === 404) status(notCovered(), true);
      else status("Sorry, the postcode lookup didn't load. Please try again.", true);
    });
  }

  function notCovered() {
    return "Sorry, the finder doesn't cover that area yet. It currently covers about " +
      Math.round(state.index.radius_m / 1609) + " miles around Bingham, Nottinghamshire.";
  }

  function useLocation() {
    if (!navigator.geolocation) { status("Your browser can't share a location. Please enter a postcode.", true); return; }
    status("Finding your location…");
    navigator.geolocation.getCurrentPosition(function (pos) {
      setPoint([pos.coords.latitude, pos.coords.longitude], "your location");
    }, function () {
      status("Location wasn't shared. Please enter your postcode instead.", true);
    }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 600000 });
  }

  function setPoint(pt, label) {
    var c = state.index.centre;
    if (km(pt, c) > state.index.radius_m / 1000 + 5) { status(notCovered(), true); return; }
    state.point = pt; state.label = label;
    status("Loading paths near " + label + "…");
    var keys = chunksNear(pt, NEAR_KM + state.index.start_radius_m / 1000 + 1);
    Promise.all([loadChunks(keys), state.starts ? null : getJSON(DATA + "starts.json").then(function (s) {
      state.starts = s.map(function (st) {   // decode path-number gaps once
        var n = 0, nums = st[4].map(function (d) { n += d; return n; });
        return { lat: st[0], lon: st[1], name: st[2], flags: st[3], nums: nums };
      });
    })]).then(function () {
      refresh(true);
    }).catch(function () {
      status("Sorry, the walk data didn't load. Please try again in a moment.", true);
    });
  }

  // ---------------------------------------------------------------- render
  var FLAG_TEXT = { big: "Large or busy car park", reserve: "Nature reserve nearby: check dog rules" };

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
    status(keep.length ? "Showing quieter paths and start points near " + state.label + "." :
      "No start points with enough quieter path within " + NEAR_KM + " km of " + state.label +
      ". Try easing a slider.", !keep.length);
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function renderList(keep) {
    var ol = $("qwf-list");
    ol.innerHTML = "";
    keep.forEach(function (r, i) {
      var li = document.createElement("li");
      var flags = r.st.flags.map(function (f) { return FLAG_TEXT[f] ? '<span class="qwf-flag">' + FLAG_TEXT[f] + "</span>" : ""; }).join("");
      var dir = "https://www.google.com/maps/dir/?api=1&destination=" + r.st.lat + "," + r.st.lon;
      li.innerHTML = '<div class="qwf-li-h"><span class="qwf-num">' + (i + 1) + '</span><b>' + esc(r.st.name) + "</b></div>" +
        '<p>' + (r.d * 0.6214).toFixed(1) + " miles away · " + (r.quietKm * 0.6214).toFixed(1) +
        " miles of quieter path within a mile · average score " + Math.round(r.mean) + "</p>" + flags +
        '<p class="qwf-acts"><button type="button" class="qwf-link" data-i="' + i + '">Show on map</button>' +
        ' <a class="qwf-link" href="' + dir + '" target="_blank" rel="noopener">Directions</a></p>';
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
      var h = document.createElement("div"); h.className = "qwf-home"; h.title = "You";
      state.home = new maplibregl.Marker({ element: h }).setLngLat([state.point[1], state.point[0]]).addTo(state.map);
    } else {
      state.home.setLngLat([state.point[1], state.point[0]]);
    }
    keep.forEach(function (r, i) {
      var el = document.createElement("div");
      el.className = "qwf-marker"; el.textContent = i + 1;
      var pop = new maplibregl.Popup({ offset: 14 }).setHTML(
        "<b>" + esc(r.st.name) + "</b><br>" + (r.quietKm * 0.6214).toFixed(1) + " miles of quieter path nearby<br>" +
        '<a href="https://www.google.com/maps/dir/?api=1&destination=' + r.st.lat + "," + r.st.lon +
        '" target="_blank" rel="noopener">Directions</a>');
      state.markers.push(new maplibregl.Marker({ element: el }).setLngLat([r.st.lon, r.st.lat]).setPopup(pop).addTo(state.map));
      bounds.extend([r.st.lon, r.st.lat]);
    });
    if (fit) state.map.fitBounds(bounds, { padding: 50, maxZoom: 13, duration: 600 });
  }

  // ---------------------------------------------------------------- map
  var TRIGGER_NAMES = { pd: "Dogs/people", lv: "Livestock", bk: "Bikes", bg: "Bangs", tr: "Traffic" };

  function pathPopup(e) {
    var f = e.features[0], r = state.rows[f.properties.n];
    if (!r) return;
    var nm = /^(footway|path|track|bridleway|cycleway|steps|public footpath|public bridleway)$/i.test(r[7]) || !r[7]
      ? "Path" : r[7];
    var bars = ["pd", "lv", "bk", "bg", "tr"].map(function (k, i) {
      return '<div class="qwf-bar"><span>' + TRIGGER_NAMES[k] + '</span><i style="width:' + r[i + 1] + '%"></i></div>';
    }).join("");
    new maplibregl.Popup().setLngLat(e.lngLat).setHTML(
      "<b>" + esc(nm) + "</b><br>Score " + f.properties.s + " · " + (r[6] / 1609).toFixed(2) + " miles" + bars
    ).addTo(state.map);
  }

  function initMap() {
    var protocol = new pmtiles.Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);
    var origin = location.origin;
    return getJSON("/walks/finder/basemap-style.json").then(function (style) {
      style.glyphs = origin + "/walks/finder/fonts/{fontstack}/{range}.pbf";
      style.sprite = origin + "/walks/finder/sprites/light";
      style.sources.protomaps.url = "pmtiles://" + origin + BASEMAP;
      var c = state.index.centre;
      var map = new maplibregl.Map({ container: "qwf-map", style: style, center: [c[1], c[0]], zoom: 9.5,
                                     attributionControl: { compact: true }, cooperativeGestures: true });
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
      map.on("load", function () {
        map.addSource("qwf-paths", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
        map.addLayer({ id: "qwf-paths-casing", type: "line", source: "qwf-paths",
          paint: { "line-color": "#ffffff", "line-width": ["interpolate", ["linear"], ["zoom"], 10, 2, 15, 6], "line-opacity": 0.8 } });
        map.addLayer({ id: "qwf-paths", type: "line", source: "qwf-paths",
          layout: { "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": ["step", ["get", "s"], "#c0392b", AMBER, "#e69500", GREEN, "#1e8a4c"],
            "line-width": ["interpolate", ["linear"], ["zoom"], 10, 1.2, 15, 4]
          } });
        map.on("click", "qwf-paths", pathPopup);
        map.on("mouseenter", "qwf-paths", function () { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", "qwf-paths", function () { map.getCanvas().style.cursor = ""; });
        refresh(true);
      });
      state.map = map;
    });
  }

  // ---------------------------------------------------------------- start
  function start() {
    if (!window.maplibregl || !window.pmtiles) { status("The map couldn't load in this browser.", true); return; }
    buildSliders();
    $("qwf-form").addEventListener("submit", function (e) { e.preventDefault(); findPostcode($("qwf-postcode").value); });
    $("qwf-locate").addEventListener("click", useLocation);
    $("qwf-quietonly").addEventListener("change", function () { refresh(false); });
    getJSON(DATA + "index.json").then(function (idx) {
      state.index = idx;
      $("qwf-attrib").insertAdjacentText("beforeend", " Data updated " + idx.built + ".");
      return initMap();
    }).catch(function () {
      status("Sorry, the walk finder isn't available right now. Please try again later.", true);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
