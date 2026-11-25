import os, sys, re, shutil, urllib.request
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-airport-3d')); os.makedirs(SHOTS, exist_ok=True)
# 空港の3D（決定事項【11/17】・画面案 design/airport-3d 4版）
#   1 入口：羽田の空港ページだけ。数字のカードの下の小さな「3Dで見る ›」（844・667 で開いてすぐ見える）と「空港の今」のカードの中の見本の絵。ほかの空港には出さない
#   2 押したときだけ three.js を読む（開く前は読まない）。読めないときは「3Dを読み込めませんでした」ともう一度
#   3 3D：上に閉じる・題「羽田 3D／機体の位置は約1分遅れ」・視点のピル（全体／管制塔／機体）・下に「羽田の近くの機体」の一覧
#   4 名札は空の機体だけ・高さつき。押すとカード（便名・どこから・特別塗装機の札と名前・機種・登録記号・高さ・着陸まで）
#   5 「この機体から見る」でピルが便名に。機体のピルを先に押すと「見たい機体を押してください」と ×
#   6 約1分遅れ：2つの答えの間をつなぐ（真ん中の時刻なら真ん中の位置）
#   7 電池20%以下で軽い表示（「ふつうに」で戻す）。出典のシート（航法には使えません）
#   8 デモ（サーバーなし）でも空港の形は出し、「デモでは機体の位置は出ません」
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js'
THREE = os.path.join(WORK, 'three-0.160.0.module.min.js')
def get_three():   # 共通の部品で用意する（同時に流しても壊れない・11/26 test-steady）
    sys.path.insert(0, HERE); from three_local import ensure_three
    return ensure_three(THREE)
now = datetime.now(timezone.utc); iso = lambda s: (now + timedelta(seconds=s)).isoformat()
P1 = [  # 1つめの答え（90秒前）
  {'id':'a1','callsign':'JAL318','lat':35.47,'lon':139.8550,'alt_ft':2400,'kt':150,'hdg':331,'fpm':-700,'phase':'arr','dist_km':14,'type':'A359','reg':'JA01XJ','trail':[]},
  {'id':'a2','callsign':'ANA59','lat':35.50,'lon':139.86,'alt_ft':3000,'kt':200,'hdg':40,'fpm':2000,'phase':'dep','dist_km':9,'type':'B789','reg':'JA871A','trail':[]},
  {'id':'a3','callsign':'JAL109','lat':35.55,'lon':139.78,'alt_ft':0,'kt':10,'hdg':330,'fpm':0,'phase':'other','dist_km':1,'type':'B763','reg':'JA602J','trail':[]},
]
P2 = [  # 2つめの答え（30秒前）
  {**P1[0], 'lat':35.50, 'lon':139.8336, 'alt_ft':1800, 'dist_km':10.5},
  {**P1[1], 'lat':35.52, 'lon':139.88, 'alt_ft':4000},
  P1[2],
]
NOWD = {'at':iso(-20),'weather':{'time':iso(-600),'wdir':170,'wspd':14,'wgst':None,'vis_m':10000,'vis_plus':True,'sky':'晴れ','ceil_ft':None},'taf':None,
        'flights':{'arr':[{'no':'JL318','place':'FUK','time':'15:40','kind':'ok'}],'dep':[{'no':'NH59','place':'CTS','time':'15:20','kind':'ok'}]}}
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');"
SEED = """() => { const id = i => A.find(a => a.iata === i).id, at = (y,m,d) => new Date(y,m-1,d,10).getTime();
  S.checkins = [['HND',2025,12,17],['CTS',2025,12,15]].map(([i,y,m,d]) => ({a:id(i), t:at(y,m,d), acc:20, term:null}));
  for(let k=0;k<5;k++) S.checkins.push({a:id('HND'), t:at(2026,1,1)+k*864e5*10, acc:20, term:null}); S.flights = []; save(); render(); }"""
async def open_app(b, server=True, h=844, battery=None, three=True, night=False, sky='day'):
    c = await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=1, timezone_id='Asia/Tokyo')
    await c.add_init_script(NEW)
    if battery is not None: await c.add_init_script("navigator.getBattery = () => Promise.resolve({ level:%s, charging:false });" % battery)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    reqs = []
    async def three_route(r):
        reqs.append('three')
        if three: await r.fulfill(path=THREE, content_type='application/javascript', headers={'Access-Control-Allow-Origin':'*'})
        else: await r.abort()
    await c.route('https://cdn.jsdelivr.net/npm/three@**', three_route)
    calls = {'traffic':0}
    async def fn(r):
        u = r.request.url; name = u.split('/functions/v1/')[1].split('?')[0]
        if name == 'airport-traffic':
            calls['traffic'] += 1
            body = {'iata':'HND','at':iso(-90),'source':'adsb.lol','planes':P1} if calls['traffic'] == 1 else {'iata':'HND','at':iso(-30),'source':'adsb.lol','planes':P2}
        elif name == 'airport-now': body = NOWD
        else: body = {}
        await r.fulfill(body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
    await c.route('https://fake.supabase.co/functions/v1/**', fn)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    if server:
        shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_a3.html'))
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
        await pg.goto('file://' + os.path.join(WORK, 'index_a3.html'))
    else:
        await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
        await pg.goto('file://' + os.path.join(WEB, 'index.html'))
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    await pg.evaluate(SEED); await pg.wait_for_timeout(300)
    if night: await pg.evaluate("document.documentElement.dataset.night = 'on'")
    if sky: await pg.evaluate("s => { a3Night = () => s; }", sky)   # 写真の昼夜をそろえる（ふだんは日の出入りで決まる）
    return c, pg, errs, reqs, calls
async def wait_js(pg, js, timeout=20000):
    for _ in range(timeout // 200):
        if await pg.evaluate(js): return True
        await pg.wait_for_timeout(200)
    return False
async def open3d(pg, calls=None):
    await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(700)
    if calls is not None: calls['traffic'] = 0   # 空港ページの「滑走路の今」の読み込みは数えない
    await pg.click('#dAirport .a3pill [data-ap3d]')
    await wait_js(pg, "(() => { const l = document.getElementById('a3Load'); return !!l && (l.hidden || /読み込めません/.test(l.innerText)); })()")
    await pg.wait_for_timeout(1200)
async def main():
    have = get_three(); allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        # 1 入口（デモ）
        c, pg, errs, reqs, _ = await open_app(b, server=False)
        await pg.evaluate("goTab('book')"); await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(500)
        r = await pg.evaluate("(() => { const b = document.querySelector('#dAirport .a3pill button'); if(!b) return null; const r = b.getBoundingClientRect(), dl = document.querySelector('#dAirport .zk-dl').getBoundingClientRect(); return {top:r.top, bottom:r.bottom, h:r.height, below:r.top >= dl.bottom, hint:document.querySelector('#dAirport .a3pill').innerText}; })()")
        check('羽田：数字のカードの下に「3Dで見る ›」（44px・844 で開いてすぐ見える）:', bool(r) and r['h'] >= 44 and r['below'] and r['bottom'] <= 844 - 80, str(r))
        check('ピルの横に「押すと読み込みます（約0.7MB）」:', bool(r) and '押すと読み込みます（約0.7MB）' in r['hint'], str(r and r['hint']))
        check('開く前は three.js を読まない:', 'three' not in reqs)
        await pg.screenshot(path=os.path.join(SHOTS, '01-entry-pill-844.png'))
        await pg.evaluate("openAirport(IATA.CTS.id)"); await pg.wait_for_timeout(300)
        check('ほかの空港（新千歳）には出さない:', await pg.evaluate("!document.querySelector('#dAirport [data-ap3d]')"))
        if have:
            await open3d(pg)
            t = await pg.inner_text('#dAp3d')
            check('デモ：3D は開き、「デモでは機体の位置は出ません」:', await pg.evaluate("document.getElementById('dAp3d').open") and 'デモでは機体の位置は出ません' in t, t[:200])
            check('デモ：canvas に描けている（WebGL）:', await pg.evaluate("!!(A3 && A3.r)"))
            await pg.screenshot(path=os.path.join(SHOTS, '08c-demo-844.png'))
        allerr += errs; await c.close()
        # 667 でもピルが開いてすぐ見える
        c, pg, errs, _, _ = await open_app(b, server=False, h=667)
        await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(400)
        bt = await pg.evaluate("document.querySelector('#dAirport .a3pill button').getBoundingClientRect().bottom")
        check('667：ピルが開いてすぐ見える:', bt <= 667 - 70, str(bt))
        await pg.screenshot(path=os.path.join(SHOTS, '01-entry-pill-667.png'))
        allerr += errs; await c.close()
        # 2 サーバーあり：空港の今のカードの中の絵・3D
        c, pg, errs, reqs, calls = await open_app(b)
        await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(900); calls['traffic'] = 0
        card = await pg.evaluate("(() => { const n = document.querySelector('#apNow'); const k = n && n.querySelector('.a3card'); if(!k) return null; const h = n.querySelector('.nowhead').getBoundingClientRect(), r = k.getBoundingClientRect(), w = n.querySelector('.wxgrid').getBoundingClientRect(), g = k.querySelector('.a3go').getBoundingClientRect(); return {under:r.top >= h.bottom, aboveWx:r.bottom <= w.top, go:g.height, txt:k.innerText}; })()")
        check('空港の今：見出しのすぐ下に見本の絵と「3Dで見る ›」（天気の上・44px）:', bool(card) and card['under'] and card['aboveWx'] and card['go'] >= 44, str(card))
        await pg.evaluate("document.querySelector('#apNow').scrollIntoView({block:'start'})"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(SHOTS, '02c-card-844.png'))
        if not have:
            print('three.js を取れないので、3D の中の確かめは飛ばす')
        else:
            await pg.click('#apNow .a3pic'); await wait_js(pg, "(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden; })()")
            await pg.wait_for_timeout(800); await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(1200)   # 2つめの答え（20秒ごとを待たずに読む）
            check('押すと three.js を読む:', 'three' in reqs)
            hd = await pg.inner_text('#dAp3d .a3top')
            check('題「羽田 3D」と「機体の位置は約1分遅れ」:', '羽田' in hd and '3D' in hd and '約1分遅れ' in hd, hd)
            pills = await pg.evaluate("[...document.querySelectorAll('[data-a3-view]')].map(b => b.innerText + ':' + b.getAttribute('aria-pressed'))")
            check('視点のピル（全体が選ばれている）:', pills == ['全体:true', '管制塔:false', '機体:false'], str(pills))
            sh = await pg.inner_text('#a3Sheet')
            check('一覧：羽田の近くの機体・機の数・JL 318 福岡から・着陸まで約○分・34R（C）へ のように番号が先:', '羽田の近くの機体' in sh and 'JL 318' in sh and '福岡から' in sh and '着陸まで約' in sh and re.search(r'\d\d[LR]?（C）へ', sh) is not None, sh)
            check('一覧：特別塗装機の札・NH 59 新千歳へ（上昇中）:', '特別塗装機' in sh and 'NH 59' in sh and '新千歳へ' in sh and '上昇中' in sh, sh)
            check('一覧：地上の機体（JAL109）は「地上」:', 'JL 109' in sh and '地上' in sh, sh)
            chips = await pg.inner_text('#a3Chips')
            check('左上に「位置を受信中」:', '位置を受信中' in chips, chips)
            tags = await pg.evaluate("[...document.querySelectorAll('.a3tag')].map(t => t.innerText)")
            # 11/21 の見回り8 で全体の視点を寄せたので、この作り物の機体（空港の約7km 東）は景色の外。端の札（向きの矢印・着陸までの分）で出る。景色の中なら高さつき
            check('名札は空の機体だけ（地上の JL 109 は出さない）・高さつきか、景色の外は端の矢印つき:', any(('JL 318' in x) and (('m' in x) or any(a in x for a in '←→↑↓')) for x in tags) and not any('JL 109' in x for x in tags), str(tags))
            r = await pg.evaluate("(() => { const W = $('a3Stage').clientWidth; return [...document.querySelectorAll('.a3tag.edge')].map(t => { const r = t.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right), Math.round(r.top)]; }).every(([l, rr, t]) => l >= 0 && rr <= W && t >= 130); })()")
            check('端の札は画面の中（上の操作の下）:', r)
            ov = await pg.evaluate("(() => { const st = document.getElementById('a3Sheet').getBoundingClientRect(); return [...document.querySelectorAll('.a3tag')].filter(t => t.getBoundingClientRect().bottom > st.top).length; })()")
            check('名札はシートに重ならない:', ov == 0, str(ov))
            small = await pg.evaluate("[...document.querySelectorAll('#dAp3d button')].filter(b => b.offsetParent && b.getBoundingClientRect().height < 40 && !b.classList.contains('a3credit')).map(b => b.innerText || b.getAttribute('aria-label'))")
            check('押す所は 40px 以上（出典の札は押せる範囲を広げている）:', small == [], str(small))
            await pg.screenshot(path=os.path.join(SHOTS, '03-overview-844.png'))
            # 6 約1分遅れでつなぐ
            mid = await pg.evaluate("(() => { const a = A3.snaps[0], b = A3.snaps[1]; if(!a || !b) return null; const ps = a3Planes((a.t + b.t) / 2 + A3_DELAY); const q = ps.find(p => p.id === 'a1'); return q && [q.lat, q.alt_ft]; })()")
            check('2つの答えの真ん中の時刻なら真ん中の位置（約1分遅れで出す）:', bool(mid) and abs(mid[0] - 35.485) < 1e-6 and abs(mid[1] - 2100) < 1e-6, str(mid))
            ahead = await pg.evaluate("(() => { const q = a3Ahead({lat:35, lon:139, alt_ft:3000, kt:100, hdg:0, fpm:-600}, 60); return [q.lat > 35.02 && q.lat < 35.03, Math.round(q.alt_ft)]; })()")
            check('次の答えがまだのときは速さと向きで先を読む:', ahead == [True, 2400], str(ahead))
            # 4 押すとカード
            await pg.click('[data-a3-pick="a1"]'); await pg.wait_for_timeout(400)
            cd = await pg.inner_text('#a3Sheet')
            check('カード：JL 318・福岡 → 羽田・特別塗装機・A350 1号機（赤のロゴ）:', 'JL 318' in cd and '福岡 → 羽田' in cd and '特別塗装機' in cd and 'A350 1号機（赤のロゴ）' in cd, cd)
            check('カード：機種 A359・登録記号 JA01XJ・高さ・着陸まで約○分:', 'A359' in cd and 'JA01XJ' in cd and '高さ' in cd and '着陸まで' in cd and '約1分遅れ' in cd, cd)
            check('カード：「この機体から見る」「機体図鑑 ›」:', 'この機体から見る' in cd and '機体図鑑' in cd, cd)
            await pg.screenshot(path=os.path.join(SHOTS, '04-plane-card-844.png'))
            await pg.click('[data-a3-follow="a1"]'); await pg.wait_for_timeout(500)
            pills = await pg.evaluate("[...document.querySelectorAll('[data-a3-view]')].map(b => b.innerText + ':' + b.getAttribute('aria-pressed'))")
            check('「この機体から見る」でピルが「JL 318」:', pills[2] == 'JL 318:true', str(pills))
            await pg.screenshot(path=os.path.join(SHOTS, '06-follow-844.png'))
            await pg.click('[data-a3-view="tower"]'); await pg.wait_for_timeout(500)
            check('管制塔の視点（塔の上 約118m。塔は 115.7m。11/24 見回り2）:', await pg.evaluate("Math.round(A3.cam.position.y)") == 118)
            await pg.screenshot(path=os.path.join(SHOTS, '05-tower-844.png'))
            # 5 機体のピルを先に押す
            await pg.evaluate("A3.sel = null; A3.view = 'all'; a3Pills(); a3Sheet()")
            await pg.click('[data-a3-view="plane"]'); await pg.wait_for_timeout(300)
            sh = await pg.inner_text('#a3Sheet')
            check('機体のピルを先に押すと「見たい機体を押してください」と ×:', '見たい機体を押してください' in sh and await pg.evaluate("!!document.querySelector('[data-a3-unpick]')"), sh[:80])
            await pg.click('[data-a3-pick="a2"]'); await pg.wait_for_timeout(400)
            pills = await pg.evaluate("[...document.querySelectorAll('[data-a3-view]')].map(b => b.innerText + ':' + b.getAttribute('aria-pressed'))")
            check('一覧から選ぶとその機体のうしろから（ピル「NH 59」）:', pills[2] == 'NH 59:true', str(pills))
            # 7 出典
            await pg.click('#a3Credit'); await pg.wait_for_timeout(300)
            src = await pg.inner_text('#a3Sheet')
            check('出典のシート：航法には使えません・AIP JAPAN・adsb.lol（ODbL）・METAR・OpenStreetMap:', '航法には使えません' in src and 'AIP JAPAN' in src and 'adsb.lol（ODbL）' in src and 'METAR' in src and 'OpenStreetMap' in src, src[:120])
            await pg.screenshot(path=os.path.join(SHOTS, '09-sources-844.png'))
            # 667
            await pg.set_viewport_size({'width':390,'height':667}); await pg.evaluate("A3.src = false; A3.sel = null; A3.view = 'all'; a3Pills(); a3Sheet()"); await pg.wait_for_timeout(600)
            await pg.click('[data-a3-pick="a1"]'); await pg.wait_for_timeout(500)
            fit = await pg.evaluate("(() => { const b = document.querySelector('[data-a3-follow]').getBoundingClientRect(); const y = document.querySelector('#a3Sheet .a3body'); return b.bottom <= innerHeight || (!!y && y.scrollHeight > y.clientHeight); })()")   # 11/21：送るのはシートの中の .a3body（シートそのものは切り抜くだけ）
            check('667：カードはシートの中で送れる（押す所が隠れたままにならない）:', fit)
            await pg.screenshot(path=os.path.join(SHOTS, '04-plane-card-667.png'))
            # 閉じる
            await pg.click('[data-a3-close]'); await pg.wait_for_timeout(300)
            check('閉じると止まる（A3 なし・ダイアログ閉じる）:', await pg.evaluate("A3 === null && !document.getElementById('dAp3d').open"))
            check('閉じたあと空港ページは開いたまま:', await pg.evaluate("document.getElementById('dAirport').open"))
        allerr += errs; await c.close()
        if have:
            # 7 電池20%以下で軽い表示
            c, pg, errs, _, _ = await open_app(b, battery=0.15)
            await open3d(pg)
            ch = await pg.inner_text('#a3Chips')
            check('電池15%：「電池が少ないので軽い表示です」・題に「軽い表示」:', '電池が少ないので軽い表示です' in ch and '軽い表示' in await pg.inner_text('#a3Sub'), ch)
            check('軽い表示では名札を出さない:', await pg.evaluate("document.querySelectorAll('.a3tag').length") == 0)
            await pg.screenshot(path=os.path.join(SHOTS, '08b-lite-844.png'))
            await pg.click('[data-a3-normal]'); await pg.wait_for_timeout(1200)
            ch = await pg.inner_text('#a3Chips')
            check('「ふつうに」で戻る:', '軽い表示' not in ch and await pg.evaluate("A3.lite === false && !!A3.r"), ch)
            allerr += errs; await c.close()
            # 夜
            c, pg, errs, _, _ = await open_app(b, night=True, sky='night')
            await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(800)
            await pg.screenshot(path=os.path.join(SHOTS, '02n-entry-night-844.png'))
            await open3d(pg); await pg.screenshot(path=os.path.join(SHOTS, '03n-overview-night-844.png'))
            allerr += errs; await c.close()
        # 2 読めないとき
        c, pg, errs, _, _ = await open_app(b, three=False)
        await open3d(pg)
        t = await pg.inner_text('#a3Load')
        check('three.js を読めないとき「3Dを読み込めませんでした」ともう一度:', '3Dを読み込めませんでした' in t and await pg.evaluate("!!document.querySelector('[data-a3-retry]')"), t)
        allerr += errs; await c.close()
        await b.close()
    print('fails', fails)
    print('errors', fails + allerr)
asyncio.run(main())
