import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# iPhone のアプリだけの画面（決定事項【11/19】design/ios-app 2版・ブランチ checkin/ios-app）
#   1 ブラウザ（Capacitor なし）では何も出ない：位置の説明・許可しなかった人のカード・図鑑などの電波がない帯・小さい説明（ホームの帯は 11/25 からウェブでも出す）。ホーム画面に追加の帯は今のまま
#   2 アプリ：ログインか「デモで試す」のあと、はじめてホームを開くと位置の説明（I1）。「次へ」で iPhone の確認（requestPermissions）。2回目は出ない
#   3 アプリ：許可しなかった人は半券の代わりに I1c のカード（設定の道・デモで試す・設定を開く）。デモで試すとカードが消えて半券に戻る
#   4 アプリ：半券を押して許可がないと分かったら I1e の小さいシート。代わりの1行（I3）
#   5 アプリ：カメラの小さい説明（I4c）ははじめての1回だけ。ボタンは「次へ」1つ
#   6 アプリ：電波がないとき、ホーム・運用・図鑑・フライトの頭に帯。運用は「最後に読んだ ○時○分」
#   7 アプリで隠すもの：ホーム画面に追加の帯・行・やり方のシート。保存・通知の代わりの文
#   8 字は13px以上・押す所は44px以上・横にはみ出さない（390×844・375×667）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json
from playwright.async_api import async_playwright
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
BASE = "localStorage.setItem('soramemo.onboarded','1');"
FAKE_CAP = """
window.__cap = []; window.__perm = 'prompt'; window.__afterAsk = 'granted';
const pos = () => ({ timestamp: Date.now(), coords: { latitude: 35.5494, longitude: 139.7798, accuracy: 12 } });
const denied = () => { const e = new Error('Location permission was denied'); return e; };
const plugins = {
  Geolocation: {
    checkPermissions: async () => { __cap.push(['geo.check']); return { location: __perm, coarseLocation: __perm }; },
    requestPermissions: async (o) => { __cap.push(['geo.ask', o]); __perm = __afterAsk; return { location: __perm, coarseLocation: __perm }; },
    getCurrentPosition: async (o) => { __cap.push(['geo.get', o]); if(__perm === 'denied') throw denied(); return pos(); },
    watchPosition: async (o, cb) => { __cap.push(['geo.watch', o]); if(__perm === 'denied'){ setTimeout(() => cb(null, denied()), 50); return 'cb-1'; } const t = setInterval(() => cb(pos(), null), 200); window.__geoT = t; return 'cb-7'; },
    clearWatch: async (o) => { __cap.push(['geo.clear', o]); clearInterval(window.__geoT); }
  },
  Share: { share: async (o) => { __cap.push(['share', o]); return {}; } },
  Browser: { open: async (o) => { __cap.push(['browser', o]); } }
};
window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios', registerPlugin: (n) => plugins[n], Plugins: plugins };
"""
MEASURE = """(sel) => { const out = { small: [], tiny: [], wide: [] }; const W = document.documentElement.clientWidth;
  document.querySelectorAll(sel).forEach(root => { if(!root.offsetParent && getComputedStyle(root).position !== 'fixed' && root.tagName !== 'DIALOG') return;
    root.querySelectorAll('*').forEach(el => { const r = el.getBoundingClientRect(); if(!r.width || !r.height) return;
      const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); const fs = parseFloat(getComputedStyle(el).fontSize);
      if(own && fs < 13) out.small.push(el.tagName + ':' + el.textContent.trim().slice(0, 12) + ':' + fs);
      if(el.tagName === 'BUTTON' && (r.height < 44 || r.width < 44)) out.tiny.push(el.textContent.trim().slice(0, 10) + ':' + Math.round(r.width) + 'x' + Math.round(r.height));
      if(r.right > W + 1 || r.left < -1) out.wide.push(el.tagName + ':' + el.className + ':' + Math.round(r.left) + '-' + Math.round(r.right)); }); });
  return out; }"""
async def open_page(b, init, errs, w=390, h=844):
    c = await b.new_context(viewport={'width':w,'height':h}, timezone_id='Asia/Tokyo', permissions=[]); await c.add_init_script(BASE + init)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
    return c, pg
async def close_auth(pg):
    await pg.evaluate("document.querySelector('#dAuth') && document.querySelector('#dAuth').open && document.querySelector('#dAuth').close()"); await pg.wait_for_timeout(150)
async def main():
    import shutil
    shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
    if not os.path.exists(os.path.join(WORK, 'config.js')):
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        # 1 ブラウザ
        c, pg = await open_page(b, '', errs)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800); await close_auth(pg)
        await c.set_offline(True); await pg.evaluate("window.dispatchEvent(new Event('offline'))"); await pg.wait_for_timeout(200)
        r = await pg.evaluate("({ why: $('dLocWhy').open, off: $('nvLocOff').hidden, net: ['nvNetOps','nvNetBook','nvNetLog'].every(id => $(id).hidden), home: $('nvNetHome').hidden === false && $('nvNetHome').innerText.includes('チェックインは保留して'), bp: $('bpass').hidden, push: PUSH_NG_TXT(), mic: MIC_NG_TXT() })")
        check('1 ブラウザでは位置の説明・I1c・図鑑などの電波がない帯を出さない（ホームの帯は 11/25 からウェブでも出す）', r['why'] is False and r['off'] and r['net'] and r['home'] and r['bp'] is False, r)
        check('1 ブラウザの通知・マイクの文は今のまま', 'ブラウザでは使えません' in r['push'] and 'ブラウザの設定' in r['mic'], r)
        await c.set_offline(False)
        inst = await pg.evaluate("(() => { localStorage.removeItem('soramemo.install.later'); renderInstall(); return { row: $('installRow').hidden }; })()")
        check('1 ブラウザではマイページの「ホーム画面に追加」は今のまま', inst['row'] is False, inst)
        await c.close()
        # 2 アプリ：デモで試すと位置の説明
        c, pg = await open_page(b, FAKE_CAP, errs)
        r0 = await pg.evaluate("$('dLocWhy').open")
        check('2 ログインしていない間は位置の説明を出さない', r0 is False, r0)
        await pg.evaluate("$('gateDemo').click()"); await pg.wait_for_timeout(900)
        r = await pg.evaluate("({ open: $('dLocWhy').open, t: $('dLocWhyBody').innerText, btn: [...$('dLocWhyBody').querySelectorAll('button')].map(x => x.textContent) })")
        check('2 デモで試したあと、はじめてのホームで位置の説明（I1）', r['open'] and '空港にいるかを確かめるために、位置を使います' in r['t'] and 'いる場所を送るのは、印を押すときだけです' in r['t'] and 'この iPhone の中で計算します' in r['t'], r['t'][:120])
        check('2 ボタンは「次へ」1つ（閉じる・あとでは置かない）', r['btn'] == ['次へ'], r['btn'])
        m = await pg.evaluate(MEASURE, '#dLocWhy')
        check('2 位置の説明：字13px以上・押す所44px以上・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(WORK, 't146_I1_844.png'))
        await pg.evaluate("document.querySelector('[data-nv=\"loc-next\"]').click()"); await pg.wait_for_timeout(500)
        r = await pg.evaluate("({ open: $('dLocWhy').open, ask: __cap.filter(x => x[0] === 'geo.ask').length, flag: localStorage.getItem('soramemo.native.locwhy') })")
        check('2 「次へ」で iPhone の確認（requestPermissions）を出し、閉じる', r['open'] is False and r['ask'] == 1 and r['flag'] == '1', r)
        await pg.evaluate("goTab('book'); goTab('home')"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("$('dLocWhy').open")
        check('2 2回目は出さない', r is False, r)
        await c.close()
        # 2b もう答えている人（許可済み）には出さない
        c, pg = await open_page(b, FAKE_CAP + "window.__perm = 'granted';", errs)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800); await close_auth(pg); await pg.evaluate("homeState()"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("({ open: $('dLocWhy').open, flag: localStorage.getItem('soramemo.native.locwhy'), watch: __cap.some(x => x[0] === 'geo.watch') })")
        check('2 許可済みの人には位置の説明を出さず、ホームで静かに位置を見る（checkPermissions を使う）', r['open'] is False and r['flag'] == '1', r)
        await c.close()
        # 3 許可しなかった人
        c, pg = await open_page(b, FAKE_CAP + "window.__perm = 'denied'; localStorage.setItem('soramemo.native.locwhy','1');", errs)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800); await close_auth(pg); await pg.evaluate("homeState()"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("({ off: $('nvLocOff').hidden, bp: $('bpass').hidden, t: $('nvLocOff').innerText, btn: [...$('nvLocOff').querySelectorAll('button')].map(x => x.textContent) })")
        check('3 許可しなかった人は半券の代わりに I1c のカード', r['off'] is False and r['bp'] is True and '位置が使えないので、チェックインできません' in r['t'], r)
        check('3 設定の道（設定 › アプリ › そらメモ › 位置情報）と2つのボタン', '位置情報' in r['t'] and 'アプリ' in r['t'] and r['btn'] == ['デモで試す', '設定を開く'], r)
        m = await pg.evaluate(MEASURE, '#nvLocOff')
        check('3 I1c：字13px以上・押す所44px以上・はみ出しなし（390）', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.evaluate("$('homeSheet').sheetGo && $('homeSheet').sheetGo('half')"); await pg.wait_for_timeout(400)
        await pg.screenshot(path=os.path.join(WORK, 't146_I1c_844.png'))
        # 4 半券を押して許可がない
        await pg.evaluate("$('bpass').hidden = false; delete $('bpass').dataset.nvHide; checkin()"); await pg.wait_for_timeout(15000)
        r = await pg.evaluate("({ open: $('dNvSheet').open, t: $('dNvSheetBody').innerText, msg: $('msg').textContent })")
        check('4 許可がないと分かったら I1e の小さいシート', r['open'] and '印を押すには、位置が要ります' in r['t'] and '設定を開く' in r['t'], r['t'][:80])
        check('4 代わりの1行（設定 › アプリ › そらメモ › 位置情報）', 'そらメモ › 位置情報' in r['msg'] and 'ブラウザ' not in r['msg'], r['msg'])
        m = await pg.evaluate(MEASURE, '#dNvSheet')
        check('4 I1e：字13px以上・押す所44px以上・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(WORK, 't146_I1e_844.png'))
        await pg.evaluate("document.querySelector('#dNvSheet [data-nv=\"demo\"]').click()"); await pg.wait_for_timeout(900)
        r = await pg.evaluate("({ demo, sheet: $('dNvSheet').open, off: $('nvLocOff').hidden, bp: $('bpass').hidden })")
        check('3 「デモで試す」でデモが始まり、カードが消えて半券に戻る', r['demo'] is True and r['sheet'] is False and r['off'] and r['bp'] is False, r)
        # 7 保存・通知の文・ホーム画面に追加
        r = await pg.evaluate("(() => { localStorage.removeItem('soramemo.install.later'); renderInstall(); return { row: $('installRow').hidden, bar: $('installBar').hidden, push: PUSH_NG_TXT(), mic: MIC_NG_TXT(), save: NV_TXT.save }; })()")
        check('7 アプリではホーム画面に追加の帯と行を出さない', r['row'] and r['bar'], r)
        check('7 通知・マイク・保存の代わりの文', r['push'] == 'アプリの通知は準備中です。' and 'そらメモ › マイク' in r['mic'] and 'iPhone に保存' in r['save'], r)
        r = await pg.evaluate("(() => { $('dBP').open && $('dBP').close(); doInstall(); return $('dBP').open; })()")
        check('7 ホーム画面に追加するやり方のシートは開かない', r is False, r)
        await c.close()
        # 5 カメラの小さい説明
        c, pg = await open_page(b, FAKE_CAP + "localStorage.setItem('soramemo.native.locwhy','1'); window.__perm = 'granted';", errs)
        await pg.evaluate("() => { window.zxReader = async () => { throw new Error('NotAllowedError'); }; }")
        await pg.evaluate("() => { goTab('log'); startCamera(); }"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("({ open: $('dNvSheet').open, t: $('dNvSheetBody').innerText, btn: [...$('dNvSheetBody').querySelectorAll('button')].map(x => x.textContent), scan: $('dScan').open })")
        check('5 はじめて搭乗券を読むとき、カメラの小さい説明（I4c）が先', r['open'] and 'カメラで読みます' in r['t'] and r['btn'] == ['次へ'] and r['scan'] is False, r)
        m = await pg.evaluate(MEASURE, '#dNvSheet')
        check('5 I4c：字13px以上・押す所44px以上・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(WORK, 't146_I4c_844.png'))
        await pg.evaluate("document.querySelector('[data-nv=\"perm-next\"]').click()"); await pg.wait_for_timeout(500)
        r = await pg.evaluate("({ scan: $('dScan').open, msg: $('scanMsg').textContent, flag: localStorage.getItem('soramemo.native.camwhy') })")
        check('5 「次へ」で読み取りへ進む。許可がないときの文はアプリの文', r['scan'] and 'そらメモ › カメラ' in r['msg'] and r['flag'] == '1', r)
        await pg.evaluate("() => { $('dScan').close(); startCamera(); }"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("({ sheet: $('dNvSheet').open, scan: $('dScan').open })")
        check('5 2回目は小さい説明を出さない', r['sheet'] is False and r['scan'], r)
        await pg.evaluate("$('dScan').close()")
        r = await pg.evaluate("(async () => { const p = nvPermWhy('mic'); await new Promise(r => setTimeout(r, 100)); const t = $('dNvSheetBody').innerText; $('dNvSheet').close(); await p; return t; })()")
        check('5 マイクの小さい説明（I4m）も nvPermWhy("mic") で出せる', '管制の音声を、マイクで聞き取ります' in r and '送りません' in r, r[:60])
        # 6 電波がない
        await pg.evaluate("localStorage.setItem('soramemo.native.lastread', JSON.stringify({ ap: OPS_AP, at: new Date(2026, 10, 19, 15, 2).getTime(), label: '北風運用' }))")
        await c.set_offline(True); await pg.evaluate("window.dispatchEvent(new Event('offline')); goTab('home')"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("({ h: $('nvNetHome').hidden, ht: $('nvNetHome').innerText })")
        check('6 ホームの帯「電波がありません／チェックインは保留して…」', r['h'] is False and 'チェックインは保留して' in r['ht'], r)
        m = await pg.evaluate(MEASURE, '#nvNetHome')
        check('6 帯：字13px以上・はみ出しなし', not m['small'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(WORK, 't146_I2_844.png'))
        await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(300)
        r = await pg.evaluate("({ h: $('nvNetBook').hidden, t: $('nvNetBook').innerText })")
        check('6 図鑑の帯「この iPhone の記録で見られます」', r['h'] is False and 'この iPhone の記録' in r['t'], r)
        await pg.screenshot(path=os.path.join(WORK, 't146_I5z_844.png'))
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1200)
        r = await pg.evaluate("({ h: $('nvNetOps').hidden, t: $('nvNetOps').innerText })")
        check('6 運用の帯と「最後に読んだのは 15:02（北風運用）」', r['h'] is False and '戻ると、自動で読み直します' in r['t'] and '15:02（北風運用）' in r['t'], r)
        await pg.screenshot(path=os.path.join(WORK, 't146_I5_844.png'))
        await c.set_offline(False); await pg.evaluate("window.dispatchEvent(new Event('online'))"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("['nvNetHome','nvNetOps','nvNetBook','nvNetLog'].every(id => $(id).hidden)")
        check('6 電波が戻ると帯は消える', r is True, r)
        await c.close()
        # 8 375×667
        c, pg = await open_page(b, FAKE_CAP + "window.__perm = 'denied'; localStorage.setItem('soramemo.native.locwhy','1');", errs, 375, 667)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800); await close_auth(pg); await pg.evaluate("homeState()"); await pg.wait_for_timeout(400)
        m = await pg.evaluate(MEASURE, '#nvLocOff')
        r = await pg.evaluate("(() => { const s = $('homeStrip').getBoundingClientRect(), t = document.querySelector('nav.tabs').getBoundingClientRect(); return { strip: Math.round(s.bottom), tabs: Math.round(t.top), off: $('nvLocOff').hidden }; })()")
        check('8 I1c（375×667）：字・押す所・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'] and r['off'] is False, (m, r))
        check('8 I1c（375×667）：今日の数字がタブ帯の上に見える', r['strip'] <= r['tabs'], r)
        await pg.screenshot(path=os.path.join(WORK, 't146_I1c_667.png'))
        await c.close()
        c, pg = await open_page(b, FAKE_CAP, errs, 375, 667)
        await pg.evaluate("$('gateDemo').click()"); await pg.wait_for_timeout(900)
        m = await pg.evaluate(MEASURE, '#dLocWhy')
        r = await pg.evaluate("(() => { const b = document.querySelector('[data-nv=\"loc-next\"]'); return b ? Math.round(b.getBoundingClientRect().bottom) : -1; })()")
        check('8 位置の説明（375×667）：字・押す所・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(WORK, 't146_I1_667.png'))
        await c.close()
        await b.close()
        # 9 Info.plist の理由の文は I1b-v2 の文・iPad も縦だけ
        import plistlib
        pl = plistlib.load(open(os.path.join(HERE, '..', '..', 'ios-app', 'ios', 'App', 'App', 'Info.plist'), 'rb'))
        check('9 位置の理由の文は「いる場所は印を押すときだけ送り」', '印を押すときだけ送り' in pl.get('NSLocationWhenInUseUsageDescription', '') and '近くの空港を出すとき' not in pl.get('NSLocationWhenInUseUsageDescription', ''), pl.get('NSLocationWhenInUseUsageDescription'))
        check('9 マイクの理由の文は「送りません」まで', '送りません' in pl.get('NSMicrophoneUsageDescription', ''), pl.get('NSMicrophoneUsageDescription'))
        check('9 iPad も縦だけ（UIRequiresFullScreen）', pl.get('UISupportedInterfaceOrientations~ipad') == ['UIInterfaceOrientationPortrait'] and pl.get('UIRequiresFullScreen') is True, pl.get('UISupportedInterfaceOrientations~ipad'))
        print('errors', errs + fails)
        if errs or fails: sys.exit(1)
asyncio.run(main())
