# 季節の印を外した（11/24 本人の指示・却下済み「季節のスタンプ」とそろえる）
# 搭乗券・空港の詳しい画面・実績の画面に「○の訪問」「四季がそろった」「四季の空港」「四季めぐり」が出ないこと、
# 実績の画面が開けて数が壊れないこと、前に選んでいた称号（season1）が残らないこと、振り返りの春夏秋冬の数は残ること
import os, sys, re
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
sys.path.insert(0, HERE); from keepls import reload_keep, goto_http
BAD = re.compile(r"[春夏秋冬]の訪問|四季がそろった|四季の空港|四季めぐり")
async def main():
    ok = True
    def check(name, cond, extra=""):
        nonlocal ok
        print(("OK " if cond else "NG ") + name + (("　" + extra) if extra else "")); ok = ok and cond
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':375,'height':812}, device_scale_factor=1, timezone_id='Asia/Tokyo'); await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.title','season1');")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await goto_http(pg, os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
        # 羽田を春夏秋冬に訪れた記録（前なら「四季の空港」が取れていた形）
        await pg.evaluate("""() => {
          const id = i => A.find(a => a.iata === i).id, cs = [];
          const at = (y,m,d,h) => new Date(y,m-1,d,h).getTime();
          [[2025,4],[2025,7],[2025,10],[2026,1]].forEach(([y,m]) => cs.push({a:id('HND'), t:at(y,m,10,12), acc:20, term:null}));
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:cs, flights:[], manual:[]}));
        }""")
        await reload_keep(pg)
        for _ in range(150):
            if await pg.evaluate('typeof render === "function" && typeof S !== "undefined" && S.checkins.length > 0'): break
            await pg.wait_for_timeout(200)
        await pg.wait_for_timeout(300)
        r = await pg.evaluate("""(() => { const s = achState(); return {ids: ACH.map(x => x.id), kinds: [...new Set(ACH.map(x => x.kind))], title: titleName(), hasSeasons: 'seasons' in s,
          cats: [...new Set(ACH.map(x => x.cat))]}; })()""")
        check("実績に season1・season10 がない", 'season1' not in r['ids'] and 'season10' not in r['ids'])
        check("fourSeason の数えがない", 'fourSeason' not in r['kinds'])
        check("前に選んだ称号「四季の空港」が出ない", r['title'] == "", r['title'])
        check("「時間と季節」の見出しがない", "時間と季節" not in r['cats'] and "時間と日付" in r['cats'])
        # 搭乗券（チェックインの直後の画面）：春・夏・秋・冬のどれでも「○の訪問」が出ない
        for m in (4, 7, 10, 1):
            await pg.evaluate(f"() => {{ const a = A.find(x => x.iata === 'HND'); showStamp(a, new Date(2026,{m-1},10,12).getTime(), false, null); }}")
            await pg.wait_for_timeout(150)
            tx = await pg.inner_text('#dStampBody')
            check(f"搭乗券（{m}月）に季節の印がない", not BAD.search(tx))
        await pg.evaluate("() => { const a = A.find(x => x.iata === 'HND'); showStamp(a, new Date(2026,0,1,6,0).getTime(), false, null); }"); await pg.wait_for_timeout(150)
        tx = await pg.inner_text('#dStampBody')
        check("元日・朝の印は残る", "元日の印" in tx and "朝の印" in tx)
        await pg.evaluate("() => { const a = A.find(x => x.iata === 'HND'); showStamp(a, new Date(2026,3,10,12).getTime(), false, null); }"); await pg.wait_for_timeout(150)
        check("時間の印がない日は空の印の行を出さない", await pg.evaluate("document.querySelectorAll('#dStampBody .marks').length") == 0)
        await pg.screenshot(path=os.path.join(WORK,'t182_stamp.png')); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        # 空港の詳しい画面
        await pg.evaluate("openAirport(A.find(x => x.iata === 'HND').id)"); await pg.wait_for_timeout(300)
        tx = await pg.inner_text('#dAirportBody')
        check("空港の詳しい画面に四季の行がない", not BAD.search(tx) and not re.search(r"^春\s*夏\s*秋\s*冬", tx, re.M), "")
        check("空港の詳しい画面に階級と押した回数は残る", "押した回数" in tx)
        await pg.screenshot(path=os.path.join(WORK,'t182_airport.png'))
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        # 実績の画面
        await pg.evaluate("goTab('ach')"); await pg.wait_for_timeout(300)
        tx = await pg.inner_text('#ach'); prog = await pg.inner_text('#achProg')
        main_n = await pg.evaluate("ACH.filter(x => !x.secret).length")
        check("実績の画面が開けて季節の実績がない", len(tx) > 100 and not BAD.search(tx))
        check("達成の数の分母が実績の数と合う", prog.strip().endswith(f"/ {main_n}"), prog)
        await pg.screenshot(path=os.path.join(WORK,'t182_ach.png'), full_page=False)
        # 振り返りの春夏秋冬の数（数字）は残す
        has_chips = await pg.evaluate("typeof SEASONS !== 'undefined' && SEASONS.length === 4 && typeof seasonOf === 'function'")
        check("振り返りの季節ごとの訪問回数の部品は残る", has_chips)
        body = await pg.evaluate("document.body.innerText")
        check("どの画面にも季節の印の文言がない（開いた画面の合計）", not BAD.search(body))
        check("ページのエラーがない", not errs, json.dumps(errs, ensure_ascii=False)[:300])
        await b.close()
    print("全部成功" if ok else "失敗あり"); sys.exit(0 if ok else 1)
asyncio.run(main())
