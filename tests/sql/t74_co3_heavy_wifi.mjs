// エアライン経営 co-v3：C点検・重整備（自動・予備機・費用・古さが戻る）と機内Wi-Fi（費用・維持費・仕事の客・満足度）
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
const acid = s.fleet[0].id, today = await q1(`select ((now() at time zone 'Asia/Tokyo')::date)::text`);
const price = Math.max(40000, Number(await q1(`select (ac_spec('lg')).price`)));
const paid = Number(await q1(`select paid from aircraft where id = ${acid}`)), base = Math.max(paid, Number(await q1(`select (ac_spec('lg')).price`)));
check('はじめは点検しない', Number(await q1(`select public.co3_heavy_run('${today}')`)) === 0, null);
// 2年半たった
await db.exec(`update aircraft set heavy_from = '${today}'::date - 912 where id = ${acid}`);
let c0 = Number(await q1(`select cash from companies where user_id = '${A}'`));
check('2年半でC点検が始まる', Number(await q1(`select public.co3_heavy_run('${today}')`)) === 1, null);
const h = (await db.query(`select * from co3_heavy where aircraft_id = ${acid}`)).rows[0];
check('大型機は10日・費用 3% × 1.3・予備機なし', h.kind === 'c' && (new Date(h.end_day) - new Date(h.start_day)) / 864e5 === 9 && Number(h.cost) === Math.ceil(base * 0.03 * 1.3) && h.spare_id === null
  && c0 - Number(await q1(`select cash from companies where user_id = '${A}'`)) === Math.ceil(base * 0.03 * 1.3), h);
s = await as(A, `select public.co_state()`);
check('予備機がいないと、その路線は飛ばない（便 0）', s.econ.find((x) => x.k === hc).flights === 0 && s.heavy.length === 1, s.heavy);
check('点検中は2回目を始めない', Number(await q1(`select public.co3_heavy_run('${today}')`)) === 0, null);
// 予備機がいれば代わりに飛ぶ
await db.exec(`delete from co3_heavy; insert into aircraft (user_id, type, reg, paid, bought_at) values ('${A}', 'lg', 'JA02ZZ', 40000, now()); update aircraft set heavy_from = '${today}'::date - 912 where id = ${acid}`);
await q1(`select public.co3_heavy_run('${today}')`);
const h2 = (await db.query(`select h.*, s.reg from co3_heavy h left join aircraft s on s.id = h.spare_id where h.aircraft_id = ${acid}`)).rows[0];
s = await as(A, `select public.co_state()`);
check('予備機がいれば代わりに飛ぶ（便はいつもどおり）', h2.reg === 'JA02ZZ' && s.econ.find((x) => x.k === hc).flights === e.flights, { h2, f: s.econ.find((x) => x.k === hc).flights });
// 重整備：8年
await db.exec(`delete from co3_heavy where aircraft_id = ${acid}; update aircraft set heavy_from = '${today}'::date - 2920, bought_at = now() - interval '9 years' where id = ${acid}`);
const age0 = Number(await q1(`select ac_age(bought_at) from aircraft where id = ${acid}`));
await q1(`select public.co3_heavy_run('${today}')`);
const h3 = (await db.query(`select * from co3_heavy where aircraft_id = ${acid}`)).rows[0];
check('8年で重整備：21日・費用 10% × 1.3・古さが新品に戻る', h3.kind === 'heavy' && (new Date(h3.end_day) - new Date(h3.start_day)) / 864e5 === 20 && Number(h3.cost) === Math.ceil(base * 0.1 * 1.3)
  && age0 < 1 && Number(await q1(`select ac_age(bought_at) from aircraft where id = ${acid}`)) === 1, { h3, age0 });
check('点検は自分の分しか見えない', Number(await as(B, `select count(*) from co3_heavy`)) === 0 && Number(await as(A, `select count(*) from co3_heavy`)) >= 1, null);
await db.exec(`delete from co3_heavy`);
// Wi-Fi
s = await as(A, `select public.co_state()`);
const r0 = Number(s.econ.find((x) => x.k === hc).revenue), up0 = Number(await q1(`select public.co3_ac_upkeep(${acid})`));
c0 = Number(await q1(`select cash from companies where user_id = '${A}'`));
s = await as(A, `select public.co3_set_wifi(${acid}, true)`);
check('Wi-Fi を付ける：値段の3%', c0 - Number(await q1(`select cash from companies where user_id = '${A}'`)) === Math.ceil(base * 0.03) && s.fleet.find((x) => x.id === acid).wifi === true, null);
check('維持費 +10%', near(Number(await q1(`select public.co3_ac_upkeep(${acid})`)), up0 * 1.1, 0.01), null);
check('収益 ＋ 仕事の客 60% × 8%', near(Number(s.econ.find((x) => x.k === hc).revenue), r0 * (1 + 0.6 * 0.08), 0.05), { r: s.econ.find((x) => x.k === hc).revenue, r0 });
check('満足度 ＋（付けた機体の割合 1/2 × 6）', Number(s.sat_parts.wifi) === 3, s.sat_parts);
c0 = Number(await q1(`select cash from companies where user_id = '${A}'`));
s = await as(A, `select public.co3_set_wifi(${acid}, false)`); s = await as(A, `select public.co3_set_wifi(${acid}, true)`);
check('外してまた付けると、もう一度お金がかかる', c0 - Number(await q1(`select cash from companies where user_id = '${A}'`)) === Math.ceil(base * 0.03), null);
await db.exec(`update companies set rating = 3 where user_id = '${A}'`);
check('格付け3：Wi-Fi は付けられない・効かない', String(await as(A, `select public.co3_set_wifi(${acid}, true)`)).includes('rating required 4') && near(Number((await as(A, `select public.co_state()`)).econ.find((x) => x.k === hc).revenue), r0, 0.05), null);
await db.exec(`update companies set rating = 2 where user_id = '${A}'; update aircraft set heavy_from = '${today}'::date - 2000`);
check('格付け2：C点検は始まらない（維持費に込み）', Number(await q1(`select public.co3_heavy_run('${today}')`)) === 0, null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
