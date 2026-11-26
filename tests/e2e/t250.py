import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 撮る人・特別塗装機の小さな足し（11/26 PM の指示・Gemini の12往復目の 2・5・7・8。撮る人用担当 satsuei/gemini-small）
#   2 いま羽田に滞在中（着いてから3時間・次の離陸まで）
#   5 撮影地から各滑走路までの距離と焦点距離の目安（撮影地の情報のシート）
#   7 特別塗装機のくわしくに「運航中／運航終了」と運航の期間、一覧の行に「終了」「○月○日まで」
#   8 特別塗装機の一覧の探す欄（登録記号・名前・航空会社）、登録記号の形なら「○○ の1日を見る」、飛行中なら「地図で見る」
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
SHOTS = os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-gemini-small'); os.makedirs(SHOTS, exist_ok=True)
now = datetime.now(timezone.utc); iso = lambda m: (now + timedelta(minutes=m)).isoformat()
today = str((now + timedelta(hours=9)).date())
SPECIAL = [{'reg':'JA819A','name':'ポケモンジェット 赤','airline':'ANA','callsign':'ANA18','lat':35.45,'lon':139.9,'alt_ft':3000,'iata':'HND','phase':'arr','src':'x','at':iso(-1),'kind':'special'}]
LBOARD = [{'reg':'JA819A','now':{'at':iso(-1),'lat':35.45,'lon':139.9,'alt_ft':3000,'callsign':'ANA18','iata':'HND','phase':'arr','kt':180},
   'today':[{'cs':'ANA18','dep':'ITM','arr':'HND','first':iso(-60),'last':iso(-1),'sch':False}],'last_day':today,'arr30':{'HND':9}},
  {'reg':'JA894A','now':None,'today':[{'cs':'ANA241','dep':'FUK','arr':'HND','first':iso(-130),'last':iso(-40),'sch':True}],'last_day':today,'arr30':{'HND':3}},
  {'reg':'JA923A','now':None,'today':[{'cs':'ANA99','dep':'CTS','arr':'HND','first':iso(-330),'last':iso(-240),'sch':True}],'last_day':today,'arr30':{'HND':2}}]
SPOT = [{'iata':'HND','name':'京浜島つばさ公園','open_kind':'always','access':'バス','parking':'あり','rules':['火気禁止'],'contact':'03-0000-0000','checked_on':'2026-11-01','sources':[]}]
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c = await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo', device_scale_factor=2)
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def h(r):
            u = r.request.url; name = u.split('fake.supabase.co')[1].split('?')[0].rsplit('/', 1)[-1]
            body = {'special_now':SPECIAL, 'livery_board':LBOARD, 'spot_info':SPOT, 'livery_plans_upcoming':[], 'airport-traffic':{'planes':[], 'at':iso(0)}}.get(name, {} if '/functions/' in u else [])
            await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/**', h); await c.route('https://fake.supabase.co/functions/**', h)
        await c.add_init_script("localStorage.setItem('soramemo.ops.hub','0'); localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','HND');")
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
        await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(1200)
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); OPS_PICKED = true; OPS_AP = 'HND'")

        # 5 距離と焦点距離
        f = await pg.evaluate("[spFocal(500, 36), spFocalTxt(spFocal(500, 36)), spFocalTxt(spFocal(3000, 36)), spFocalTxt(spFocal(40, 65))]")
        check('5：500m・中型機は 300mm（36mm×500÷60）', abs(f[0] - 300) < 0.01 and f[1] == '約300mm', f)
        check('5：遠いと「1,000mm以上」・近いと「50mmより短く」', f[2] == '1,000mm以上' and f[3] == '50mmより短く', f)
        d = await pg.evaluate("spRwyDist('HND', '京浜島つばさ公園')")
        check('5：羽田の京浜島は4本の滑走路の距離を近い順に出す', len(d) == 4 and all(d[i]['m'] <= d[i+1]['m'] for i in range(3)) and 100 < d[0]['m'] < 3000, d)
        check('5：知らない撮影地は空', await pg.evaluate("spRwyDist('HND', 'ない所').length === 0 && spRwyDistHTML('XXX', 'a') === ''"))
        await pg.evaluate("spLoadInfo('HND')"); await pg.wait_for_timeout(500)
        await pg.evaluate("$('dSpotInfoBody').innerHTML = spInfoHTML('HND', '京浜島つばさ公園'); $('dSpotInfo').showModal()"); await pg.wait_for_timeout(300)
        txt = await pg.inner_text('#dSpotInfoBody')
        check('5：撮影地の情報に「滑走路まで」と中型機・大型機の焦点距離', '滑走路まで' in txt and '中型機' in txt and '大型機' in txt and '35mm判' in txt, txt[-200:])
        await pg.locator('#dSpotInfoBody .sprwyd').scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, '01_spot_distance.png'))
        await pg.evaluate("$('dSpotInfo').close()")

        # 7 運航の期間
        t = await pg.evaluate("[spbTerm('JA228J', '2026-11-25'), spbTerm('JA828J', '2026-11-25'), spbTerm('JA828J', '2027-01-05'), spbTerm('JA819A', '2026-11-25')]")
        check('7：始まりと終わりが分かる機体は「〜（予定）」', t[0]['st'] == 'on' and t[0]['txt'] == '2026年4月1日〜2027年3月31日（予定）' and t[0]['tag'] == '', t[0])
        check('7：60日以内に終わる機体は札「12月31日まで」', t[1]['st'] == 'on' and t[1]['tag'] == '12月31日まで', t[1])
        check('7：終わった機体は「終了」', t[2]['st'] == 'end' and t[2]['tag'] == '終了' and '終了' in t[2]['txt'], t[2])
        check('7：期間が分からない機体は文が空', t[3]['st'] == 'on' and t[3]['txt'] == '' and t[3]['tag'] == '', t[3])

        # 2 滞在中
        await pg.evaluate("loadSpecial().then(() => loadSpbLive())"); await pg.wait_for_timeout(1200)
        mem = await pg.evaluate("JSON.parse(localStorage.getItem('soramemo.spStay') || '{}')")
        check('2：着陸に向かう特別塗装機を端末に覚える（登録記号・空港・時刻だけ）', 'JA819A' in mem and mem['JA819A']['iata'] == 'HND' and set(mem['JA819A']) == {'iata', 't'}, mem)
        html = await pg.evaluate("SPB_LIVE = " + json.dumps(LBOARD) + "; SPB_LIVE_AT = Date.now(); spInboundHTML()")
        check('2：40分前に着いた機体は「いま羽田空港に滞在中」', '滞在中' in html and 'ピカチュウジェットNH' in html and '次の離陸まで（推定）' in html, html[:300])
        check('2：4時間前に着いた機体は出さない・飛んでいる機体は滞在に入れない', 'ポケモンジェット 緑' not in html and html.count('ポケモンジェット 赤') == 1)
        await pg.evaluate("SPECIAL.set('JA894A', { reg:'JA894A', name:'ピカチュウジェットNH', iata:'HND', phase:'dep', callsign:'ANA242', kind:'special' })")
        html2 = await pg.evaluate("spInboundHTML()")
        check('2：離陸していった機体は滞在から外れる', 'spstay' not in html2 or 'ピカチュウジェットNH・' not in html2.split('spstay')[1], html2[:300])
        await pg.evaluate("SPECIAL.delete('JA894A')")
        old = await pg.evaluate("localStorage.setItem('soramemo.spStay', JSON.stringify({ JA1: { iata:'HND', t:Date.now() - 4 * 36e5 } })); Object.keys(spStayMem())")
        check('2：3時間を過ぎた覚えは捨てる', old == [], old)

        # 8 探す・7 一覧の札・8 地図で見る
        await pg.evaluate("openSpecial()"); await pg.wait_for_timeout(1500)
        n0 = await pg.locator('#dSpecialBody .spbrow').count()
        await pg.fill('#spbQ', 'ピカチュウ'); await pg.wait_for_timeout(300)
        names = await pg.locator('#dSpecialBody .spbrow .t b').all_text_contents()
        check('8：「ピカチュウ」で探すと名前に入る機体だけ', len(names) > 0 and len(names) < n0 and all('ピカチュウ' in x for x in names), names)
        check('8：打っても探す欄は消えない（字が残る・地図も残る）', await pg.evaluate("document.activeElement && document.activeElement.id === 'spbQ' && $('spbQ').value === 'ピカチュウ' && !!document.querySelector('#spbMap.leaflet-container')"))
        await pg.screenshot(path=os.path.join(SHOTS, '02_search.png'))
        await pg.fill('#spbQ', 'ja 819a'); await pg.wait_for_timeout(300)
        regs = await pg.locator('#dSpecialBody .spbrow .reg').all_inner_texts()
        check('8：小文字・空白でも登録記号で見つかる', regs == ['JA819A'], regs)
        await pg.fill('#spbQ', 'JA123A'); await pg.wait_for_timeout(300)
        check('8：一覧にない登録記号は「JA123A の1日を見る」', await pg.locator('#spbFindOut [data-plane="JA123A"]').count() == 1 and '見つかりません' in await pg.inner_text('#spbFindOut'))
        await pg.fill('#spbQ', ''); await pg.wait_for_timeout(300)
        check('8：消すと全部に戻る', await pg.locator('#dSpecialBody .spbrow').count() == n0)
        tags = await pg.locator('#dSpecialBody .spbterm').all_text_contents()
        check('7：一覧の行に「12月31日まで」の札（JA828J）', '12月31日まで' in tags, tags)
        await pg.click('#dSpecialBody [data-spb-reg="JA819A"]'); await pg.wait_for_timeout(500)
        per = await pg.inner_text('#dSpecialBody .spbperiod')
        check('7：くわしくに「運航中」と期間の行', '運航中' in per and '期間は発表されていません' in per, per)
        check('8：飛行中の機体に「地図で見る」', await pg.locator('#dSpecialBody [data-spb-map="JA819A"]').count() == 1)
        await pg.locator('#dSpecialBody .spbperiod').scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, '03_detail.png'))
        await pg.click('#dSpecialBody [data-spb-map="JA819A"]'); await pg.wait_for_timeout(600)
        check('8：「地図で見る」で一覧の地図にその機体の名札', await pg.evaluate("SPB_FOCUS === 'JA819A' && SPB_REG === null && !!document.querySelector('#spbMap .spbfocus')"))
        await pg.screenshot(path=os.path.join(SHOTS, '04_map_focus.png'))
        await pg.evaluate("$('dSpecial').close()"); await pg.wait_for_timeout(300)
        check('8：閉じると地図の選びを戻す', await pg.evaluate("SPB_FOCUS === null"))
        await pg.evaluate("openSpecial('JA228J')"); await pg.wait_for_timeout(600)
        per = await pg.inner_text('#dSpecialBody .spbperiod')
        check('7：期間の分かる機体は「2026年4月1日〜2027年3月31日（予定）」', '2026年4月1日〜2027年3月31日（予定）' in per, per)
        check('8：飛んでいない機体には「地図で見る」を出さない', await pg.locator('#dSpecialBody [data-spb-map]').count() == 0)
        sw = await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        check('スマホ幅で横にはみ出さない', sw)
        print('errors', errs)
        await b.close()
    print(fails if fails else '[]')
asyncio.run(main())
