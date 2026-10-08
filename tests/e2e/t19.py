import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, base64
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(500)
        # 訪問回数 3/5/20/50 の空港を用意
        await pg.evaluate("""() => { const id = i => A.find(a => a.iata === i).id, cs = []; let t = Date.parse('2026-01-01T12:00:00+09:00');
          for(const [i,n] of [['WKJ',3],['KUH',5],['HKD',20],['CTS',49],['AKJ',1]]) for(let k=0;k<n;k++) cs.push({a:id(i), t:(t+=36e5*5), acc:20, term:null});
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:cs, flights:[], manual:[]})); }""")
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500)
        await pg.click('nav.tabs button[data-v=book]'); await pg.wait_for_timeout(200); await pg.screenshot(path=os.path.join(WORK,'w_book.png'))
        for i in range(4):
            await pg.click(f'#book .cell.got >> nth={i}'); await pg.wait_for_timeout(250)
            print(i, (await pg.inner_text('#dStampBody')).replace('\n',' ')[:120])
            await pg.screenshot(path=os.path.join(WORK,f'w_detail{i}.png')); 
            if i==0:
                await pg.click('#dStamp [data-share-a]'); await pg.wait_for_timeout(900)
                src=await pg.get_attribute('#shareImg','src'); open(os.path.join(WORK,'w_card.png'),'wb').write(base64.b64decode(src.split(',')[1])); await pg.click('#shareClose')
            else: await pg.keyboard.press('Escape')
        # 50回目のチェックイン（新千歳）で機長に昇格
        await pg.click('nav.tabs button[data-v=home]')
        await c.grant_permissions(['geolocation']); await c.set_geolocation({'latitude':42.7752,'longitude':141.6923,'accuracy':20})
        await pg.click('#checkin'); await pg.wait_for_timeout(400); await c.set_geolocation({'latitude':42.7753,'longitude':141.6924,'accuracy':18}); await pg.wait_for_timeout(1500)
        print('checkin:', (await pg.inner_text('#dStampBody')).replace('\n',' ')[:160]); await pg.screenshot(path=os.path.join(WORK,'w_rankup.png'))
        print(errs); await b.close()
asyncio.run(main())
