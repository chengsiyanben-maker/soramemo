import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json, glob, subprocess
from playwright.async_api import async_playwright
# 11/20：web/ に config.js があるのでサーバー版で開く。ログインしていないと便に付けられないので、デモ（端末に保存）に入ってから試す
# バーコードを読む部品（zxing）は手元の node_modules から渡す。なければ作業用フォルダに入れる
def zxing():
    for c in [os.environ.get('ZXING_UMD',''), '/tmp/build/node_modules/@zxing/library/umd/index.min.js', os.path.join(WORK,'zx','node_modules/@zxing/library/umd/index.min.js')]:
        if c and os.path.exists(c): return c
    d=os.path.join(WORK,'zx'); os.makedirs(d, exist_ok=True)
    subprocess.run(['npm','i','--silent','--prefix',d,'@zxing/library@0.21.3'], check=True)
    return os.path.join(d,'node_modules/@zxing/library/umd/index.min.js')
ZX = zxing()
sys.path.insert(0, HERE); import make_bp_fixtures; make_bp_fixtures.make(os.path.join(WORK,'bp'))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo'); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@zxing/**', lambda r: r.fulfill(path=ZX, content_type='application/javascript'))
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400)
        if not await pg.evaluate("demo"): await pg.evaluate("$('toggleDemo').click(); 0"); await pg.wait_for_timeout(800)
        await pg.evaluate("S.flights.length = 0; S.manual.length = 0; save(); render()")
        print('解析:', await pg.evaluate("JSON.stringify(parseBCBP('M1TANAKA/TARO         EABC123 HNDCTSJL 0501 152Y012A0045 000'))"))
        # 6月1日の羽田→新千歳のフライト（航空会社なし）を記録しておく
        await pg.evaluate("""() => { const id=i=>A.find(a=>a.iata===i).id, y=new Date().getFullYear(), d=new Date(y,5,1,8).getTime();
          S.flights.push({id:'a'+(d+6e6), from:id('HND'), to:id('CTS'), dep:d, arr:d+6e6, km:km(BY[id('HND')],BY[id('CTS')]), airline:null, no:null, fare:null, seat:null}); save(); render(); }""")
        await pg.click('nav.tabs button[data-v=log]'); await pg.wait_for_timeout(200)
        # 1) 記録済みのフライトに付ける（PDF417）
        await pg.set_input_files('#bpFile', os.path.join(WORK,'bp','pdf_past.png')); await pg.wait_for_timeout(1500)
        print('1:', (await pg.inner_text('#dBPBody')).replace('\n',' ')[:160])
        await pg.click('[data-bp-act=apply]'); await pg.wait_for_timeout(300)
        v = await pg.evaluate("JSON.stringify(S.flights.map(f=>[f.airline,f.no,f.seat]))"); print('  付けた後:', v)
        if v != '[["JL","JL501","12A"]]': errs.append('記録済みのフライトに付かない '+v)
        await pg.click('#dBP [data-close]')
        # 2) まだ飛んでいない（QR）→ 搭乗予定 → チェックインでフライトになったら自動で付く
        await pg.set_input_files('#bpFile', os.path.join(WORK,'bp','qr_future.png')); await pg.wait_for_timeout(1500)
        print('2:', (await pg.inner_text('#dBPBody')).replace('\n',' ')[:160])
        await pg.click('[data-bp-act=pending]'); await pg.wait_for_timeout(200); await pg.click('#dBP [data-close]')
        print('  予定:', (await pg.inner_text('#bpPending')).replace('\n',' '))
        jdf = int(open(os.path.join(WORK,'bp','jd.txt')).read().split()[1])
        await pg.evaluate(f"""() => {{ const id=i=>A.find(a=>a.iata===i).id, y=new Date().getFullYear(), d=new Date(y,0,1,9); d.setDate({jdf}); const t=d.getTime();
          S.flights.push({{id:'a'+(t+9e6), from:id('HND'), to:id('OKA'), dep:t, arr:t+9e6, km:km(BY[id('HND')],BY[id('OKA')]), airline:null, no:null, fare:null, seat:null}}); save(); render(); }}""")
        await pg.wait_for_timeout(400)
        v = await pg.evaluate("JSON.stringify(S.flights.map(f=>[BY[f.to].iata,f.airline,f.no,f.seat]))"); n = await pg.evaluate("bpPending().length"); print('  自動で付いた:', v, '| 予定の残り:', n)
        if '"OKA","NH","NH995","33K"' not in v or n != 0: errs.append('搭乗予定が自動で付かない '+v)
        # 3) 過去で記録なし → 記録帳に追加
        await pg.set_input_files('#bpFile', os.path.join(WORK,'bp','pdf_manual.png')); await pg.wait_for_timeout(1500)
        await pg.click('[data-bp-act=manual]'); await pg.wait_for_timeout(300)
        v = await pg.evaluate("JSON.stringify(S.manual)"); print('3: 記録帳:', v)
        if '"airline":"JL"' not in v: errs.append('記録帳に入らない '+v)
        # 搭乗券でないもの
        await pg.click('#dBP [data-close]'); await pg.evaluate("handleBarcode('https://example.com')"); print('4:', (await pg.inner_text('#dBPBody'))[:20])
        ls = await pg.evaluate("JSON.stringify(localStorage)"); ok = 'TANAKA' not in ls and 'ABC123' not in ls; print('名前や予約番号が保存されていない:', ok)
        if not ok: errs.append('名前か予約番号が保存されている')
        print(errs); await b.close()
asyncio.run(main())
