# エアライン経営の画面を一通り押して、表示の不具合を探す（試遊版。本番にはつながない）
#   node tools/build.mjs && node tools/build_play.mjs <フォルダ> && python3 tools/play/sweep_ui.py <フォルダ> [方針…]
#   方針ごとに：資金を足して方針を変え、機体を買って路線に入れる → 会社・路線・機体・守り神の各画面で、ボタンを順に押す
#   （売る・返す・はじめから などの消える操作は押さない） → 押すたびに、画面の文字に NaN・undefined・[object・Infinity がないか、エラーがないかを見る
#   → 3日進めて朝のまとめも見る
import asyncio, http.server, threading, functools, sys, re, time, os
from playwright.async_api import async_playwright

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'play-out')
POL = sys.argv[2:] or ['fsc', 'mcc', 'lcc', 'regional', 'cargo', 'pj']
SKIP = re.compile(r'data-sell|data-lease-return|data-mk-cancel|data-sdel|data-cs-end|data-inv-withdraw|ally_leave|data-ally-leave|data-ally-kick|playReset|data-remove-friend|schedAuto')
BAD = re.compile(r'NaN|undefined|\[object|Infinity|null円|null万')

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8766), functools.partial(H, directory=OUT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
issues = []
def note(pol, kind, what, detail=''):
    k = (pol, kind, what, str(detail)[:120])
    if k in [(a, b, c, str(d)[:120]) for a, b, c, d in issues]: return
    issues.append((pol, kind, what, detail)); print(f'  [{kind}] {what} … {str(detail)[:240]}')

async def idle(pg):
    for _ in range(600):
        if await pg.evaluate('() => window.play && window.play.busy() === 0'): break
        await pg.wait_for_timeout(100)
    await pg.wait_for_timeout(250)

async def scan(pg, pol, where):
    for v in ['co', 'routes', 'fleet', 'gods']:
        t = await pg.evaluate(f'() => (document.getElementById("v-{v}") || {{}}).innerText || ""')
        for m in BAD.finditer(t):
            note(pol, '表示', f'{where}：{v} の画面に「{m.group(0)}」', t[max(0, m.start() - 60):m.end() + 40].replace('\n', ' '))
        for m in re.finditer(r'搭乗率 (\d+)%', t):
            if int(m.group(1)) > 100: note(pol, '表示', f'{where}：搭乗率が100%を超える', m.group(0))
    msg = await pg.evaluate('() => (document.getElementById("coMsg") || {}).innerText || ""')
    if '保存できませんでした' in msg: note(pol, '操作', f'{where}：「保存できませんでした」（サーバーの断りに日本語の知らせがない）', await pg.evaluate('() => window.__lastErr || ""'))

async def run(b, pol):
    print(f'\n=== 方針 {pol} ===')
    c = await b.new_context(viewport={'width': 400, 'height': 860}); pg = await c.new_page()
    pg.on('pageerror', lambda e: note(pol, 'エラー', 'ページのエラー', str(e)[:300]))
    pg.on('console', lambda m: note(pol, 'エラー', 'console', m.text[:300]) if m.type == 'error' and 'play.invalid' not in m.text and 'Failed to load resource' not in m.text else None)
    await pg.goto('http://127.0.0.1:8766/index.html')
    for _ in range(600):
        if await pg.evaluate('() => document.getElementById("playLoad").hidden'): break
        await pg.wait_for_timeout(200)
    await idle(pg)
    # サーバーの断りを覚えておく（「保存できませんでした」のとき、何で断られたかを出す）
    await pg.evaluate('''() => { const o = sb.rpc.bind(sb); sb.rpc = async (n, a) => { const r = await o(n, a); if (r.error) window.__lastErr = n + ': ' + r.error.message; return r; }; }''')
    await pg.evaluate("async () => { await play.sql(`update companies set cash = cash + 5000000, rating = 5`); }")
    await pg.evaluate(f"async () => {{ await coRpc('co3_set_policy', {{p_policy:'{pol}'}}); }}"); await idle(pg)
    # 機体を買って路線に入れる
    await pg.evaluate("""async () => { const {data} = await sb.rpc('co_hangar'); const seen = new Set();
      for (const h of data) { if (seen.has(h.icao) || seen.size >= 3) continue; seen.add(h.icao); await coRpc('co_buy', {p_ride: h.ride}); }
      if (CO.small) for (const t of (CO.small || []).slice(0, 1)) await coRpc('co3_buy_small', {p_code: t.code});
      const rs = coRoutes(); let i = 0;
      for (const a of CO.fleet) { const r = rs[i++ % rs.length]; if (a.kind === 'freighter') continue; await coRpc('co_assign', {p_aircraft: a.id, p_route: r.k}); } }""")
    await idle(pg)
    for v in ['co', 'routes', 'fleet', 'gods']:
        await pg.evaluate(f"goTab('{v}')"); await idle(pg)
        await pg.evaluate('() => document.querySelectorAll("details").forEach(d => d.open = true)')
        await scan(pg, pol, f'{v} を開いた')
        # 押せるボタンを順に（押すと描き直されるので、毎回数え直す）
        done = set()
        for _ in range(80):
            cands = await pg.evaluate(f'''() => [...document.querySelectorAll("#v-{v} button:not([disabled]), #v-{v} [role=tab]")]
              .filter(b => b.offsetParent).map((b, i) => ({{i, key: b.outerHTML.slice(0, 160), text: b.innerText.trim().slice(0, 30)}}))''')
            nxt = next((x for x in cands if x['key'] not in done and not SKIP.search(x['key'])), None)
            if not nxt: break
            done.add(nxt['key'])
            try:
                await pg.evaluate(f'''() => {{ const b = [...document.querySelectorAll("#v-{v} button:not([disabled]), #v-{v} [role=tab]")].filter(b => b.offsetParent)[{nxt['i']}]; b && b.click(); }}''')
            except Exception as e:
                note(pol, 'エラー', f'{v}：「{nxt["text"]}」が押せない', e); continue
            await idle(pg)
            await pg.evaluate('() => document.querySelectorAll("details").forEach(d => d.open = true)')
            await scan(pg, pol, f'{v}：「{nxt["text"]}」を押したあと')
            await pg.evaluate("() => { document.getElementById('coMsg') && (document.getElementById('coMsg').innerText = ''); window.__lastErr = ''; }")
            if not await pg.evaluate(f"() => document.getElementById('v-{v}').classList.contains('on')"): await pg.evaluate(f"goTab('{v}')"); await idle(pg)
        print(f'  {v}：{len(done)}個のボタンを押した')
    for d in range(3):
        await pg.evaluate('async () => { await play.advance(1); }'); await idle(pg)
        await pg.evaluate("async () => { await reload(); await loadCompanyServer(); DIRTY.game = true; goTab('co'); }"); await idle(pg)
        await scan(pg, pol, f'{d + 1}日進めたあと')
    await c.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for pol in POL:
            try: await run(b, pol)
            except Exception as e: note(pol, '止まった', '調べる道具が止まった', e)
        await b.close()
    print(f'\n=== まとめ：{len(issues)}件 ===')
    for x in issues: print('\t'.join(str(y)[:300] for y in x))
asyncio.run(main())
