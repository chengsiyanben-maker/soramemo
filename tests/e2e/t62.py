import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 使う人ごとの構成：気軽に（はじめ）・撮影・修行。タブの並び、ホームのカード、はじめの見方、使い方から勧める
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
BOARD = {'iata': 'HND', 'now': iso(0), 'hours': [{'h': h, 'flights': 10, 'late': 0, 'cancel': 0, 'ref': 0} for h in range(24)], 'next_arr': [{'flight': 'NH212', 'other': 'LHR', 'sched': iso(25), 't': iso(25), 'intl': True, 'aircraft': 'B789'}],
         'next_dep': [{'flight': 'JL903', 'other': 'OKA', 'sched': iso(30), 't': iso(30), 'aircraft': 'A359'}, {'flight': 'BC101', 'other': 'UKB', 'sched': iso(40), 't': iso(40), 'aircraft': 'B738'}]}
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def page(c, errs):
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
    return pg
async def ctx(b, extra=''):
    c = await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');" + extra)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    async def rpc(r):
        name = r.request.url.rsplit('/', 1)[-1]
        await r.fulfill(status=200, body=json.dumps(BOARD if name == 'airport_board' else []), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
    await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
    await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{"planes":[]}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
    return c
TABS = "[...document.querySelectorAll('nav.tabs button')].filter(b => !b.hidden).map(b => b.dataset.v).join(',')"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c = await ctx(b); pg = await page(c, errs)
        check('はじめは気軽に（ホーム・図鑑・フライトの3つのタブ）:', await pg.evaluate(TABS) == 'home,book,log' and await pg.is_hidden('#personaCard'))
        # 撮影
        await pg.evaluate("$('dSettings').showModal()"); await pg.click('[data-persona="spot"]'); await pg.wait_for_timeout(1200)
        check('撮影：タブ:', await pg.evaluate(TABS) == 'ops,home,book,log')
        check('撮影：運用から・撮る人:', await pg.evaluate("currentView()") == 'ops' and await pg.evaluate("VIEW.ops") == 'photo')
        check('撮影：成績はマイページから:', '成績を開く' in (await pg.inner_text('#personaMore')))
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(1200)
        t = await pg.inner_text('#personaCard')
        check('撮影：ホームのカード:', '羽田' in t and 'NH212' in t and 'A359' in t and 'BC101' not in t)
        await pg.locator('#homeSheet .sbody').screenshot(path=os.path.join(WORK, 't62_spot.png'))
        # 修行
        await pg.evaluate("$('dSettings').showModal()"); await pg.click('[data-persona="shugyo"]'); await pg.wait_for_timeout(800)
        check('修行：タブ:', await pg.evaluate(TABS) == 'home,sg,log,stats' and await pg.evaluate("VIEW.log") == 'sg')
        t = await pg.inner_text('#personaCard')
        check('修行：ホームのカード:', 'PP' in t or 'FOP' in t)
        await pg.locator('#homeSheet .sbody').screenshot(path=os.path.join(WORK, 't62_shugyo.png'))
        await pg.reload(); await pg.wait_for_timeout(800); await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        check('修行：開き直しても覚えている:', await pg.evaluate(TABS) == 'home,sg,log,stats')
        await c.close()
        # 使い方から勧める（運用を羽田で3日・30分以上）
        d = lambda k: (now + timedelta(hours=9) - timedelta(days=k)).strftime('%Y-%m-%d')
        usage = json.dumps({'ops': {d(1): {'HND': 120}, d(3): {'HND': 200}, d(5): {'HND': 90}}, 'days': [d(5), d(3), d(1)]})
        c = await ctx(b, f"if(!localStorage.getItem('soramemo.usage')) localStorage.setItem('soramemo.usage', {json.dumps(usage)});"); pg = await page(c, errs)
        for _ in range(40):
            if await pg.evaluate("$('dPersona').open"): break
            await pg.wait_for_timeout(200)
        check('勧める画面が出る:', await pg.evaluate("$('dPersona').open") and '撮影する人' in (await pg.inner_text('#dPersona')))
        await pg.screenshot(path=os.path.join(WORK, 't62_suggest.png'))
        await pg.click('[data-persona-yes]'); await pg.wait_for_timeout(800)
        check('この構成にする:', await pg.evaluate("PERSONA") == 'spot' and await pg.evaluate(TABS) == 'ops,home,book,log')
        await c.close()
        c = await ctx(b, f"if(!localStorage.getItem('soramemo.usage')) localStorage.setItem('soramemo.usage', {json.dumps(usage)});"); pg = await page(c, errs)
        for _ in range(40):
            if await pg.evaluate("$('dPersona').open"): break
            await pg.wait_for_timeout(200)
        await pg.click('[data-persona-no]'); await pg.wait_for_timeout(300)
        check('今のままにする:', await pg.evaluate("PERSONA") == 'casual' and await pg.evaluate("!!usageGet().declined"))
        await pg.reload(); await pg.wait_for_timeout(800); await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(2000)
        check('断ったらしばらく聞かない:', not await pg.evaluate("$('dPersona').open"))
        await c.close()
        print('errors', errs + fails); await b.close()
asyncio.run(main())
