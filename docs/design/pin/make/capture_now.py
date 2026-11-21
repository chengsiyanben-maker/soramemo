# -*- coding: utf-8 -*-
# 本番（soramemo.jp）をデモで開き、今の画面を撮る（make/now/ に jpg）。2版の「今の画面」に使う。
# 00a：ホーム（近くの空港のシート）／00b：空港のページ／00c：運用タブの特別塗装機の通知のボタンのあたり
import os, asyncio
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); NOW = os.path.join(HERE, "now")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="ja-JP", timezone_id="Asia/Tokyo",
                                  geolocation={"latitude": 35.5494, "longitude": 139.7798}, permissions=["geolocation"])
        pg = await ctx.new_page()
        await pg.goto("https://soramemo.jp/", wait_until="domcontentloaded"); await pg.wait_for_timeout(4000)
        await pg.evaluate("""() => { document.querySelectorAll('dialog[open]').forEach(d=>d.close()); const b=document.querySelector('#gateDemo')||document.querySelector('#loginDemo'); b && b.click(); }""")
        await pg.wait_for_timeout(7000)
        await pg.evaluate("() => document.querySelectorAll('dialog[open]').forEach(d=>d.close())"); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=os.path.join(NOW, "00a.jpg"), type="jpeg", quality=72)
        r = await pg.evaluate("""() => { const b=[...document.querySelectorAll('button')].find(x=>/ほか\\d/.test(x.textContent) && x.offsetParent); if(!b) return null; b.click(); return b.textContent; }"""); print("near", r)
        await pg.wait_for_timeout(2500)
        await pg.screenshot(path=os.path.join(NOW, "00d.jpg"), type="jpeg", quality=72)
        await pg.evaluate("() => document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
        r = await pg.evaluate("""() => { try{ openAirport('HND'); return 'fn'; }catch(e){} const b=[...document.querySelectorAll('*')].find(x=>x.children.length===0 && /東京国際空港（羽田）/.test(x.textContent) && x.offsetParent); if(!b) return null; b.click(); return b.tagName; }"""); print("ap", r)
        await pg.wait_for_timeout(5000)
        await pg.screenshot(path=os.path.join(NOW, "00b.jpg"), type="jpeg", quality=72)
        await pg.evaluate("() => document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
        await pg.evaluate("""() => { const b=document.querySelector('nav.tabs button[data-v=ops]'); b && b.click(); }"""); await pg.wait_for_timeout(8000)
        y = await pg.evaluate("""() => { const b=document.querySelector('[data-sp-push]')||[...document.querySelectorAll('h3,h4,b')].find(x=>/特別塗装機/.test(x.textContent)&&x.offsetParent); if(!b) return 'none'; b.scrollIntoView({block:'center'}); return b.textContent; }"""); print("sp", y)
        await pg.wait_for_timeout(1500)
        await pg.screenshot(path=os.path.join(NOW, "00c.jpg"), type="jpeg", quality=72)
        await b.close()
asyncio.run(main())
