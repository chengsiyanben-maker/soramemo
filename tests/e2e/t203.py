# 印を押す速さの計測（11/26 test-steady。t195 の 1 から分けた）
#   遅い電波（返事に2秒）で押す：位置が取れてからハンコまで・押してからの長い処理（画面が止まる時間）を3回測り、いちばんよい回で見る
#   上限はゆるめ（ハンコ 0.8 秒・長い処理 150ms。手元で1本だけ流すとハンコ 0.1 秒前後・長い処理 60〜100ms）。数字は毎回出す
#   ほかのテストと同時に流すと揺れるので、決まり（返事を待たずにハンコ・仮の印）は t195 で確かめる
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, shutil
from playwright.async_api import async_playwright
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
sys.path.insert(0, HERE); from stamp_perf import GEO, WATCH
CTS = (42.7752, 141.6923)
STAMP_MAX, LT_MAX, TRIES = 800, 150, 3
async def once(p):
    b = await p.chromium.launch(); c = await b.new_context(viewport={'width':390,'height':844}, permissions=['geolocation'])
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');" + GEO)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && window.__fake'); await pg.wait_for_timeout(500)
    await pg.evaluate('__fake.login()'); await pg.wait_for_function('S.checkins.length >= 1'); await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); HOME_POS = null; POS_LAST = null; GEO_WARM = null; homeLocStop()")
    await pg.evaluate('window.__netDelay = 2000; window.__mkFlight = true')
    await pg.evaluate(f'__geo.lat = {CTS[0]}; __geo.lon = {CTS[1]}; __geo.delay = 200; __geo.acc = 20')
    await pg.evaluate(WATCH); await pg.wait_for_timeout(700)
    r = await pg.evaluate("({ stamp: __stampAt == null ? null : __stampAt - __t0 - 200, lt: Math.max(0, ...__lt.filter(([s]) => s >= __t0 - 5).map(x => x[1])) })")
    await b.close(); return r, errs
async def main():
    res, allerrs = [], []
    async with async_playwright() as p:
        for i in range(TRIES):
            r, errs = await once(p); res.append(r); allerrs += errs
            print(f'  {i + 1}回目: ハンコ {r["stamp"] and round(r["stamp"])}ms・長い処理 {round(r["lt"])}ms')
            if r['stamp'] is not None and r['stamp'] <= STAMP_MAX and r['lt'] < LT_MAX: break   # 1回でよい値が出れば終わり
    st = min((r['stamp'] for r in res if r['stamp'] is not None), default=None); lt = min(r['lt'] for r in res)
    fails = []
    if st is None or st > STAMP_MAX: fails.append(f'位置が取れてからハンコまで {STAMP_MAX}ms 以内（いちばんよい回 {st and round(st)}ms）')
    if lt >= LT_MAX: fails.append(f'押してからの長い処理 {LT_MAX}ms 未満（いちばんよい回 {round(lt)}ms）')
    for f in fails: print('FAIL ' + f)
    if not fails: print(f'ok   ハンコ {round(st)}ms・長い処理 {round(lt)}ms（{len(res)}回のうちいちばんよい回）')
    print('errors', fails + allerrs)
if __name__ == "__main__": asyncio.run(main())
