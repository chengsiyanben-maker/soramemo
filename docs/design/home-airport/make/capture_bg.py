# -*- coding: utf-8 -*-
# 地図の背景を撮る：main の web/ を http://localhost:8765/ で開き（cd web && python3 -m http.server 8765）、デモに入って
# ホームの地図だけを残して撮る。bg-hnd＝羽田に寄った今の地図（滑走路と判定範囲はアプリの描いたもの）、
# bg-wide＝羽田と新千歳が上の半分に入る広い地図（アプリの印は外し、空港の点は build.py が描く）。点の位置は bgpos.json
import asyncio, os, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = HERE + '/bg'; os.makedirs(OUT, exist_ok=True)
APS = json.load(open(HERE + '/src/aps.json', encoding='utf-8'))
HOOK = """Object.defineProperty(window,'L',{configurable:true,get(){return this.__L},set(v){this.__L=v;try{v.Map.addInitHook(function(){(window.__maps=window.__maps||[]).push(this)})}catch(e){}}});"""
HIDE = "body *{visibility:hidden!important} .hmap,.hmap *{visibility:visible!important} .hmap .leaflet-control-container{display:none!important}"
async def main():
    pos = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, w, h, dpr in (('', 390, 844, 2), ('-667', 375, 667, 1)):
            pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
            await pg.add_init_script(HOOK)
            await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo')&&document.getElementById('gateDemo').click()")
            await pg.wait_for_timeout(3500)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
            await pg.add_style_tag(content=HIDE)
            idx = await pg.evaluate("(()=>{const m=window.__maps||[];return m.findIndex(x=>x.getContainer().closest('.hmap')||x.getContainer().classList.contains('hmap'))})()")
            print('home map', idx, await pg.evaluate("(window.__maps||[]).length"))
            M = "window.__maps[%d]" % idx
            # 羽田（空港にいるとき）：シートの上に滑走路が来るよう、少し下げて寄せる
            await pg.evaluate(M + ".invalidateSize();" + M + ".setView([35.536,139.786],13.2,{animate:false})")
            await pg.wait_for_timeout(2500)
            await pg.screenshot(path='%s/bg-hnd%s.png' % (OUT, name))
            pos['hnd' + name] = await pg.evaluate("(()=>{const m=%s;const q=m.latLngToContainerPoint([35.549678,139.786958]);return {hnd:[q.x,q.y]}})()" % M)
            # 広い地図（ふだん）
            await pg.evaluate("(()=>{const m=%s;document.querySelectorAll('.hmap .leaflet-overlay-pane,.hmap .leaflet-marker-pane,.hmap .leaflet-shadow-pane,.hmap .leaflet-tooltip-pane').forEach(e=>e.style.setProperty('display','none','important'));m.fitBounds([[34.6,139.0],[43.4,141.9]],{paddingTopLeft:[40,70],paddingBottomRight:[40,%d],animate:false})})()" % (M, int(h * 0.56)))
            print(await pg.evaluate(M+'.getZoom()'), await pg.evaluate(M+'.getMinZoom()'), await pg.evaluate('JSON.stringify('+M+'.getCenter())'))
            await pg.wait_for_timeout(3000)
            await pg.screenshot(path='%s/bg-wide%s.png' % (OUT, name))
            pos['wide' + name] = await pg.evaluate("(()=>{const m=%s;const r={};for(const a of %s){const q=m.latLngToContainerPoint([a[4],a[5]]);r[a[2]]=[Math.round(q.x*10)/10,Math.round(q.y*10)/10]}const u=m.latLngToContainerPoint([35.70,139.50]);r.ME=[u.x,u.y];return r})()" % (M, json.dumps(APS)))
            await pg.close()
        await b.close()
    json.dump(pos, open(OUT + '/bgpos.json', 'w'), indent=0)
asyncio.run(main())
