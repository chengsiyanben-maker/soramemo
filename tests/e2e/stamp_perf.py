# 印を押してからハンコが出るまでの時間と、画面が止まる長い処理（50ms 超）を測る（11/25 stamp-fast）
#   python3 tests/e2e/stamp_perf.py [web のフォルダ]   … 前後を比べるときは、前の web/ を git archive で取り出して渡す
#   偽のサーバー（fake_sb.js）と偽の位置を使う。CPU は4倍遅く（スマホの見当）。印は 1,500 件・便は 700 件持っている人
import os, sys, json, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE,'..','..','web'))
WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
PAGE = os.path.join(WORK, 'index_stamp_perf.html')
shutil.copy(os.path.join(WEB, 'index.html'), PAGE)
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
# 偽の位置：__geo.delay ミリ秒たってから、押したあとの時刻の位置を返す
GEO = """window.__geo = {delay:300, acc:20, lat:35.5494, lon:139.7798, calls:0};
(() => { const W = new Map(); let n = 0;
  const pos = () => ({coords:{latitude:__geo.lat, longitude:__geo.lon, accuracy:__geo.acc}, timestamp:Date.now()});
  const g = { watchPosition(ok){ const id = ++n; __geo.calls++; W.set(id, setTimeout(() => { if(W.has(id)) ok(pos()); }, __geo.delay)); return id; },
    clearWatch(id){ clearTimeout(W.get(id)); W.delete(id); },
    getCurrentPosition(ok){ __geo.calls++; setTimeout(() => ok(pos()), __geo.delay); } };
  Object.defineProperty(navigator, 'geolocation', {configurable:true, get(){ return g; }}); })();"""
MANY = """() => { const db = __fake.db, t0 = Date.now() - 400*864e5;
  for(let i = 0; i < 1500; i++) db.checkins.unshift({airport_id: A[(i*7) % 40].id, terminal_id:null, created_at:new Date(t0 + i*6*36e5).toISOString(), accuracy_m:20});
  for(let i = 0; i < 700; i++) db.flights.push({id:1000+i, from_airport:A[(i*7+3) % 40].id, to_airport:A[(i*7) % 40].id, dep_at:new Date(t0 + i*12*36e5).toISOString(), arr_at:new Date(t0 + i*12*36e5 + 2*36e5).toISOString(), distance_km:800, status:'verified', airline: i%3 ? 'JL' : 'NH', flight_no:null}); }"""
WATCH = """() => { window.__lt = []; new PerformanceObserver(l => { for(const e of l.getEntries()) __lt.push([e.startTime, e.duration]); }).observe({type:'longtask'});
  window.__stampAt = null; const d = document.getElementById('dStamp');
  new MutationObserver(() => { if(d.open && __stampAt == null) __stampAt = performance.now(); }).observe(d, {attributes:true, attributeFilter:['open']});
  window.__t0 = performance.now(); document.getElementById('checkin').dispatchEvent(new MouseEvent('click', {detail:0, bubbles:true})); }"""
# どこで待っているか：関数ごとにかかった時間（ミリ秒・押してから始まった時刻 @）を数える
PARTS = """() => { window.__parts = {}; const T0 = () => window.__t0 || performance.now();
  for(const fn of ['getPos','ckPos','flushQueue','sendCheckin','reload','loadServer','render','renderHome','renderVisible','updateAuthUI','applyPlan','renderRide','authAfterLoad','showStamp','ckAfter','ckSend']){
    const orig = window[fn]; if(typeof orig !== 'function') continue;
    window[fn] = function(){ const s = performance.now(), r = orig.apply(this, arguments), put = () => { const e = performance.now(); (__parts[fn] = __parts[fn] || []).push(Math.round(s - T0()) + '+' + Math.round(e - s)); };
      if(r && typeof r.then === 'function') r.then(put, put); else put(); return r; }; } }"""
async def run(p, name, net=0, geo=300, offline=False, fnfail=False, cpu=4, warm=False, acc=20):
    b = await p.chromium.launch(); c = await b.new_context(viewport={'width':390,'height':844}, permissions=['geolocation'])
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');" + GEO)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + PAGE); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && window.__fake'); await pg.wait_for_timeout(500)
    await pg.evaluate(MANY); await pg.evaluate('__fake.login()'); await pg.wait_for_function('S.checkins.length > 1000', timeout=30000); await pg.wait_for_timeout(1500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    cdp = await c.new_cdp_session(pg); await cdp.send('Emulation.setCPUThrottlingRate', {'rate': cpu})
    await pg.evaluate(f'__geo.acc = {acc}; __geo.delay = {geo}; window.__netDelay = {net}; window.__fnFail = {str(fnfail).lower()}')
    await pg.evaluate('HOME_POS = null; try{ POS_LAST = null; GEO_WARM = null; }catch(e){} typeof homeLocStop === "function" && homeLocStop()')   # 直近の位置なしから（warm のときだけ見張りを付け直す）
    if warm: await pg.evaluate('typeof homeLocStart === "function" && (HOME_WATCH != null || homeLocStart())'); await pg.wait_for_timeout(geo + 400)
    if offline: await c.set_offline(True)
    before = await pg.evaluate('S.checkins.length')
    await pg.evaluate(PARTS)
    await pg.evaluate(WATCH)
    await pg.wait_for_timeout(max(9000, geo + net * 12 + 4000))
    r = await pg.evaluate("""() => ({ stamp: __stampAt == null ? null : Math.round(__stampAt - __t0),
      parts: window.__parts, t0: Math.round(__t0), lt: __lt.filter(([s]) => s >= __t0 - 5), msg: document.getElementById('msg').textContent, q: (JSON.parse(localStorage.getItem('soramemo.queue.u1') || '[]')).length })""")
    after = await pg.evaluate('S.checkins.length'); lt = [d for s, d in r['lt']]
    out = {'name':name, 'stamp_ms':r['stamp'], 'longest_ms':round(max(lt)) if lt else 0, 'long_total_ms':round(sum(lt)), 'long_n':len(lt), 'lt_at':[(round(a-0), round(d)) for a, d in r['lt']], 't0':r.get('t0'), 'added':after - before, 'queue':r['q'], 'msg':r['msg'][:60], 'parts':r['parts'], 'errs':errs}
    await b.close(); return out
async def main():
    async with async_playwright() as p:
        res = []
        if os.environ.get('ONLY'): res.append(await run(p, os.environ['ONLY'], acc=int(os.environ.get('ACC', '20')))); print(json.dumps(res[0], ensure_ascii=False)); return
        res.append(await run(p, 'ふつう（電波よい・位置0.3秒）'))
        res.append(await run(p, '遅い電波（1回 2秒）', net=2000))
        res.append(await run(p, '位置がなかなか取れない（6秒）', geo=6000))
        res.append(await run(p, '直近の位置あり（ホームで見張り中）', warm=True))
        res.append(await run(p, '屋内（誤差120m）', acc=120))
        res.append(await run(p, 'オフライン', offline=True))
        res.append(await run(p, 'サーバーが断る', fnfail=True))
        for r in res: print(json.dumps(r, ensure_ascii=False))
if __name__ == "__main__": asyncio.run(main())
