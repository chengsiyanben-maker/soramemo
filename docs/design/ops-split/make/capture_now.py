# -*- coding: utf-8 -*-
# 本番（soramemo.jp）をデモで開き、運用タブの今の並びを撮る（make/now/ に jpg）。
import os, asyncio
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); NOW = os.path.join(HERE, "now")
VIEWS = ["runway", "board", "day", "ontime", "art", "strip", "photo"]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="ja-JP", timezone_id="Asia/Tokyo")
        await pg.goto("https://soramemo.jp/", wait_until="domcontentloaded"); await pg.wait_for_timeout(4000)
        await pg.evaluate("""() => { document.querySelectorAll('dialog[open]').forEach(d=>d.close()); const b=document.querySelector('#gateDemo')||document.querySelector('#loginDemo'); b && b.click(); }""")
        await pg.wait_for_timeout(5000)
        # 開いたシートなどを閉じる
        await pg.evaluate("() => document.querySelectorAll('dialog[open]').forEach(d=>d.close())"); await pg.wait_for_timeout(500)
        await pg.evaluate("""() => { const b=document.querySelector('nav.tabs button[data-v=ops]'); b && b.click(); }""")
        await pg.wait_for_timeout(8000)
        for i, v in enumerate(VIEWS):
            ok = await pg.evaluate("""v => { const b=document.querySelector('#opsViews [data-vw="ops:'+v+'"]'); if(b){b.click(); return b.outerHTML.slice(0,120);} return [...document.querySelectorAll('#opsViews button')].map(x=>x.outerHTML.slice(0,90)).join('|'); }""", v)
            print(v, ok[:300])
            await pg.wait_for_timeout(3500); await pg.evaluate("window.scrollTo(0,0)")
            await pg.screenshot(path=os.path.join(NOW, f"{i:02d}-{v}.jpg"), type="jpeg", quality=70, full_page=True)
        await b.close()
asyncio.run(main())
