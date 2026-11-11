# -*- coding: utf-8 -*-
# 5版の地図の写真を撮る（出典の札の高さも空けて寄せる・引き上げた位置は一覧と同じ番号の点・ヘリポート）。capture_v4.py を写したもの
# 4版の説明：4版の地図の写真を撮る（開いたときは点なし・引き上げた位置だけ点。右はズームのボタンの幅を空ける）。3版の capture_v3.py を写したもの
# もとの説明：3版の地図の写真を撮る（先頭＝半券の空港に寄せ、ほかは小さい点）。今のアプリ（web/ を http://localhost:8765/ で開く）のデモに入り、位置を入れてホームの地図だけを撮る。
# アプリのコードは変えない（撮るときにページの中で印を足して、シート・タブ帯を見えなくするだけ）。
# 使い方：(cd web && python3 -m http.server 8765 &) ; python3 capture.py ; python3 make_near.py
import asyncio, os, sys, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_near_v5 as make_near
OUT = make_near.OUT
MAPS = os.path.join(HERE, 'maps'); os.makedirs(MAPS, exist_ok=True)

P = {'ushiku': (35.975, 140.149), 'ryu': (35.9063, 140.2422), 'tokyo': (35.681, 139.767), 'osaka': (34.7025, 135.4959), 'kazo': (36.1310, 139.6017),
     'yao': (34.6265, 135.6010), 'chofu': (35.6518, 139.5440), 'shinkiba': (35.6459, 139.8270), 'kawagoe': (35.9073, 139.4826)}
F = {'竜ヶ崎飛行場': (35.906276, 140.242152, 'field'), '大利根飛行場': (35.85937, 140.241219, 'field'), '八尾空港': (34.596298, 135.602997, 'field'),
     '加須滑空場': (36.1866, 139.61748, 'glider'), '大利根滑空場': (36.16458, 139.67117, 'glider'), '羽生滑空場': (36.19942, 139.6031, 'glider'),
     '板倉滑空場': (36.26616, 139.63388, 'glider'), '妻沼第2滑空場': (36.20044, 139.43405, 'glider'), 'ホンダエアポート': (35.97633, 139.524125, 'field'), '妻沼滑空場': (36.21338, 139.41697, 'glider'),
     '成田国際空港': (35.76858, 140.388714, 'civ'), '大阪国際空港（伊丹）': (34.780853, 135.440829, 'civ'), '調布空港': (35.6717, 139.528, 'civ'), '東京国際空港（羽田）': (35.5494, 139.7798, 'civ'), '東京ヘリポート': (35.635924, 139.839475, 'heli')}
JOBS = [  # 地図の名前, 位置, 先頭, 一覧の点（5版では出さない：引き上げた位置の地図は狭く、番号が「いまここ」と重なるため。review-4 の6 の「先頭だけ」）, 高さを測るページ, 夜, 距離, 中か
 ('s02-v5', 'ushiku', '竜ヶ崎飛行場', [], '02-home-near-v5.html', False, 11.3, False),
 ('s02f-v5', 'ushiku', '竜ヶ崎飛行場', ['大利根飛行場'], '02b-home-near-full-v5.html', False, 11.3, False),
 ('s03-v5', 'ryu', '竜ヶ崎飛行場', [], '03-home-in-field-v5.html', False, 0, True),
 ('s04-v5', 'tokyo', '東京ヘリポート', [], '04-home-heli-v5.html', False, 8.2, False),
 ('s06-v5', 'osaka', '大阪国際空港（伊丹）', [], '06-home-osaka-v5.html', False, 10.1, False),
 ('s06b-v5', 'yao', '八尾空港', [], '06b-home-yao-v5.html', False, 3.4, False),
 ('s07-v5', 'kazo', '加須滑空場', [], '07-home-kazo-v5.html', False, 6.3, False),
 ('s07f-v5', 'kazo', '加須滑空場', ['大利根滑空場', '羽生滑空場', '板倉滑空場'], '07b-home-kazo-full-v5.html', False, 6.3, False),
 ('s08-v5', 'chofu', '調布空港', [], '08-home-chofu-v5.html', False, 2.6, False),
 ('s09-v5', 'kawagoe', 'ホンダエアポート', [], '09-home-kawagoe-v5.html', False, 8.5, False),
 ('s12-v5', 'tokyo', '東京国際空港（羽田）', [], '12-home-civonly-on-v5.html', False, 14.7, False),
 ('s02n-v5', 'ushiku', '竜ヶ崎飛行場', [], '02-home-near-v5-night.html', True, 11.3, False),
 ('s07fn-v5', 'kazo', '加須滑空場', ['大利根滑空場', '羽生滑空場', '板倉滑空場'], '07b-home-kazo-full-v5-night.html', True, 6.3, False),
 ('s04n-v5', 'tokyo', '東京ヘリポート', [], '04-home-heli-v5-night.html', True, 8.2, False),
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
.nf-no{width:24px;height:24px;margin:-12px 0 0 -12px;border-radius:50%;background:#16233A;color:#fff;display:grid;place-items:center;font:800 13px/1 var(--gothic);box-shadow:0 0 0 2px #fff,0 2px 6px rgba(15,23,42,.35)}
html.nt .nf-no{background:#DCE3EA;color:#05070B;box-shadow:0 0 0 2px #05070B}
.nt-mel{position:absolute;left:24px;top:-4px;white-space:nowrap;font:800 15px var(--gothic);color:#DCE3EA}
"""
JS = r"""async ([lat, lon, head, dkm, within, fields, top, night, HEAD_X]) => {
  const p = {lat, lon};
  document.documentElement.classList.toggle('nt', night);
  if(!document.getElementById('injcss')){ const s = document.createElement('style'); s.id = 'injcss'; s.textContent = INJ; document.head.appendChild(s); }
  HOME_POS = p; let ha = [...A, ...XA].find(x => x.name === head); if(!ha && HEAD_X){ const t = XA.find(x => x.name === '竜ヶ崎飛行場'); ha = Object.assign({}, t, {name:head, lat:HEAD_X[0], lon:HEAD_X[1], radius:600}); } showNearest({a:ha, km:dkm, term:null, within});
  await new Promise(r => setTimeout(r, 1200)); await renderHomeMap();
  const n = HOME_NEAR, a = n.a, rad = a.radius || 1500;
  const pad = homeMapPad(); pad.b = innerHeight - top + 60; pad.r += 60;
  if(night){ HOME_LAYER.remove(); HOME_LAYER = L.layerGroup().addTo(HOME_MAP); pad.t = 140;
    const C = '#8996A7';
    L.circle([a.lat, a.lon], {radius:rad, color:C, weight:1.4, dashArray:'5 5', fill:false}).addTo(HOME_LAYER);
    const rw = (typeof OPS_AIRPORTS !== 'undefined' && OPS_AIRPORTS[a.iata] && OPS_AIRPORTS[a.iata].rwy) || [];
    for(const r of rw) L.polyline([[r[1], r[2]], [r[5], r[6]]], {color:'#DCE3EA', weight:4, opacity:.85, lineCap:'round'}).addTo(HOME_LAYER);
    L.circleMarker([a.lat, a.lon], {radius:14, color:'#DCE3EA', weight:2, fill:false}).addTo(HOME_LAYER);
    L.marker([a.lat, a.lon], {icon:L.divIcon({className:'', html:'<div class="nt-ap">' + (/^[A-Z0-9]{3}$/.test(a.iata) ? a.iata + ' ' + godShort(a) : a.name.replace(/（.*）/,'')) + '<span>判定範囲 ' + homeKm(rad/1000) + '</span></div>', iconSize:[0,0]})}).addTo(HOME_LAYER);
    if(!n.within) L.polyline([[a.lat, a.lon], [lat, lon]], {color:C, weight:1.6, dashArray:'1 6', lineCap:'round'}).addTo(HOME_LAYER);
    L.marker([lat, lon], {icon:L.divIcon({className:'', html:'<div class="nt-me"></div><div class="nt-mel">いまここ</div>', iconSize:[18,18], iconAnchor:[9,9]})}).addTo(HOME_LAYER);
  }
  for(const [nm, fl, fo, kd, no] of fields){
    if(no){ L.marker([fl, fo], {interactive:false, icon:L.divIcon({className:'', html:'<div class="nf-no">' + no + '</div>', iconSize:[0,0]})}).addTo(HOME_LAYER); continue; }
    const col = night ? (kd === 'glider' ? '#5CC1F0' : kd === 'civ' ? '#AEB9C6' : '#7BC48E') : (kd === 'glider' ? '#1F7FB6' : kd === 'civ' ? '#7A1F5C' : '#3D7A4E');
    L.circleMarker([fl, fo], {radius:4.5, color: night ? '#0D1218' : '#fff', weight:1.5, fill:true, fillColor:col, fillOpacity:1, interactive:false}).addTo(HOME_LAYER);
    if(false) L.marker([fl, fo], {interactive:false, icon:L.divIcon({className:'', html:'<div class="nf-l">' + nm + '</div>', iconSize:[0,0]})}).addTo(HOME_LAYER);   // 低い画面は名前を出さず点だけ
  }
  let b = L.latLng(a.lat, a.lon).toBounds(rad * 2);
  if(n.km <= HOME_FIT_KM) b = b.extend([lat, lon]);
  for(const f of fields) if(f[4]) b = b.extend([f[1], f[2]]);   // 番号の点は見える範囲に入れる
  HOME_MAP.fitBounds(b, {paddingTopLeft:[pad.l, pad.t], paddingBottomRight:[pad.r, pad.b], maxZoom:14, animate:false});
  { const ab = document.querySelector('#homeMap .hm-ap b'); if(ab && !/^[A-Z0-9]{3}$/.test(a.iata)) ab.textContent = a.name.replace(/（.*）/,''); }
  const ap = document.querySelector('#homeMap .hm-ap'); if(ap){ const c = HOME_MAP.latLngToContainerPoint([a.lat, a.lon]); ap.classList.toggle('l', c.x > document.getElementById('homeMap').clientWidth * .5); }
  return {name:a.name, km:n.km, within:n.within};
}"""

async def main():
    make_near.build()
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        tops = {}
        for job in JOBS:
            for h in (844, 740, 667):
                pg = await br.new_page(viewport={'width': 390, 'height': h})
                await pg.goto('file://' + os.path.join(OUT, job[4]))
                tops[(job[0], h)] = await pg.evaluate("document.getElementById('hs').getBoundingClientRect().top")
                await pg.close()
        print(tops)
        for h in (844, 740, 667):
            pg = await br.new_page(viewport={'width': 390, 'height': h}, device_scale_factor=2 if h == 844 else 1)
            await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo').click()")
            await pg.wait_for_timeout(2500)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
            await pg.evaluate('INJ => { window.INJ = INJ }', INJ_CSS)
            for name, pos, head, fields, _, night, dkm, within in JOBS:
                if os.environ.get('ONLY') and name not in os.environ['ONLY'].split(','): continue
                if h == 740 and 'f' not in name.split('-')[0][3:]: continue
                lat, lon = P[pos]
                r = await pg.evaluate(JS.replace('INJ;', 'window.INJ;'), [lat, lon, head, dkm, within, [[f, *F[f], i + 1] for i, f in enumerate(fields) if False], tops[(name, h)], night, list(F[head][:2]) if head in F else None])
                await pg.wait_for_timeout(3000)
                await pg.screenshot(path=os.path.join(MAPS, '%s-%d.jpg' % (name, h)), type='jpeg', quality=78)
                print(name, h, r)
            await pg.close()
        await br.close()
    make_near.build()
asyncio.run(main())
