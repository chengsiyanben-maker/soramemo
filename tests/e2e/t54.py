import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# ステータスの先読み（そらメモ＋）と年額プランのボタン
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        # 今年のANA便（羽田→那覇・スタンダード）を2便、JAL便（羽田→新千歳・セイバー）を1便
        await pg.evaluate("""() => { const id=i=>IATA[i].id, y=new Date().getFullYear(), T=(m,d)=>new Date(y,m,d,9).getTime();
          S.flights = [{id:'x1',from:id('HND'),to:id('OKA'),dep:T(5,1),arr:T(5,1)+9e6,km:km(BY[id('HND')],BY[id('OKA')]),airline:'NH',no:'NH995',fare:'ANA:E_STD',seat:null},
                       {id:'x2',from:id('OKA'),to:id('HND'),dep:T(5,3),arr:T(5,3)+9e6,km:km(BY[id('HND')],BY[id('OKA')]),airline:'NH',no:'NH996',fare:'ANA:E_STD',seat:null},
                       {id:'x3',from:id('HND'),to:id('CTS'),dep:T(6,1),arr:T(6,1)+6e6,km:820,airline:'JL',no:'JL501',fare:'JAL:Y_SAVER',seat:null}]; S.manual = []; ACH_MEMO = null; render(); }""")
        await pg.evaluate("goTab('stats')"); await pg.wait_for_timeout(300)
        print('無料 JALの次の段階:', [l for l in (await pg.inner_text('#statusBox')).split('\n') if 'クリスタル' in l][:1])
        print('無料 先読み:', await pg.is_visible('#planJoin'), '| ぼかし:', await pg.locator('#statusBox .yp.locked').count())
        # 加入中
        await pg.evaluate('PLUS = true; renderStatus()')
        txt = (await pg.inner_text('#statusBox .plan')).replace('\n',' / ')
        print('＋ ANA 1区間と回数:', [l for l in txt.split(' / ') if '1区間' in l or 'あと' in l and '回' in l])
        await pg.click('[data-plan-car=JAL]'); await pg.wait_for_timeout(200)
        jt=(await pg.inner_text('#statusBox .plan')).split('\n'); print('＋ JAL 1区間と回数:', [l for l in jt if '1区間' in l or ('あと' in l and '回' in l)])
        await pg.select_option('#planFare', 'JAL:Y_FLEX'); await pg.wait_for_timeout(200)
        print('＋ JAL フレックス:', [l for l in (await pg.inner_text('#statusBox .plan')).split('\n') if '1区間' in l])
        # 年額プランのボタン
        await pg.evaluate('PLUS = false; renderPlusSettings()'); await pg.click('#openSettings'); await pg.wait_for_timeout(200)
        print('申し込み:', await pg.inner_text('#plusBtn'), '/', await pg.inner_text('#plusBtnYear'), '|', (await pg.inner_text('#plusInfo'))[-40:])
        print(errs); await b.close()
asyncio.run(main())
