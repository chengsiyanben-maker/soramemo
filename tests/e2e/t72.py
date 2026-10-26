import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 特別塗装機の画面：運用の「羽田に来る特別塗装機」から開く。一覧は いま飛んでいる・今日飛んだ・この30日・しばらく見ていない。
# 航空会社で絞り込み、機体を押すと今日の足あと（時刻表で埋めた便は「時刻表から」）と30日に来た空港。戻ると一覧へ
import asyncio, json, threading, http.server, socketserver, functools
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
jst = (now + timedelta(hours=9)).date()
BOARD = [
  {'reg':'JA339J','now':{'at':iso(-1),'lat':35.2,'lon':137.0,'alt_ft':24300,'callsign':'JAL113','iata':None,'phase':None,'kt':450},
   'today':[{'cs':'JAL503','dep':'HND','arr':'CTS','first':iso(-400),'last':iso(-310),'sch':False},
            {'cs':'JAL113','dep':'HND','arr':'ITM','first':iso(-25),'last':iso(-1),'sta':iso(30),'sch':True}],
   'last_day':str(jst),'arr30':{'CTS':14,'ITM':18,'HND':52}},
  {'reg':'JA819A','now':{'at':iso(-1),'lat':35.45,'lon':139.9,'alt_ft':3000,'callsign':'ANA18','iata':'HND','phase':'arr','kt':180},
   'today':[{'cs':'ANA18','dep':'ITM','arr':'HND','first':iso(-60),'last':iso(-1),'sch':False}],'last_day':str(jst),'arr30':{'HND':9}},
  {'reg':'JA05RK','now':None,'today':[{'cs':'JTA41','dep':'HND','arr':'OKA','first':iso(-300),'last':iso(-150),'sch':False}],'last_day':str(jst),'arr30':{'OKA':5}},
  {'reg':'B-16740','now':None,'today':[],'last_day':str(jst - timedelta(days=3)),'arr30':{'NRT':2}},
]
SPECIAL = [{'reg':'JA819A','name':'ポケモンジェット 赤','airline':'ANA','callsign':'ANA18','lat':35.45,'lon':139.9,'alt_ft':3000,'iata':'HND','phase':'arr','src':'x','at':iso(-1),'kind':'special'}]
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=WORK)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{PORT}/index_server_test.html'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c = await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo', bypass_csp=True)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            body = BOARD if name == 'livery_board' else SPECIAL if name == 'special_now' else []
            await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{"planes":[]}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate("setOpsAirport('HND'); goTab('ops')"); await pg.wait_for_timeout(1800)
        sp = await pg.inner_text('#opsSpecial')
        check('運用：羽田に来る特別塗装機（飛んでいる2機のうち羽田行き1機）:', '羽田に来る特別塗装機' in sp and 'ポケモンジェット 赤' in sp and '着陸に向かっている' in sp and 'JAL Jubilee' not in sp.split('いま飛んでいる特別塗装機')[0])
        await pg.click('#opsSpecial [data-spb-open=""]'); await pg.wait_for_timeout(800)
        check('すべての特別塗装機を開く:', await pg.evaluate("$('dSpecial').open"))
        t = await pg.inner_text('#dSpecialBody')
        check('いま飛んでいる2機・今日飛んだ1機・この30日1機:', await pg.locator('#dSpecialBody h4:has-text("いま飛んでいる") + ul .spbrow').count() == 2
              and await pg.locator('#dSpecialBody h4:has-text("今日飛んだ") + ul .spbrow').count() == 1 and await pg.locator('#dSpecialBody h4:has-text("この30日") + ul .spbrow').count() == 1)
        check('行き先と着く時刻（推定）・今日の便の数:', 'JL113' in t and '着（推定）' in t and '今日 2便目' in t and '羽田→新千歳→伊丹' in t)
        check('しばらく見ていない機体はたたむ:', await pg.locator('#dSpecialBody details.spbnone').count() == 1 and 'しばらく見ていない' in t)
        check('いま飛んでいる機体は、着く順:', (await pg.locator('#dSpecialBody h4:has-text("いま飛んでいる") + ul .spbrow').first.get_attribute('data-spb-reg')) == 'JA819A')
        await pg.click('[data-spb-tab="intl"]'); await pg.wait_for_timeout(300)
        check('海外で絞り込む:', await pg.locator('#dSpecialBody h4 + ul .spbrow').count() == 1 and await pg.locator('[data-spb-tab="intl"]').get_attribute('aria-pressed') == 'true')
        await pg.click('[data-spb-tab="all"]'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(WORK, 't72_list.png'))
        AXE = os.path.join(HERE, '..', 'a11y', 'node_modules', 'axe-core', 'axe.min.js')
        async def axe(name):
            if not os.path.exists(AXE): return
            await pg.add_script_tag(path=AXE); r = await pg.evaluate("axe.run(document.querySelector('dialog[open]'), {runOnly:['wcag2a','wcag2aa']})")
            v = [(x['id'], len(x['nodes'])) for x in r['violations']]; check(f'アクセシビリティ（{name}）{v}:', not v)
        await axe('一覧')
        await pg.click('[data-spb-reg="JA339J"]'); await pg.wait_for_timeout(300)
        d = await pg.inner_text('#dSpecialBody')
        check('機体の画面：いまの便と時刻:', 'JAL Jubilee Express' in d and 'JL113' in d and '着く時刻（推定）' in d and '24,300' in d)
        check('今日の足あと（2便、時刻表から・いま）:', await pg.locator('.spblegs li').count() == 2 and '時刻表から' in d and await pg.locator('.spblegs li.now').count() == 1)
        check('この30日に来た空港（多い順）:', (await pg.locator('.spbaps span').first.inner_text()).startswith('羽田'))
        check('通知が使えない端末では通知のボタンを出さない:', await pg.locator('[data-spb-push]').count() == 0)
        check('戻るボタンに移る:', await pg.evaluate("document.activeElement && document.activeElement.hasAttribute('data-spb-back')"))
        await pg.screenshot(path=os.path.join(WORK, 't72_detail.png'))
        await axe('機体の画面')
        await pg.click('[data-spb-back]'); await pg.wait_for_timeout(300)
        check('戻ると一覧、押した機体に移る:', await pg.locator('#spbMap').count() == 1 and await pg.evaluate("document.activeElement && document.activeElement.dataset.spbReg") == 'JA339J')
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
        check('閉じる:', not await pg.evaluate("$('dSpecial').open"))
        # 通知から開いたとき（#special-登録記号）は、その機体の画面
        await pg.goto(URL + '#special-JA05RK'); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(1500)
        check('リンクから機体の画面:', await pg.evaluate("$('dSpecial').open && SPB_REG === 'JA05RK'") and 'いまは地上か、記録の外' in await pg.inner_text('#dSpecialBody'))
        check('まだ始まっていない塗装は一覧に入れない:', await pg.evaluate("!('JA56AN' in LIVERY_NAMES) && 'JA609A' in LIVERY_NAMES"))
        print('errors', errs + fails); srv.shutdown(); await b.close()
asyncio.run(main())
