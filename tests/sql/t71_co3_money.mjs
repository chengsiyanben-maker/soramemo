// エアライン経営 co-v3：ラウンジ・マイル制度・安全への投資と会社の出来事・借金
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
// 手計算は満足度の倍率なし（満足度60）で確かめる。満足度は t47
await db.exec(`update companies set satisfaction = 60`).catch(() => {});
let s = await as(A, `select public.co_buy('r:JA01XJ')`);
const ac = s.fleet[0];
const hc = `${Math.min(ids.HND, ids.CTS)}-${Math.max(ids.HND, ids.CTS)}`;
s = await as(A, `select public.co_assign(${ac.id}, '${hc}')`);
// この手計算は上級席なしで確かめる（上級席は t46）
if (fs.existsSync(dir + '20261028000102_co3_cabin_fare.sql')) s = await as(A, `select public.co3_set_premium(0)`);
const v2gross = Number(s.gross);
check('スイッチがオフ：co-v2 の収益のまま・econ なし', s.v3 === false && s.econ === null && v2gross > 0, { v3: s.v3, g: v2gross });

// スイッチをオンにする
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
s = await as(A, `select public.co_state()`);
const e = s.econ.find((x) => x.k === hc);
const acid = s.fleet[0].id, rev0 = Number(e.revenue), cost0 = Number(e.cost), biz = 0.60;   // 羽田⇄新千歳は大きい空港どうし（仕事の客 60%）
const E = async () => (await as(A, `select public.co_state()`)).econ.find((x) => x.k === hc);
const cash = async () => Number(await q1(`select cash from companies where user_id = '${A}'`));
check('はじめ：ラウンジなし・マイルなし・安全は普通・借金なし', s.money3.miles === 0 && s.money3.safety === 'normal' && s.money3.debt === 0 && s.money3.lounges.length === 0, s.money3);
// ラウンジ
let c0 = await cash();
s = await as(A, `select public.co3_build_lounge('HND')`);
check('羽田にラウンジ1段（40,000）', c0 - (await cash()) === 40000 && s.money3.lounges[0].level === 1, s.money3.lounges);
let e1 = await E();
check('収益 ＋ 仕事の客 60% × 5%', near(Number(e1.revenue), rev0 * (1 + biz * 0.05), 0.05), { r: e1.revenue, rev0 });
check('満足度の内わけ：ラウンジ +2', Number(s.sat_parts.lounge) === 2, s.sat_parts);
check('訪れていない空港には建てられない', String(await as(A, `select public.co3_build_lounge('FUK')`)).includes('not visited'), null);
await as(A, `select public.co3_build_lounge('HND')`); s = await as(A, `select public.co3_build_lounge('HND')`);
check('3段まで・満足度 +6', s.money3.lounges[0].level === 3 && Number(s.sat_parts.lounge) === 6 && String(await as(A, `select public.co3_build_lounge('HND')`)).includes('lounge max'), s.sat_parts);
const revL = Number((await E()).revenue);
// マイル（同じ路線にほかの会社がいないと集まり方は効かない。費用は引かれる）
s = await as(A, `select public.co3_set_miles(2)`);
check('マイル2段：ほかの会社がいないので 収益 −4% だけ', near(Number((await E()).revenue), revL * 0.96, 0.05) && Number(s.sat_parts.miles) === 2, { r: (await E()).revenue, revL });
await db.exec(`update companies set miles_since = (now() at time zone 'Asia/Tokyo')::date - 90 where user_id = '${A}'`);
check('続けた日数：90日で 8% × 1.25 ＝ 10%', near(Number(await q1(`select public.co3_miles_eff('${A}')`)), 0.10, 1e-9), null);
check('ほかの会社がいる路線：仕事の客 × 10%', near(Number(await q1(`select public.co3_extra_rev_mult('${A}', 'XXX', 'YYY', 0.6, 'fsc', 1)`)), (1 + 0.6 * 0.10) * 0.96, 1e-9), null);
s = await as(A, `select public.co3_set_miles(0)`);
check('やめると0日から', s.money3.miles_since === null && Number(s.money3.miles_eff) === 0, s.money3);
// 安全への投資
const cN = Number((await E()).cost);
s = await as(A, `select public.co3_set_safety('high')`);
check('手厚い：運航の費用 ＋2ポイント（普通 +1 → 手厚い +3）', near(Number((await E()).cost), cN / (1 + 0.01 / 0.71) * (1 + 0.03 / 0.71), 0.05) && s.money3.safety === 'high', { c: (await E()).cost, cN });
s = await as(A, `select public.co3_set_safety('low')`);
const rl = s.money3.rates, rh = (await (async () => { await as(A, `select public.co3_set_safety('high')`); return (await as(A, `select public.co_state()`)).money3.rates; })());
check('手厚いと起きやすさ 0.4 ÷ 1.5（半分以下）', near(Number(rh.drink) / Number(rl.drink), 0.4 / 1.5, 1e-9) && near(Number(rh.maint) / Number(rl.maint), 0.4 / 1.5, 1e-9), { rl, rh });
// 出来事：飲酒問題
const today = await q1(`select ((now() at time zone 'Asia/Tokyo')::date)::text`);
const sat0 = Number(await q1(`select satisfaction from companies where user_id = '${A}'`)), rep0 = Number(await q1(`select public.co_rep_points('${A}')`));
const revD = Number((await E()).revenue);
check('飲酒問題を起こす（試験用）', Number(await q1(`select public.co3_events_draw('${today}', 'drink')`)) === 1, null);
check('満足度 −10・評判 −40・収益 −20%', near(Number(await q1(`select satisfaction from companies where user_id = '${A}'`)), sat0 - 10, 0.01) && Number(await q1(`select public.co_rep_points('${A}')`)) === rep0 - 40
  && (await db.exec(`update companies set satisfaction = ${sat0} where user_id = '${A}'`), near(Number((await E()).revenue), revD * 0.8, 0.05)), null);   // 収益は満足度を戻してから比べる
check('同じ日に2回は起きない', Number(await q1(`select public.co3_events_draw('${today}', 'drink')`)) === 0, null);
await db.exec(`update co3_events set day = day - 3, until_day = until_day - 3 where user_id = '${A}'`);
check('3日たつと収益は戻る', near(Number((await E()).revenue), revD, 0.05), null);
// 整備のミス：その機種がすべて2日運休
check('整備のミスを起こす（試験用）', Number(await q1(`select public.co3_events_draw('${today}', 'maint')`)) === 1, null);
check('A350 が2日運休（予備機なし）・評判 −30 も', (await q1(`select public.co3_ac_grounded(${acid}, '${today}')`)) === 'down' && Number(await q1(`select public.co_rep_points('${A}')`)) === rep0 - 70, null);
s = await as(A, `select public.co_state()`);
check('会社の状態と新聞に出る', s.money3.events.length === 2 && (await db.query(`select count(*)::int n from co3_news where user_id = '${A}' and kind = 'event'`)).rows[0].n === 2, s.money3.events);
check('出来事は自分の分しか見えない', Number(await as(B, `select count(*) from co3_events`)) === 0 && Number(await as(A, `select count(*) from co3_events`)) === 2, null);
// 借金
const room = Number(s.money3.debt_room), v0 = Number(await q1(`select public.co_value('${A}')`));
check('借りられるのは会社の価値の半分', room === Math.floor(v0 * 0.5), { room, v0 });
c0 = await cash();
s = await as(A, `select public.co3_borrow(100000)`);
check('100,000 借りる：資金が増え、会社の価値は変わらない', (await cash()) - c0 === 100000 && s.money3.debt === 100000 && Math.abs(Number(await q1(`select public.co_value('${A}')`)) - v0) <= 2, null);
check('上限を超えて借りられない', String(await as(A, `select public.co3_borrow(${room * 4})`)).includes('debt limit'), null);
await db.exec(`update companies set debt_at = now() - interval '31 days' where user_id = '${A}'`);
c0 = await cash();
await q1(`select public.co3_events_draw('${today}', 'none')`);
check('30日たつと利息 3%（3,000）', c0 - (await cash()) === 3000, { d: c0 - (await cash()) });
s = await as(A, `select public.co3_borrow(-100000)`);
check('返す', s.money3.debt === 0 && (await q1(`select debt_at from companies where user_id = '${A}'`)) === null, s.money3);
check('借金より多くは返せない', String(await as(A, `select public.co3_borrow(-1)`)).includes('invalid amount'), null);
check('ラウンジは自分の分しか見えない', Number(await as(B, `select count(*) from co3_lounges`)) === 0, null);
await db.exec(`update companies set rating = 2 where user_id = '${A}'`);
s = await as(A, `select public.co_state()`);
check('格付け2：使えない・ラウンジの満足度は数えない', String(await as(A, `select public.co3_borrow(10)`)).includes('rating required 3') && Number(s.sat_parts.lounge) === 0, s.sat_parts);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
