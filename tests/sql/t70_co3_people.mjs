// エアライン経営 co-v3：乗員・整備士と地上の仕事（要る人・いる人・雇う・足りないと運休・故障が増える・給料・地上の仕事の自社）
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
if (fs.existsSync(dir + '20261028000102_co3_cabin_fare.sql')) s = await as(A, `select public.co3_set_premium(0)`);
const v2gross = Number(s.gross);
check('スイッチがオフ：co-v2 の収益のまま・econ なし', s.v3 === false && s.econ === null && v2gross > 0, { v3: s.v3, g: v2gross });

// スイッチをオンにする
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
s = await as(A, `select public.co_state()`);
const e = s.econ.find((x) => x.k === hc);
const acid = s.fleet[0].id, fl0 = e.flights, cost0 = Number(e.cost), up0 = Number(s.upkeep);
let p = s.people;
check('A350 は2機分・はじめは3機分いる', p.need === 2 && p.crew === 3 && p.mech === 3 && p.crew_ratio == 1 && p.mech_mult == 1 && p.cost == 0, p);
// 機体を増やして要る人を超える：A350 を3機（6機分）
await db.exec(`insert into aircraft (user_id, type, reg, route_key, paid, bought_at) select '${A}', 'lg', 'JA0' || g || 'ZZ', k, 40000, now() from (values (2, '${[ids.HIJ, ids.GAJ].sort((x, y) => x - y).join('-')}'), (3, '${[ids.CTS, ids.HIJ].sort((x, y) => x - y).join('-')}')) v(g, k)`).catch(async (err) => { console.log('insert', err.message); });
s = await as(A, `select public.co_state()`); p = s.people;
check('3機で6機分要る・乗員は 3 ÷ 6 の割合まで', p.need === 6 && near(Number(p.crew_ratio), 0.5, 1e-9) && near(Number(p.mech_mult), 2, 1e-9), p);
const r1 = Number(await q1(`select public.co3_breakdown_rate(${acid})`));
// 格付け2：足りなくても起きない
await db.exec(`update companies set rating = 2 where user_id = '${A}'`);
s = await as(A, `select public.co_state()`);
check('格付け2：人の不足は起きない', s.people.crew_ratio == 1 && s.people.mech_mult == 1 && near(r1, Number(await q1(`select public.co3_breakdown_rate(${acid})`)) * 2, 1e-9), s.people);
const flR2 = s.econ.find((x) => x.k === hc).flights;
check('格付け2：雇えない', String(await as(A, `select public.co3_hire('crew', 1)`)).includes('rating required 3'), null);
await db.exec(`update companies set rating = 5 where user_id = '${A}'`);
s = await as(A, `select public.co_state()`);
check('格付け3から：便は 乗員の割合まで', s.econ.find((x) => x.k === hc).flights === Math.floor(flR2 * 0.5), { a: s.econ.find((x) => x.k === hc).flights, flR2 });
// 雇う
let c0 = Number(await q1(`select cash from companies where user_id = '${A}'`));
s = await as(A, `select public.co3_hire('crew', 3)`);
check('乗員3組を雇う：採用費 6,000・6機分いる', c0 - Number(await q1(`select cash from companies where user_id = '${A}'`)) === 6000 && s.people.crew === 6 && s.people.crew_ratio == 1, s.people);
check('便が元に戻る', s.econ.find((x) => x.k === hc).flights === flR2, null);
s = await as(A, `select public.co3_hire('mech', 3)`);
check('整備士3機分：故障は元に戻る・給料 3×20＋3×15＝105/日', s.people.mech_mult == 1 && Number(s.people.cost) === 105 && near(r1 / 2, Number(await q1(`select public.co3_breakdown_rate(${acid})`)), 1e-9), s.people);
const up1 = Number(s.upkeep);
s = await as(A, `select public.co3_hire('mech', -3)`);
check('減らす（採用費は戻らない）・給料が減る', s.people.mech_hired === 0 && up1 - Number(s.upkeep) === 45, { up1, u: s.upkeep });
check('いない人は減らせない', String(await as(A, `select public.co3_hire('mech', -1)`)).includes('invalid hire'), null);
await db.exec(`update companies set cash = 100 where user_id = '${A}'`);
check('お金が足りないと雇えない', String(await as(A, `select public.co3_hire('crew', 1)`)).includes('not enough cash'), null);
await db.exec(`update companies set cash = 500000 where user_id = '${A}'`);
// 地上の仕事
check('拠点がないと自社にできない', String(await as(A, `select public.co3_set_ground('self')`)).includes('no home airport'), null);
await db.exec(`update companies set home_airport = ${ids.HND} where user_id = '${A}'`);
s = await as(A, `select public.co_state()`); const costA = Number(s.econ.find((x) => x.k === hc).cost), upA = Number(s.upkeep);
s = await as(A, `select public.co3_set_ground('self')`);
check('地上の仕事を自社：拠点を発着する便の運航の費用 −3%・人件費 30/日', near(Number(s.econ.find((x) => x.k === hc).cost), costA * 0.97, 0.02) && Number(s.upkeep) - upA === 30 && s.people.ground === 'self', { c: s.econ.find((x) => x.k === hc).cost, costA });
check('役職「乗員」：守り神の階級 +1機分', (await (async () => { await db.exec(`update companies set roles = jsonb_build_object('crew', ${ids.HND}) where user_id = '${A}'`); return (await as(A, `select public.co_state()`)).people.crew; })()) === 6 + 1 + Number(await q1(`select rank_tier(1)`)), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
