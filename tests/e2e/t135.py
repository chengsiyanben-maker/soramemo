import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web'))
# 遅れ・欠航のお知らせ：同じ便の出発の遅れ・到着の遅れ・見込みと実際・何度も届いた欠航を、便ごとに1枚にまとめる（fix/fw-merge の入れ直し・11/16）
# 通知のまとめ方（alert_merge.ts）とそろえる：便名の0をそろえる・共同運航（出発・到着・定刻が同じ）は1枚で、便名は運航情報の便 → JAL・ANA
import asyncio
from playwright.async_api import async_playwright
A = lambda flight, kind, at, dep, arr, msg: {'flight':flight, 'kind':kind, 'at':at, 'dep':dep, 'arr':arr, 'message':msg}
OF = '・航空会社の運航情報。使用する飛行機の手配ができないため出発が遅れました。）'
L = [A('NH1605', 'delay_dep', '2026-11-04T11:05:09Z', 'ITM', 'KCZ', 'NH1605（伊丹→高知）は、出発が約76分遅れました（定刻 10:00 → 出発 11:16' + OF),
     A('NH1605', 'delay_arr', '2026-11-04T11:05:09Z', 'ITM', 'KCZ', 'NH1605（伊丹→高知）は、到着が約72分遅れました（定刻 10:45 → 到着 11:57' + OF),
     A('NH1605', 'delay_arr', '2026-11-04T02:30:07Z', 'ITM', 'KCZ', 'NH1605（伊丹→高知）は、到着が約69分遅れる見込みです（定刻 10:45 → 変更後 11:54' + OF),
     A('NH1605', 'delay_dep', '2026-11-04T02:20:05Z', 'ITM', 'KCZ', 'NH1605（伊丹→高知）は、出発が約76分遅れました（定刻 10:00 → 出発 11:16' + OF),
     A('NU211', 'cancel', '2026-11-04T10:50:08Z', 'OKA', 'UEO', 'NU211（那覇→久米島）は、欠航です（航空会社の運航情報。）'),
     A('NU211', 'cancel', '2026-11-04T04:30:15Z', 'OKA', 'UEO', 'NU211（那覇→久米島）は、欠航です（航空会社の運航情報。）'),
     A('6J095', 'delay_dep', '2026-11-04T08:15:12Z', 'HND', 'OIT', '6J095（羽田→大分）は、出発が約150分遅れました（17:14ごろ離陸・推定）'),
     A('6J095', 'delay_arr', '2026-11-04T08:15:12Z', 'HND', 'OIT', '6J095（羽田→大分）は、到着の定刻（16:10）から1時間以上たっても、まだ飛行中です（推定）'),
     # 共同運航：ADO の便と ANA の便名が同じ便（出発・到着・定刻 07:30 が同じ）。0 のある便名もそろえる
     A('HD011', 'delay_dep', '2026-11-04T07:00:00Z', 'HND', 'CTS', 'HD011（羽田→新千歳）は、出発が約90分遅れました（定刻 07:30 → 出発 09:00・推定）'),
     A('NH4711', 'delay_dep', '2026-11-04T07:05:00Z', 'HND', 'CTS', 'NH4711（羽田→新千歳）は、出発が約90分遅れました（定刻 07:30 → 出発 09:00' + OF),
     A('HD11', 'delay_arr', '2026-11-04T07:10:00Z', 'HND', 'CTS', 'HD11（羽田→新千歳）は、到着が約85分遅れる見込みです（定刻 09:05 → 変更後 10:30・推定）'),
     # 同じ区間でも定刻のちがう別の便は別の1枚
     A('NH4713', 'delay_dep', '2026-11-04T07:20:00Z', 'HND', 'CTS', 'NH4713（羽田→新千歳）は、出発が約70分遅れました（定刻 08:30 → 出発 09:40' + OF),
     # サーバーが定刻（std）を返すときは、それで共同運航をまとめる
     dict(A('JL3101', 'cancel', '2026-11-04T06:00:00Z', 'HND', 'MMB', 'JL3101（羽田→女満別）は、欠航です（航空会社の運航情報。）'), std='2026-11-04T01:00:00Z'),
     dict(A('NH4799', 'cancel', '2026-11-04T06:01:00Z', 'HND', 'MMB', 'NH4799（羽田→女満別）は、欠航です（推定）'), std='2026-11-04T01:00:00Z')]
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); c = await b.new_context(viewport={'width':400,'height':860})
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.join(WEB, 'index.html')); await pg.wait_for_timeout(800)
        r = await pg.evaluate("L => { const el = document.createElement('div'); el.innerHTML = fwHTML(L, 'ITM', false); return { n:el.querySelectorAll('.fwc').length, cards:[...el.querySelectorAll('.fwc')].map(x => x.innerText.replace(/\\s+/g, ' ')), tile:(() => { const t = document.createElement('div'); t.innerHTML = delayTileHTML(L); return t.innerText.replace(/\\s+/g, ' '); })() }; }", L)
        for x in r['cards']: print(' ', x[:160])
        check('便ごとに1枚（15件 → 6枚）:', r['n'] == 6)
        c1 = next(x for x in r['cards'] if 'NH1605' in x)
        check('出発と到着の遅れを1枚に（新しいほう：到着 11:57）:', '+76分' in c1 and '出発' in c1 and '11:16' in c1 and '到着' in c1 and '11:57' in c1 and '11:54' not in c1.split('原文')[0])
        check('便名は元の書き方のまま（6J095）:', any('6J095' in x.split('原文')[0] for x in r['cards']))
        check('同じ欠航は1枚:', sum('NU211' in x for x in r['cards']) == 1)
        check('計器のタイルも便の数（遅れ4・欠航2）:', '4件' in r['tile'] and '欠航2' in r['tile'])
        co = [x for x in r['cards'] if 'NH4711' in x or 'HD011' in x or 'HD11 ' in x]
        check('共同運航は1枚で、便名は運航情報の便（NH4711）:', len(co) == 1 and 'NH4711' in co[0].split('原文')[0] and 'HD0' not in co[0].split('原文')[0])
        check('共同運航の1枚に到着の見込み（10:30）も:', bool(co) and '10:30' in co[0].split('原文')[0])
        check('定刻のちがう便は別の1枚（NH4713）:', sum('NH4713' in x for x in r['cards']) == 1)
        cx = [x for x in r['cards'] if 'MMB' in x]
        check('定刻（std）が同じ欠航は1枚で、便名は運航情報の便（JL3101）:', len(cx) == 1 and 'JL3101' in cx[0] and '航空会社' in cx[0].split('原文')[0] and 'NH4799' not in cx[0].split('原文')[0])
        print('errors', errs, 'fails', fails); await b.close()
        sys.exit(1 if fails or errs else 0)
asyncio.run(main())
