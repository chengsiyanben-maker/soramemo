# iPhone で軽く・隠れないように（11/26 3時20分・6時40分 PM・checkin/perf-ios）。見た目は変えない
#   1 iPhone の形（セーフエリア 上47・下34）：下のタブ帯・下から出るシートの最後のボタン・まるごとの画面の最後が、ホームバーに入らない
#   2 シートやダイアログを開いているあいだ、ページは「引っ張って更新」しない（overscroll-behavior）
#   3 3D：開くまで three.js を読まない・裏に回ったら描かず取りに行かない（戻るとすぐ取る）・閉じたら形と材質と絵を返す
#   4 運用の地図の機体：見ていないあいだ（document.hidden）は取りに行かない
#   5 「ホーム画面に追加」の帯：初めて開いた瞬間は出さない。3回目に開いたとき・最初の印のあとから
#   6 範囲の外で断られた保留の印：あとに「乗った便は、フライトの ＋ から記録帳に足せます」
#   390・375・iPhone 14（セーフエリアあり）で撮る（docs/pm/shots-perf-ios/）
import os, sys, json, shutil, urllib.request
from datetime import datetime, timedelta, timezone
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-perf-ios')); os.makedirs(SHOTS, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_perf.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
UA_I = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js'
THREE = os.path.join(WORK, 'three-0.160.0.module.min.js')
def get_three():   # 自分で用意する（ほかのテストの順に頼らない）
    if os.path.exists(THREE) and os.path.getsize(THREE) > 100000: return True
    try:
        with urllib.request.urlopen(THREE_URL, timeout=30) as r: open(THREE, 'wb').write(r.read())
        return os.path.getsize(THREE) > 100000
    except Exception as e:
        print('three.js を取れない:', e); return False
now = datetime.now(timezone.utc); iso = lambda s: (now + timedelta(seconds=s)).isoformat()
PL = [{'id':'a1','callsign':'JAL318','lat':35.50,'lon':139.8336,'alt_ft':1800,'kt':150,'hdg':331,'fpm':-700,'phase':'arr','dist_km':10,'type':'A359','reg':'JA01XJ','trail':[]}]
fails = []
def ok(cond, msg):
    print(('ok   ' if cond else 'FAIL ') + msg)
    if not cond: fails.append(msg)
async def waitjs(pg, expr, timeout=20000):
    for _ in range(timeout // 200):
        if await pg.evaluate(expr): return True
        await pg.wait_for_timeout(200)
    return False
HIDE = "v => { Object.defineProperty(document, 'hidden', { configurable:true, get:() => v }); Object.defineProperty(document, 'visibilityState', { configurable:true, get:() => v ? 'hidden' : 'visible' }); document.dispatchEvent(new Event('visibilitychange')); }"
async def page(p, b, dev=None, w=390, h=844, opens=None, inset=None):
    kw = dict(p.devices[dev]) if dev else dict(viewport={'width':w,'height':h}, device_scale_factor=2, user_agent=UA_I)
    c = await b.new_context(**kw, reduced_motion='reduce', timezone_id='Asia/Tokyo')
    init = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.zk.swipe','1');"
    if opens is not None: init += f"if(!sessionStorage.getItem('__o')){{ sessionStorage.setItem('__o','1'); localStorage.setItem('soramemo.install.opens','{opens}'); }}"
    await c.add_init_script(init)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    reqs = {'three':0, 'traffic':0}
    async def three_route(r):
        reqs['three'] += 1
        await r.fulfill(path=THREE, content_type='application/javascript', headers={'Access-Control-Allow-Origin':'*'})
    await c.route('https://cdn.jsdelivr.net/npm/three@**', three_route)
    async def fn(r):
        name = r.request.url.split('/functions/v1/')[1].split('?')[0]
        if name == 'airport-traffic': reqs['traffic'] += 1; body = {'iata':'HND','at':iso(-30),'source':'adsb.lol','planes':PL}
        elif name == 'airport-now': body = {'at':iso(-20),'weather':None,'taf':None,'flights':{'arr':[],'dep':[]}}
        else: body = {}
        await r.fulfill(body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
    await c.route('https://fake.supabase.co/functions/v1/**', fn)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    if inset:
        s = await c.new_cdp_session(pg); await s.send('Emulation.setSafeAreaInsetsOverride', {'insets':{'top':inset[0],'bottom':inset[1],'left':0,'right':0}})
    await pg.goto('file://' + os.path.join(WORK, 'index_perf.html'))
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && window.__fake'); await pg.wait_for_timeout(500)
    return c, pg, errs, reqs
async def main():
    have3 = get_three(); allerrs = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1・2 iPhone 14 の形（セーフエリア 上47・下34）
        for dev, inset, tag in (('iPhone 14', (47, 34), 'iphone14'), (None, None, '375')):
            c, pg, errs, reqs = await (page(p, b, dev=dev, inset=inset) if dev else page(p, b, w=375, h=667))
            await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1200)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
            bot = inset[1] if inset else 0
            r = await pg.evaluate("""B => { const H = innerHeight, vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
              const tabs = [...document.querySelectorAll('nav.tabs button')].filter(vis).map(e => e.getBoundingClientRect().bottom);
              return { H, tabs: Math.max(...tabs) }; }""", bot)
            ok(r['tabs'] <= r['H'] - bot, f'{tag} 1 下のタブ帯がホームバーに入らない（{r}）')
            await pg.screenshot(path=os.path.join(SHOTS, f'home-{tag}.png'))
            # 下から出るシート：中身を長くして最後のボタンの位置を見る（どのシートも同じ作り）
            r = await pg.evaluate("""B => { const d = $('dOpsAp'); d.showModal(); const box = d.querySelector('.dlg');
              const extra = document.createElement('div'); extra.id = '__extra'; extra.innerHTML = Array.from({length:30}, (_, i) => `<p>行 ${i + 1}</p>`).join('') + '<button type="button" id="__last" class="btn2" style="width:100%">いちばん下のボタン</button>';
              box.appendChild(extra); box.scrollTop = 1e6; const H = innerHeight, l = $('__last').getBoundingClientRect(), dr = d.getBoundingClientRect();
              return { H, last: Math.round(l.bottom), dlg: Math.round(dr.bottom), top: Math.round(dr.top), ov: getComputedStyle(document.documentElement).overscrollBehaviorY, dov: getComputedStyle(d).overscrollBehaviorY }; }""", bot)
            ok(r['last'] <= r['H'] - bot and r['dlg'] <= r['H'] + 1 and r['top'] >= 0, f'{tag} 1 下から出るシートの最後のボタンがホームバーに入らない（{r}）')
            ok(r['ov'] == 'none' and r['dov'] == 'contain', f'{tag} 2 シートを開いているあいだページは引っ張って更新しない（{r}）')
            await pg.screenshot(path=os.path.join(SHOTS, f'sheet-{tag}.png'))
            await pg.evaluate("$('__extra').remove(); $('dOpsAp').close()")
            ov = await pg.evaluate("getComputedStyle(document.documentElement).overscrollBehaviorY")
            ok(ov != 'none' or await pg.evaluate("document.documentElement.dataset.view === 'home'"), f'{tag} 2 閉じたら元に戻る（{ov}）')
            # まるごとの画面（spfull）：高さは見えている高さ・最後がホームバーに入らない
            r = await pg.evaluate("""B => { const d = $('dData'); d.showModal(); const extra = document.createElement('div'); extra.id = '__extra2';
              extra.innerHTML = Array.from({length:40}, (_, i) => `<p>行 ${i + 1}</p>`).join('') + '<button type="button" id="__last2" class="btn2" style="width:100%">いちばん下</button>';
              (d.querySelector('.dlg') || d).appendChild(extra); d.scrollTop = 1e6; const H = innerHeight, l = $('__last2').getBoundingClientRect(), dr = d.getBoundingClientRect();
              const out = { H, last: Math.round(l.bottom), h: Math.round(dr.height) }; extra.remove(); d.close(); return out; }""", bot)
            ok(r['h'] == r['H'] and r['last'] <= r['H'] - bot, f'{tag} 1 まるごとの画面の最後がホームバーに入らない（{r}）')
            allerrs += errs; await c.close()
        # 3 3D
        if not have3: print('three.js を取れないので 3D は飛ばす')
        else:
            c, pg, errs, reqs = await page(p, b)
            await pg.evaluate("localStorage.setItem('soramemo.install.later','1')")
            ok(reqs['three'] == 0, f'3 開く前は three.js を読まない（{reqs}）')
            await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(700)
            reqs['traffic'] = 0
            await pg.click('#dAirport .a3pill [data-ap3d]')
            await waitjs(pg, "(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden && A3 && A3.r; })()"); await pg.wait_for_timeout(800)
            ok(reqs['three'] == 1 and reqs['traffic'] >= 1, f'3 開くと three.js を読み、機体を取りに行く（{reqs}）')
            await pg.evaluate(HIDE, True); t0 = reqs['traffic']
            await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(300)
            r = await pg.evaluate("({ paused: !!A3.paused, raf: A3.raf })")
            d0 = await pg.evaluate("A3.drawn || 0"); await pg.wait_for_timeout(700); d1 = await pg.evaluate("A3.drawn || 0")
            ok(r['paused'] and reqs['traffic'] == t0 and d0 == d1, f'3 裏に回ると描かず取りに行かない（{r}・取得 {reqs["traffic"] - t0}・描いた時刻 {d0}→{d1}）')
            await pg.evaluate(HIDE, False); await pg.wait_for_timeout(800)
            r = await pg.evaluate("({ paused: !!A3.paused })"); d2 = await pg.evaluate("A3.drawn || 0")
            ok(not r['paused'] and reqs['traffic'] == t0 + 1 and d2 > d1, f'3 戻るとすぐ描き、1回取りに行く（取得 {reqs["traffic"] - t0}）')
            await pg.evaluate("closeAp3d()"); await pg.wait_for_timeout(300)
            r = await pg.evaluate("({ A3: A3 === null, freed: window.__a3Freed || 0, open: $('dAp3d').open })")
            ok(r['A3'] and r['freed'] > 20 and not r['open'], f'3 閉じたら形・材質・絵を返す（{r}）')
            allerrs += errs; await c.close()
        # 4 運用の地図の機体：見ていないあいだは取りに行かない
        c, pg, errs, reqs = await page(p, b)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(2500)
        if await pg.evaluate("!!OPS_MAP && TRAFFIC_TIMER != null"):
            t0 = reqs['traffic']; await pg.evaluate("loadTraffic()"); await pg.wait_for_timeout(300)
            ok(reqs['traffic'] == t0 + 1, f'4 見ているときは取りに行く（{reqs["traffic"] - t0}）')
            await pg.evaluate(HIDE, True); t1 = reqs['traffic']
            for _ in range(3): await pg.evaluate("loadTraffic()")
            await pg.wait_for_timeout(300)
            ok(reqs['traffic'] == t1, f'4 見ていないあいだは取りに行かない（{reqs["traffic"] - t1}）')
            await pg.evaluate(HIDE, False); await pg.wait_for_timeout(500)
            ok(reqs['traffic'] == t1 + 1, f'4 戻ったら間隔を待たずに1回（{reqs["traffic"] - t1}）')
        else:
            ok(await pg.evaluate("typeof loadTraffic === 'function'"), '4 地図がない見方なので、取りに行く関数があることだけ確かめる')
        allerrs += errs; await c.close()
        # 5 ホーム画面に追加の帯
        c, pg, errs, reqs = await page(p, b, opens=0)
        r = await pg.evaluate("({ bar: $('installBar').hidden, opens: localStorage.getItem('soramemo.install.opens'), row: $('installRow').hidden })")
        ok(r['bar'] and r['opens'] == '1' and not r['row'], f'5 初めて開いた瞬間は帯を出さない（マイページの行は出す）（{r}）')
        await pg.screenshot(path=os.path.join(SHOTS, 'install-first-390.png'))
        await pg.evaluate("showStamp(BY[IATA.HND.id], Date.now(), true, null, null, false)"); await pg.wait_for_timeout(300)
        await pg.evaluate("S.checkins.push({a:IATA.HND.id, t:Date.now(), acc:20, term:null}); showStamp(BY[IATA.HND.id], Date.now(), true, null, null, false)"); await pg.wait_for_timeout(300)
        await pg.evaluate("$('dStamp').open && $('dStamp').close()"); await pg.wait_for_timeout(200)
        ok(not await pg.evaluate("$('installBar').hidden"), '5 最初の印のあとから帯を出す')
        await pg.screenshot(path=os.path.join(SHOTS, 'install-after-stamp-390.png'))
        allerrs += errs; await c.close()
        c, pg, errs, reqs = await page(p, b, opens=2)
        ok(not await pg.evaluate("$('installBar').hidden") and await pg.evaluate("localStorage.getItem('soramemo.install.opens')") == '3', '5 3回目に開いたときから帯を出す')
        allerrs += errs; await c.close()
        # 6 範囲の外で断られた保留の印
        c, pg, errs, reqs = await page(p, b)
        r = await pg.evaluate("""(() => { const p = { lat:35.70, lon:139.60, acc:20 };
          return { q: ckWhyText('out_of_range', p, '', true), now: ckWhyText('out_of_range', p, '', false), other: ckWhyText('low_accuracy', p, '', true) }; })()""")
        ok(r['q'].endswith('乗った便は、フライトの ＋ から記録帳に足せます。') and r['q'].startswith(r['now']) and '記録帳' not in r['now'] and '記録帳' not in r['other'], f'6 保留の印の範囲の外だけに記録帳への道（{r}）')
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
        await pg.evaluate("""(() => { qSave([{ a:IATA.HND.id, ts:Date.now() - 60e3, t:Date.now() - 60e3, lat:35.70, lon:139.60, acc:20, cid:'x1', ok:true }]); window.__fnFail = 'out_of_range'; })()""")
        await pg.evaluate("sendCheckin = async (x, q) => ({ ok:false, reason:'out_of_range', message:'out of range' })")
        await pg.evaluate("flushQueue(true)"); await pg.wait_for_timeout(1200)
        msg = await pg.inner_text('#msg')
        ok('送れませんでした' in msg and msg.count('記録帳') == 1 and msg.rstrip().endswith('記録帳に足せます。') and '（' in msg and '記録帳に足せます）' not in msg, f'6 送り直しの文は最後に1回（{msg}）')
        allerrs += errs; await c.close()
        await b.close()
    print('errors', fails + allerrs if (fails or allerrs) else [])
    if fails or allerrs: sys.exit(1)
if __name__ == "__main__": asyncio.run(main())
