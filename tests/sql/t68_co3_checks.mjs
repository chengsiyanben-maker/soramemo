// エアライン経営 co-v3：定期点検（A点検。飛んだ時間・自動・おまかせ・自分で入れる・期限切れ・故障が半分）
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
const acid = s.fleet[0].id;
const today = await q1(`select ((now() at time zone 'Asia/Tokyo')::date)::text`);
const at = (hm) => `('${today}'::date + time '${hm}') at time zone 'Asia/Tokyo'`;
const acr = async () => (await db.query(`select * from aircraft where id = ${acid}`)).rows[0];
const cash = async () => Number(await q1(`select cash from companies where user_id = '${A}'`));
// 前の日に飛んだ便：6便のうち1便が欠航 → 5便 × 100分
await db.exec(`insert into co3_leg_status (user_id, day, route_key, leg, dep, arr, dep_at, status, aircraft_id)
  select '${A}', '${today}'::date - 1, '${hc}', g, 'HND', 'CTS', now() - interval '1 day', case when g = 3 then 'cxl' else 'ok' end, ${acid} from generate_series(1, 6) g`);
await q1(`select public.co3_checks_run()`);
check('飛んだ時間：欠航を除く5便 × 100分 ＝ 500分', (await acr()).fly_min === 500, await acr());
const iv = 1200 * 60;
check('A350（大型）の間隔は1,200時間', Number(await q1(`select co3.a_interval_min('lg')`)) === iv, null);
// 格付け2：期限が来たら自動で点検（お金はかからない）・維持費は +10%
await db.exec(`update companies set rating = 2 where user_id = '${A}'; update aircraft set fly_min = ${iv} where id = ${acid}`);
const up2 = Number(await q1(`select public.co3_ac_upkeep(${acid})`)); let c0 = await cash();
check('格付け2：期限の夜に自動で点検・お金はかからない', Number(await q1(`select public.co3_checks_run('${today}'::date - 5)`)) === 1 && (await acr()).check_min === iv && (await cash()) === c0 && !!(await acr()).checked_day, await acr());
await db.exec(`update companies set rating = 5 where user_id = '${A}'`);
check('格付け1・2 は維持費 +10%（自動の点検の分）', near(up2, Number(await q1(`select public.co3_ac_upkeep(${acid})`)) * 1.1, 0.01), { up2 });
// 格付け3以上・おまかせ：期限の夜に点検、費用は 値段の0.2% × 1.3（ゲームの整備会社）× 1.1（おまかせ）
await db.exec(`update aircraft set fly_min = check_min + ${iv} where id = ${acid}`);
const paid = Math.max(Number((await acr()).paid), Number(await q1(`select (ac_spec('lg')).price`)));
c0 = await cash();
await q1(`select public.co3_checks_run('${today}'::date - 5)`);
check('おまかせ：点検の費用 ＝ 値段の0.2% × 1.3 × 1.1', Math.abs(c0 - (await cash()) - Math.ceil(paid * 0.002 * 1.3 * 1.1)) <= 1 && (await acr()).fly_min === (await acr()).check_min, { d: c0 - (await cash()), want: Math.ceil(paid * 0.002 * 1.3 * 1.1) });
// 自分で入れる：頼んでいないと期限を過ぎて飛べない（欠航＝会社のせい）
s = await as(A, `select public.co3_set_check_mode('self')`);
check('点検のやり方：自分で入れる', s.check_mode === 'self', s.check_mode);
await db.exec(`update aircraft set fly_min = check_min + ${iv} + 60, checked_day = null where id = ${acid}`);
check('頼んでいなければ点検しない', Number(await q1(`select public.co3_checks_run('${today}'::date - 5)`)) === 0, null);
check('期限切れ：飛べない（check）', (await q1(`select public.co3_ac_grounded(${acid}, '${today}')`)) === 'check', null);
await q1(`select public.co3_legs_check(${at('03:45')})`);
const x = (await db.query(`select status, cause from co3_leg_status where user_id = '${A}' and day = '${today}' and leg = 1`)).rows[0];
check('期限切れの機体の便は欠航（点検切れ・会社のせい）', x.status === 'cxl' && x.cause === 'check', x);
check('定時率に数える（会社のせい）', Number((await db.query(`select * from co3_ontime('${A}')`)).rows[0].own_cxl) === 1, null);
s = await as(A, `select public.co_state()`);
check('会社の状態：点検まで −1時間・頼んでいない', s.fleet[0].check_left_hours === -1 && s.fleet[0].check_req === false, s.fleet[0]);
s = await as(A, `select public.co3_request_check(${acid}, true)`);
c0 = await cash();
check('頼むとその夜に点検（費用は 0.2% × 1.3、おまかせより安い）', Number(await q1(`select public.co3_checks_run('${today}'::date - 5)`)) === 1
  && Math.abs(c0 - (await cash()) - Math.ceil(paid * 0.002 * 1.3)) <= 1 && (await acr()).check_req === false, { d: c0 - (await cash()) });
check('点検したら飛べる', (await q1(`select public.co3_ac_grounded(${acid}, '${today}')`)) === null, null);
// 点検の後30日は故障が半分
const r1 = Number(await q1(`select public.co3_breakdown_rate(${acid})`));
await db.exec(`update aircraft set checked_day = '${today}'::date - 40 where id = ${acid}`);
check('点検の後30日は故障が半分', near(r1 * 2, Number(await q1(`select public.co3_breakdown_rate(${acid})`)), 1e-9), { r1 });
await db.exec(`update companies set rating = 2 where user_id = '${A}'`);
check('格付け2：点検のやり方は変えられない', String(await as(A, `select public.co3_set_check_mode('auto')`)).includes('rating required 3'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
