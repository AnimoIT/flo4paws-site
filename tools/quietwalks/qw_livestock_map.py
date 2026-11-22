#!/usr/bin/env python3
"""S372 (R-B3c): map for Flo to check the red livestock paths round Cluny.

    python3 qw_livestock_map.py <dir holding out/> <output.html>   (after a French build)
"""
import csv
import glob
import json
import math
import os
import sys

SRC, OUTF = sys.argv[1], sys.argv[2]
C = (46.4346, 4.6595)          # Cluny
RADIUS_KM, SAMPLE_EACH, GAP_KM = 8, 15, 0.7
KX = 111.32 * math.cos(math.radians(C[0]))

grass = {r["way_id"]: int(r["grass_pct"] or 0) for r in csv.DictReader(open(os.path.join(SRC, "out/livestock_check.csv")))}
rows = [r for f in sorted(glob.glob(os.path.join(SRC, "out/finder/chunks/*.json"))) for r in json.load(open(f))]


def mid(r):
    lo, la = r[8][len(r[8]) // 2]
    return la, lo


def km(a, b):
    return math.hypot((a[0] - b[0]) * 110.54, (a[1] - b[1]) * KX)


sel = [r for r in rows if r[2] >= 60 and km(mid(r), C) <= RADIUS_KM]
paths = []
for r in sel:
    gp = grass.get(str(r[0]), 0)
    paths.append({"id": r[0], "lv": r[2], "g": gp, "w": r[9], "len": r[6], "name": r[7],
                  "on": gp >= 25, "geo": [[la, lo] for lo, la in r[8]]})
# sample: longest first in each group, spread out
picked = []
for on in (True, False):
    n = 0
    for p in sorted((p for p in paths if p["on"] == on), key=lambda p: (-p["len"], p["id"])):
        m = (p["geo"][len(p["geo"]) // 2])
        if p["len"] < 300 or any(km(m, q["geo"][len(q["geo"]) // 2]) < GAP_KM for q in picked):
            continue
        picked.append(p)
        n += 1
        if n == SAMPLE_EACH:
            break
picked.sort(key=lambda p: (-p["geo"][len(p["geo"]) // 2][0], p["geo"][len(p["geo"]) // 2][1]))  # north to south
for i, p in enumerate(picked, 1):
    p["n"] = i
on_n = sum(p["on"] for p in paths)

html = r"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chemins « bétail » autour de Cluny</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
*{box-sizing:border-box}body{margin:0;font:15px/1.45 system-ui,sans-serif;color:#1d2420;display:grid;grid-template-columns:minmax(0,1fr) 360px;height:100vh}
#map{height:100vh}aside{overflow:auto;padding:16px 18px;border-left:1px solid #ddd;background:#fafaf7}
h1{font-size:20px;margin:0 0 6px}p{margin:6px 0}.k{display:inline-block;width:22px;height:5px;border-radius:3px;vertical-align:middle;margin-right:6px}
ol{padding-left:22px;margin:8px 0}li{margin:6px 0}li .nm{color:#666;font-size:13px}
.b{display:inline-flex;gap:4px;margin-top:3px}.b button{font:13px system-ui;padding:5px 8px;border:1px solid #bbb;background:#fff;border-radius:6px;cursor:pointer}
.b button.on{background:#1d2420;color:#fff;border-color:#1d2420}
textarea{width:100%;height:120px;font:12px monospace}#copy{padding:8px 12px;font:14px system-ui;border-radius:6px;border:1px solid #1d2420;background:#1d2420;color:#fff;cursor:pointer}
.num{background:#fff;border:2px solid #1d2420;border-radius:50%;width:24px;height:24px;line-height:20px;text-align:center;font:bold 12px system-ui}
@media(max-width:800px){body{grid-template-columns:1fr;grid-template-rows:60vh auto;height:auto}#map{height:60vh}aside{border-left:0}}
</style></head><body>
<div id="map"></div>
<aside>
<h1>Chemins « bétail » autour de Cluny</h1>
<p>Flo, l'outil classe ces chemins comme « bétail probable » (rouge dans la carte des balades). Peux-tu nous dire, d'après ce que tu connais du terrain, s'il y a vraiment des vaches, chevaux ou moutons ?</p>
<p><span class="k" style="background:#c0392b"></span>sur une prairie permanente déclarée (PAC) : __ON__ chemins<br>
<span class="k" style="background:#8e44ad"></span>seulement « pré » dans OpenStreetMap : __OFF__ chemins</p>
<p>Il y en a __ALL__ dans un rayon de __R__ km. Inutile de tout regarder : réponds pour les <b>30 chemins numérotés</b> si tu peux (même « je ne sais pas » aide). Tu peux aussi cliquer sur n'importe quel autre chemin.</p>
<ol id="list"></ol>
<p><b>Autres chemins cliqués</b></p><ol id="extra"></ol>
<p><button id="copy">Copier mes réponses</button> puis colle-les dans un message à Ian.</p>
<textarea id="out" readonly></textarea>
<p style="font-size:12px;color:#666">Données : © contributeurs OpenStreetMap (ODbL) ; IGN – RPG prairies permanentes 2025, Licence Ouverte 2.0. Construit le 22 novembre 2026 (S372). Tes réponses restent dans ce navigateur jusqu'à ce que tu les copies.</p>
</aside>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
{
const P=__PATHS__;
const OPTS=[["oui","Bétail vu"],["non","Jamais vu"],["parfois","Parfois"],["?","Je ne sais pas"]];
let A={};try{A=JSON.parse(localStorage.getItem("s372_lv")||"{}")}catch(e){}
const save=()=>{try{localStorage.setItem("s372_lv",JSON.stringify(A))}catch(e){};render()};
const map=L.map("map").setView([__CLAT__,__CLON__],13);
L.tileLayer("https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© contributeurs OpenStreetMap"}).addTo(map);
const byId={};
const btns=id=>'<span class="b">'+OPTS.map(([v,t])=>`<button data-id="${id}" data-v="${v}" class="${A[id]===v?'on':''}">${t}</button>`).join('')+'</span>';
const desc=p=>`${p.name||'chemin'} · ${Math.round(p.len)} m · bétail ${p.lv} · prairie PAC ${p.g} % · bois ${p.w} %`;
for(const p of P){
  const l=L.polyline(p.geo,{color:p.on?"#c0392b":"#8e44ad",weight:p.n?6:3,opacity:p.n?.95:.6}).addTo(map);
  l.bindPopup(()=>`<b>${p.n?'n° '+p.n+' – ':''}chemin ${p.id}</b><br>${desc(p)}<br>${btns(p.id)}<br><a href="https://www.openstreetmap.org/way/${p.id}" target="_blank">voir sur OSM</a>`);
  byId[p.id]={p,l};
  if(p.n){const m=p.geo[Math.floor(p.geo.length/2)];
    L.marker(m,{icon:L.divIcon({className:"",html:`<div class="num">${p.n}</div>`,iconSize:[24,24]})}).on("click",()=>l.openPopup(m)).addTo(map)}
}
document.addEventListener("click",e=>{const b=e.target.closest(".b button");if(!b)return;const id=+b.dataset.id;A[id]=A[id]===b.dataset.v?undefined:b.dataset.v;if(!A[id])delete A[id];save();
  document.querySelectorAll(`.b button[data-id="${id}"]`).forEach(x=>x.classList.toggle("on",A[id]===x.dataset.v))});
function render(){
  const S=P.filter(p=>p.n).sort((a,b)=>a.n-b.n);
  document.getElementById("list").innerHTML=S.map(p=>`<li value="${p.n}"><a href="#" data-z="${p.id}">${p.on?'🟥':'🟪'} ${p.name||'chemin'}</a> <span class="nm">${Math.round(p.len)} m</span><br>${btns(p.id)}</li>`).join('');
  const X=Object.keys(A).map(Number).filter(id=>byId[id]&&!byId[id].p.n);
  document.getElementById("extra").innerHTML=X.map(id=>`<li><a href="#" data-z="${id}">chemin ${id}</a> : ${OPTS.find(o=>o[0]===A[id])[1]}</li>`).join('')||'<li style="list-style:none;color:#888">aucun</li>';
  document.getElementById("out").value="S372 bétail Cluny\n"+Object.entries(A).map(([id,v])=>{const p=byId[id].p;return `${p.n?'n°'+p.n:'-'}\t${id}\t${p.on?'PAC':'OSM'}\t${v}`}).join("\n");
}
document.addEventListener("click",e=>{const a=e.target.closest("a[data-z]");if(!a)return;e.preventDefault();const {p,l}=byId[+a.dataset.z];map.fitBounds(l.getBounds(),{maxZoom:16});l.openPopup(p.geo[Math.floor(p.geo.length/2)])});
document.getElementById("copy").addEventListener("click",async()=>{const t=document.getElementById("out");try{await navigator.clipboard.writeText(t.value)}catch(e){t.select()}});
render();
}
</script></body></html>"""
for k, v in {"__PATHS__": json.dumps(paths, separators=(",", ":"), ensure_ascii=False),
             "__ON__": str(on_n), "__OFF__": str(len(paths) - on_n), "__ALL__": str(len(paths)),
             "__R__": str(RADIUS_KM), "__CLAT__": str(C[0]), "__CLON__": str(C[1])}.items():
    html = html.replace(k, v)
open(OUTF, "w", encoding="utf-8").write(html)
print(f"{len(paths)} paths ({on_n} on RPG grass), {len(picked)} numbered "
      f"({sum(p['on'] for p in picked)} PAC / {sum(not p['on'] for p in picked)} OSM), {os.path.getsize(OUTF) / 1e6:.2f} MB")
