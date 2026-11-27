# -*- coding: utf-8 -*-
# 本番（soramemo.jp）をデモで開き、今の画面を撮る（make/now/ に jpg）。
# 00a：運用タブの案内板（羽田・到着）の「海外の航空会社（いま近くにいる便）」／00b：ホームの乗る便のカード（時刻表にない便）
import os, asyncio, json, datetime
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); NOW = os.path.join(HERE, "now")
async def main():
    day = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime("%Y-%m-%d")
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="ja-JP", timezone_id="Asia/Tokyo")
        await pg.goto("https://soramemo.jp/", wait_until="domcontentloaded"); await pg.wait_for_timeout(4000)
        await pg.evaluate("""() => { document.querySelectorAll('dialog[open]').forEach(d=>d.close()); const b=document.querySelector('#gateDemo')||document.querySelector('#loginDemo'); b && b.click(); }""")
        await pg.wait_for_timeout(5000)
        await pg.evaluate("() => document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
        await pg.evaluate("""() => { const b=document.querySelector('nav.tabs button[data-v=ops]'); b && b.click(); }""")
        await pg.wait_for_timeout(6000)
        r = await pg.evaluate("""() => { const b=document.querySelector('#opsViews [data-vw="ops:board"]'); b && b.click(); return !!b; }"""); print("board", r)
        await pg.wait_for_timeout(5000)
        await pg.evaluate("""() => { const t=[...document.querySelectorAll('button')].find(x=>x.textContent.trim()==='到着'); t && t.click(); }"""); await pg.wait_for_timeout(3000)
        y = await pg.evaluate("""() => { const h=[...document.querySelectorAll('h3')].find(x=>x.textContent.includes('海外の航空会社')); if(!h) return -1; const r=h.getBoundingClientRect(); window.scrollTo(0, r.top+scrollY-200); return r.top; }"""); print("foreign", y)
        await pg.wait_for_timeout(1500)
        await pg.screenshot(path=os.path.join(NOW, "00a.jpg"), type="jpeg", quality=72)
        plan = {"intl": True, "dep": "LHR", "arr": "HND", "airline": "BA", "no": "BA5", "day": day}
        await pg.evaluate("p => localStorage.setItem('soramemo.plan', JSON.stringify(p))", plan)
        await pg.evaluate("""() => { const b=document.querySelector('nav.tabs button[data-v=home]'); b && b.click(); }"""); await pg.wait_for_timeout(1000)
        await pg.evaluate("() => { try{ renderRide(true) }catch(e){} }"); await pg.wait_for_timeout(6000)
        y = await pg.evaluate("""() => { const c=document.getElementById('rideCard'); if(!c||c.hidden) return 'hidden'; c.scrollIntoView({block:'center'}); return c.textContent.slice(0,200); }"""); print("ride", y)
        await pg.wait_for_timeout(1500)
        await pg.screenshot(path=os.path.join(NOW, "00b.jpg"), type="jpeg", quality=72)
        await b.close()
asyncio.run(main())
