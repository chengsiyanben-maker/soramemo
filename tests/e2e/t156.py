import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 滑走路の札と風をそろえる（11/21 改善担当の見回りの6番。運用予想担当）
#   深夜（23時〜6時）は「深夜」を時刻で、北・南を風で決めるので、札は「時刻と風から推定」。昼は今までどおり「風から推定」
#   推定のわけは、出している風（○°から・○kt）と食い違わない言い方にする（250°・12kt で「北寄りの風」と言わない）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
JST = timezone(timedelta(hours=9))
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, at, metar, shot=None):
    c = await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo', device_scale_factor=2 if shot else 1)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    async def h(r):
        u = r.request.url; name = u.split('fake.supabase.co')[1].split('?')[0].rsplit('/', 1)[-1]
        m = dict(metar, time=(at - timedelta(minutes=10)).isoformat())
        body = {'metar':m, 'airport-traffic':{'planes':[], 'at':at.isoformat()}}.get(name, {} if '/functions/' in u else [])
        await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
    await c.route('https://fake.supabase.co/rest/**', h); await c.route('https://fake.supabase.co/functions/**', h)
    await c.add_init_script("localStorage.setItem('soramemo.ops.hub','0'); localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','HND'); localStorage.setItem('soramemo.view.ops','runway');")
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.clock.set_fixed_time(at)
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(1500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); OPS_PICKED = true")
    await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1800)
    tag = await pg.inner_text('#opsInfo .opssrc') if await pg.locator('#opsInfo .opssrc').count() else ''
    mode = await pg.inner_text('#opsInfo .mode'); wind = await pg.inner_text('#opsInfo .otiles .otile')
    if shot: await pg.screenshot(path=shot)
    await c.close()
    return tag, mode, wind, errs
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); allerr = []
        # 1. 推定の関数（時刻と風を変えて）
        c = await b.new_context(); pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_function('typeof estimateHaneda === "function"')
        E = lambda wdir, wspd, t: pg.evaluate("([d, s, t]) => estimateHaneda({ wdir:d, wspd:s }, new Date(t))", [wdir, wspd, t])
        e = await E(250, 12, '2026-11-21T05:40:00+09:00')
        check('5時40分・250°12kt：深夜・北風', e['mode'] == 'nightN' and e['night'], e['mode'])
        check('5時40分・250°12kt：わけに「深夜（23時〜6時）」と「横風に近く」・「北寄りの風」と言わない', e['whyPlain'].startswith('深夜（23時〜6時）') and '横風に近く' in e['whyPlain'] and '北寄りの風' not in e['whyPlain'], e['whyPlain'])
        check('5時40分：くわしいわけ（そらメモ＋）にも「深夜」と追い風のノット', e['why'].startswith('深夜（23時〜6時）') and '7ノット以下' in e['why'], e['why'])
        e = await E(330, 12, '2026-11-21T12:00:00+09:00')
        check('12時・330°12kt：北風・「北寄りの風なので」・「深夜」と言わない', e['mode'] == 'north' and e['whyPlain'] == '北寄りの風なので、北風の運用と推定', e['whyPlain'])
        e = await E(250, 4, '2026-11-21T12:00:00+09:00')
        check('12時・250°4kt：「風が弱いので」', e['mode'] == 'north' and e['whyPlain'].startswith('風が弱いので'), e['whyPlain'])
        e = await E(250, 12, '2026-11-21T12:00:00+09:00')
        check('12時・250°12kt：「横風に近く」', e['mode'] == 'north' and e['whyPlain'].startswith('横風に近く'), e['whyPlain'])
        e = await E(160, 15, '2026-11-21T23:30:00+09:00')
        check('23時30分・160°15kt：深夜・南風・「南寄りの風」', e['mode'] == 'nightS' and '南寄りの風' in e['whyPlain'] and e['whyPlain'].startswith('深夜'), e['whyPlain'])
        e = await pg.evaluate("estimateHaneda(null, new Date('2026-11-21T02:00:00+09:00'))")
        check('気象通報なしの深夜：わけは「深夜…」＋ふだんの向き', e['mode'] == 'nightN' and e['whyPlain'].startswith('深夜（23時〜6時）') and 'ふだんの向き' in e['whyPlain'], e['whyPlain'])
        allerr += errs; await c.close()
        # 2. 画面の札（見回りの写真と同じ 5時40分・250°12kt）
        shot = os.path.join(WORK, 't156-night-390.png')
        tag, mode, wind, errs = await page(b, datetime(2026, 11, 21, 5, 40, tzinfo=JST), {'wdir':250, 'wspd':12, 'vis_m':9999}, shot)
        check('深夜：運用は「深夜・北風運用」・札は「時刻と風から推定」', mode == '深夜・北風運用' and tag == '時刻と風から推定', [mode, tag])
        check('深夜：風の欄は 250° から・12kt（札と同じ風）', '250' in wind and '12' in wind, wind)
        allerr += errs
        tag, mode, wind, errs = await page(b, datetime(2026, 11, 21, 12, 0, tzinfo=JST), {'wdir':330, 'wspd':12, 'vis_m':9999})
        check('昼：運用は「北風運用」・札は今までどおり「風から推定」', mode == '北風運用' and tag == '風から推定', [mode, tag])
        allerr += errs
        tag, mode, wind, errs = await page(b, datetime(2026, 11, 21, 23, 30, tzinfo=JST), {'wdir':160, 'wspd':15, 'vis_m':9999})
        check('23時30分・南風：「深夜・南風運用」・札は「時刻と風から推定」', mode == '深夜・南風運用' and tag == '時刻と風から推定', [mode, tag])
        allerr += errs
        print('写真:', shot)
        await b.close()
        print('fails', fails); print('errors', allerr if allerr or fails else [])
asyncio.run(main())
