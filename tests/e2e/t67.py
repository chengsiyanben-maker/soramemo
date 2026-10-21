import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# データの使い方：ログインしていないときは案内だけ。ログインすると3つを選べて、サーバーに保存する
import asyncio, json
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860})
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(800)
        await pg.evaluate("$('dSettings').showModal()"); await pg.wait_for_timeout(200)
        await pg.click('#openData'); await pg.wait_for_timeout(300)
        check('ログインしていないとき:', 'ログインして使っているときに選べます' in await pg.inner_text('#dData'))
        await pg.click('#dData [data-close]'); await pg.evaluate("$('dSettings').close()")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        await pg.evaluate("$('dSettings').showModal()"); await pg.wait_for_timeout(200)
        await pg.click('#openData'); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#dData'); print('DATA', t[:300].replace('\n', ' | '))
        sw = pg.locator('#dData [data-dpref]')
        check('3つの切り替え（はじめは統計だけオン）:', await sw.count() == 3 and [await sw.nth(i).get_attribute('aria-checked') for i in range(3)] == ['true', 'false', 'false'])
        check('外に出さないもの:', 'チェックインした場所' in t and 'メールアドレス' in t)
        await pg.click('#dData [data-dpref="stats"]'); await pg.wait_for_timeout(300)
        await pg.click('#dData [data-dpref="offers"]'); await pg.wait_for_timeout(300)
        dp = await pg.evaluate('window.__dp'); print('DP', dp)
        check('保存した中身:', dp == {'stats': False, 'offers': True, 'research': False} and await pg.locator('#dData [data-dpref="stats"]').get_attribute('aria-checked') == 'false')
        await pg.screenshot(path=os.path.join(WORK, 't67_data.png'))
        print('errors', errs)
        await b.close()
asyncio.run(main())
if fails: print('NG', fails); sys.exit(1)
