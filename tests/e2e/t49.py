import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, base64
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo'); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1')")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400)
        await pg.click('#openSettings'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(200)
        cts = await pg.evaluate("'a:'+A.find(a=>a.iata=='CTS').id")
        for v in ['t:HND-T1', cts]:
            await pg.select_option('#demoAirport', v); await pg.click('#checkin'); await pg.wait_for_timeout(700)
            if v != cts: await pg.click('#dStamp [data-close]')
        async with pg.expect_file_chooser() as fc: await pg.click('#dStamp [data-photo-a]')
        await (await fc.value).set_files(os.path.join(HERE,'fixtures','photo.jpg')); await pg.wait_for_timeout(1500)
        src = await pg.get_attribute('#shareImg', 'src'); print('種類:', src[:23], '| 共有の名前:', await pg.evaluate("$('shareGo').dataset.fname"))
        open(os.path.join(WORK,'photo_out.jpg'),'wb').write(base64.b64decode(src.split(',')[1]))
        print(errs); await b.close()
asyncio.run(main())
