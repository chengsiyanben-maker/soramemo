import os, sys, re
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
sys.path.insert(0, HERE); from keepls import reload_keep, goto_http
# 11/25 本人の指示：実績の「元日の印」を外し、分類「時間と季節」を季節の言葉を使わない名前（時間帯）にする
#   印をもらった画面・実績の画面・称号のどこにも出ない。実績の数が1つ減っても壊れない。朝の印・夜の印は残る
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
BAD = re.compile(r'元日の印|時間と季節')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':375,'height':812}, device_scale_factor=1, timezone_id='Asia/Tokyo'); await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
        # 前に「元日の印」を称号にしていた人
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.title','ny'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await goto_http(pg, os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
        await pg.evaluate("""() => {
          const id = i => A.find(a => a.iata === i).id, cs = [];
          const at = (y,m,d,h) => new Date(y,m-1,d,h).getTime();
          // 元日の朝6時と夜23時（前なら「元日の印」が取れた形。朝の印・夜の印は今も取れる）
          cs.push({a:id('HND'), t:at(2026,1,1,6), acc:20, term:null}); cs.push({a:id('CTS'), t:at(2026,1,1,23), acc:20, term:null});
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:cs, flights:[], manual:[]}));
        }""")
        await reload_keep(pg)
        for _ in range(150):
            if await pg.evaluate('typeof render === "function" && typeof S !== "undefined" && S.checkins.length > 0'): break
            await pg.wait_for_timeout(200)
        await pg.wait_for_timeout(400)
        r = await pg.evaluate("""(() => { const s = achState(); return {
            ny: ACH.filter(x => x.id === 'ny' || x.kind === 'newyear' || /元日/.test(x.name)).map(x => x.id),
            cats: [...new Set(ACH.map(x => x.cat))], time: ACH.filter(x => x.cat === '時間帯').map(x => x.id),
            done: ['morn1','night1','ny'].filter(i => s.done.has(i)), marks: timeMarks(new Date(2026,0,1,6).getTime()), title: titleName() }; })()""")
        check('実績の一覧に元日の印がない', r['ny'] == [], r['ny'])
        check('分類「時間と季節」がなく「時間帯」がある', '時間と季節' not in r['cats'] and '時間帯' in r['cats'], r['cats'])
        check('分類の名前に季節の言葉がない', not any(re.search(r'季節|四季|[春夏秋冬]', c or '') for c in r['cats']), r['cats'])
        check('時間帯の実績は朝と夜の4つ', r['time'] == ['morn1','morn10','night1','night10'], r['time'])
        check('朝の印・夜の印はもらえる・元日の印はもらわない', r['done'] == ['morn1','night1'], r['done'])
        check('元日でも時間の印は朝の印だけ', r['marks'] == ['朝の印'], r['marks'])
        check('前に元日の印の称号を選んでいた人にも称号が出ない', r['title'] == '' and await pg.is_hidden('#titlePill'), r['title'])
        # 印をもらった画面
        await pg.evaluate("(() => { const a = A.find(x => x.iata === 'HND'); showStamp(a, new Date(2026,0,1,12).getTime(), false, null, null, false); })()"); await pg.wait_for_timeout(2500)
        st = await pg.inner_text('#dStampBody')
        check('印をもらった画面に元日の印がない', not BAD.search(st), BAD.findall(st))
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        # 実績の画面
        await pg.evaluate("goTab('ach')"); await pg.wait_for_timeout(400)
        body = await pg.evaluate("document.body.innerText")
        check('実績の画面に元日の印・時間と季節がない', not BAD.search(body), BAD.findall(body))
        await pg.evaluate("renderAch()"); heads = await pg.evaluate("[...document.querySelectorAll('#ach .achgrp h3')].map(h => h.textContent)")
        check('実績の画面に「時間帯」の分類が出て「時間と季節」はない', '時間帯' in heads and '時間と季節' not in heads, heads)
        n = await pg.evaluate("(() => { const s = achState(), m = ACH.filter(x => !x.secret); return {all: m.length, got: m.filter(x => s.done.has(x.id)).length}; })()")
        check('実績の数が数えられる', n['all'] > 0 and 0 <= n['got'] <= n['all'], n)
        await pg.screenshot(path=os.path.join(WORK,'t192_ach.png'), full_page=False)
        check('ページのエラーがない', not errs, errs)
        await b.close()
    print('fails:', fails); sys.exit(1 if fails else 0)
asyncio.run(main())
