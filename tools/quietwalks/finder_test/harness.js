// S373/B5 finder harness: run a finder.js on a page in jsdom with a stub map and fixture data,
// script a visitor, and print a JSON record of everything the page shows.
//   node harness.js <page.html> <finder.js> <fixture.json> [extra-script.js ...] > record.json
// fixture.json: {"files": {url: json, ...}, "scenario": [...steps], "geo": [lat, lon]}
"use strict";
const fs = require("fs");
const crypto = require("crypto");
const { JSDOM } = require("jsdom");

const [pagePath, finderPath, fixturePath, ...extra] = process.argv.slice(2);
const fx = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
const html = fs.readFileSync(pagePath, "utf8").replace(/<script\b[^>]*src=[^>]*><\/script>/g, "");
const dom = new JSDOM(html, { runScripts: "outside-only", url: fx.origin || "https://www.flo4paws.co.uk/walks/quiet-walk-finder/" });
const w = dom.window;
const log = [];
const h = (o) => crypto.createHash("sha256").update(JSON.stringify(o)).digest("hex").slice(0, 16);

// ---- stub map library
class Bounds { constructor(a, b) { this.b = [a, b]; } extend(p) { this.b.push(p); return this; } }
class Popup {
  constructor(o) { this.o = o; } setHTML(s) { this.html = s; return this; }
  setLngLat(p) { this.ll = p; return this; } addTo() { log.push(["popup", this.ll && [this.ll.lng ?? this.ll[0], this.ll.lat ?? this.ll[1]], this.html]); return this; }
}
class Marker {
  constructor(o) { this.el = o.element; } setLngLat(p) { this.p = p; return this; } setPopup(pp) { this.pop = pp; return this; }
  addTo() { w.__markers.push(this); return this; } remove() { w.__markers = w.__markers.filter((m) => m !== this); }
}
class FakeMap {
  constructor(o) {
    this.o = o; this.sources = {}; this.layers = []; this.handlers = {}; w.__map = this;
    setTimeout(() => (this.handlers["load"] || []).forEach((f) => f()), 0);
  }
  on(ev, a, b) { const f = b || a; const k = b ? ev + ":" + a : ev; (this.handlers[k] = this.handlers[k] || []).push(f); return this; }
  addControl() {} isStyleLoaded() { return true; }
  getStyle() { return { layers: [{ id: "label1", type: "symbol" }] }; }
  addSource(id, s) { const self = this; this.sources[id] = { data: s.data, setData(d) { this.data = d; log.push(["setData", id, d.features.length, h(d)]); } }; }
  getSource(id) { return this.sources[id]; }
  addLayer(l, before) { this.layers.push([l.id, JSON.stringify(l.paint || {}), before]); }
  fitBounds(b, o) { log.push(["fitBounds", h(b.b), o]); } flyTo(o) { log.push(["flyTo", o]); }
  getCanvas() { return { style: {} }; } setLayoutProperty(...a) { log.push(["layout", ...a]); }
}
w.__markers = [];
w.maplibregl = { Map: FakeMap, Marker, Popup, LngLatBounds: Bounds, NavigationControl: class {}, addProtocol() {} };
w.pmtiles = { Protocol: class { constructor() { this.tile = () => {}; } } };
w.gtag = (...a) => log.push(["gtag", ...a]);
w.fetch = (url) => {
  const u = String(url).replace(/^https?:\/\/[^/]+/, "");
  log.push(["fetch", u]);
  if (!(u in fx.files)) return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error("404")) });
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(JSON.parse(JSON.stringify(fx.files[u]))) });
};
Object.defineProperty(w.navigator, "geolocation", { value: {
  getCurrentPosition: (ok) => setTimeout(() => ok({ coords: { latitude: fx.geo[0], longitude: fx.geo[1] } }), 0) } });
if (fx.today) {   // freeze "today" for date-dependent pages
  const T = new Date(fx.today + "T12:00:00Z").getTime(); const D = w.Date;
  w.Date = class extends D { constructor(...a) { super(...(a.length ? a : [T])); } static now() { return T; } };
}

function snap(label) {
  const $ = (id) => w.document.getElementById(id);
  const st = $("qwf-status");
  return {
    label,
    status: st && [st.textContent, st.className],
    list: $("qwf-list") && $("qwf-list").innerHTML,
    resultsHidden: $("qwf-results") && $("qwf-results").hidden,
    sliders: [...w.document.querySelectorAll(".qwf-slider")].map((s) => s.textContent + "=" + s.querySelector("input").value),
    banners: [...w.document.querySelectorAll(".qwf-banner")].map((b) => (b.hidden ? "hidden:" : "") + b.textContent.trim()),
    markers: w.__markers.map((m) => [m.p, m.el.className, m.el.textContent, m.el.title, m.pop && m.pop.html]),
    attrib: $("qwf-attrib") && $("qwf-attrib").textContent,
    layers: w.__map && w.__map.layers,
    log: log.splice(0),
  };
}
const tick = (ms = 20) => new Promise((r) => setTimeout(r, ms));

(async () => {
  for (const f of extra) w.eval(fs.readFileSync(f, "utf8"));
  w.eval(fs.readFileSync(finderPath, "utf8"));
  await tick(50);
  const out = [snap("loaded")];
  for (const step of fx.scenario) {
    const [act, a, b] = step;
    const $ = (id) => w.document.getElementById(id);
    if (act === "search") { $(fx.searchInput || "qwf-postcode").value = a; $("qwf-form").dispatchEvent(new w.Event("submit", { cancelable: true })); }
    else if (act === "slider") { const i = $("qwf-s-" + a); i.value = String(b); i.dispatchEvent(new w.Event("input")); }
    else if (act === "quietonly") { $("qwf-quietonly").checked = !!a; $("qwf-quietonly").dispatchEvent(new w.Event("change")); }
    else if (act === "locate") { $("qwf-locate").click(); }
    else if (act === "show") { const btn = w.document.querySelector('#qwf-list button[data-i="' + a + '"]'); if (btn) { btn.scrollIntoView = () => {}; $("qwf-map").scrollIntoView = () => {}; btn.click(); } }
    else if (act === "pathclick") {
      const feats = w.__map.sources["qwf-paths"].data.features; const f = feats[a % feats.length];
      (w.__map.handlers["click:qwf-paths"] || []).forEach((fn) => fn({ features: [f], lngLat: { lng: 1, lat: 2 } }));
    }
    else if (act === "pick") { const el = w.document.querySelector(a); if (el) el.click(); }
    await tick(60);
    out.push(snap(step.join(" ")));
  }
  process.stdout.write(JSON.stringify(out, null, 1));
})().catch((e) => { console.error(e); process.exit(2); });
