// エアライン経営 co-v3：機体の故障と予備機（格付け3から）・定時率（会社のせいの欠航だけ）
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
const L = s.legs[hc], rev = Number(e.revenue) / e.flights, acid = s.fleet[0].id;
const today = await q1(`select ((now() at time zone 'Asia/Tokyo')::date)::text`);
const at = (hm) => `('${today}'::date + time '${hm}') at time zone 'Asia/Tokyo'`;
// 1年あたりの回数：新しい世代の新品（A350）は1回、役職「整備」で ×0.7、古くなると増える
check('新品の新世代：年1回', Number(await q1(`select public.co3_breakdown_rate(${acid})`)) === 1, await q1(`select public.co3_breakdown_rate(${acid})`));
await db.exec(`update companies set roles = '{"maint": "${ids.HND}"}' where user_id = '${A}'`);
check('役職「整備」：×0.7', near(Number(await q1(`select public.co3_breakdown_rate(${acid})`)), 0.7, 1e-9), null);
await db.exec(`update companies set roles = '{}' where user_id = '${A}'; update aircraft set bought_at = now() - interval '5 years' where id = ${acid}`);
check('古くなる（古さ −20%）と ＋1.5 → 年2.5回', near(Number(await q1(`select public.co3_breakdown_rate(${acid})`)), 2.5, 1e-9), await q1(`select public.co3_breakdown_rate(${acid})`));
await db.exec(`update aircraft set bought_at = now() where id = ${acid}`);
// 格付け2のうちは故障しない
await db.exec(`update companies set rating = 2 where user_id = '${A}'`);
await db.exec(`create or replace function public.co3_breakdown_rate(p_aircraft bigint) returns numeric language sql stable as $$ select 1000::numeric $$`);   // 試験：かならず故障する
check('格付け2：故障を引かない', Number(await q1(`select public.co3_breakdown_draw('${today}')`)) === 0, null);
await db.exec(`update companies set rating = 3 where user_id = '${A}'`);
// 予備機（路線に入れていない旅客機）があれば代わりに飛ぶ
await db.exec(`insert into aircraft (user_id, type, paid, reg) values ('${A}', 'nb', 1000, 'JA02SP')`);
check('格付け3：故障を引く（試験ではかならず）', Number(await q1(`select public.co3_breakdown_draw('${today}')`)) === 1, null);
let bk = (await db.query(`select b.*, s.reg as spare_reg from co3_breakdowns b left join aircraft s on s.id = b.spare_id where b.aircraft_id = ${acid}`)).rows[0];
check('1〜3日運休・予備機 JA02SP', bk.days >= 1 && bk.days <= 3 && bk.spare_reg === 'JA02SP', bk);
check('予備機が飛ぶ日は spare', (await q1(`select public.co3_grounded('${A}', '${hc}', '${today}')`)) === 'spare', null);
check('同じ機体が運休中なら、もう引かない', Number(await q1(`select public.co3_breakdown_draw('${today}')`)) === 0, null);
await q1(`select public.co3_legs_check(${at('03:45')})`);
let x = (await db.query(`select * from co3_leg_status where user_id = '${A}' and day = '${today}' and leg = 1`)).rows[0];
check('予備機の日：便はいつもどおり（本物の便がなければ定時）・予備機の印', x.status === 'ok' && x.spare === true && x.cause === null, x);
// 予備機がないと欠航（会社のせい）。対応してくださいはその日のはじめの1便だけ
await db.exec(`update co3_breakdowns set spare_id = null where aircraft_id = ${acid}`);
check('予備機がなければ down', (await q1(`select public.co3_grounded('${A}', '${hc}', '${today}')`)) === 'down', null);
const cash0 = Number(await q1(`select cash from companies where user_id = '${A}'`));
await q1(`select public.co3_legs_check(${at('06:45')})`); await q1(`select public.co3_legs_check(${at('09:45')})`);
const st = (await db.query(`select leg, status, cause, loss from co3_leg_status where user_id = '${A}' and day = '${today}' order by leg`)).rows;
check('故障の日：9:30・12:30 は欠航（会社のせい）・収益0', st[1].status === 'cxl' && st[1].cause === 'breakdown' && st[2].status === 'cxl' && near(Number(st[1].loss), rev, 0.02), st);
check('欠航の分を引く（2便）', Math.abs(cash0 - Number(await q1(`select cash from companies where user_id = '${A}'`)) - 2 * Math.ceil(rev)) <= 3, null);
const tb = (await db.query(`select leg, cause, kind from co3_troubles where user_id = '${A}' and day = '${today}' and cause = 'breakdown'`)).rows;
check('対応してくださいは、はじめの1便（9:30）だけ', tb.length === 1 && tb[0].leg === 2 && tb[0].kind === 'cxl', tb);
// 定時率：3便のうち2便が会社のせいの欠航 → 33% → −15、自分のせいの欠航 −2。評判 −20
s = await as(A, `select public.co_state()`);
check('満足度の目標値：定時率 −15・自分のせいの欠航 −2', Number(s.sat_parts.ontime) === -15 && Number(s.sat_parts.own_cxl) === -2 && near(Number(s.sat_parts.ontime_rate), 1 / 3, 0.001), s.sat_parts);
check('評判：定時率 70%未満で −20', Number(await q1(`select public.co3_ontime_rep('${A}')`)) === -20, null);
check('会社の状態：いまの故障', s.breakdowns.length === 1 && s.breakdowns[0].reg === 'JA01XJ' && s.breakdowns[0].spare_reg === null, s.breakdowns);
check('トラブルの原因：機体の故障', s.troubles.some((y) => y.cause === 'breakdown'), null);
check('点数：95% +10・90% +5・80% 0・70% −8・それより下 −15', Number(await q1(`select co3.ontime_points(0.96)`)) === 10 && Number(await q1(`select co3.ontime_points(0.9)`)) === 5
  && Number(await q1(`select co3.ontime_points(0.85)`)) === 0 && Number(await q1(`select co3.ontime_points(0.7)`)) === -8 && Number(await q1(`select co3.ontime_points(0.5)`)) === -15, null);
// 格付け2なら定時率は数えない
await db.exec(`update companies set rating = 2 where user_id = '${A}'`);
s = await as(A, `select public.co_state()`);
check('格付け2：定時率は目標値に入れない', Number(s.sat_parts.ontime) === 0 && Number(s.sat_parts.own_cxl) === 0 && s.sat_parts.ontime_rate === null, s.sat_parts);
check('故障の表：自分の分だけ読める・直接は書けない', Number(await as(B, `select count(*) from co3_breakdowns`)) === 0 && Number(await as(A, `select count(*) from co3_breakdowns`)) === 1
  && String(await as(A, `delete from co3_breakdowns`)).startsWith('ERROR'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
