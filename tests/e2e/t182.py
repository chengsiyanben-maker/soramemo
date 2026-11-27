import os, sys, re
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
sys.path.insert(0, HERE); from keepls import reload_keep, goto_http
# 11/24 本人の指示：季節の印（「夏の訪問」など）と「四季がそろった」、実績の「四季の空港」「四季めぐり」を外す（却下済み「季節のスタンプ」とそろえる）
#   印をもらった画面・空港の詳しい画面・実績の画面・称号のどこにも出ない。実績の数（全体・もらった数）が2つ減っても壊れない。振り返りの季節ごとの回数（数字）は残る
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
BAD = re.compile(r'[春夏秋冬]の訪問|四季がそろった|四季の空港|四季めぐり')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':375,'height':812}, device_scale_factor=1, timezone_id='Asia/Tokyo'); await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
        # 前に「四季の空港」を称号にしていた人
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.title','season1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await goto_http(pg, os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
        await pg.evaluate("""() => {
          const id = i => A.find(a => a.iata === i).id, cs = [];
          const at = (y,m,d,h) => new Date(y,m-1,d,h).getTime();
          // 羽田を春夏秋冬すべてで（前なら「四季の空港」が取れた形）
          [1,4,7,10].forEach(m => cs.push({a:id('HND'), t:at(2025,m,10,12), acc:20, term:null}));
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:cs, flights:[], manual:[]}));
        }""")
        await reload_keep(pg)
        for _ in range(150):
            if await pg.evaluate('typeof render === "function" && typeof S !== "undefined" && S.checkins.length > 0'): break
            await pg.wait_for_timeout(200)
        await pg.wait_for_timeout(400)
        r = await pg.evaluate("""(() => { const s = achState(); return { ids: ACH.filter(x => /season/.test(x.id) || x.kind === 'fourSeason').map(x => x.id), done: [...s.done].filter(x => /season/.test(x)), seasonsKey: 'seasons' in s, title: titleName() }; })()""")
        check('実績の一覧に四季の実績がない', r['ids'] == [], r['ids'])
        check('四季の実績がもらった扱いにならない', r['done'] == [], r['done'])
        check('前に四季の称号を選んでいた人にも称号が出ない', r['title'] == '' and await pg.is_hidden('#titlePill'), r['title'])
        # 印をもらった画面
        await pg.evaluate("(() => { const a = A.find(x => x.iata === 'HND'); showStamp(a, new Date(2025,6,10,12).getTime(), false, null, null, false); })()"); await pg.wait_for_timeout(2500)
        st = await pg.inner_text('#dStampBody')
        check('印をもらった画面に季節の印がない', not BAD.search(st), BAD.findall(st))
        await pg.screenshot(path=os.path.join(WORK,'t182_stamp.png'))
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        # 空港の詳しい画面
        await pg.evaluate("openAirport(A.find(x => x.iata === 'HND').id)"); await pg.wait_for_timeout(300)
        ap = await pg.inner_text('#dAirportBody')
        check('空港の詳しい画面に春夏秋冬の印・四季がない', not BAD.search(ap) and not re.search(r'^\s*春\s*夏\s*秋\s*冬', ap, re.M), BAD.findall(ap))
        check('空港の詳しい画面は開ける（押した回数が出る）', '押した回数' in ap)
        await pg.screenshot(path=os.path.join(WORK,'t182_airport.png'))
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        # 実績の画面
        await pg.evaluate("goTab('ach')"); await pg.wait_for_timeout(400)
        body = await pg.evaluate("document.body.innerText")
        check('実績の画面に四季の実績がない', not BAD.search(body), BAD.findall(body))
        n = await pg.evaluate("(() => { const s = achState(), m = ACH.filter(x => !x.secret); return {all: m.length, got: m.filter(x => s.done.has(x.id)).length}; })()")
        check('実績の数が数えられる', n['all'] > 0 and 0 <= n['got'] <= n['all'], n)
        await pg.screenshot(path=os.path.join(WORK,'t182_ach.png'), full_page=False)
        # 振り返りの季節ごとの回数（数字）は残す
        has = await pg.evaluate("(() => { const s = yearStats(2025); return Array.isArray(s.season) && s.season.join(',') === '1,1,1,1'; })()")
        check('振り返りの季節ごとの回数の部品は残っている', has)
        check('ページのエラーがない', not errs, errs)
        await b.close()
    print('fails:', fails); sys.exit(1 if fails else 0)
asyncio.run(main())
