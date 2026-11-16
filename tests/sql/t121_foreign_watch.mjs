// 乗る便に選んだ時刻表にない便の見張りの表（移行 182）
//   1. foreign_watch_sync：選ばれた便のうち、時刻表になく ODPT で見られる会社でない便だけを足す（呼び出し符号・いつもの空港と時刻）
//   2. 選ばれなくなった便・古い便は消す・同じ便は1行・何度流しても同じ
//   3. foreign_watch_put：状態を書く（形のちがう値は直す・ない便は無視）。foreign_watch_rows：前後1日だけ
//   4. RLS・権限：anon・authenticated は表も関数も使えない。仕事に上限
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.sql')).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const one = async (sql, p) => (await db.query(sql, p)).rows[0];
const rows = async (sql, p) => (await db.query(sql, p)).rows;
const as = async (role, sql, p) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql, p); return r.rows; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };

const today = (await one(`select (now() at time zone 'Asia/Tokyo')::date::text d`)).d;
const D = async (k) => (await one(`select ($1::date + $2::int)::text d`, [today, k])).d;
const dow = (await one(`select extract(dow from $1::date)::int d`, [today])).d;
await db.exec(`
  insert into public.foreign_usual (callsign, iata, dep_here, dow, mins, n, spread, last_day) values
    ('BAW5', 'HND', 0, -1, 400, 20, 10, '${today}'), ('BAW5', 'HND', 0, ${dow}, 395, 4, 5, '${today}'), ('BAW5', 'NRT', 0, -1, 420, 5, 10, '${today}'),
    ('BAW6', 'HND', 1, -1, 690, 20, 10, '${today}'),
    ('SKY701', 'HND', 1, -1, 480, 30, 5, '${today}'), ('SKY701', 'FUK', 0, -1, 600, 30, 5, '${today}');
  insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
    ('${today}', 'JL5', 'HND', 'JFK', now(), now() + interval '12 hours', 'ODPT（JAL）');
  insert into public.push_subs (endpoint, p256dh, auth, flights) values
    ('https://e/1', 'k', 'a', array['BA5@${today}', 'BA006@${today}', 'JL5@${today}', 'NH9999@${today}']),
    ('https://e/2', 'k', 'a', array['BA5@${today}', 'BC701@${await D(1)}', 'KE703@${await D(5)}', 'XX1@${today}', 'bad']);`);

// 1
let n = (await as('service_role', 'select public.foreign_watch_sync() n'))[0]?.n;
let w = await rows(`select flight, svc_date::text d, callsign, dep, arr, usual_dep, usual_arr, usual_n from public.foreign_watch order by flight`);
const by = Object.fromEntries(w.map((r) => [r.flight, r]));
check('時刻表になく ODPT で見られる会社でない便だけ（BA5・BA6・BC701）', n === 3 && w.map((r) => r.flight).join() === 'BA5,BA6,BC701', w);
check('同じ便を2人が選んでも1行・先頭の0を除く（BA006 → BA6）', w.filter((r) => r.flight === 'BA5').length === 1 && by.BA6?.callsign === 'BAW6', w);
check('いつもの到着空港と時刻（その曜日を先に）', by.BA5?.arr === 'HND' && by.BA5.usual_arr === 395 && by.BA5.usual_n === 4 && by.BA5.dep === null, by.BA5);
check('日本を出る便は出発空港と時刻', by.BA6?.dep === 'HND' && by.BA6.usual_dep === 690 && by.BA6.arr === null, by.BA6);
check('ODPT にない日本の会社（スカイマーク）は両方の空港', by.BC701?.callsign === 'SKY701' && by.BC701.dep === 'HND' && by.BC701.arr === 'FUK' && by.BC701.d === await D(1), by.BC701);
check('JAL（時刻表にある）・NH（ODPT の会社）・遠い日・表にない記号・形のちがう値は入らない', !by.JL5 && !by.NH9999 && !by.KE703 && !by.XX1, w.map((r) => r.flight));

// 2
n = (await as('service_role', 'select public.foreign_watch_sync() n'))[0]?.n;
check('何度流しても同じ（足す数0）', n === 0 && (await one(`select count(*)::int c from public.foreign_watch`)).c === 3, n);
await db.exec(`insert into public.foreign_watch (flight, svc_date, callsign) values ('KE1', '${await D(-5)}', 'KAL1')`);
await db.exec(`update public.push_subs set flights = array['BA5@${today}'] where endpoint = 'https://e/2'; update public.push_subs set flights = '{}' where endpoint = 'https://e/1'`);
await as('service_role', 'select public.foreign_watch_sync()');
w = await rows(`select flight from public.foreign_watch order by flight`);
check('選ばれなくなった便・古い便は消える', w.map((r) => r.flight).join() === 'BA5', w);

// 3
let k = (await as('service_role', `select public.foreign_watch_put($1::jsonb) n`, [JSON.stringify([
  { flight: 'BA5', svc_date: today, state: { phase: 'air' }, late: 42, event: 'divert', eta: '2026-11-16T22:00:00Z' },
  { flight: 'BA5', svc_date: today, state: 'x', late: 99999, event: 'nope' },
  { flight: 'ZZ1', svc_date: today, late: 5 }, { flight: 'bad', svc_date: today }])]))[0]?.n;
const s = await one(`select state, late, event, eta from public.foreign_watch where flight = 'BA5'`);
check('状態を書く（ない便・形のちがう便名は無視、同じ便は1つ目）', k === 1 && s.state.phase === 'air' && s.late === 42 && s.event === 'divert' && s.eta.toISOString() === '2026-11-16T22:00:00.000Z', { k, s });
k = (await as('service_role', `select public.foreign_watch_put($1::jsonb) n`, [JSON.stringify([{ flight: 'BA5', svc_date: today, state: 'x', late: 99999, event: 'nope' }])]))[0]?.n;
const s2 = await one(`select state, late, event from public.foreign_watch where flight = 'BA5'`);
check('形のちがう値は直す（状態は空・ずれは1440まで・知らない event は null）', k === 1 && JSON.stringify(s2.state) === '{}' && s2.late === 1440 && s2.event === null, s2);
await db.exec(`insert into public.foreign_watch (flight, svc_date, callsign) values ('KE2', '${await D(-3)}', 'KAL2')`);
const rr = await as('service_role', 'select flight from public.foreign_watch_rows()');
check('foreign_watch_rows は前後1日だけ', Array.isArray(rr) && rr.map((r) => r.flight).join() === 'BA5', rr);

// 4
for (const role of ['anon', 'authenticated']) {
  for (const q of ['select * from public.foreign_watch', 'select public.foreign_watch_sync()', 'select * from public.foreign_watch_rows()', `select public.foreign_watch_put('[]'::jsonb)`]) {
    const r = await as(role, q);
    check(`${role} は使えない：${q.slice(0, 40)}`, typeof r === 'string' && /permission denied/.test(r), r);
  }
}
check('RLS が有効', (await one(`select relrowsecurity r from pg_class where relname = 'foreign_watch'`)).r === true, null);
const cfg = Object.fromEntries((await rows(`select proname, proconfig from pg_proc where proname in ('foreign_watch_sync', 'foreign_watch_put')`)).map((x) => [x.proname, x.proconfig ?? []]));
check('書く関数に lock_timeout', cfg.foreign_watch_sync?.includes('lock_timeout=5s') && cfg.foreign_watch_put?.includes('lock_timeout=10s'), cfg);
const sql = fs.readFileSync(dir + '20261116000182_foreign_watch.sql', 'utf8');
check('仕事に statement_timeout と lock_timeout・pg_cron がない所では作らない', /foreign-watch-sync[^]*set statement_timeout = '30s'; set lock_timeout = '5s';/.test(sql) && sql.includes("where extname = 'pg_cron') then return"), null);

console.log(bad ? `NG ${bad}` : 'すべて OK'); process.exit(bad ? 1 : 0);
