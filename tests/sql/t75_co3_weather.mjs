// エアライン経営 co-v3：天気の備え（気象通報の読み方・防除氷・横風の訓練・CAT III・雷）と台風の計画欠航
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
import { wxFlags } from '../../supabase/functions/_shared/co3_wx.js';
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
if (fs.existsSync(dir + '20261028000103_co3_cabin_fare.sql')) s = await as(A, `select public.co3_set_premium(0)`);
const v2gross = Number(s.gross);
check('スイッチがオフ：co-v2 の収益のまま・econ なし', s.v3 === false && s.econ === null && v2gross > 0, { v3: s.v3, g: v2gross });

// スイッチをオンにする
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
s = await as(A, `select public.co_state()`);
const e = s.econ.find((x) => x.k === hc);
// 気象通報の読み方
const W = (raw, o = {}) => wxFlags({ raw, wspd: 5, wgst: null, vis_m: 9999, ...o });
check('雪：-SN・SHSN・-RASN・FZRA', W('RJCC 280000Z 34012KT 3000 -SN BKN010 M03/M05 Q1002').snow && W('RJCC 280000Z 34012KT 3000 SHSN FEW010').snow && W('RJSS 280000Z 3000 -RASN BKN010').snow && W('RJCC 280000Z 3000 FZRA OVC005').snow, null);
check('雪でないもの：RA・備考の SN', !W('RJTT 280000Z 4000 RA BKN010').snow && !W('RJTT 280000Z 9999 FEW030 RMK 1SN').snow, null);
check('強風：平均25ノット・瞬間35ノット', W('x', { wspd: 25 }).wind && W('x', { wspd: 18, wgst: 35 }).wind && !W('x', { wspd: 20, wgst: 30 }).wind, null);
check('霧：視程 800m 未満・FG・BCFG', W('RJAA 0400 FG', { vis_m: 400 }).fog && W('RJAA 1500 BCFG FEW001', { vis_m: 1500 }).fog && !W('RJAA 3000 BR', { vis_m: 3000 }).fog, null);
check('雷：TS・TSRA・VCTS', W('RJTT 6000 TSRA FEW020CB').ts && W('RJTT 9999 VCTS').ts && !W('RJTT 9999 FEW020').ts, null);
// 天気の備え（欠航の確率の倍率）
const acid = s.fleet[0].id, at = `'2026-12-01 10:30+09'`;
const mult = async () => Number(await q1(`select public.co3_wx_cxl_mult('${A}', 'HND', 'CTS', ${acid}, ${at})`));
const dmul = async () => Number(await q1(`select public.co3_wx_delay_mult('${A}', 'HND', 'CTS', ${at})`));
check('天気の記録がなければ1', (await mult()) === 1 && (await dmul()) === 1, null);
await db.exec(`insert into co3_wx (iata, at, snow) values ('CTS', '2026-12-01 10:00+09', true)`);
check('新千歳が雪：備えなしなら1', (await mult()) === 1, null);
check('アプリから天気の記録は読めない', String(await as(A, `select count(*) from co3_wx`)).startsWith('ERROR'), null);
let c0 = Number(await q1(`select cash from companies where user_id = '${A}'`));
s = await as(A, `select public.co3_build_prep('deice', 'CTS')`);
check('新千歳を訪れていないと建てられない', String(s).includes('not visited'), null);
await db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${A}', ${ids.CTS}, 42.77, 141.69, 10, now())`);
s = await as(A, `select public.co3_build_prep('deice', 'CTS')`);
check('防除氷1段（5,000）：雪の欠航 −30%・遅れは半分', c0 - Number(await q1(`select cash from companies where user_id = '${A}'`)) === 5000 && near(await mult(), 0.7, 1e-9) && (await dmul()) === 0.5, s.wx);
await as(A, `select public.co3_build_prep('deice', 'CTS')`); await as(A, `select public.co3_build_prep('deice', 'CTS')`);
check('3段で −70%・4段目はない', near(await mult(), 0.3, 1e-9) && String(await as(A, `select public.co3_build_prep('deice', 'CTS')`)).includes('prep max'), null);
await db.exec(`update co3_wx set snow = false, wind = true`);
check('強風：訓練なしは1', (await mult()) === 1, null);
s = await as(A, `select public.co3_set_wind_training('high')`);
check('横風の訓練・手厚い：−40%・毎日 機体1機あたり3', near(await mult(), 0.6, 1e-9) && Number(await q1(`select public.co3_wx_cost('${A}')`)) === 3, null);
const upA = Number(s.upkeep); s = await as(A, `select public.co3_set_wind_training('none')`);
check('訓練の費用は維持費に入る', upA - Number(s.upkeep) === 3, { upA, u: s.upkeep });
await db.exec(`update co3_wx set wind = false, fog = true`);
check('CAT III の空港（国の資料の8空港）', Number(await q1(`select count(*) from co3_cat3_airports`)) === 8, null);
await db.exec(`delete from co3_cat3_airports where iata = 'CTS'`);
s = await as(A, `select public.co3_set_cat3(${acid})`);
check('霧：CAT III の空港でなければ効かない', (await mult()) === 1 && s.fleet[0].cat3 === true, null);
await db.exec(`insert into co3_cat3_airports (iata) values ('CTS')`);
check('CAT III の空港で、付けた機体は霧の欠航 −80%', near(await mult(), 0.2, 1e-9), null);
await db.exec(`update co3_wx set fog = false, ts = true`);
check('雷：備えなしなら遅れはそのまま', (await dmul()) === 1, null);
await as(A, `select public.co3_build_prep('thunder', 'CTS')`);
check('雷の作業の備え：遅れが半分', (await dmul()) === 0.5, null);
// 台風
await db.exec(`set co3.season_day = '2026-09-10'`);
s = await as(A, `select public.co_state()`);
const r0 = Number(s.econ.find((x) => x.k === hc).revenue);
check('予報がなければ決められない', String(await as(A, `select public.co3_typhoon_decide('${hc}', true)`)).includes('no typhoon'), null);
await db.exec(`insert into co3_typhoon_fcst (iata, day) values ('CTS', '2026-09-11')`);
s = await as(A, `select public.co_state()`);
check('会社の状態：明日の台風の路線', s.wx.typhoon.length === 1 && s.wx.typhoon[0].k === hc && s.wx.typhoon[0].cancel === null, s.wx.typhoon);
s = await as(A, `select public.co3_typhoon_decide('${hc}', true)`);
check('計画欠航を決める', s.wx.typhoon[0].cancel === true, s.wx.typhoon);
await db.exec(`set co3.season_day = '2026-09-11'`);
const rep0 = Number(await q1(`select public.co_rep_points('${A}')`));
s = await as(A, `select public.co_state()`);
check('計画欠航した日：便を出さない・収益0', Number(s.econ.find((x) => x.k === hc).revenue) === 0 && s.econ.find((x) => x.k === hc).flights === 0, null);
// 飛ばして、台風が来た（本物の便の半分以上が欠航）
await db.exec(`update co3_typhoon_plan set cancel = false;
  insert into flight_schedule (svc_date, flight, dep, arr, std, sta, source, dep_status) select '2026-09-11', 'JL9' || g, 'CTS', 'HND', '2026-09-11 10:00+09', '2026-09-11 11:30+09', 'test', case when g <= 6 then 'Cancelled' end from generate_series(1, 10) g`);
s = await as(A, `select public.co_state()`);
check('飛ばして台風が来た：収益0・評判 −10', Number(s.econ.find((x) => x.k === hc).revenue) === 0 && Number(await q1(`select public.co_rep_points('${A}')`)) === rep0 - 10, null);
await db.exec(`set co3.season_day = '2026-09-12'`);
check('次の日は足止めで半分', near(Number((await as(A, `select public.co_state()`)).econ.find((x) => x.k === hc).revenue), r0 * 0.5, 0.05), null);
await as(A, `select public.co3_build_prep('typhoon', 'CTS')`);
check('避難の備え1段では大型機は足止めのまま・2段で戻る', near(Number((await as(A, `select public.co_state()`)).econ.find((x) => x.k === hc).revenue), r0 * 0.5, 0.05)
  && (await as(A, `select public.co3_build_prep('typhoon', 'CTS')`), near(Number((await as(A, `select public.co_state()`)).econ.find((x) => x.k === hc).revenue), r0, 0.05)), null);
// それた
await db.exec(`update flight_schedule set dep_status = null where svc_date = '2026-09-11'; set co3.season_day = '2026-09-11'`);
check('飛ばして台風がそれた：収益 +30%', near(Number((await as(A, `select public.co_state()`)).econ.find((x) => x.k === hc).revenue), r0 * 1.3, 0.05), null);
check('備えはほかの会社に見えない', Number(await as(B, `select count(*) from co3_wx_prep`)) === 0 && Number(await as(B, `select count(*) from co3_typhoon_plan`)) === 0, null);
check('予報はアプリから書けない', String(await as(A, `insert into co3_typhoon_fcst (iata, day) values ('HND', '2026-09-20')`)).startsWith('ERROR') && String(await as(A, `select public.admin_co3_typhoon('HND', '2026-09-20')`)).includes('admin only'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
