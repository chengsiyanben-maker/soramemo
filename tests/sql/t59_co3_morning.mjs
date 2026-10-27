// エアライン経営 co-v3：朝のまとめ（毎晩の記録・前の日とのちがい・欠航・神対応・実際の空）
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
await db.exec(`update companies set rating = 5`).catch(() => {});   // 格付けの鍵は t63 で試す。ここでは解放ずみの形で
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
const today = await q1(`select ((now() at time zone 'Asia/Tokyo')::date)::text`);
check('記録がないうちは、朝のまとめは空', s.morning && s.morning.profit === null && s.morning.cancelled === 0, s.morning);
check('スイッチがオフなら記録しない', (await db.exec(`update ops.flags set value = 'false' where key = 'co_v3'`), Number(await q1(`select public.co3_daily_record()`))) === 0, null);
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
// 2日前と前の日の記録（毎晩の処理を日付を指定して動かす）
check('毎晩の記録：会社ごとに1行', Number(await q1(`select public.co3_daily_record('${today}'::date - 2)`)) >= 1, null);
await db.exec(`update co3_daily set satisfaction = 39.4 where user_id = '${A}' and day = '${today}'::date - 2`);
await db.exec(`update companies set satisfaction = 39.7 where user_id = '${A}'`);
await q1(`select public.co3_daily_record('${today}'::date - 1)`);
const p2 = Number(await q1(`select profit from co3_daily where user_id = '${A}' and day = '${today}'::date - 2`));
const y = (await db.query(`select * from co3_daily where user_id = '${A}' and day = '${today}'::date - 1`)).rows[0];
s = await as(A, `select public.co_state()`);
check('記録：収益 − 維持費 ＝ もうけ・満足度・路線と機体の数', Number(y.profit) === Number(y.gross) - Number(y.upkeep) && Number(y.gross) === Number(s.gross) && Number(y.satisfaction) === 39.7 && y.routes === 1 && y.fleet === 1, y);
check('朝のまとめ：前の日のもうけ・その前の日・満足度', Number(s.morning.profit) === Number(y.profit) && Number(s.morning.prev_profit) === p2
  && Number(s.morning.sat) === 39.7 && Number(s.morning.prev_sat) === 39.4, s.morning);
// 前の日の本物の欠航 → トラブル → 朝のまとめに欠航の数と、対応が必要な数
await db.exec(`insert into co_sky (route_key, day, n, cxl, avg4, mult) values ('${hc}', '${today}'::date - 1, 18, 2, 20, 0.9)
  on conflict (route_key, day) do update set n = excluded.n, cxl = excluded.cxl, avg4 = excluded.avg4, mult = excluded.mult`);
await q1(`select public.co3_trouble_detect()`);
s = await as(A, `select public.co_state()`);
check('朝のまとめ：欠航 1便・対応が必要 1件', Number(s.morning.cancelled) === 1 && Number(s.morning.open) === 1, s.morning);
check('朝のまとめ：実際の空（倍率 0.9 の路線）', s.morning.sky.length === 1 && s.morning.sky[0].k === hc && Number(s.morning.sky[0].mult) === 0.9 && s.morning.sky[0].cxl === 2, s.morning.sky);
s = await as(A, `select public.co3_trouble_respond(${s.troubles[0].id}, 'transfer')`);
check('朝のまとめ：神対応 1件・対応が必要 0件', Number(s.morning.god) === 1 && Number(s.morning.open) === 0, s.morning);
check('毎日の記録の表：自分の分だけ読める・直接は書けない', Number(await as(B, `select count(*) from co3_daily`)) === 0 && Number(await as(A, `select count(*) from co3_daily`)) === 2
  && String(await as(A, `update co3_daily set profit = 999999`)).startsWith('ERROR'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
