# -*- coding: utf-8 -*-
# 3版：02 入口を本物の羽田の空港ページで見せる（review-1 の3）。main の web/ を http://localhost:8765/ で開き、デモで羽田の空港ページを開く。
# 撮るときにページの中へ入口（空港の今のカードの中の見本の絵）を描き足すだけで、アプリのコードは変えない。
#  02a 開いたとき（入口は空港の今のカードの中だけ）／02b 開いたとき＋数字のカードの下に小さな「3Dで見る ›」／02c 送ったところ（入口のカード）
# 使い方：(cd web && python3 -m http.server 8765 &) ; python3 capture_v3.py → make/now/v3-*.jpg と ../02a〜02c-*-v3.html
import asyncio, os, json, base64
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
NOW = os.path.join(HERE, 'now')
SCENE = open(os.path.join(HERE, 'scene.js'), encoding='utf-8').read()
CSS = """
.t3d{position:relative;height:184px;border-radius:18px;overflow:hidden;background:#C9DDF0;margin:4px 0 0}
.t3d canvas{position:absolute;inset:0;width:100%;height:100%}
.t3d .lb{position:absolute;left:10px;bottom:10px;font:600 13px/1 var(--gothic,system-ui);background:rgba(255,255,255,.88);border-radius:999px;padding:6px 10px;color:#6B7280}
.t3d .go3{position:absolute;right:10px;bottom:10px;height:44px;padding:0 16px;border-radius:999px;background:#0F1B2D;color:#fff;font:800 15px/1 var(--gothic,system-ui);display:inline-flex;align-items:center;gap:6px;border:0;box-shadow:0 12px 28px -18px rgba(15,23,42,.45)}
.t3f{font:500 13px/1.5 var(--gothic,system-ui);color:#6B7280;margin:8px 2px 4px}
.x3d{display:flex;align-items:center;gap:10px;margin:12px 0 2px}
.x3d button{height:44px;padding:0 16px 0 12px;border-radius:999px;border:0;background:#EEF1F5;color:#24292F;font:800 15px/1 var(--gothic,system-ui);display:inline-flex;align-items:center;gap:8px}
.x3d button svg{width:20px;height:20px;stroke:#24292F;fill:none;stroke-width:1.8;stroke-linejoin:round}
.x3d span{font:500 13px/1.4 var(--gothic,system-ui);color:#6B7280}
"""
CUBE = '<svg viewBox="0 0 24 24"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/></svg>'
THUMB = "{sky:'day',cam:{pos:HND.P(450,-5300,2900),tgt:HND.P(100,-500,0),fov:46,cy:.52},planeScale:3.4}"
JS = r"""async ([css, scene, pill, cube]) => {
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const now = document.getElementById('apNow'); const head = now.querySelector('.nowhead');
  const sp = head.querySelector('span'); if (sp) sp.textContent = sp.textContent.trim() + '・機体 12機';
  const box = document.createElement('div');
  box.innerHTML = '<div class="t3d"><canvas id="cv3"></canvas><span class="lb">© OpenStreetMap</span><button class="go3">3Dで見る ›</button></div><p class="t3f">押すと読み込みます（約1.5MB）</p>';
  head.after(box);
  drawAirport(document.getElementById('cv3'), THUMB);
  if (pill) {
    const dl = document.querySelector('#dAirportBody .zk-dl');
    const x = document.createElement('div'); x.className = 'x3d';
    x.innerHTML = '<button>' + cube + '3Dで見る ›</button><span>空港の今・機体 12機<br>約1分遅れ</span>';
    dl.after(x);
  }
  // 測る：足した所の字の大きさと押す所
  const out = {small: [], tap: []};
  document.querySelectorAll('.t3d *, .t3f, .x3d, .x3d *').forEach(e => { if (!e.childNodes.length || ![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
    const fs = parseFloat(getComputedStyle(e).fontSize); if (fs < 12.95) out.small.push(e.textContent.trim().slice(0, 12) + ':' + fs); });
  document.querySelectorAll('.t3d .go3, .x3d button').forEach(e => { const r = e.getBoundingClientRect(); if (r.height < 43.5 || r.width < 43.5) out.tap.push(e.textContent + r.height); });
  return out;
}""".replace('THUMB', THUMB)
SHOTS = [('02a', False, False), ('02b', True, False), ('02c', False, True)]
async def main():
    os.makedirs(NOW, exist_ok=True); res = {}
    async with async_playwright() as p:
        br = await p.chromium.launch()
        for h in (844, 740, 667):
            for name, pill, scroll in SHOTS:
                pg = await br.new_page(viewport={'width': 390, 'height': h}, device_scale_factor=2)
                await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
                await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo').click()")
                await pg.wait_for_timeout(2500)
                await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
                await pg.evaluate("openAirport(Object.keys(BY).find(k=>BY[k].iata==='HND'))"); await pg.wait_for_timeout(3000)
                await pg.evaluate(SCENE)   # 描き手を読み込む（window.drawAirport）
                res[(name, h)] = await pg.evaluate(JS, [CSS, '', pill, CUBE])
                if scroll:
                    await pg.evaluate("(()=>{const d=document.querySelector('#dAirport .dlg');const n=document.getElementById('apNow');d.scrollTop+=n.getBoundingClientRect().top-d.getBoundingClientRect().top-24;})()")
                await pg.wait_for_timeout(400)
                info = await pg.evaluate("""()=>{const g=document.querySelector('.t3d .go3').getBoundingClientRect();const tb=document.querySelector('nav.tabs');const t=tb?tb.getBoundingClientRect().top:innerHeight;const x=document.querySelector('.x3d button');return {go3:Math.round(g.top),tabs:Math.round(t),pill:x?Math.round(x.getBoundingClientRect().top):null}}""")
                res[(name, h)]['pos'] = info
                await pg.screenshot(path=os.path.join(NOW, 'v3-%s-%d.jpg' % (name, h)), type='jpeg', quality=82)
                await pg.close()
        await br.close()
    for k, v in res.items(): print(k, json.dumps(v, ensure_ascii=False))
    json.dump({'%s-%d' % k: v for k, v in res.items()}, open(os.path.join(NOW, 'v3-pos.json'), 'w'), ensure_ascii=False, indent=1)
    # 1画面1ファイルの HTML（高さで写真を選ぶ）
    T = {'02a': '02a 3版：開いたとき（入口は空港の今のカードの中だけ）', '02b': '02b 3版：開いたとき＋数字のカードの下に「3Dで見る ›」', '02c': '02c 3版：送ったところ（空港の今のカードの入口）'}
    F = {'02a': '02a-open-v3', '02b': '02b-open-pill-v3', '02c': '02c-scrolled-v3'}
    for name, _, _ in SHOTS:
        im = {h: 'data:image/jpeg;base64,' + base64.b64encode(open(os.path.join(NOW, 'v3-%s-%d.jpg' % (name, h)), 'rb').read()).decode() for h in (844, 740, 667)}
        css = ('html,body{margin:0;background:#AEB4BB}img{display:none;width:100%;height:100vh;object-fit:cover;object-position:top}'
               '.h844{display:block}@media (max-height:792px){.h844{display:none}.h740{display:block}}@media (max-height:703px){.h740{display:none}.h667{display:block}}')
        html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>%s</style></head><body>'
                '<img class="h844" src="%s" alt="%s"><img class="h740" src="%s" alt=""><img class="h667" src="%s" alt=""></body></html>') % (T[name], css, im[844], T[name], im[740], im[667])
        open(os.path.join(OUT, F[name] + '.html'), 'w', encoding='utf-8').write(html)
    print('ok')
asyncio.run(main())
