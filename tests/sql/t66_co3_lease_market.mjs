// エアライン経営 co-v3：リースと中古機
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
// 手計算は満足度の倍率なし（満足度60）で確かめる。満足度は t47
await db.exec(`update companies set satisfaction = 60`).catch(() => {});
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
let s = await as(A, `select public.co_state()`);
check('はじめはリース 2機まで', s.lease_room === 2, typeof s === 'string' ? s : s.lease_room);
const cash0 = Number(s.cash);
s = await as(A, `select public.co3_lease('ride', 'r:JA01XJ')`);
const ac = s.fleet.find((x) => x.reg === 'JA01XJ');
const full = Number(await q1(`select (ac_spec('lg')).price`));
check('乗った機体をリース：お金は減らない・リースの印', ac && ac.lease === true && Number(s.cash) === cash0, { ac, cash: s.cash, cash0 });
check('リース料：機体の値段の0.15%/日（半額は使わない）', near(Number(ac.lease_fee), full * 0.0015, 0.01), { fee: ac.lease_fee, full });
check('維持費にリース料が入る', Number(s.upkeep) >= Math.round(Number(ac.lease_fee)), { up: s.upkeep, fee: ac.lease_fee });
check('リースの機体は会社の価値に入れない', Number(s.value) < cash0 + full * 0.5, s.value);
check('リースの機体は売れない', String(await as(A, `select public.co_sell(${ac.id})`)).includes('leased'), null);
check('同じ機体は2回借りられない', String(await as(A, `select public.co3_lease('ride', 'r:JA01XJ')`)).includes('already owned'), null);
s = await as(A, `select public.co_state()`);
check('借りられる数：残り1', s.lease_room === 1, s.lease_room);
await db.exec(`insert into aircraft (user_id, type, paid, reg, icao) values ('${A}', 'nb', 1000, 'JA02ZZ', 'B738'), ('${A}', 'nb', 1000, 'JA03ZZ', 'B738')`);
s = await as(A, `select public.co_state()`);
check('自社機2機ごとに1機ふえる：2＋1 − 1 ＝ 2', s.lease_room === 2, s.lease_room);
s = await as(A, `select public.co3_lease_return(${ac.id})`);
check('リースを返す：機体はなくなる・お金は戻らない', !s.fleet.some((x) => x.id === ac.id), null);
// 中古機：格付け2から。B が A350 に乗っていれば買える
const own = s.fleet.find((x) => x.reg === 'JA02ZZ');
check('格付け1：売りに出せない', String(await as(A, `select public.co3_market_list(${own.id}, 100)`)).includes('rating required 2'), null);
await db.exec(`update companies set rating = 2`);
check('値段は 30〜150%', String(await as(A, `select public.co3_market_list(${own.id}, 200)`)).includes('invalid price'), null);
s = await as(A, `select public.co3_market_list(${own.id}, 120)`);
const lst = s.fleet.find((x) => x.id === own.id).listed;
check('売りに出す：いまの値段の120%・7日', lst && Number(lst.price) === Math.round(1000 * 1.2) && Math.abs(new Date(lst.expires) - Date.now() - 7 * 864e5) < 6e4, lst);
check('同じ機体は2回出せない', String(await as(A, `select public.co3_market_list(${own.id}, 100)`)).includes('already listed'), null);
await as(B, `select public.co_state()`);
await db.exec(`update companies set cash = 100000, rating = 2 where user_id = '${B}'`);
let sb = await as(B, `select public.co_state()`);
check('売り場：B から見える・B は B737 を知らないので買えない', sb.market.length === 1 && sb.market[0].reg === 'JA02ZZ' && sb.market[0].can_buy === false && sb.market[0].seller === s.name, sb.market);
check('知らない機種は買えない', String(await as(B, `select public.co3_market_buy(${lst.id})`)).includes('type not known'), null);
// B が B737 に乗る（フライトと毎日の記録）
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no, airline) values
  ('${B}', ${ids.HND}, ${ids.CTS}, now() - interval '2 days', now() - interval '2 days' + interval '90 minutes', 819.6, 'NH55', 'NH');
  insert into flight_history (svc_date, flight, dep, arr, std, sta, type, reg, aircraft) values
    (((now() - interval '2 days') at time zone 'Asia/Tokyo')::date, 'NH55', 'HND', 'CTS', now() - interval '2 days', now() - interval '2 days' + interval '90 minutes', 'B738', 'JA99NH', '738') on conflict do nothing;
  insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${B}', ${ids.CTS}, 42.77, 141.69, 10, now() - interval '2 days' + interval '100 minutes')`);
sb = await as(B, `select public.co_state()`);
check('B737 に乗ったので買える', sb.market[0].can_buy === true, sb.market);
const cashA = Number(await q1(`select cash from companies where user_id = '${A}'`));
sb = await as(B, `select public.co3_market_buy(${lst.id})`);
if (typeof sb === 'string') console.log('BUY', sb);
check('買う：B の機体に・B のお金が減る', sb.fleet && sb.fleet.some((x) => x.reg === 'JA02ZZ') && Number(sb.cash) === 100000 - 1200, { cash: sb.cash });
check('A に値段の95%が入る（維持費の精算 ±3）', Math.abs(Number(await q1(`select cash from companies where user_id = '${A}'`)) - cashA - 1140) <= 3, null);
check('売れた機体は A の機体から消える', !(await as(A, `select public.co_state()`)).fleet.some((x) => x.reg === 'JA02ZZ'), null);
// 1日1機・同じ相手30日
const o3 = (await as(A, `select public.co_state()`)).fleet.find((x) => x.reg === 'JA03ZZ');
s = await as(A, `select public.co3_market_list(${o3.id}, 50)`);
const lst2 = s.fleet.find((x) => x.id === o3.id).listed;
check('1日1機まで', String(await as(B, `select public.co3_market_buy(${lst2.id})`)).includes('one per day'), null);
await db.exec(`update co3_market set sold_at = sold_at - interval '2 days' where status = 'sold'`);
check('同じ相手とは30日に1回', String(await as(B, `select public.co3_market_buy(${lst2.id})`)).includes('same partner'), null);
s = await as(A, `select public.co3_market_cancel(${lst2.id})`);
check('取り下げる', !s.fleet.find((x) => x.id === o3.id).listed, null);
check('売り場の表は直接は書けない', String(await as(A, `update co3_market set price = 1`)).startsWith('ERROR'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
