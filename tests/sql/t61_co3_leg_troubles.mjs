// エアライン経営 co-v3：便ごとのトラブル（出発の3時間前に、本物の便の欠航・遅れから。遅れの続き方・夜・カード・お金）
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
const L = s.legs[hc], rev = Number(e.revenue) / e.flights;
const today = await q1(`select ((now() at time zone 'Asia/Tokyo')::date)::text`);
const at = (hm) => `('${today}'::date + time '${hm}') at time zone 'Asia/Tokyo'`;
// 本物の便（その日の運航情報）：便の定刻 ± 何分、状態、変更後の出発の遅れ（分）
let fno = 100;
const real = async (leg, off, cancel, late) => db.exec(`insert into flight_schedule (svc_date, flight, dep, arr, std, sta, source, dep_status, etd) values
  ('${today}', 'JL${fno++}', '${L[leg].f}', '${L[leg].to}', ${at('00:00')} + interval '${L[leg].t + off} minutes', ${at('00:00')} + interval '${L[leg].t + off + 90} minutes', 'test',
   ${cancel ? `'Cancelled'` : 'null'}, ${late == null ? 'null' : `${at('00:00')} + interval '${L[leg].t + off + late} minutes'`})`);
await real(0, -20, true, null); await real(0, 30, true, null);           // 6:30 の便：近くの2便とも欠航
await real(1, 10, false, 70);                                              // 9:30 の便：70分遅れ
await real(2, -60, false, 0);                                              // 12:30 の便：本物は定時（前の便から遅れが続く）
await real(4, 0, false, 150);                                              // 18:30 の便：150分遅れ
await real(5, 5, true, null);                                              // 21:30 の便：欠航
const lst = async (leg) => (await db.query(`select * from co3_leg_status where user_id = '${A}' and day = '${today}' and leg = ${leg}`)).rows[0];
const trb = async (leg) => (await db.query(`select * from co3_troubles where user_id = '${A}' and day = '${today}' and leg = ${leg}`)).rows[0];
check('スイッチがオフなら決めない', (await db.exec(`update ops.flags set value = 'false' where key = 'co_v3'`), Number(await q1(`select public.co3_legs_check(${at('03:45')})`))) === 0, null);
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
const cash0 = Number(await q1(`select cash from companies where user_id = '${A}'`));
check('3:45：出発の3時間前になった 6:30 の便だけ決める', Number(await q1(`select public.co3_legs_check(${at('03:45')})`)) === 1, null);
check('同じ時刻にもう一度動かしても決めない', Number(await q1(`select public.co3_legs_check(${at('03:45')})`)) === 0, null);
let x = await lst(1);
check('6:30：近くの本物の便が2便とも欠航 → 欠航', x.status === 'cxl' && x.real_n === 2 && x.real_cxl === 2, x);
check('欠航は収益0：その便の収益を引く', Math.abs(cash0 - Number(await q1(`select cash from companies where user_id = '${A}'`)) - Math.ceil(rev)) <= 2 && near(Number(x.loss), rev, 0.02), { loss: x.loss, rev });
let tr = await trb(1);
check('夜（3:45）に決まったものは朝7時から：神対応は8時まで、対応は13時まで', tr.kind === 'cxl'
  && new Date(tr.created_at).getTime() === new Date((await q1(`select (${at('07:00')})::text`))).getTime()
  && (new Date(tr.god_until) - new Date(tr.created_at)) === 3600e3 && (new Date(tr.deadline) - new Date(tr.created_at)) === 6 * 3600e3, tr);
s = await as(A, `select public.co_state()`);
let t1 = s.troubles.find((y) => y.leg === 1);
check('6:30 の欠航：合うのは振替の手配だけ（19時より前）', JSON.stringify(t1.fits) === '["transfer"]' && t1.dep === L[0].f, t1);
// 9:30 の便（6:45 に決まる）：70分遅れ → 遅れ・−10%・対応してください（軽食は2時間以上なので合わない）
check('6:45：9:30 の便', Number(await q1(`select public.co3_legs_check(${at('06:45')})`)) === 1, null);
x = await lst(2);
check('9:30：本物の遅れ 70分 → 遅れ・その便の収益の10%を引く', x.status === 'delay' && x.delay_min === 70 && near(Number(x.loss), rev * 0.1, 0.02), x);
tr = await trb(2);
s = await as(A, `select public.co_state()`);
check('1時間以上の遅れは対応してください（合うカードはない）', tr && tr.kind === 'delay' && tr.delay_min === 70 && JSON.stringify(s.troubles.find((y) => y.leg === 2).fits) === '[]', tr);
// 12:30 の便：本物は定時だが、前の便の遅れ 70分 − 折り返しの余裕（180 − 100 − 40 ＝ 40分）＝ 30分が続く
await q1(`select public.co3_legs_check(${at('09:45')})`);
x = await lst(3);
check('12:30：前の便から30分続く → 遅れ（1時間より短いので対応はいらない）', x.status === 'delay' && x.delay_min === 30 && x.carried === 30 && !(await trb(3)), x);
// 15:30 の便：本物の便が近くにない、前の便の遅れ 30 − 40 → 0 → 定時
await q1(`select public.co3_legs_check(${at('12:45')})`);
x = await lst(4);
check('15:30：近くに本物の便がない・遅れは吸収された → 定時', x.status === 'ok' && x.delay_min === 0 && x.real_n === 0 && Number(x.loss) === 0, x);
// 18:30：150分遅れ → 軽食とおわびが合う。21:30：欠航 → 振替とホテルが合う
await q1(`select public.co3_legs_check(${at('15:45')})`); await q1(`select public.co3_legs_check(${at('18:45')})`);
s = await as(A, `select public.co_state()`);
check('18:30 の150分遅れ：軽食とおわびが合う', JSON.stringify(s.troubles.find((y) => y.leg === 5).fits) === '["snack"]', s.troubles.find((y) => y.leg === 5));
check('21:30 の欠航：振替の手配とホテルの手配が合う', JSON.stringify(s.troubles.find((y) => y.leg === 6).fits) === '["transfer","hotel"]', s.troubles.find((y) => y.leg === 6));
// 対応：6:30 の欠航に7時台に振替 → 神対応。18:30 の遅れに軽食 → 神対応。9:30 の遅れに振替 → ふつう
const id = async (leg) => Number((await trb(leg)).id);
check('6:30 の欠航に 7:10 の振替の手配 → 神対応', (await q1(`select public.co3_trouble_do('${A}', ${await id(1)}, 'transfer', false, ${at('07:10')})`)) === 'god', null);
check('18:30 の150分遅れに 15:50 の軽食とおわび → 神対応', (await q1(`select public.co3_trouble_do('${A}', ${await id(5)}, 'snack', false, ${at('15:50')})`)) === 'god', null);
check('9:30 の70分遅れに振替の手配 → ふつう（合わない）', (await q1(`select public.co3_trouble_do('${A}', ${await id(2)}, 'transfer', false, ${at('07:05')})`)) === 'normal', null);
check('21:30 の欠航にホテルの手配 → 神対応', (await q1(`select public.co3_trouble_do('${A}', ${await id(6)}, 'hotel', false, ${at('18:50')})`)) === 'god', null);
// 実際の空：本物の便と照らして決めた日の路線は、欠航の分を倍率から除く
await db.exec(`insert into co_sky (route_key, day, n, cxl, avg4, mult) values ('${hc}', '${today}'::date - 1, 18, 2, 18, 0.9) on conflict (route_key, day) do update set n = 18, cxl = 2, avg4 = 18, mult = 0.9`);
check('照らしていない日は除かない', Number(await q1(`select public.co3_sky_cxl_back('${A}', '${hc}')`)) === 0, null);
await db.exec(`insert into co3_leg_status (user_id, day, route_key, leg, dep, arr, dep_at, status, real_n) values ('${A}', '${today}'::date - 1, '${hc}', 1, 'HND', 'CTS', now() - interval '1 day', 'ok', 2)`);
check('照らした日は欠航の分（2 ÷ 20 ＝ 10%）を戻す', Number(await q1(`select public.co3_sky_cxl_back('${A}', '${hc}')`)) === 0.1, null);
// 表：自分の分だけ読める・直接は書けない
check('便ごとの結果の表：自分の分だけ読める・直接は書けない', Number(await as(B, `select count(*) from co3_leg_status`)) === 0 && Number(await as(A, `select count(*) from co3_leg_status`)) === 7
  && String(await as(A, `update co3_leg_status set status = 'ok'`)).startsWith('ERROR'), null);
// 朝のまとめ（次の日に見ると前の日の遅れ・欠航の数）
s = await as(A, `select public.co_state()`);
check('朝のまとめ：前の日に決めた便 1便', Number(s.morning.legs_done) === 1, s.morning);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
