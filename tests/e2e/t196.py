# 電波・位置が悪いときの続き（11/25 stamp-edge・本人が貼った案の 1〜4）
#   1 iPhone で「正確な位置情報」が OFF（誤差が数km）：何が足りないかと直し方のカード。送らない・ハンコを出さない・判定できないボタン（もう一度）は出さない
#   1 位置の許可がない（ウェブ）：直し方のカード、ホームの半券の代わりに「位置が使えない」のカード
#   2 送信待ち：その場で数と図鑑に入り、読み直しても残る。ホームのシートと図鑑の詳しい所に「送信待ち（14:22 記録）」の札。押すと送り直す。いくつ溜まっても記録した順に送る
#   3 送れて確定したら「羽田空港の印が確定しました」の札（2秒）
#   4 文の言い方（通信が混み合っている・電波がない・範囲の外・同じ日にもう一度・ずれ・時計のずれ）。エラーの英語は出さない
#   390・375 で撮る（docs/pm/shots-stamp-edge/）
import os, sys, json, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-stamp-edge')); os.makedirs(SHOTS, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
HND = (35.5494, 139.7798); CTS = (42.7752, 141.6923); NEAR_HND = (35.574, 139.7798)   # 羽田の判定範囲の外・残り 1km 未満
IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1'
# 偽の位置（stamp_perf の GEO に「許可がない」を足したもの）
GEO = """window.__geo = {delay:150, acc:20, lat:35.5494, lon:139.7798, deny:false};
(() => { const W = new Map(); let n = 0;
  const pos = () => ({coords:{latitude:__geo.lat, longitude:__geo.lon, accuracy:__geo.acc}, timestamp:Date.now()});
  const g = { watchPosition(ok, ng){ const id = ++n; W.set(id, setTimeout(() => { if(!W.has(id)) return; if(__geo.deny) ng && ng({code:1, message:'denied'}); else ok(pos()); }, __geo.delay)); return id; },
    clearWatch(id){ clearTimeout(W.get(id)); W.delete(id); },
    getCurrentPosition(ok, ng){ setTimeout(() => __geo.deny ? ng && ng({code:1}) : ok(pos()), __geo.delay); } };
  Object.defineProperty(navigator, 'geolocation', {configurable:true, get(){ return g; }}); })();"""
WATCH = """() => { window.__stampAt = null; const d = document.getElementById('dStamp');
  new MutationObserver(() => { if(d.open && __stampAt == null) __stampAt = performance.now(); }).observe(d, {attributes:true, attributeFilter:['open']});
  document.getElementById('checkin').dispatchEvent(new MouseEvent('click', {detail:0, bubbles:true})); }"""
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
    b = await p.chromium.launch()
    kw = dict(viewport={'width':w,'height':h}, permissions=['geolocation'], device_scale_factor=2)
    if ua: kw['user_agent'] = ua
    c = await b.new_context(**kw)
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');" + GEO)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && window.__fake'); await pg.wait_for_timeout(500)
    await pg.evaluate('__fake.login()'); await waitjs(pg, 'S.checkins.length >= 1'); await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); HOME_POS = null; POS_LAST = null; GEO_WARM = null; homeLocStop(); S.checkins.forEach(x => x.t -= 3*36e5)")
    return b, c, pg, errs
async def at(pg, ll, acc=20):
    await pg.evaluate(f'__geo.lat = {ll[0]}; __geo.lon = {ll[1]}; __geo.acc = {acc}; HOME_POS = null; POS_LAST = null; GEO_WARM = null')
async def press(pg, wait=900):
    await pg.evaluate(WATCH); await pg.wait_for_timeout(wait)
async def closeall(pg):
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
QLEN = "JSON.parse(localStorage.getItem('soramemo.queue.u1') || '[]').length"
async def main():
    allerrs = []
    async with async_playwright() as p:
        for (w, h) in [(390, 844), (375, 667)]:
            sz = f'{w}x{h}'
            # 1 正確な位置情報が OFF（iPhone・誤差 3km）
            b, c, pg, errs = await page(p, w, h, IPHONE)
            await pg.evaluate('window.__calls = []'); await at(pg, HND, acc=3000); await press(pg, 10800)   # 誤差が大きいと位置は10秒待つ（取り方は変えていない）
            r = await pg.evaluate("({open: $('dNvSheet').open, kind: $('dNvSheetBody').dataset.ck, txt: $('dNvSheetBody').innerText, btns: [...$('dNvSheetBody').querySelectorAll('button')].map(x => x.textContent), stamp: __stampAt != null, calls: window.__calls.length})")
            ok(r['open'] and r['kind'] == 'precise' and '正確な位置情報' in r['txt'] and '設定' in r['txt'] and 'Safari' in r['txt'], f'{sz} 1 正確な位置情報 OFF のカード（{r["txt"][:60]}）')
            ok(not r['stamp'] and r['calls'] == 0, f'{sz} 1 ハンコを出さず、送らない（送った {r["calls"]}回）')
            ok(not any('もう一度' in x or 'チェックイン' in x for x in r['btns']), f'{sz} 1 判定できないボタンは出さない（{r["btns"]}）')
            await pg.screenshot(path=os.path.join(SHOTS, f'precise-off-{w}.png'))
            allerrs += errs; await b.close()
            # 1 位置の許可がない（ウェブ）
            b, c, pg, errs = await page(p, w, h, IPHONE)
            await pg.evaluate('__geo.deny = true'); await press(pg, 800)
            r = await pg.evaluate("({open: $('dNvSheet').open, kind: $('dNvSheetBody').dataset.ck, txt: $('dNvSheetBody').innerText, card: !$('nvLocOff').hidden, bp: $('bpass').hidden})")
            ok(r['open'] and r['kind'] == 'denied' and '位置の許可' in r['txt'], f'{sz} 1 許可がないときのカード（{r["txt"][:40]}）')
            await pg.screenshot(path=os.path.join(SHOTS, f'denied-sheet-{w}.png'))
            await closeall(pg); await pg.wait_for_timeout(200)
            ok(r['card'] and r['bp'], f'{sz} 1 ホームは半券の代わりに「位置が使えない」のカード（card {r["card"]}・半券を隠す {r["bp"]}）')
            await pg.screenshot(path=os.path.join(SHOTS, f'denied-home-{w}.png'))
            await pg.click('#nvLocOff [data-nv="demo"]'); await pg.wait_for_timeout(600)
            ok(await pg.evaluate('demo === true'), f'{sz} 1 カードの「デモで試す」が動く')
            allerrs += errs; await b.close()
            # 2・3・4 送信待ち（電波はあるのに届かない＝通信が混み合っている）
            b, c, pg, errs = await page(p, w, h)
            hnd = await pg.evaluate("A.find(a => a.iata === 'HND').id"); n0 = await pg.evaluate(f'S.checkins.filter(c => c.a === {hnd}).length')
            await pg.evaluate('window.__offline = true'); await at(pg, HND); await press(pg)
            m = await pg.inner_text('#msg'); ok('通信が混み合っているため、いまの記録を端末に保存しました。つながり次第送ります。' in m, f'{sz} 4 通信が混んでいるときの文（{m}）')
            ok(await pg.evaluate(QLEN) == 1, f'{sz} 2 保留に入る')
            await closeall(pg); await pg.evaluate('reload()'); await pg.wait_for_timeout(900)
            r = await pg.evaluate(f"({{n: S.checkins.filter(c => c.a === {hnd}).length, q: S.checkins.filter(c => c.queued).length, vis: visited().has({hnd})}})")
            ok(r['n'] == n0 + 1 and r['q'] == 1 and r['vis'], f'{sz} 2 読み直しても数と図鑑に残る（{r}）')
            bar = await pg.inner_text('#queueBar'); tags = await pg.evaluate("document.querySelectorAll('#queueBar .qtag').length")
            import re
            ok(tags == 1 and re.search(r'送信待ち（\d{1,2}:\d{2} 記録）', bar) and '羽田空港' in bar, f'{sz} 2 ホームのシートに送信待ちの札（{bar[:60]}）')
            await pg.evaluate("$('homeSheet') && typeof sheetSnap === 'function' ? sheetSnap('home', 'full') : 0"); await pg.wait_for_timeout(400)
            await pg.evaluate("$('queueBar').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(300)
            await pg.screenshot(path=os.path.join(SHOTS, f'queue-home-{w}.png'))
            await pg.evaluate(f'openAirport({hnd})'); await pg.wait_for_timeout(500)
            zt = await pg.evaluate("[...document.querySelectorAll('#dAirportBody .qtags .qtag')].map(x => x.textContent)")
            hist = await pg.evaluate("[...document.querySelectorAll('#dAirportBody .hist .qw')].length")
            ok(len(zt) == 1 and '送信待ち（' in zt[0] and hist == 1, f'{sz} 2 図鑑の詳しい所に送信待ちの札（{zt}・記録の行 {hist}）')
            await pg.screenshot(path=os.path.join(SHOTS, f'queue-zukan-{w}.png'))
            # 押すと送り直す（まだ届かない → 残る）
            await pg.click('#dAirportBody .qtag'); await pg.wait_for_timeout(500)
            ok(await pg.evaluate(QLEN) == 1, f'{sz} 2 届かないうちは送信待ちのまま')
            await closeall(pg)
            # いくつ溜まっても記録した順に：前の時刻の分を後ろに足しておく（並びが逆でも時刻順に送る）
            await pg.evaluate("""(() => { const k = 'soramemo.queue.u1', q = JSON.parse(localStorage.getItem(k)); const t = q[0].ts;
              q[0].ts = t; q.push({lat:%f, lon:%f, acc:20, ts:t - 2*36e5, a:A.find(a => a.iata === 'CTS').id, term:null}); localStorage.setItem(k, JSON.stringify(q)); renderQueue(); })()""" % CTS)
            ok(await pg.evaluate("document.querySelectorAll('#queueBar .qtag').length") == 2, f'{sz} 2 2件の札')
            await pg.evaluate('window.__offline = false; window.__calls = []')
            await pg.click('#queueBar .qtag'); await pg.wait_for_timeout(1200)
            calls = await pg.evaluate('window.__calls.map(c => c.ts)')
            ok(len(calls) == 2 and calls[0] < calls[1], f'{sz} 2 押すと送り直し、記録した順に送る（{calls}）')
            t = await pg.evaluate("(() => { const t = $('smToast'); return t ? {show: t.classList.contains('show'), txt: t.textContent} : null; })()")
            ok(t and t['show'] and '印が確定しました' in t['txt'] and '2件' in t['txt'], f'{sz} 3 確定の札（{t}）')
            await pg.screenshot(path=os.path.join(SHOTS, f'confirmed-{w}.png'))
            await pg.wait_for_timeout(2300)
            ok(not await pg.evaluate("$('smToast').classList.contains('show')"), f'{sz} 3 札は2秒で消える')
            ok(await pg.evaluate(QLEN) == 0 and await pg.is_hidden('#queueBar') and await pg.evaluate('!S.checkins.some(c => c.queued)'), f'{sz} 2 送れたら札が消え、本物の記録に入れ替わる')
            allerrs += errs; await b.close()
            if w != 390: continue
            # 3 1件だけのとき：「羽田空港の印が確定しました」・電波がないときの文
            b, c, pg, errs = await page(p, w, h)
            await c.set_offline(True); await at(pg, HND); await press(pg)
            m = await pg.inner_text('#msg'); ok('電波が届かないため、いまの記録を端末に保存しました。つながり次第送ります。' in m, f'4 電波がないときの文（{m}）')
            await closeall(pg); await c.set_offline(False); await pg.evaluate('window.dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(1200)
            t = await pg.evaluate("$('smToast') ? $('smToast').textContent : ''")
            ok(t == '羽田空港の印が確定しました', f'3 1件の確定の札（{t}）')
            allerrs += errs; await b.close()
            # 4 文の言い方
            b, c, pg, errs = await page(p, w, h)
            await at(pg, (35.70, 139.70)); await press(pg, 1500)
            m = await pg.inner_text('#msg'); ok(re.search(r'いちばん近い.+まであと [\d.,]+ km です。空港に入るとチェックインできます。', m), f'4 範囲の外（{m}）')
            await pg.evaluate(f"S.checkins.push({{a:{hnd}, t:Date.now() - 60000, acc:20, term:null}})"); await at(pg, HND); await press(pg, 800)
            m = await pg.inner_text('#msg'); ok(m == '本日のチェックインは完了しています。続けて今日の便を記録できます。', f'4 同じ日にもう一度（{m}）')
            await at(pg, NEAR_HND, acc=900); await press(pg, 11000)
            m = await pg.inner_text('#msg'); ok('建物の中のため、現在地が少しずれているようです。' in m, f'4 誤差が残りの距離より大きい範囲の外は「ずれている」（{m}）')
            r = await pg.evaluate("[ckWhyText('stale_position', null, 'x'), ckWhyText('stale_position', null, '24時間以上前のチェックインは送れません。', true), ckWhyText('bad_request', null, 'FunctionsHttpError 500'), ckWhyText('server', null, 'x'), ckWhyText('low_accuracy', null, 'x')]")
            ok(r[0] == '端末の日時がずれているようです。設定で『自動設定』をオンにしてください。', f'4 時計のずれ（{r[0]}）')
            ok(r[1].startswith('24時間以上前'), f'4 保留の古い分はサーバーの文のまま（{r[1]}）')
            ok('サーバーで問題が起きました' in r[2] and 'Error' not in r[2] and 'サーバーで問題' in r[3], f'4 英語は出さない（{r[2]}）')
            ok(r[4].startswith('建物の中のため、現在地が少しずれているようです。'), f'4 誤差が大きい（{r[4]}）')
            allerrs += errs; await b.close()
    print('errors', allerrs if not fails else fails + allerrs)
if __name__ == "__main__": asyncio.run(main())
