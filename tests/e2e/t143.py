import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# iPhone のアプリ（Capacitor）の中だけで働く薄い入れ物（決定事項【11/18】作り方 A・ブランチ checkin/ios-app）
#   1 ブラウザ（Capacitor なし）では何も変わらない：NATIVE は false・navigator.geolocation は元のまま・ロボット除けは今までどおり
#   2 アプリの中（偽の Capacitor）：位置は @capacitor/geolocation に回る（1回・見張り・止める・拒否は code 1）
#   3 共有：字と URL は @capacitor/share・閉じたら AbortError・画像つきは元の navigator.share
#   4 外のリンク（target=_blank・window.open）は @capacitor/browser で開く。アプリの中のリンクはそのまま
#   5 アプリの中ではロボット除け（Turnstile）と Web Push を使わない（APNs ができるまで）。ログインの画面に Turnstile の箱が出ない
#   6 ios-app/build_www.mjs（ios-app で npm ci 済みのときだけ）：www/ に capacitor.js が入り、config.js より前に読む・sw.js は入れない
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json, subprocess, shutil
from playwright.async_api import async_playwright
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
CFG = "Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { turnstileSiteKey: '1x00000000000000000000AA' }); } });"
BASE = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');" + CFG
# 偽の Capacitor：ネイティブの部品の呼ばれ方を window.__cap に残す
FAKE_CAP = """
window.__cap = []; window.__geoDeny = false; window.__shareCancel = false;
const pos = () => ({ timestamp: Date.now(), coords: { latitude: 35.5494, longitude: 139.7798, accuracy: 12 } });
const plugins = {
  Geolocation: {
    getCurrentPosition: async (o) => { __cap.push(['geo.get', o]); if(__geoDeny) throw new Error('Location permission was denied'); return pos(); },
    watchPosition: async (o, cb) => { __cap.push(['geo.watch', o]); const t = setInterval(() => cb(pos(), null), 100); window.__geoT = t; return 'cb-7'; },
    clearWatch: async (o) => { __cap.push(['geo.clear', o]); clearInterval(window.__geoT); }
  },
  Share: { share: async (o) => { __cap.push(['share', o]); if(__shareCancel) throw new Error('Share canceled'); return {}; } },
  Browser: { open: async (o) => { __cap.push(['browser', o]); } }
};
window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios', registerPlugin: (n) => plugins[n], Plugins: plugins };
"""
async def open_page(b, init, errs, w=390, h=844):
    c = await b.new_context(viewport={'width':w,'height':h}, timezone_id='Asia/Tokyo', permissions=[]); await c.add_init_script(BASE + init)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://challenges.cloudflare.com/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_turnstile.js'), content_type='application/javascript'))
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
    return c, pg
async def main():
    shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
    if not os.path.exists(os.path.join(WORK, 'config.js')):
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        # 1 ブラウザ
        c, pg = await open_page(b, '', errs)
        r = await pg.evaluate("({ n: NATIVE, cap: CAP_ON, geoOwn: Object.prototype.hasOwnProperty.call(navigator, 'geolocation'), capt: captchaOn(), ds: document.documentElement.dataset.native || '' })")
        check('1 ブラウザでは NATIVE は false・入れ物は入らない', r['n'] is False and r['cap'] is None and not r['geoOwn'] and r['ds'] == '', r)
        check('1 ブラウザではロボット除けは今までどおり（鍵があれば使う）', r['capt'] is True)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        pl = await pg.evaluate("(() => { PLUS = false; renderPlusSettings(); return { b1: $('plusBtn').hidden, info: $('plusInfo').textContent }; })()")
        check('1 ブラウザではそらメモ＋の申し込みのボタンは今までどおり', pl['b1'] is False, pl)
        await pg.screenshot(path=os.path.join(WORK, 't143_web_home.png')); await c.close()
        # 2〜5 アプリの中
        c, pg = await open_page(b, FAKE_CAP, errs)
        r = await pg.evaluate("({ n: NATIVE, cap: CAP_ON, ds: document.documentElement.dataset.native })")
        check('2 アプリの中では NATIVE・位置／共有／リンクの入れ物が入る', r['n'] is True and r['cap'] == {'geo':True,'share':True,'link':True} and r['ds'] == 'ios', r)
        g = await pg.evaluate("""new Promise(res => navigator.geolocation.getCurrentPosition(p => res({ lat: p.coords.latitude, acc: p.coords.accuracy, ts: typeof p.timestamp }), e => res({ err: e.code }), { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }))""")
        calls = await pg.evaluate("__cap.filter(x => x[0] === 'geo.get').pop()")
        check('2 1回の位置はネイティブから（緯度・精度・時刻の形はブラウザと同じ）', g.get('lat') == 35.5494 and g.get('acc') == 12 and g.get('ts') == 'number', g)
        check('2 1回の位置の設定（高い精度・時間切れ）がそのまま渡る', calls and calls[1] == {'enableHighAccuracy':True,'timeout':5000,'maximumAge':0}, calls)
        w = await pg.evaluate("""new Promise(res => { let n = 0; const id = navigator.geolocation.watchPosition(p => { n++; if(n === 3){ navigator.geolocation.clearWatch(id); setTimeout(() => res({ n, id: typeof id, clear: __cap.filter(x => x[0] === 'geo.clear').map(x => x[1]) }), 300); } }, () => {}, {}); })""")
        check('2 見張りは数の id を返し、止めるとネイティブの clearWatch に cb-7 が渡る', w['id'] == 'number' and w['clear'] == [{'id':'cb-7'}], w)
        n2 = await pg.evaluate("new Promise(res => { const before = __cap.length; setTimeout(() => res(__cap.length - before), 400); })")
        check('2 止めたあとは呼ばれない', n2 == 0, n2)
        d = await pg.evaluate("""(async () => { __geoDeny = true; const r = await new Promise(res => navigator.geolocation.getCurrentPosition(() => res('ok'), e => res(e.code))); __geoDeny = false; return r; })()""")
        check('2 拒否はブラウザと同じ code 1', d == 1, d)
        # 3 共有
        s = await pg.evaluate("""(async () => { await navigator.share({ title: 'JA01XJの1日', text: 'てすと', url: 'https://soramemo.jp/#special-JA01XJ' }); __shareCancel = true; let name = ''; try{ await navigator.share({ text: 'x' }); }catch(e){ name = e.name; } __shareCancel = false; return { last: __cap.filter(x => x[0] === 'share')[0][1], name }; })()""")
        check('3 字と URL の共有はネイティブの共有シート', s['last'].get('url') == 'https://soramemo.jp/#special-JA01XJ' and s['last'].get('text') == 'てすと', s)
        check('3 共有を閉じたら AbortError（今の「閉じたら何もしない」がそのまま効く）', s['name'] == 'AbortError', s)
        # 4 外のリンク
        await pg.evaluate("""(() => { const a = document.createElement('a'); a.href = 'https://www.odpt.org/'; a.target = '_blank'; a.id = 'capTestA'; a.textContent = 'ODPT'; document.body.appendChild(a); const i = document.createElement('a'); i.href = '#ops'; i.id = 'capTestIn'; i.textContent = 'in'; document.body.appendChild(i); })()""")
        pops = []; pg.context.on('page', lambda x: pops.append(x))
        await pg.evaluate("document.getElementById('capTestA').click()"); await pg.wait_for_timeout(200)
        await pg.evaluate("window.open('https://adsb.lol/', '_blank')"); await pg.wait_for_timeout(200)
        bw = await pg.evaluate("__cap.filter(x => x[0] === 'browser').map(x => x[1].url)")
        check('4 target=_blank と window.open の外のリンクはアプリの中のブラウザで開く', bw == ['https://www.odpt.org/', 'https://adsb.lol/'] and not pops, (bw, len(pops)))
        await pg.evaluate("document.getElementById('capTestIn').click()"); await pg.wait_for_timeout(200)
        bw2 = await pg.evaluate("__cap.filter(x => x[0] === 'browser').length")
        check('4 アプリの中のリンク（#ops）はそのまま', bw2 == 2, bw2)
        # 5 ロボット除け・通知
        r = await pg.evaluate("({ capt: captchaOn(), push: pushOK() })")
        check('5 アプリの中ではロボット除けも Web Push も使わない', r == {'capt': False, 'push': False}, r)
        await pg.evaluate("authOpen('login')"); await pg.wait_for_timeout(600)
        cap_html = await pg.evaluate("($('auCap') && $('auCap').innerHTML) || ''")
        check('5 ログインの画面に Turnstile の箱が出ない', cap_html.strip() == '', cap_html[:80])
        await pg.screenshot(path=os.path.join(WORK, 't143_app_login.png'))
        # 5 そらメモ＋の申し込みの入口はアプリの中では出さない（ログインした人でも）
        await pg.evaluate("document.querySelector('#dAuth') && document.querySelector('#dAuth').close()")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        pl = await pg.evaluate("(() => { PLUS = false; renderPlusSettings(); const a = { info: $('plusInfo').textContent, b1: $('plusBtn').hidden, b2: $('plusBtnYear').hidden }; PLUS = true; PLUS_UNTIL = null; renderPlusSettings(); a.plus = $('plusInfo').textContent; a.pb = $('plusBtn').hidden; PLUS = false; return a; })()")
        check('5 アプリの中ではそらメモ＋の申し込み・解約のボタンを出さない', pl['b1'] and pl['b2'] and pl['pb'] and 'できません' in pl['info'] and pl['plus'].startswith('加入中'), pl)
        await pg.evaluate("document.querySelector('#dAuth') && document.querySelector('#dAuth').close()"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(WORK, 't143_app_home.png')); await c.close()
        await b.close()
        # 6 build_www.mjs
        if os.path.exists(os.path.join(ROOT, 'ios-app', 'node_modules', '@capacitor', 'core')):
            out = subprocess.run(['node', os.path.join(ROOT, 'ios-app', 'build_www.mjs')], capture_output=True, text=True)
            www = os.path.join(ROOT, 'ios-app', 'www'); html = open(os.path.join(www, 'index.html'), encoding='utf-8').read() if os.path.exists(os.path.join(www, 'index.html')) else ''
            i1, i2 = html.find('<script src="capacitor.js"></script>'), html.find('<script src="config.js"></script>')
            check('6 www/ に capacitor.js が入り、config.js より前に読む', out.returncode == 0 and os.path.exists(os.path.join(www, 'capacitor.js')) and 0 <= i1 < i2, out.stderr[-200:])
            check('6 www/ にサービスワーカーと公開ページを入れない', not os.path.exists(os.path.join(www, 'sw.js')) and not os.path.exists(os.path.join(www, 'now.html')) and os.path.exists(os.path.join(www, 'config.js')))
        else:
            print('（ios-app で npm ci していないので 6 は飛ばす）')
        print('errors', errs + fails)
asyncio.run(main())
