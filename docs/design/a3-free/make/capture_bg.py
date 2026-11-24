# -*- coding: utf-8 -*-
# 案の下の絵（背景）を撮る：main の web/ を http://localhost:8765/ で開き、デモで羽田の3D を開き、
# 時計を昼（11/24 13時30分）にずらし、a3Camera を差し替えて4つの見方のカメラを置き、上の操作を隠して撮る
# 使い方：python3 capture_bg.py [test]   （test は 390 幅の1倍だけ）
import asyncio, os, sys, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE + '/bg'; os.makedirs(OUT, exist_ok=True)
INIT = "(()=>{const off=Date.UTC(2026,10,24,4,30)-Date.now();const N=Date.now;window.Date=class extends Date{constructor(...a){a.length?super(...a):super(N()+off)}static now(){return N()+off}};})()"
HIDE = '#dAp3d .a3top,#dAp3d .a3pills,#dAp3d .a3chip,#dAp3d .a3sheet,#dAp3d .a3card,#dAp3d [class*=a3lab],#dAp3d [class*=a3edge],#dAp3d [class*=a3tag],#dAp3d [class*=a3src],#dAp3d button{visibility:hidden!important}'
# 名前: [カメラの位置 x,y,z（m・x は東・z は南・y は高さ）, 見る点, 画角, 機体を追う id（あれば位置を機体から）]
CAMS = json.loads(open(HERE + '/cams.json').read())
PATCH = """
window.__orig = window.__orig || a3Camera;
a3Camera = function(ps){
  const c = window.__cam; if(!c) return window.__orig(ps);
  const cam = A3.cam; a3TowerClip(false);
  let p = c.pos, l = c.look;
  if(c.follow){ const o = A3.objs.get(c.follow); if(o){ const g = o.g.position; p = [g.x + c.pos[0], g.y + c.pos[1], g.z + c.pos[2]]; l = [g.x + c.look[0], g.y + c.look[1], g.z + c.look[2]]; } }
  if(c.ground){ const T = A3.THREE, rc = new T.Raycaster(new T.Vector3(p[0], 2000, p[2]), new T.Vector3(0, -1, 0)); const hit = rc.intersectObjects(A3.scene.children, true).find(h => h.object.isMesh && !h.object.userData.sky); const gy = hit ? hit.point.y : 0; window.__gy = [gy, hit && (hit.object.name || hit.object.type), c.ground]; p = [p[0], gy + c.ground, p[2]]; l = [l[0], gy + c.ground + (l[1]||0), l[2]]; }
  cam.near = c.near || (c.ground ? 0.3 : 5); cam.userData.fov = c.fov; a3ViewOffset(); cam.updateProjectionMatrix();
  cam.position.set(p[0], p[1], p[2]); cam.lookAt(l[0], l[1], l[2]);
};
"""
async def main():
    test = len(sys.argv) > 1 and sys.argv[1] == 'test'
    sizes = ((390, 844, '', 1),) if test else ((390, 844, '', 2), (375, 667, '-667', 1))
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for w, h, s, dpr in sizes:
            pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr, bypass_csp=True)
            await pg.add_init_script(INIT)
            await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo')&&document.getElementById('gateDemo').click()")
            await pg.wait_for_timeout(2500)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); openAp3d()"); await pg.wait_for_timeout(14000)
            await pg.screenshot(path='%s/now%s.png' % (OUT, s))
            await pg.add_style_tag(content=HIDE)
            await pg.evaluate(PATCH)
            # シートを閉じた形の画角（a3ViewOffset はシートの高さで中心をずらすので、シートを隠した分だけ）
            for name, c in CAMS.items():
                if test and len(sys.argv) > 2 and name not in sys.argv[2:]: continue
                if c.get('app'):   # 今の機体の視点をそのまま使う（空の機体のうち、高さが c.app の範囲のもの）
                    print(name, await pg.evaluate("""c => { window.__cam = null; const lo = c.app[0], hi = c.app[1];
                      const ks = [...A3.objs.entries()].filter(([k, o]) => a3Air(o.p) && o.g.position.y > lo && o.g.position.y < hi).sort((a, b) => a[1].g.position.y - b[1].g.position.y);
                      if(!ks.length) return 'なし'; A3.view = 'plane'; A3.sel = ks[0][0]; A3.yaw = c.yaw || 0; A3.dirty = true; return ks[0][0] + ' ' + Math.round(ks[0][1].g.position.y); }""", c))
                else:
                    await pg.evaluate("c => { A3.view = 'all'; A3.sel = null; A3.yaw = 0; window.__cam = c; A3.dirty = true; }", c)
                await pg.wait_for_timeout(2500)
                await pg.screenshot(path='%s/%s%s.png' % (OUT, name, s))
                print(name, await pg.evaluate("JSON.stringify(window.__gy||null)"))
            await pg.close()
        await b.close()
asyncio.run(main())
