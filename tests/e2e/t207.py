import os, sys, json, shutil, asyncio, threading, functools, http.server
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 羽田の空港ページの不合格の直し（11/26 checkin/hnd-fix・改善担当 kaizen-hnd-done-1126 の 7・6・3）。並びは変えない
#   7：375幅で「もっと見る」が縦書きにならない・天気の枠の字が切れない・12px より小さい字がない・押す所が 44px・送ったら × の後ろをぼかす
#   6：airport-now が読めないとき、見出しごと消さずに前の値と「○時○分に読んだ情報です」「もう一度」。前の値がなくても見出しと「もう一度」
#      運用の一覧のカードは、読めていないあいだ前の数に「約○分前」（同じ日・6時間まで。過ぎた時刻は出さない）
#   3：特別塗装機の行（ボタンの行）で、時刻と名前が縦に落ちない
#   偽のサーバーを使う。本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); WEB = os.path.join(ROOT, 'web')
BASE = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); WORK = os.path.join(BASE, 'hnd-fix')
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
def serve():
    shutil.rmtree(WORK, ignore_errors=True); shutil.copytree(WEB, WORK)
    open(os.path.join(WORK, 'config.js'), 'w').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=WORK))
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv.server_address[1]
now = datetime.now(timezone.utc); iso = lambda s: (now + timedelta(seconds=s)).isoformat()
PL = ['SIN', 'PVG', 'BKK', 'DEL', 'CTS', 'FUK', 'OKA']
FL = [{'no': f'JL {30 + i}', 'airline': 'JAL', 'place': PL[i % 7], 'sched': iso(600 * i), 'est': None, 'kind': 'ontime', 'term': 'T3', 'type': '77W'} for i in range(8)]
NOWD = {'at': iso(-20), 'weather': {'time': iso(-600), 'wdir': None, 'wspd': 14, 'wgst': None, 'vis_m': 10000, 'vis_plus': True, 'sky': '晴れ', 'ceil_ft': None}, 'taf': None, 'flights': {'arr': FL, 'dep': FL}}
MODE = {'now': 'ok'}   # ok・fail（airport-now を 500 にする）
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');"
async def page(b, port, w=375, h=667):
    c = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True)
    await c.add_init_script(NEW)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    async def fn(r):
        name = r.request.url.split('/functions/v1/')[1].split('?')[0]
        if name == 'airport-now' and MODE['now'] == 'fail': return await r.fulfill(status=500, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
        body = NOWD if name == 'airport-now' else {'planes': [], 'ground': [], 'at': iso(-30)} if name == 'airport-traffic' else {}
        await r.fulfill(body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
    await c.route('https://fake.supabase.co/functions/v1/**', fn)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{port}/index.html')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    return c, pg, errs
async def open_hnd(pg):
    await pg.evaluate("$('dAirport').open && $('dAirport').close()")
    await pg.evaluate("openAirport(IATA.HND.id)")
    await pg.wait_for_function("(() => { const b = document.getElementById('apNow'); return b && (b.hidden || !/読み込み中/.test(b.innerText)); })()", timeout=15000)
    await pg.wait_for_timeout(300)
SMALL = """(() => { const out = []; for(const e of document.querySelectorAll('#dAirport *')){ if(!e.offsetParent) continue; const t = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(''); if(!t) continue; const fs = parseFloat(getComputedStyle(e).fontSize); if(fs < 12) out.push(e.tagName + '.' + e.className + ':' + fs + ':' + t.slice(0, 12)); } return out; })()"""
# 押せる所：ボタンの上下2px の所を押してもそのボタンに当たるか（見た目の高さ36px のピルも、当たりは44px）
HIT = """(() => [...document.querySelectorAll('#dAirport .nowterms button, #dAirport .pinpill')].filter(b => b.offsetParent).map(b => { b.scrollIntoView({ block:'center' }); const r = b.getBoundingClientRect(), x = r.left + r.width / 2;
  const up = document.elementFromPoint(x, r.top - 2), dn = document.elementFromPoint(x, r.bottom + 2); return [b.innerText.trim(), Math.round(r.height), !!up && b.contains(up), !!dn && b.contains(dn)]; }))()"""
SHOTS = os.path.join(ROOT, 'docs', 'pm', 'shots-hnd-fix'); os.makedirs(SHOTS, exist_ok=True)
async def shot(pg, name): await pg.wait_for_timeout(300); await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
async def main():
    port = serve(); allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for (w, h) in ((375, 667), (390, 844)):
            tag = f'{w}x{h}'
            MODE['now'] = 'ok'
            c, pg, errs = await page(b, port, w, h)
            await open_hnd(pg)
            # ---- 7：375幅の崩れ
            r = await pg.evaluate("(() => { const m = document.querySelector('[data-now-more]'); const rr = m.getBoundingClientRect(); return [Math.round(rr.width), Math.round(rr.height), m.innerText]; })()")
            check(f'{tag} 「もっと見る」は横に1行（縦書きにならない）', r[0] > r[1] and r[1] <= 48 and r[2] == 'もっと見る', r)
            r = await pg.evaluate("[...document.querySelectorAll('#apNow .wxgrid b')].map(e => [e.innerText.replace(/\\n/g, '/'), e.scrollWidth <= e.clientWidth + 1])")
            check(f'{tag} 天気の枠の字が切れない（風向きが決まらない「変わりやすい」・10km以上）', all(x[1] for x in r) and any('変わり' in x[0] for x in r), r)
            check(f'{tag} 見通しの単位は小さく（10 と km以上 を分ける）', await pg.evaluate("!!document.querySelector('#apNow .wxgrid b .wxu') && document.querySelector('#apNow .wxgrid b .wxu').innerText === 'km以上'"))
            r = await pg.evaluate(SMALL)
            check(f'{tag} 空港ページに 12px より小さい字がない', r == [], r)
            await pg.evaluate("document.querySelector('[data-now-more]').scrollIntoView({ block:'center' })"); await shot(pg, f'1-more-{tag}')
            r = await pg.evaluate(HIT)
            check(f'{tag} ターミナルの絞り込みとピン止めのピル：当たりは上下に4px 広い（見た目は36px のまま）', len(r) >= 1 and all(x[2] and x[3] for x in r), r)
            # 送ったら × の後ろをぼかす（上に戻ったら消す）
            await pg.evaluate("$('dAirportBody').scrollTop = 900"); await pg.wait_for_timeout(400)
            r = await pg.evaluate("({ sc: $('dAirportBody').classList.contains('cxsc'), op: getComputedStyle(document.querySelector('#dAirportBody .cxbar'), '::before').opacity })")
            check(f'{tag} 送ると × の後ろに紙の色のぼかし', r['sc'] and float(r['op']) > 0.9, r)
            await shot(pg, f'2-x-scrolled-{tag}')
            await pg.evaluate("$('dAirportBody').scrollTop = 0"); await pg.wait_for_timeout(400)
            check(f'{tag} 上に戻るとぼかしは消える', not await pg.evaluate("$('dAirportBody').classList.contains('cxsc')"))
            # ---- 6：airport-now が読めない
            check(f'{tag} 読めた答えを空港ごとに残す', await pg.evaluate("!!nowPrev('HND')"))
            MODE['now'] = 'fail'
            await open_hnd(pg)
            r = await pg.evaluate("({ hid: $('apNow').hidden, t: $('apNow').innerText, wx: !!document.querySelector('#apNow .wxgrid'), retry: !!document.querySelector('#apNow [data-now-retry]') })")
            check(f'{tag} 読めないとき：見出しを残し、前の値（天気・便）と「○時○分に読んだ情報です」「もう一度」', not r['hid'] and '空港の今' in r['t'] and 'に読んだ情報です' in r['t'] and 'いまは読み込めませんでした' in r['t'] and r['wx'] and r['retry'], r['t'][:120])
            await pg.evaluate("$('apNow').scrollIntoView({ block:'start' })"); await shot(pg, f'3-now-fail-prev-{tag}')
            MODE['now'] = 'ok'
            await pg.click('#apNow [data-now-retry]')
            ok = False
            try: await pg.wait_for_function("!document.querySelector('#apNow .nowfail') && !!document.querySelector('#apNow .wxgrid')", timeout=10000); ok = True
            except Exception: pass
            check(f'{tag} 「もう一度」で読み直し、読めたら一言は消える', ok)
            MODE['now'] = 'fail'
            await pg.evaluate("localStorage.removeItem(NOW_MEMO)")
            await open_hnd(pg)
            r = await pg.evaluate("({ hid: $('apNow').hidden, t: $('apNow').innerText, retry: !!document.querySelector('#apNow [data-now-retry]') })")
            check(f'{tag} 前の値もないとき：見出しと「いまは読み込めませんでした」「もう一度」（消さない）', not r['hid'] and '空港の今' in r['t'] and 'いまは読み込めませんでした' in r['t'] and r['retry'], r['t'][:80])
            await shot(pg, f'4-now-fail-none-{tag}')
            MODE['now'] = 'ok'
            if w == 375:
                # 前の日の答えは使わない（24時間より前）
                r = await pg.evaluate("(() => { const o = { HND:{ at:Date.now() - 25 * 36e5, d:{ weather:{ sky:'晴れ' } } } }; localStorage.setItem(NOW_MEMO, JSON.stringify(o)); return nowPrev('HND'); })()")
                check('24時間より前の答えは前の値に使わない', r is None, r)
                # ---- 6：運用の一覧のカード（読めていないあいだは前の数に「約○分前」）
                await pg.evaluate("$('dAirport').close()")
                r = await pg.evaluate("""(() => { localStorage.removeItem(OH_STAT_MEMO); OPS_AP = 'HND';
                  const t = Date.now(); BOARD = { next_arr:[{ sched:new Date(t + 20 * 60000).toISOString() }, { sched:new Date(t - 30 * 60000).toISOString() }], next_dep:[{ sched:new Date(t + 9 * 60000).toISOString() }],
                    hours:[{ flights:10, late:2, cancel:1 }, { flights:12, late:0, cancel:0 }] }; BOARD_AP = 'HND';
                  OPS_CUR = { op:{ label:'北風運用', arr:['34L', '34R'], dep:['05'] }, prov:false }; SPECIAL_AT = t;
                  ohStatKeep(); const kept = JSON.parse(localStorage.getItem(OH_STAT_MEMO)).HND;
                  // 電波がない：答えを手放す（数字は覚えた分だけ）
                  BOARD = null; BOARD_AP = null; OPS_CUR = null; SPECIAL_AT = 0;
                  const o = JSON.parse(localStorage.getItem(OH_STAT_MEMO)); for(const k of ['bAt', 'rwAt', 'spAt']) o.HND[k] -= 5 * 60000; localStorage.setItem(OH_STAT_MEMO, JSON.stringify(o));
                  const ids = ['runway', 'board', 'special', 'late', 'strip', 'day', 'ontime'];
                  return { kept:!!kept.b && !!kept.rw && kept.sp != null, cards:ids.map(id => { const c = OH_CARDS.find(x => x[0] === id), d = document.createElement('div'); d.innerHTML = ohCardHTML(c); return [id, !d.querySelector('.na'), d.innerText.replace(/\\s+/g, ' ')]; }) }; })()""")
                check('一覧のカードの数を覚える（案内板・滑走路・特別塗装機）', r['kept'], r)
                for cid, ok, txt in r['cards']:
                    check(f'電波がないとき {cid} のカード：「—」でなく前の数と「約5分前」', ok and ('約5分前' in txt or cid == 'ontime' and '約5分前' in txt), txt)
                bd = [x for x in r['cards'] if x[0] == 'board'][0][2]
                check('案内板のカード：過ぎた時刻は出さず、次の着（20分後）を出す', '着' in bd, bd)
                r = await pg.evaluate("""(() => { const o = JSON.parse(localStorage.getItem(OH_STAT_MEMO)); for(const k of ['bAt', 'rwAt', 'spAt']) o.HND[k] -= 7 * 36e5; localStorage.setItem(OH_STAT_MEMO, JSON.stringify(o));
                  const d = document.createElement('div'); d.innerHTML = ohCardHTML(OH_CARDS.find(x => x[0] === 'late')); return !!d.querySelector('.na'); })()""")
                check('6時間より前の数は使わない（「—」に戻る）', r)
                # ---- 3：特別塗装機のボタンの行は横に並ぶ
                await pg.evaluate("document.querySelectorAll('nav.tabs button')[3].click()"); await pg.wait_for_timeout(1200)
                await pg.evaluate("opsHubOpen('special')"); await pg.wait_for_timeout(1200)
                r = await pg.evaluate("""(() => { const d = document.createElement('div'); d.className = 'fwbox'; d.innerHTML = '<ul class="spin"><li><button type="button"><span class="tm hot">—</span><span class="tx"><b>テスト塗装B</b><small>JL456・着陸に向かっている</small></span></button></li><li><div><span class="tm hot">—</span><span class="tx"><b>テスト塗装C</b><small>NH78</small></span></div></li></ul>';
                  ($('opsPSpecial').querySelector('.fwlist') || $('opsPSpecial')).appendChild(d); const rows = [...d.querySelectorAll('li')].map(li => { const tm = li.querySelector('.tm').getBoundingClientRect(), tx = li.querySelector('.tx').getBoundingClientRect(); return [Math.round(tm.left), Math.round(tx.left), Math.round(tm.top - tx.top)]; }); d.remove(); return rows; })()""")
                check('特別塗装機：ボタンの行も時刻と名前が横に並び、2行の左がそろう', len(r) == 2 and r[0][1] == r[1][1] and r[0][1] > r[0][0], r)
            allerr += errs; await c.close()
        await b.close()
    print('JS のエラー', allerr)
    if allerr: fails.append('JS のエラー')
    print('fails', fails)
    print('全部成功' if not fails else 'errors ' + str(fails))
    sys.exit(1 if fails else 0)
asyncio.run(main())
