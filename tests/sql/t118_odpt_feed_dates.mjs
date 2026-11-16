// ODPT のデータの時刻（移行 179）：odpt_feed_dates と odpt_feed_date_put
//   1. 入れる・上書きで行が増えない・dc:date は前より古くしない・null は前の値を残す
//   2. 形のちがう feed は入れない・同じ feed が2つ来たら新しい方
//   3. RLS：anon・authenticated は読めるが書けない。関数は service_role だけ
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
const get = async () => Object.fromEntries((await rows(`select feed, dc_date, n from public.odpt_feed_dates order by feed`)).map((r) => [r.feed, { d: r.dc_date?.toISOString() ?? null, n: r.n }]));

let r = await put([{ feed: 'FlightInformationDeparture:JAL', dc_date: '2026-11-16T14:30:00+09:00', n: 120 }, { feed: 'FlightSchedule:ANA', dc_date: null, n: 0 }]);
check('service_role は入れられる（2行）', Array.isArray(r) && r[0].k === 2, r);
let g = await get();
check('dc:date は時刻として入る', g['FlightInformationDeparture:JAL']?.d === '2026-11-16T05:30:00.000Z' && g['FlightInformationDeparture:JAL'].n === 120, g);
check('dc:date がないときは null', g['FlightSchedule:ANA']?.d === null, g);

await put([{ feed: 'FlightInformationDeparture:JAL', dc_date: '2026-11-16T14:35:00+09:00', n: 118 }]);
g = await get();
check('新しい dc:date で上書き・行は増えない', g['FlightInformationDeparture:JAL'].d === '2026-11-16T05:35:00.000Z' && g['FlightInformationDeparture:JAL'].n === 118 && Object.keys(g).length === 2, g);
await put([{ feed: 'FlightInformationDeparture:JAL', dc_date: '2026-11-16T14:00:00+09:00', n: 5 }]);
g = await get();
check('古い dc:date では戻さない（件数は書き直す）', g['FlightInformationDeparture:JAL'].d === '2026-11-16T05:35:00.000Z' && g['FlightInformationDeparture:JAL'].n === 5, g);
await put([{ feed: 'FlightInformationDeparture:JAL', dc_date: null, n: 0 }]);
g = await get();
check('null が来ても前の dc:date は残る', g['FlightInformationDeparture:JAL'].d === '2026-11-16T05:35:00.000Z', g);

r = await put([{ feed: 'bad feed; drop', dc_date: null }, { feed: 'FlightSchedule', dc_date: null }, { feed: 'FlightSchedule:JAL', dc_date: '2026-11-16T03:00:00+09:00', n: 10 }, { feed: 'FlightSchedule:JAL', dc_date: '2026-11-16T04:00:00+09:00', n: 20 }]);
g = await get();
check('形のちがう feed は入れない・同じ feed は新しい方の1行', r[0].k === 1 && g['FlightSchedule:JAL']?.d === '2026-11-15T19:00:00.000Z' && g['FlightSchedule:JAL'].n === 20 && Object.keys(g).length === 3, { r, g });
r = await put({ not: 'array' });
check('配列でなければ何もしない', r[0].k === 0, r);
r = await put([{ feed: 'FlightSchedule:JAL', dc_date: null, n: 999999 }]);
g = await get();
check('件数は 100000 まで', g['FlightSchedule:JAL'].n === 100000, g);

for (const role of ['anon', 'authenticated']) {
  const s = await as(role, 'select count(*)::int c from public.odpt_feed_dates');
  check(`${role} は読める`, Array.isArray(s) && s[0].c === 3, s);
  const w = await as(role, `insert into public.odpt_feed_dates (feed) values ('FlightSchedule:XX')`);
  check(`${role} は表に書けない`, typeof w === 'string' && /permission denied|row-level security/.test(w), w);
  const u = await as(role, `update public.odpt_feed_dates set n = 1`);
  check(`${role} は書き直せない`, typeof u === 'string' && /permission denied/.test(u), u);
  const f = await as(role, `select public.odpt_feed_date_put('[]'::jsonb)`);
  check(`${role} は関数を呼べない`, typeof f === 'string' && /permission denied/.test(f), f);
}
const rls = (await rows(`select relrowsecurity from pg_class where relname = 'odpt_feed_dates'`))[0];
check('RLS が有効', rls.relrowsecurity === true, rls);
const cfg = (await rows(`select proconfig from pg_proc where proname = 'odpt_feed_date_put'`))[0];
check('関数に lock_timeout 5s と search_path', (cfg.proconfig ?? []).includes('lock_timeout=5s') && (cfg.proconfig ?? []).some((x) => x.startsWith('search_path=')), cfg);

console.log(bad ? `NG ${bad}` : 'すべて OK'); process.exit(bad ? 1 : 0);
