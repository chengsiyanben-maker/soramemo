// エアライン経営 co-v3：便の時刻（おまかせのスケジュール）と便ごとの客
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
const L = s.legs[hc], sum = (k) => L.reduce((a, x) => a + Number(x[k]), 0);
check('6便（820km：1便100分、間隔180分）', L.length === 6 && L.map((x) => x.t).join(',') === '390,570,750,930,1110,1290' && L.every((x) => x.ta === x.t + 100), L.map((x) => [x.t, x.ta]));
check('向き：羽田と新千歳を交互（路線の a から）', L.every((x, i) => x.f === (i % 2 ? L[1].f : L[0].f)) && L[0].f !== L[1].f && L[0].to === L[1].f, L.map((x) => x.f + '>' + x.to));
check('6:30〜23:30 の中', L.every((x) => x.t >= 390 && x.ta <= 1410), null);
check('便の客の合計 ＝ 路線の運んだ客', near(sum('biz') + sum('lei'), Number(e.carried), 0.5), { legs: sum('biz') + sum('lei'), carried: e.carried });
check('仕事の客の合計 ＝ 路線の計算の仕事の客（biz_pax）', near(sum("biz"), Number(e.biz), 0.5) && Number(e.biz) > 0, { legs: sum("biz"), econ: e.biz });
check('どの便も席を超えない', L.every((x) => Number(x.biz) + Number(x.lei) <= Number(x.seats) + 0.01), L.map((x) => Number(x.biz) + Number(x.lei)));
check('仕事の客は朝（6:30）が昼（12:30）より多い、旅行の客は昼が多い', Number(L[0].biz) > Number(L[2].biz) && Number(L[2].lei) > Number(L[0].lei), L.map((x) => [x.biz, x.lei]));
// 便数を2便に：運べる客は 2 × 369 × 0.85。満席を超えないように回す
s = await as(A, `select public.co3_set_flights('${hc}', 2)`);
const L2 = s.legs[hc], e2 = s.econ.find((x) => x.k === hc);
check('2便：便の客の合計 ＝ 運んだ客、どちらも席の中', L2.length === 2 && near(L2.reduce((a, x) => a + Number(x.biz) + Number(x.lei), 0), Number(e2.carried), 0.5)
  && L2.every((x) => Number(x.biz) + Number(x.lei) <= Number(x.seats) + 0.01), L2);
check('2便：間隔は (1020 − 100) ÷ 1 ＝ 920分', L2[1].t - L2[0].t === 920, L2.map((x) => x.t));
// 本拠地が新千歳なら新千歳から出る
await db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${A}', ${ids.CTS}, 42.77, 141.69, 10, now())`);
s = await as(A, `select public.co3_set_home(${ids.CTS})`);
check('本拠地 新千歳：1便目は新千歳から', s.legs[hc][0].f === 'CTS', s.legs[hc][0]);
// 機体がない路線は出さない
await db.exec(`update aircraft set route_key = null where user_id = '${A}'`);
s = await as(A, `select public.co_state()`);
check('機体がない路線は便がない', !s.legs[hc], s.legs);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
