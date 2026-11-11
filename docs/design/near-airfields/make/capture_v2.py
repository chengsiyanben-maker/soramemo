# -*- coding: utf-8 -*-
# 地図の写真を撮る。今のアプリ（web/ を http://localhost:8765/ で開く）のデモに入り、位置を入れてホームの地図だけを撮る。
# アプリのコードは変えない（撮るときにページの中で印を足して、シート・タブ帯を見えなくするだけ）。
# 使い方：(cd web && python3 -m http.server 8765 &) ; python3 capture.py ; python3 make_near.py
import asyncio, os, sys, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_near_v2 as make_near
OUT = make_near.OUT
MAPS = os.path.join(HERE, 'maps'); os.makedirs(MAPS, exist_ok=True)

P = {'ushiku': (35.975, 140.149), 'ryu': (35.9063, 140.2422), 'tokyo': (35.681, 139.767), 'osaka': (34.7025, 135.4959), 'kazo': (36.1310, 139.6017)}
F = {'竜ヶ崎飛行場': (35.906276, 140.242152, 'field'), '大利根飛行場': (35.85937, 140.241219, 'field'), '八尾空港': (34.596298, 135.602997, 'field'),
     '加須滑空場': (36.1866, 139.61748, 'glider'), '大利根滑空場': (36.16458, 139.67117, 'glider'), '羽生滑空場': (36.19942, 139.6031, 'glider'),
     '板倉滑空場': (36.26616, 139.63388, 'glider'), '妻沼第2滑空場': (36.20044, 139.43405, 'glider'), 'ホンダエアポート': (35.97633, 139.524125, 'field'), '妻沼滑空場': (36.21338, 139.41697, 'glider')}
JOBS = [  # 地図の名前, 位置, 番外編の印, 高さを測るページ, 夜
 ('s02-v2', 'ushiku', ['竜ヶ崎飛行場', '大利根飛行場'], '02-home-near-v2.html', False),
 ('s03-v2', 'ryu', ['大利根飛行場'], '03-home-in-field-v2.html', False),
 ('s04-v2', 'tokyo', [], '04-home-none-v2.html', False),
 ('s06-v2', 'osaka', ['八尾空港'], '06-home-yao-v2.html', False),
 ('s07-v2', 'kazo', ['加須滑空場', '大利根滑空場', '羽生滑空場', '板倉滑空場', '妻沼第2滑空場', 'ホンダエアポート', '妻沼滑空場'], '07-home-kazo-v2.html', False),
 ('s02n-v2', 'ushiku', ['竜ヶ崎飛行場', '大利根飛行場'], '02-home-near-v2-night.html', True),
]
INJ_CSS = """
#homeSheet,nav.tabs,.leaflet-control-zoom,#homeEdge{visibility:hidden!important}
.nf-l{position:absolute;left:8px;top:-11px;white-space:nowrap;font:500 13px/22px var(--gothic);color:#4B5563;padding:0 4px;
 text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff,0 0 2px #fff}
html.nt .leaflet-tile-pane{filter:invert(1) hue-rotate(180deg) brightness(.8) contrast(1.05) saturate(.25)!important}html.nt .maplibregl-canvas{filter:none!important}
html.nt .hmap,html.nt .leaflet-container{background:#05070B!important}
.topzone{visibility:hidden!important}
html.nt .nf-l{color:#AEB9C6;text-shadow:0 0 3px #05070B,0 0 3px #05070B,0 0 3px #05070B}
.nt-ap{position:absolute;white-space:nowrap;font:800 15px/1.3 var(--gothic);color:#DCE3EA;transform:translate(-100%,-50%);left:-22px}
.nt-ap span{display:block;font-size:13px;font-weight:700;color:#8996A7}
.nt-me{width:18px;height:18px;border-radius:50%;background:#F0AC4E;box-shadow:0 0 0 8px rgba(240,172,78,.18)}
.nt-mel{position:absolute;left:24px;top:-4px;white-space:nowrap;font:800 15px var(--gothic);color:#DCE3EA}
"""
JS = r"""async ([lat, lon, fields, top, night]) => {
  const p = {lat, lon};
  document.documentElement.classList.toggle('nt', night);
  if(!document.getElementById('injcss')){ const s = document.createElement('style'); s.id = 'injcss'; s.textContent = INJ; document.head.appendChild(s); }
  HOME_POS = p; showNearest(nearest(p));
  await new Promise(r => setTimeout(r, 1200)); await renderHomeMap();
  const n = HOME_NEAR, a = n.a, rad = a.radius || 1500;
  const pad = homeMapPad(); pad.b = innerHeight - top + 28;
  if(night){ HOME_LAYER.remove(); HOME_LAYER = L.layerGroup().addTo(HOME_MAP); pad.t = 140;
    const C = '#8996A7';
    L.circle([a.lat, a.lon], {radius:rad, color:C, weight:1.4, dashArray:'5 5', fill:false}).addTo(HOME_LAYER);
    const rw = (typeof OPS_AIRPORTS !== 'undefined' && OPS_AIRPORTS[a.iata] && OPS_AIRPORTS[a.iata].rwy) || [];
    for(const r of rw) L.polyline([[r[1], r[2]], [r[5], r[6]]], {color:'#DCE3EA', weight:4, opacity:.85, lineCap:'round'}).addTo(HOME_LAYER);
    L.circleMarker([a.lat, a.lon], {radius:14, color:'#DCE3EA', weight:2, fill:false}).addTo(HOME_LAYER);
    L.marker([a.lat, a.lon], {icon:L.divIcon({className:'', html:'<div class="nt-ap">' + code(a) + ' ' + godShort(a) + '<span>判定範囲 ' + homeKm(rad/1000) + '</span></div>', iconSize:[0,0]})}).addTo(HOME_LAYER);
    if(!n.within) L.polyline([[a.lat, a.lon], [lat, lon]], {color:C, weight:1.6, dashArray:'1 6', lineCap:'round'}).addTo(HOME_LAYER);
    L.marker([lat, lon], {icon:L.divIcon({className:'', html:'<div class="nt-me"></div><div class="nt-mel">いまここ</div>', iconSize:[18,18], iconAnchor:[9,9]})}).addTo(HOME_LAYER);
  }
  for(const [nm, fl, fo, kd] of fields){
    const col = night ? (kd === 'glider' ? '#5CC1F0' : '#7BC48E') : (kd === 'glider' ? '#1F7FB6' : '#3D7A4E');
    L.circleMarker([fl, fo], {radius:4.5, color: night ? '#0D1218' : '#fff', weight:1.5, fill:true, fillColor:col, fillOpacity:1, interactive:false}).addTo(HOME_LAYER);
    if(innerHeight >= 700 && fields.length <= 3) L.marker([fl, fo], {interactive:false, icon:L.divIcon({className:'', html:'<div class="nf-l">' + nm + '</div>', iconSize:[0,0]})}).addTo(HOME_LAYER);   // 低い画面は名前を出さず点だけ
  }
  let b = L.latLng(a.lat, a.lon).toBounds(rad * 2);
  if(n.km <= HOME_FIT_KM) b = b.extend([lat, lon]);
  HOME_MAP.fitBounds(b, {paddingTopLeft:[pad.l, pad.t], paddingBottomRight:[pad.r, pad.b], maxZoom:14, animate:false});
  { const ab = document.querySelector('#homeMap .hm-ap b'); if(ab && a.kind) ab.textContent = a.name; }
  const ap = document.querySelector('#homeMap .hm-ap'); if(ap){ const c = HOME_MAP.latLngToContainerPoint([a.lat, a.lon]); ap.classList.toggle('l', c.x > document.getElementById('homeMap').clientWidth * .5); }
  return {name:a.name, km:n.km, within:n.within};
}"""

async def main():
    make_near.build()
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        tops = {}
        for job in JOBS:
            for h in (844, 667):
                pg = await br.new_page(viewport={'width': 390, 'height': h})
                await pg.goto('file://' + os.path.join(OUT, job[3]))
                tops[(job[0], h)] = await pg.evaluate("document.getElementById('hs').getBoundingClientRect().top")
                await pg.close()
        print(tops)
        for h in (844, 667):
            pg = await br.new_page(viewport={'width': 390, 'height': h}, device_scale_factor=2 if h == 844 else 1)
            await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo').click()")
            await pg.wait_for_timeout(2500)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
            await pg.evaluate('INJ => { window.INJ = INJ }', INJ_CSS)
            for name, pos, fields, _, night in JOBS:
                lat, lon = P[pos]
                r = await pg.evaluate(JS.replace('INJ;', 'window.INJ;'), [lat, lon, [[f, *F[f]] for f in fields], tops[(name, h)], night])
                await pg.wait_for_timeout(3000)
                await pg.screenshot(path=os.path.join(MAPS, '%s-%d.jpg' % (name, h)), type='jpeg', quality=78)
                print(name, h, r)
            await pg.close()
        await br.close()
    make_near.build()
asyncio.run(main())
