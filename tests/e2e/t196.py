# 電波・位置が悪いときの続き（11/25 stamp-edge・本人が貼った案から PM が選んだ4つ）
#   1 大まかな位置しか届かない（iOS の「正確な位置情報」が OFF など）：直し方のカードを出し、半券（判定できないボタン）は隠す。送らない。良い位置が届けば半券に戻る
#   2 位置の許可がない（ウェブ）：直し方のカード。iPhone の Safari なら 設定 › アプリ › Safari › 位置情報
#   3 送信待ち：地図・図鑑・数はその場で増え、ホームのシートと図鑑の詳しい所に「送信待ち（14:22 記録）」の札。開き直しても残る。押すと送り直す
#   4 送れて確定したら「羽田空港の印が確定しました」の札（2秒）。いくつ溜まっても時刻の順に送る
#   5 文の言い方：範囲の外・同じ日にもう一度・端末の時計のずれ・建物の中（エラーの番号や英語は出さない）
#   6 390・375 で撮る
import os, sys, json, shutil, re
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-stamp-edge')); os.makedirs(SHOTS, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
sys.path.insert(0, HERE); from stamp_perf import GEO, WATCH
HND = (35.5494, 139.7798); OUT = (35.70, 139.70)
IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1'
fails = []
def ok(cond, msg):
    print(('ok   ' if cond else 'FAIL ') + msg)
    if not cond: fails.append(msg)
async def waitjs(pg, expr, timeout=20000):
    for _ in range(timeout // 100):
        if await pg.evaluate(expr): return True
        await pg.wait_for_timeout(100)
    return False
async def page(p, w=390, h=844, ua=None):
    b = await p.chromium.launch(); kw = dict(viewport={'width':w,'height':h}, permissions=['geolocation'])
    if ua: kw['user_agent'] = ua
    c = await b.new_context(**kw)
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');" + GEO)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && window.__fake'); await pg.wait_for_timeout(500)
    await pg.evaluate('__fake.login()'); await waitjs(pg, 'S.checkins.length >= 1'); await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); HOME_POS = null; POS_LAST = null; GEO_WARM = null; homeLocStop(); window.__calls = []")
    return b, c, pg, errs
async def at(pg, ll, delay=150, acc=20):
    await pg.evaluate(f'__geo.lat = {ll[0]}; __geo.lon = {ll[1]}; __geo.delay = {delay}; __geo.acc = {acc}')
async def press(pg):
    await pg.evaluate("S.checkins.forEach(x => x.t -= 25000); HOME_POS = null; POS_LAST = null; GEO_WARM = null")
    await pg.evaluate(WATCH)
async def shot(pg, name):
    await pg.screenshot(path=os.path.join(SHOTS, name))
CARD = "(() => { const e = $('nvLocOff'); return { card: !e.hidden, t: e.innerText, bp: $('bpass').hidden, btn: [...e.querySelectorAll('button')].map(x => x.textContent) }; })()"
async def main():
    allerrs = []
    async with async_playwright() as p:
        for w, h in ((390, 844), (375, 667)):
            # 1 大まかな位置（誤差 3.2km）
            b, c, pg, errs = await page(p, w, h)
            await at(pg, HND, acc=3200); await press(pg); await pg.wait_for_timeout(10800)   # 位置の取り方は変えない：誤差 300m 超は10秒待ってから
            r = await pg.evaluate(CARD)
            ok(r['card'] and '正確な位置情報' in r['t'] and '3.2km' in r['t'] and r['bp'], f'1 {w} 大まかな位置：カードを出し、半券を隠す（{r["t"][:40]}…・半券 hidden={r["bp"]}）')
            ok(r['btn'] == ['もう一度位置を確かめる'], f'1 {w} 判定するボタンは出さない（{r["btn"]}）')
            ok(await pg.evaluate('window.__calls.length') == 0 and await pg.evaluate('__stampAt == null'), f'1 {w} 判定できない位置は送らず、ハンコも出さない')
            m = await pg.inner_text('#msg'); ok(not re.search(r'[A-Za-z]', re.sub(r'\d[\d.,]*\s*(km|m)', '', m)), f'1 {w} 英語やエラーの番号を出さない（{m}）')
            await pg.evaluate("$('homeSheet').sheetGo && $('homeSheet').sheetGo('half')"); await pg.wait_for_timeout(400)
            await shot(pg, f'approx-{w}.png')
            await at(pg, HND, acc=20); await pg.click('#nvLocOff [data-locre]'); await pg.wait_for_timeout(1200)
            r = await pg.evaluate(CARD)
            ok(not r['card'] and not r['bp'], f'1 {w} 「もう一度位置を確かめる」で良い位置が届くと半券に戻る（card={r["card"]}）')
            allerrs += errs; await b.close()
            # 2 位置の許可がない（iPhone の Safari）
            b, c, pg, errs = await page(p, w, h, ua=IPHONE)
            await pg.evaluate("navigator.geolocation.watchPosition = (ok, err) => { setTimeout(() => err && err({code:1}), 50); return 99; }")
            await press(pg); await pg.wait_for_timeout(800)
            r = await pg.evaluate(CARD)
            ok(r['card'] and r['bp'] and 'Safari' in r['t'] and '位置情報' in r['t'], f'2 {w} 許可がない：Safari の直し方のカード・半券を隠す（{r["t"][:60]}…）')
            ok(r['btn'] == ['デモで試す'], f'2 {w} 判定するボタンは出さない（{r["btn"]}）')
            await shot(pg, f'denied-{w}.png')
            allerrs += errs; await b.close()
            # 3・4 送信待ち → 開き直しても残る → 押すと送り直す → 確定の札
            b, c, pg, errs = await page(p, w, h)
            hid = await pg.evaluate("A.find(a => a.iata === 'HND').id")
            before = await pg.evaluate(f"S.checkins.filter(c => c.a === {hid}).length")
            await pg.evaluate('window.__offline = true'); await at(pg, HND); await press(pg); await pg.wait_for_timeout(1000)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())"); await pg.wait_for_timeout(300)
            pills = await pg.evaluate("(() => { const e = $('qPills'); return { on: !e.hidden, t: e.innerText.replace(/\\s+/g, ' ') }; })()")
            ok(pills['on'] and re.search(r'送信待ち（\d{1,2}:\d{2} 記録）', pills['t'].replace(' ', '').replace('記録', ' 記録')) is not None and '羽田空港' in pills['t'], f'3 {w} ホームのシートに「送信待ち（時刻 記録）」の札（{pills["t"]}）')
            ok(await pg.evaluate(f"S.checkins.filter(c => c.a === {hid}).length") == before + 1, f'3 {w} 数はその場で増える')
            await shot(pg, f'queue-home-{w}.png')
            await pg.evaluate('reload()'); await pg.wait_for_timeout(1500)   # 開き直したとき（サーバーから読み直す）
            r = await pg.evaluate(f"({{ n: S.checkins.filter(c => c.a === {hid}).length, q: S.checkins.filter(c => c.queued).length, pill: !$('qPills').hidden }})")
            ok(r['n'] == before + 1 and r['q'] == 1 and r['pill'], f'3 {w} 読み直しても送信待ちの印は残る（{r}）')
            await pg.evaluate(f'openAirport({hid})'); await pg.wait_for_timeout(500)
            zp = await pg.evaluate("(() => { const e = document.querySelector('#dAirportBody .qpills'); return e ? e.innerText.replace(/\\s+/g, '') : null; })()")
            ok(zp is not None and '送信待ち' in zp and '記録' in zp, f'3 {w} 図鑑の詳しい所にも札（{zp}）')
            await shot(pg, f'queue-zukan-{w}.png')
            await pg.evaluate('window.__offline = false'); await pg.click('#dAirportBody .qpill'); await pg.wait_for_timeout(1200)
            t = await pg.evaluate("(() => { const t = $('smToast'); return t ? { show: t.classList.contains('show'), txt: t.textContent } : null; })()")
            ok(t and t['show'] and t['txt'] == '羽田空港の印が確定しました', f'4 {w} 確定の札（{t}）')
            ok(await pg.evaluate("qLoad().length") == 0 and await pg.evaluate("!document.querySelector('#dAirportBody .qpills')") and await pg.evaluate("$('qPills').hidden"), f'4 {w} 送れたら札が消える（図鑑もホームも）')
            await shot(pg, f'confirmed-{w}.png')
            await pg.wait_for_timeout(2300)
            ok(not await pg.evaluate("$('smToast').classList.contains('show')"), f'4 {w} 確定の札は2秒で消える')
            allerrs += errs; await b.close()
        # 4 時刻の順に送る（溜まった順がばらばらでも）
        b, c, pg, errs = await page(p)
        await pg.evaluate("""(() => { const n = Date.now(), q = [[-600e3], [-1800e3], [-60e3]].map(([d]) => ({lat:35.5494, lon:139.7798, acc:20, ts:n + d, t:n + d, a:A.find(a => a.iata === 'HND').id, term:null}));
          localStorage.setItem('soramemo.queue.u1', JSON.stringify(q)); renderQueue(); })()""")
        n = await pg.evaluate("$('qPills').querySelectorAll('.qpill').length"); ok(n == 3, f'4 3件溜まると札が3つ（{n}）')
        await pg.evaluate('window.__calls = []'); await pg.click('#qPills .qpill'); await pg.wait_for_timeout(1500)
        ts = await pg.evaluate('window.__calls.map(c => c.ts)')
        ok(len(ts) == 3 and ts == sorted(ts), f'4 時刻の順に送る（{ts}）')
        t = await pg.evaluate("$('smToast').textContent"); ok('羽田空港など3件の印が確定しました' == t, f'4 3件のときの札（{t}）')
        allerrs += errs; await b.close()
        # 5 文の言い方
        b, c, pg, errs = await page(p)
        await at(pg, OUT); await press(pg); await pg.wait_for_timeout(1500)
        m = await pg.inner_text('#msg'); ok(re.fullmatch(r'いちばん近い.+まであと \d+\.\d km です。空港に入るとチェックインできます。', m) is not None, f'5 範囲の外（{m}）')
        await at(pg, OUT, acc=600); await press(pg); await pg.wait_for_timeout(11500)
        m = await pg.inner_text('#msg'); ok(m.startswith('建物の中のため、現在地が少しずれているようです。いちばん近い'), f'5 誤差が大きい範囲の外は「建物の中」を添える（{m}）')
        await at(pg, HND); await press(pg); await pg.wait_for_timeout(1500); await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        await pg.evaluate("HOME_POS = null; POS_LAST = null; GEO_WARM = null; S.checkins[S.checkins.length - 1].t -= 25000"); await pg.evaluate(WATCH); await pg.wait_for_timeout(800)
        m = await pg.inner_text('#msg'); ok(m == '本日のチェックインは完了しています。続けて今日の便を記録できます。', f'5 同じ日にもう一度（{m}）')
        await pg.evaluate("window.__fnFail = {reason:'stale_position', message:'古い位置は使えません。もう一度チェックインしてください。'}")
        await pg.evaluate(f"__geo.lat = 42.7752; __geo.lon = 141.6923"); await press(pg); await pg.wait_for_timeout(1500)
        m = await pg.inner_text('#msg'); ok('端末の日時がずれているようです。設定で『自動設定』をオンにしてください。' in m, f'5 端末の時計のずれ（{m}）')
        await pg.evaluate("window.__fnFail = null; window.__offline = true; __geo.lat = 26.2058; __geo.lon = 127.6469"); await press(pg); await pg.wait_for_timeout(1200)
        t = await pg.evaluate("($('smToast') || {}).textContent || $('msg').textContent"); ok(t == '通信が混み合っているため、いまの記録を端末に保存しました。つながり次第送ります。', f'5 通信が混んでいる（{t}）')
        allerrs += errs; await b.close()
    print('errors', allerrs if not fails else fails + allerrs)
if __name__ == "__main__": asyncio.run(main())
