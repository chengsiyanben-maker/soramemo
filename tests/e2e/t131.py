import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運用予想：画面の予想を学ぶ予想 predict_rotation_v2（learn_hi）に切り替え。v2 が null・空なら predict_rotation_reg に戻す
#   特別塗装機の予定の便（src=livery）は割合がないので「0%（null回）」と出さない。学ぶ予想は前の42日。「推定です」の書き方は今のまま
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
_d = datetime.now(timezone.utc); now = datetime(_d.year, _d.month, _d.day, 3, 0, tzinfo=timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
today = (now + timedelta(hours=9)).strftime('%Y-%m-%d')
KNOWN = {'callsign': 'JAL313', 'dep': 'HND', 'arr': 'FUK', 'first': iso(-30), 'last': iso(-2)}
V2 = {'reg': 'JA01XJ', 'src': 'reg', 'method': 'learn_hi', 'estimate': True, 'known': KNOWN, 'next': [
    {'callsign': 'JAL320', 'dep': 'FUK', 'arr': 'HND', 'time': '15:30', 'seen': None, 'share': None, 'src': 'livery'},
    {'callsign': 'JAL333', 'dep': 'HND', 'arr': 'FUK', 'time': '18:10', 'seen': 7, 'share': 0.66, 'src': 'learn'},
    {'callsign': 'JAL340', 'dep': 'FUK', 'arr': 'HND', 'time': '20:40', 'seen': 4, 'share': 0.5, 'src': 'base'}]}
REG = {'reg': 'JA01XJ', 'src': 'reg', 'known': KNOWN, 'next': [{'callsign': 'JAL999', 'dep': 'FUK', 'arr': 'HND', 'time': '16:00', 'seen': 5, 'share': 0.82}]}
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        mode = {'v2': V2, 'reg': REG, 'v2status': 200}
        calls = []
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}'); calls.append(name)
            if name == 'predict_rotation_v2' and mode['v2status'] != 200:
                return await r.fulfill(status=mode['v2status'], body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
            out = {'reg_history': [{'day': today, 'callsign': 'JAL313', 'dep': 'HND', 'arr': None, 'first': iso(-30), 'last': iso(-2), 'type': 'B738'}],
                   'predict_rotation': {'reg': body.get('p_reg'), 'known': None, 'next': []},
                   'predict_rotation_v2': mode['v2'], 'predict_rotation_reg': mode['reg']}.get(name, [])
            await r.fulfill(status=200, body=json.dumps(out), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); await pg.clock.set_fixed_time(now); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)

        # 1. v2 に中身があれば v2 を使い、reg は呼ばない
        calls.clear()
        d = await pg.evaluate("loadPrediction('JA01XJ')")
        check('v2 を使う:', d and d.get('method') == 'learn_hi' and 'predict_rotation_v2' in calls and 'predict_rotation_reg' not in calls)
        check('順番は 時刻表→v2:', calls.index('predict_rotation') < calls.index('predict_rotation_v2'))
        h = await pg.evaluate("predictionHTML(%s)" % json.dumps(V2))
        check('塗装機の予定の便は割合を出さない:', '特別塗装機の予定の便から' in h and 'null' not in h and '>0%' not in h and 'で0%' not in h)
        check('学ぶ予想は前の42日:', '前の42日で66%（7回）' in h)
        check('今までの決め方は前の60日:', '前の60日で50%（4回）' in h)
        check('推定の書き方は今のまま・塗装機の一文:', '推定です。' in h and '機体の入れ替えで違うことがあります' in h and '航空会社の運航情報にある予定の便も使っています' in h)

        # 2. v2 の next が空なら reg に戻す
        mode['v2'] = dict(V2, next=[]); calls.clear()
        d = await pg.evaluate("loadPrediction('JA01XJ')")
        check('v2 が空なら reg:', d and d['next'][0]['callsign'] == 'JAL999' and 'predict_rotation_reg' in calls)
        # 3. v2 が null・失敗なら reg に戻す
        mode['v2'] = None
        d = await pg.evaluate("loadPrediction('JA01XJ')")
        check('v2 が null なら reg:', d and d['next'][0]['callsign'] == 'JAL999')
        mode['v2'] = V2; mode['v2status'] = 404
        d = await pg.evaluate("loadPrediction('JA01XJ')")
        check('v2 がない（404）なら reg:', d and d['next'][0]['callsign'] == 'JAL999')
        mode['v2status'] = 200
        # 4. どちらも次の便がないときは、いまの便が分かる方で「予想できません」
        mode['v2'] = dict(V2, next=[]); mode['reg'] = dict(REG, next=[])
        d = await pg.evaluate("loadPrediction('JA01XJ')")
        h = await pg.evaluate("d => predictionHTML(d)", d)
        check('両方空なら予想できません:', d and d.get('known') and 'まだ記録が足りず予想できません' in h)
        mode['v2'] = {'reg': 'JA01XJ', 'known': None, 'next': [], 'src': 'reg', 'method': 'learn_hi', 'estimate': True}; mode['reg'] = {'reg': 'JA01XJ', 'known': None, 'next': [], 'src': 'reg'}
        d = await pg.evaluate("loadPrediction('JA01XJ')")
        h = await pg.evaluate("d => predictionHTML(d)", d)
        check('いまの便が分からない:', 'まだ分かっていません' in h)

        # 5. 機体のくわしく（画面）：v2 の予想が出る。スマホ幅で撮る
        mode['v2'] = V2; mode['reg'] = REG
        await pg.evaluate("openPlane('JA01XJ')"); await pg.wait_for_timeout(800)
        tp = await pg.inner_text('#dPlane'); print('PLANE', tp[:400].replace('\n', ' | '))
        check('機体のくわしくに v2 の予想:', 'JL333' in tp and '予想・66%' in tp and '予想・塗装機の予定' in tp and '予想・0%' not in tp and 'JL999' not in tp)
        check('機体のくわしくの注記:', '航空会社の運航情報にある予定の便も' in tp and '推定' in tp)
        await pg.screenshot(path=os.path.join(WORK, 't131_plane.png'))
        await b.close()
        check('ページのエラーなし:', not errs)
        if errs: print(errs)
    print('errors', fails)
asyncio.run(main())
