import os, sys, re
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# adsb.lol の出典をどこでも押せる形に（11/21 PM・adsb.lol の返事「すぐ見える所に出典がない・押せるリンクがない」）
#   1) 字だけで見える「adsb.lol」がないか、src/index.html を読んで確かめる（チェックインの持ち場）
#      下の担当の持ち場（撮る人用・運用予想）と経営・絵（canvas）の字・コメントは除く。下の担当には ADSB_A を使ってもらう依頼を出した
#   2) 画面で：乗る便の箱・ピン止め・空港の3D の出典・ゴーアラウンドの設定・運用の専用ページの i にリンクがある
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, threading, http.server, socketserver, functools
from playwright.async_api import async_playwright
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)

# ---- 1) 字だけの adsb.lol を探す ----
OTHERS = {
  # 撮る人用（satsuei.md）
  'spRegWhy', 'spDetailHTML',
  # 運用予想（yosoku.md）
  'specialHTML', 'spbListHTML', 'spbDetailHTML', 'planeHTML', 'PRED_NOTE',
}
SRC = open(os.path.join(HERE, '..', '..', 'src', 'index.html'), encoding='utf-8').read()
src = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group(0).count('\n'), SRC, flags=re.S).split('\n')   # 何行にもわたるコメントは消す（行の番号は保つ）   # web/ は1行に詰めてあるので、元の src/ を読む
cur, plain = '(html)', []
for i, l in enumerate(src, 1):
    m = re.match(r'(?:async\s+)?function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=', l)
    if m: cur = m.group(1) or m.group(2)
    if 'adsb.lol' not in l: continue
    if '${ADSB_A}' in l or 'href="https://adsb.lol"' in l: continue   # 同じ段落にリンクがある（2回目の名前は字のままでよい）
    t = l
    t = re.sub(r'/\*.*?\*/', '', t); t = re.sub(r'(^|\s)//.*$', '', t); t = re.sub(r'<!--.*?-->', '', t)
    if 'adsb.lol' not in t: continue
    if 'fillText' in l: continue                       # 共有の絵（canvas）の字は押せない
    if '会社の機体として買えます' in l: continue        # 経営の画面（経営担当の持ち場）
    if cur in OTHERS: continue
    if cur in ('a3ShellHTML', 'a3Credit', 'A3_CREDIT'): continue       # 空港の3D の角の出典はボタン（押すと「データの出典」が開き、そこにリンク。ボタンの中にリンクは置けない）
    plain.append((i, cur, l.strip()[:80]))
check('チェックインの持ち場に字だけの adsb.lol がない', not plain, plain)
check('ADSB_A はリンクで、新しい窓・noopener', any(re.search(r'const ADSB_A = `<a class="adsbl" href="https://adsb\.lol" target="_blank" rel="noopener">adsb\.lol</a>`', l) for l in src))

# ---- 2) 画面で ----
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=WORK)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{PORT}/index_server_test.html'
LINK = 'a[href="https://adsb.lol"]'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c = await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo', bypass_csp=True)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{"planes":[]}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.abort())
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(800)
        await pg.evaluate("openGa('set')"); await pg.wait_for_timeout(400)
        r = await pg.evaluate('''(() => {
          const has = h => { const d = document.createElement("div"); d.innerHTML = h; const a = d.querySelector('a[href="https://adsb.lol"]'); return !!a && a.textContent === "adsb.lol" && a.target === "_blank" && /noopener/.test(a.rel); };
          const a3 = document.createElement("div"); a3SrcHTML(a3);
          return { ul: has(UL_SRC), pin: has(PIN_FOOT), a3: has(a3.innerHTML), ga: has($("dGaBody").innerHTML), txt: !document.body.innerText.includes("${ADSB_A}") && !$("dGaBody").innerHTML.includes("${ADSB_A}") };
        })()''')
        check('乗る便（時刻表にない便）の出典の1行にリンク', r['ul'])
        check('ピン止めの注意の1行にリンク', r['pin'])
        check('空港の3D の「データの出典」にリンク', r['a3'])
        check('ゴーアラウンドの設定の注意にリンク', r['ga'])
        check('${ADSB_A} がそのまま字で出ていない', r['txt'])
        await pg.evaluate('document.getElementById("dGa") && document.getElementById("dGa").close()')
        # 色は字のまま（下線だけ）
        col = await pg.evaluate('''(() => { const p = document.createElement("p"); p.className = "fwnote"; p.innerHTML = UL_SRC; document.body.appendChild(p);
          const a = p.querySelector("a.adsbl"), s = getComputedStyle(a), q = getComputedStyle(a.parentNode); const o = { c: s.color, pc: q.color, u: s.textDecorationLine }; p.remove(); return o; })()''')
        check('リンクの色は字の色のまま・下線', col['c'] == col['pc'] and 'underline' in col['u'], col)
        # 運用の専用ページ：i から1回で出典のリンク
        await pg.evaluate("setOpsAirport('HND'); goTab('ops')"); await pg.wait_for_timeout(1500)
        card = pg.locator('#opsHubList [data-ohub]').first
        if await card.count():
            await card.click(); await pg.wait_for_timeout(900)
            check('専用ページで i が見える', await pg.locator('#opsInfoBtn').is_visible())
            await pg.click('#opsInfoBtn'); await pg.wait_for_timeout(400)
            check('i の出典と注意に adsb.lol のリンク', await pg.locator('#dOpsSrc ' + LINK).is_visible())
        else:
            check('運用の一覧のカードが出る', False)
        check('エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
