import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# ODPT のデータの時刻（dc:date）を出典の近くに出す（ODPT の約束・11/16）
#   サーバーの odpt_feed_at() が { status_at, timetable_at } を返したら、出典の文に「運航情報 ○時○分・時刻表 ○月○日時点」
#   取れないとき・返さないときは今までの文のまま。3分に1回までしか読まない。偽のサーバーを使う（本物の Supabase には接続しない）
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
ST = (now - timedelta(minutes=3)).isoformat(); TT = (now - timedelta(days=5)).isoformat()
jst = lambda d: d + timedelta(hours=9)
st_txt = f"{jst(now - timedelta(minutes=3)).hour}時{jst(now - timedelta(minutes=3)).minute:02d}分"
tt_d = jst(now - timedelta(days=5)); tt_txt = f"{tt_d.month}月{tt_d.day}日"
async def run(b, body, status=200):
    c = await b.new_context(viewport={'width':390,'height':844})
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    calls = []
    async def feed(r):
        calls.append(1); await r.fulfill(status=status, body=body, content_type='application/json')
    await c.route('**/rest/v1/rpc/odpt_feed_at', feed)
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');")
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    for _ in range(50):
        if await pg.evaluate('typeof loadOdptAt === "function" && typeof SERVER !== "undefined"'): break
        await pg.wait_for_timeout(100)
    before = await pg.evaluate('ODPT_CREDIT')
    await pg.evaluate('loadOdptAt()'); await pg.wait_for_timeout(300)
    after = await pg.evaluate('ODPT_CREDIT')
    await pg.evaluate('loadOdptAt()'); await pg.wait_for_timeout(200)
    return c, pg, errs, before, after, calls
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c, pg, errs, before, after, calls = await run(b, json.dumps({'status_at':ST, 'timetable_at':TT}))
        check('読む前は今までの文（時点なし）', '時点' not in before and '出典：公共交通オープンデータセンター（正確' in before)
        check('運航情報の時刻（今日は時分だけ）', f'運航情報 {st_txt}' in after, after[:80])
        check('時刻表の日（日付だけ）', f'時刻表 {tt_txt}時点' in after, after[:80])
        check('注意書きとくわしくは残る', '航空会社へ直接問い合わせないでください' in after and 'terms.html#data' in after)
        check('3分の間は読み直さない', len(calls) == 1, len(calls))
        # 描いた画面にも入る（空港の今と同じ出典の部品）
        html = await pg.evaluate('OPS_CREDIT_S()')
        check('描くときに新しい文が入る', st_txt in html)
        # 運用タブなどからは少しあと（8秒）に読む：開いた直後の本数を増やさない
        n0 = len(calls); await pg.evaluate('ODPT_AT_READ = 0; loadOdptAtSoon(); loadOdptAtSoon()'); await pg.wait_for_timeout(1000)
        check('少しあとに読む：すぐには読まない', len(calls) == n0, len(calls))
        await pg.wait_for_timeout(7800)
        check('少しあとに読む：8秒後に1回だけ', len(calls) == n0 + 1, len(calls))
        check('エラーなし', not errs, errs); await c.close()
        # 運航情報だけ（時刻表は null）
        c, pg, errs, before, after, calls = await run(b, json.dumps({'status_at':ST, 'timetable_at':None}))
        check('運航情報だけのとき', f'運航情報 {st_txt}時点' in after and '時刻表' not in after, after[:80]); await c.close()
        # 取れないとき・変な形のときは今までの文のまま
        for label, body, code in [('500', '{}', 500), ('関数がない（404）', '{"message":"not found"}', 404), ('形がちがう', '{"status_at":"きのう"}', 200), ('空', 'null', 200)]:
            c, pg, errs, before, after, calls = await run(b, body, code)
            check(f'{label}：今までの文のまま', after == before and '時点' not in after)
            check(f'{label}：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
