// エアライン経営 co-v3：出資（申し込み・認める・20%と49%の上限・毎日の受け渡し・30日後の引き上げ）
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
// B：羽田⇄広島を飛ぶ会社（友だち）
const hh = `${Math.min(ids.HND, ids.HIJ)}-${Math.max(ids.HND, ids.HIJ)}`;
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no, airline) values ('${B}', ${ids.HND}, ${ids.HIJ}, now() - interval '1 day', now() - interval '1 day' + interval '80 minutes', 674, 'NH671', 'NH');
  insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${B}', ${ids.HND}, 35.55, 139.78, 10, now());`);
await as(B, `select public.co_state()`);
await db.exec(`update companies set rating = 5, safety = 'low', satisfaction = 60, cash = 500000 where user_id = '${B}';
  insert into aircraft (user_id, type, reg, route_key, paid, bought_at) values ('${B}', 'nb', 'JA77BB', '${hh}', 20000, now())`);
const codeB = await q1(`select friend_code from companies where user_id = '${B}'`);
const vB = Number(await q1(`select public.co_value('${B}')`));
check('会社の価値の20%を超えては出せない', String(await as(A, `select public.co3_inv_offer('${codeB}', ${Math.floor(vB * 0.2) + 1})`)).includes('invest limit'), null);
const amt = Math.floor(vB * 0.1);
let s2 = await as(A, `select public.co3_inv_offer('${codeB}', ${amt})`);
check('申し込む（まだお金は動かない）', s2.invest.list[0].status === 'offer' && s2.invest.list[0].role === 'out', s2.invest);
check('同じ相手に2つは出せない', String(await as(A, `select public.co3_inv_offer('${codeB}', 10)`)).includes('already invested'), null);
let cA = Number(await q1(`select cash from companies where user_id = '${A}'`)), cB = Number(await q1(`select cash from companies where user_id = '${B}'`));
let sB = await as(B, `select public.co_state()`);
const vB2 = Number(await q1(`select public.co_value('${B}')`));
sB = await as(B, `select public.co3_inv_answer(${sB.invest.list[0].id}, true)`);
const pct = Number(sB.invest.list[0].pct);
check('認める：お金が動き、割合 ＝ 金額 ÷ 相手の価値', cA - Number(await q1(`select cash from companies where user_id = '${A}'`)) === amt && Number(await q1(`select cash from companies where user_id = '${B}'`)) - cB === amt && near(pct, amt / vB2, 1e-4), { pct, want: amt / vB2 });
const pB = Number(await q1(`select public.co3_profit_pre('${B}')`));
check('出した側：相手のもうけ × 割合を受け取る', near(Number(await q1(`select public.co3_inv_flow('${A}')`)), pct * pB, 0.01), null);
check('受けた側：同じだけ引かれる', near(Number(await q1(`select public.co3_inv_flow('${B}')`)), -pct * pB, 0.01)
  && Math.abs(Number(await q1(`select public.co3_gross('${B}')`)) - (Number(await q1(`select public.co3_gross_pre('${B}')`)) - Math.round(pct * pB))) <= 1, null);
check('30日たつまで引き上げられない', String(await as(A, `select public.co3_inv_withdraw(${sB.invest.list[0].id})`)).includes('invest locked'), null);
// 49%の上限：ほかの会社 3社から
const U = ['00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000303'];
for (const u of U) await db.exec(`insert into auth.users (id) values ('${u}'); insert into companies (user_id, name, rating, cash, friend_code) values ('${u}', 'X', 5, 10000000, 'X${u.slice(-3)}AAAA')`);
const vB3 = Number(await q1(`select public.co_value('${B}')`));
const take = Math.floor(vB3 * 0.19);
for (const u of U) await as(u, `select public.co3_inv_offer('${codeB}', ${take})`);
sB = await as(B, `select public.co_state()`);
const offers = sB.invest.list.filter((x) => x.status === 'offer');
await db.exec(`update co3_invest set pct = 0.35 where investor = '${A}'`);   // すでに35%を受けている形にする
check('合計49%を超える出資は受けられない', String(await as(B, `select public.co3_inv_answer(${offers[0].id}, true)`)).includes('invest total limit'), null);
await db.exec(`update co3_invest set pct = ${pct} where investor = '${A}'`);
await as(B, `select public.co3_inv_answer(${offers[0].id}, true)`);
check('49%までなら受けられる', (await q1(`select status from co3_invest where id = ${offers[0].id}`)) === 'active', null);
await as(B, `select public.co3_inv_answer(${offers[1].id}, false)`);
// 30日後に引き上げ：そのときの価値 × 割合
await db.exec(`update co3_invest set accepted_at = now() - interval '31 days' where investor = '${A}'`);
cA = Number(await q1(`select cash from companies where user_id = '${A}'`));
const back = Math.floor(Number(await q1(`select public.co_value('${B}')`)) * pct);
s2 = await as(A, `select public.co3_inv_withdraw(${Number(await q1(`select id from co3_invest where investor = '${A}' and status = 'active'`))})`);
const r = (await db.query(`select status, returned from co3_invest where investor = '${A}'`)).rows[0];
check('引き上げ：そのときの価値 × 割合が戻る', r.status === 'withdrawn' && Math.abs(Number(r.returned) - back) <= 2 && Math.abs(Number(await q1(`select cash from companies where user_id = '${A}'`)) - cA - Number(r.returned)) <= 2, { r, back });
check('ほかの会社の出資は見えない', Number(await as(U[2], `select count(*) from co3_invest where investor <> '${U[2]}' and target <> '${U[2]}'`)) === 0, null);
await db.exec(`update companies set rating = 2 where user_id = '${A}'`);
check('格付け2：出資できない', String(await as(A, `select public.co3_inv_offer('${codeB}', 10)`)).includes('rating required 3'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
