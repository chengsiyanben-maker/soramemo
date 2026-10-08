import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
UA_A='Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Mobile Safari/537.36'
UA_I='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
async def run(b, ua, label):
    c=await b.new_context(viewport={'width':400,'height':860}, user_agent=ua); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1')")
    pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400)
    print(label, '案内:', await pg.is_visible('#installBar'))
    if 'Android' in ua:
        # Chrome がインストールを提案したときの動き
        await pg.evaluate("""() => { const e = new Event('beforeinstallprompt'); e.prompt = () => { window.__prompted = true; }; e.userChoice = Promise.resolve({outcome:'accepted'}); window.dispatchEvent(e); }""")
        await pg.click('#installBar [data-install=go]'); await pg.wait_for_timeout(200); print('  ボタン1つで提案:', await pg.evaluate('!!window.__prompted'))
    else:
        await pg.click('#installBar [data-install=go]'); await pg.wait_for_timeout(200); print('  手順:', (await pg.inner_text('#dBPBody')).replace('\n',' ')[:70]); await pg.click('#dBP [data-close]')
        await pg.click('#installBar [data-install=later]'); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(300)
        print('  閉じた後は出ない:', not await pg.is_visible('#installBar'), '| 設定には残る:', await pg.evaluate("!$('installRow').hidden"))
    print('  errors', errs); await c.close()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); await run(b, UA_A, 'Android'); await run(b, UA_I, 'iPhone'); await b.close()
asyncio.run(main())
