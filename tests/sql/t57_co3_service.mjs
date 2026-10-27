// エアライン経営 co-v3：機内食と預ける荷物（満足度・費用・収益・旅行の客）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`set co3.season_day = '2026-05-20'`);   // 季節の需要のない日で手計算する（季節は t72）
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
await db.exec(`update companies set rating = 5`).catch(() => {});   // 格付けの鍵は t63 で試す。ここでは解放ずみの形で
await db.exec(`update companies set safety = 'low'`).catch(() => {});   // 安全への投資の費用（普通 +1ポイント）は t71 で試す。ここでは費用 +0 で手計算
// 手計算は満足度の倍率なし（満足度60）で確かめる。満足度は t47
await db.exec(`update companies set satisfaction = 60`).catch(() => {});
let s = await as(A, `select public.co_buy('r:JA01XJ')`);
const ac = s.fleet[0];
const hc = `${Math.min(ids.HND, ids.CTS)}-${Math.max(ids.HND, ids.CTS)}`;
s = await as(A, `select public.co_assign(${ac.id}, '${hc}')`);
// この手計算は上級席なしで確かめる（上級席は t46）
if (fs.existsSync(dir + '20261026000092_co3_cabin_fare.sql')) s = await as(A, `select public.co3_set_premium(0)`);
const v2gross = Number(s.gross);
check('スイッチがオフ：co-v2 の収益のまま・econ なし', s.v3 === false && s.econ === null && v2gross > 0, { v3: s.v3, g: v2gross });

// スイッチをオンにする
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
s = await as(A, `select public.co_state()`);
const e = s.econ.find((x) => x.k === hc);
check('はじめは機内食なし・荷物無料', s.meal === 'none' && s.bag === 'free' && Number(s.sat_parts.meal) === -8 && Number(s.sat_parts.bag) === 0, { meal: s.meal, bag: s.bag, p: s.sat_parts });
const e0 = s.econ.find((x) => x.k === hc);
// 機内食 無料：満足度 +8、費用 ×(1 + 0.02/0.71)（FSC）。収益と客は同じ
s = await as(A, `select public.co3_set_service('free', 'free')`);
let e1 = s.econ.find((x) => x.k === hc);
check('無料：満足度の機内食 +8', s.meal === 'free' && Number(s.sat_parts.meal) === 8, s.sat_parts);
check('無料：費用 +2ポイント（FSC は ×1.0282）', near(Number(e1.cost), Number(e0.cost) * (1 + 0.02 / 0.71), 0.02) && near(Number(e1.revenue), Number(e0.revenue), 0.01), { c0: e0.cost, c1: e1.cost });
// 有料：満足度 −3、収益 +3%
s = await as(A, `select public.co3_set_service('paid', 'free')`);
e1 = s.econ.find((x) => x.k === hc);
check('有料：満足度 −3・収益 +3%・費用は同じ', Number(s.sat_parts.meal) === -3 && near(Number(e1.revenue), Number(e0.revenue) * 1.03, 0.02) && near(Number(e1.cost), Number(e0.cost), 0.01), { r0: e0.revenue, r1: e1.revenue });
// 荷物 有料：満足度 −4、旅行の客 −5%（1社なので取り分は同じ、旅行の客だけ減る）、収益 +4%
s = await as(A, `select public.co3_set_service('none', 'paid')`);
e1 = s.econ.find((x) => x.k === hc);
const own0 = Number(e0.own), lei0 = 1190 * 0.4 * 0.85;
check('荷物有料：満足度 −4', Number(s.sat_parts.bag) === -4, s.sat_parts);
check('荷物有料：旅行の客 −5%', near(Number(e1.own), own0 - lei0 * 0.05, 0.1), { own0, own1: e1.own, want: own0 - lei0 * 0.05 });
check('荷物有料：1人あたりの収益 +4%（仕事の客の割合が少し増える分を直して）',
  near(Number(e1.revenue) / Number(e1.carried), Number(e0.revenue) / Number(e0.carried) * 1.04 * (1 + 0.2 * 714 / (714 + lei0 * 0.95)) / (1 + 0.2 * 714 / (714 + lei0)), 0.002),
  { r0: Number(e0.revenue) / Number(e0.carried), r1: Number(e1.revenue) / Number(e1.carried) });
check('選べないものは入れられない', String(await as(A, `select public.co3_set_service('gold', 'free')`)).includes('invalid service'), null);
check('会社の表は直接は書けない', String(await as(A, `update companies set meal = 'free'`)).startsWith('ERROR') || Number(await q1(`select count(*) from companies where meal = 'free'`)) === 0, null);
// 貨物の会社は客がいないので満足度に効かない
await as(A, `select public.co3_set_policy('cargo')`);
s = await as(A, `select public.co_state()`);
check('貨物の会社：機内食と荷物は満足度に効かない', Number(s.sat_parts.meal) === 0 && Number(s.sat_parts.bag) === 0, s.sat_parts);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
