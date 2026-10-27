import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 一般の人が行けない飛行場（硫黄島・南鳥島）：全クリに数えない枠と、実績「なぜあなたはそこに行けるの！？？？」
import asyncio, shutil
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    LOC = os.path.join(WORK, 'local'); os.makedirs(LOC, exist_ok=True); shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(LOC, 'index.html'))
    open(os.path.join(LOC, 'config.js'), 'w').write('window.SORAMEMO_CONFIG = {};')
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c = await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(LOC,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(400)
        await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(300)
        await pg.click('#v-book [data-seg="extra"]'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#bookExtra')
        check('まだ押していない秘密の枠は名前を隠す:', '一般の人が行けない飛行場　0 / 5' in t and '硫黄島' not in t)
        await pg.click('#v-book [data-seg="ach"]'); await pg.wait_for_timeout(200)
        a = await pg.text_content('#ach'); n0 = await pg.inner_text('#achProg')
        check('達成前の実績は「？？？」:', '？？？' in a and 'なぜあなたは' not in a)
        await pg.evaluate("""() => { S = Object.assign(blank(), { checkins:[{a:4001, t:Date.now() - 36e5, acc:20, term:null}], flights:[], manual:[] }); save(); render(); }""")
        await pg.wait_for_timeout(300)
        a = await pg.text_content('#ach'); n1 = await pg.inner_text('#achProg')
        check('硫黄島で押すと実績を達成:', 'なぜあなたはそこに行けるの！？？？' in a)
        tot0 = n0.split('/')[1].strip(); tot1 = n1.split('/')[1].strip()
        check('全クリ（達成の数）には数えない:', tot0 == tot1 and await pg.evaluate("achState().done.has('sc1')"))
        check('86空港の図鑑には入らない:', await pg.evaluate('visited().size') == 0 and await pg.evaluate('visitedExtra().has(4001)'))
        await pg.click('#v-book [data-seg="extra"]'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#bookExtra')
        check('押したら名前が出る:', '硫黄島航空基地' in t and '1 / 5' in t)
        await pg.screenshot(path=os.path.join(WORK, 't70_secret.png'), full_page=True)
        await b.close()
    print('errors', errs + fails)
asyncio.run(main())
