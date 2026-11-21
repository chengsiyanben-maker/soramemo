// ODPT のデータの時刻を返す関数（移行 191）：odpt_feed_at()
//   1. 行がないときは { status_at: null, timetable_at: null }
//   2. 運航情報（出発・到着）と時刻表それぞれの、いちばん新しい dc:date。dc:date がない行は飛ばす
//   3. anon・authenticated が呼べる。表には書けないまま（RLS は移行179 のまま）
//   4. 時間の上限 2秒・search_path・security invoker
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
const rows = async (sql, p) => (await db.query(sql, p)).rows;
const as = async (role, sql, p) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql, p); return r.rows; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const put = (p) => as('service_role', 'select public.odpt_feed_date_put($1::jsonb) k', [JSON.stringify(p)]);
const at = async (role = 'anon') => { const r = await as(role, 'select public.odpt_feed_at() j'); return Array.isArray(r) ? r[0].j : r; };
const iso = (v) => (v == null ? null : new Date(v).toISOString());

let j = await at();
check('行がないときは両方 null', j && 'status_at' in j && 'timetable_at' in j && j.status_at === null && j.timetable_at === null, j);

await put([
  { feed: 'FlightInformationDeparture:JAL', dc_date: '2026-11-21T10:02:00+09:00', n: 120 },
  { feed: 'FlightInformationArrival:ANA', dc_date: '2026-11-21T10:05:00+09:00', n: 98 },
  { feed: 'FlightInformationDeparture:ANA', dc_date: null, n: 0 },
  { feed: 'FlightSchedule:JAL', dc_date: '2026-11-15T04:00:00+09:00', n: 900 },
  { feed: 'FlightSchedule:ANA', dc_date: '2026-11-18T04:00:00+09:00', n: 800 },
]);
j = await at();
check('運航情報は出発・到着のいちばん新しい dc:date', iso(j.status_at) === '2026-11-21T01:05:00.000Z', j);
check('時刻表はいちばん新しい dc:date', iso(j.timetable_at) === '2026-11-17T19:00:00.000Z', j);
check('返す形は2つの鍵だけ', Object.keys(j).sort().join(',') === 'status_at,timetable_at', j);

await put([{ feed: 'FlightInformationArrival:ANA', dc_date: '2026-11-21T10:30:00+09:00', n: 99 }]);
j = await at('authenticated');
check('取り込みで新しくなると返す時刻も新しくなる（authenticated）', iso(j.status_at) === '2026-11-21T01:30:00.000Z', j);

const db2rows = await rows(`select count(*)::int c from public.odpt_feed_dates`);
check('行は5つのまま（関数は表を変えない）', db2rows[0].c === 5, db2rows);

for (const role of ['anon', 'authenticated']) {
  const w = await as(role, `insert into public.odpt_feed_dates (feed) values ('FlightSchedule:XX')`);
  check(`${role} は今までどおり表に書けない`, typeof w === 'string' && /permission denied|row-level security/.test(w), w);
}
const p = await as('anon', `select has_function_privilege('anon', 'public.odpt_feed_at()', 'execute') a, has_function_privilege('authenticated', 'public.odpt_feed_at()', 'execute') b`);
check('anon・authenticated に実行の許可', Array.isArray(p) && p[0].a === true && p[0].b === true, p);
const cfg = (await rows(`select proconfig, prosecdef, provolatile from pg_proc where proname = 'odpt_feed_at'`))[0];
check('関数に statement_timeout 2s と search_path', (cfg.proconfig ?? []).includes('statement_timeout=2s') && (cfg.proconfig ?? []).some((x) => x.startsWith('search_path=')), cfg);
check('security invoker・stable', cfg.prosecdef === false && cfg.provolatile === 's', cfg);

console.log(bad ? `NG ${bad}` : 'すべて OK'); process.exit(bad ? 1 : 0);
