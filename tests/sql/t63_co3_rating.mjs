// エアライン経営 co-v3：会社の格付け（条件・上がる・下がらない・解放の鍵）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`update ops.flags set value = 'true' where key = 'game_released'`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id) values ('${A}'), ('${B}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('HND','CTS','GAJ','HIJ')`)).rows.map((r) => [r.iata, r.id]));
const near = (a, b, tol) => Math.abs(a - b) <= tol;

// 統計と表
check('空港の統計：羽田の乗降客数（令和7年）', Number(await q1(`select pax from co3_airport_stats where iata = 'HND'`)) === 91542534, null);
check('統計はだれでも読める', Number(await as(A, `select count(*) from co3_airport_stats`)) > 80, null);
check('本物の便の表はアプリから読めない', String(await as(A, `select count(*) from co3_route_real`)).startsWith('ERROR'), null);
check('スイッチははじめオフ', (await q1(`select value from ops.flags where key = 'co_v3'`)) === false, null);

// 本物の便：羽田⇄新千歳 前の28日、毎日 片道10便ずつ（B738）
await db.exec(`insert into flight_history (svc_date, flight, dep, arr, std, sta, type)
  select (now() at time zone 'Asia/Tokyo')::date - d, 'JL' || (500 + i * 2 + s), case s when 0 then 'HND' else 'CTS' end, case s when 0 then 'CTS' else 'HND' end,
         now() - d * interval '1 day', now() - d * interval '1 day' + interval '90 minutes', 'B738'
    from generate_series(1, 28) d, generate_series(0, 9) i, generate_series(0, 1) s`);
const n = Number(await q1(`select public.co3_route_real_refresh()`));
const rr = (await db.query(`select flights, avg_seats from co3_route_real where a = 'CTS' and b = 'HND'`)).rows[0];
check('本物の便：1日20便・平均170席', n >= 1 && Number(rr.flights) === 20 && Number(rr.avg_seats) === 170, rr);

// A：羽田⇄新千歳を飛んで、乗った A350 を買って入れる
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no, airline) values
  ('${A}', ${ids.HND}, ${ids.CTS}, now() - interval '1 day', now() - interval '1 day' + interval '90 minutes', 819.6, 'JL501', 'JL');
  insert into flight_history (svc_date, flight, dep, arr, std, sta, type, reg, aircraft) values
    (((now() - interval '1 day') at time zone 'Asia/Tokyo')::date, 'JL501', 'HND', 'CTS', now() - interval '1 day', now() - interval '1 day' + interval '90 minutes', 'A359', 'JA01XJ', '359')
    on conflict do nothing;
  insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${A}', ${ids.HND}, 35.55, 139.78, 10, now());`);
await as(A, `select public.co_state()`);
await db.exec(`update companies set cash = 500000 where user_id = '${A}'`);
let s = await as(A, `select public.co_buy('r:JA01XJ')`);
const hc = `${Math.min(ids.HND, ids.CTS)}-${Math.max(ids.HND, ids.CTS)}`;
await as(A, `select public.co_assign(${s.fleet[0].id}, '${hc}')`);
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
s = await as(A, `select public.co_state()`);
check('はじめは格付け1・いまの数（路線1・機体1）', s.rating === 1 && s.rating_have.routes === 1 && s.rating_have.fleet === 1 && s.rating_have.intl === 0, { r: s.rating, h: s.rating_have });
check('格付け1：運賃は変えられない', String(await as(A, `select public.co3_set_fare('${hc}', -1)`)).includes('rating required 2'), null);
check('格付け1：機内食と荷物は変えられない', String(await as(A, `select public.co3_set_service('free', 'free')`)).includes('rating required 2'), null);
check('格付け3まで：上級席の割合は変えられない', String(await as(A, `select public.co3_set_premium(0)`)).includes('rating required 4'), null);
// 路線5本・機体3機 → 格付け2
const ap = (await db.query(`select id from airports where iata ~ '^[A-Z]{3}$' order by id limit 40`)).rows.map((r) => r.id);
let flown = 0;
const fly = async (n) => { for (let j = 0; j < n; j++) { const i = flown++; await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km)
  values ('${A}', ${ap[10 + i]}, ${ap[11 + i]}, now() - interval '${10 + i} days', now() - interval '${10 + i} days' + interval '1 hour', 500)`); } };
const buy = async (n) => db.exec(`insert into aircraft (user_id, type, paid) select '${A}', 'nb', 1000 from generate_series(1, ${n})`);
await fly(4); await buy(1);
s = await as(A, `select public.co_state()`);
check('路線5本・機体2機ではまだ1', s.rating === 1 && s.rating_have.routes === 5 && s.rating_have.fleet === 2, s.rating_have);
await buy(1);
s = await as(A, `select public.co_state()`);
check('路線5本・機体3機で格付け2・上がった時刻', s.rating === 2 && !!s.rating_at, { r: s.rating, at: s.rating_at });
check('格付け2：運賃と機内食を変えられる', !String(await as(A, `select public.co3_set_fare('${hc}', -1)`)).startsWith('ERROR') && !String(await as(A, `select public.co3_set_service('free', 'free')`)).startsWith('ERROR'), null);
// 路線12本・機体8機・評判★3・30日 → 格付け3（30日に足りないうちは2のまま）
await fly(7); await buy(5);
s = await as(A, `select public.co_state()`);
check('路線12本・機体8機でも始めて30日たたないうちは2', s.rating === 2 && s.rating_have.routes === 12 && s.rating_have.fleet === 8 && s.rating_have.stars >= 3 && s.rating_have.days < 30, s.rating_have);
await db.exec(`update companies set created_at = now() - interval '40 days' where user_id = '${A}'`);
s = await as(A, `select public.co_state()`);
check('30日たって格付け3', s.rating === 3, s.rating_have);
// 下がらない
await db.exec(`delete from aircraft where user_id = '${A}' and route_key is null`);
s = await as(A, `select public.co_state()`);
check('機体が減っても格付けは下がらない', s.rating === 3 && s.rating_have.fleet === 1, s.rating_have);
check('格付け3：上級席はまだ', String(await as(A, `select public.co3_set_premium(0)`)).includes('rating required 4'), null);
// 4・5 の条件（計算だけ）
const ro = async (a, b, c, d, e) => Number(await q1(`select co3.rating_of(${a}, ${b}, ${c}, ${d}, ${e})`));
check('格付け4：国際線1本・路線25・機体20・★4、または 国際線なしで 路線30・機体25・★4', await ro(25, 1, 20, 4, 99) === 4 && await ro(25, 0, 20, 4, 99) === 3 && await ro(30, 0, 25, 4, 99) === 4, null);
check('格付け5：国際線5本・路線40・機体35・★5', await ro(40, 5, 35, 5, 99) === 5 && await ro(40, 4, 35, 5, 99) === 4, null);
check('★が足りなければ上がらない', await ro(12, 0, 8, 2, 99) === 2, null);
check('格付けは自分で書きかえられない', String(await as(A, `update companies set rating = 5`)).startsWith('ERROR') || Number(await q1(`select rating from companies where user_id = '${A}'`)) === 3, null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
