// エアライン経営 co-v3：自分で組むスケジュール（つながり・折り返し・運用時間・便数・客・トラブル）
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
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('HND','CTS','GAJ','HIJ','FUK')`)).rows.map((r) => [r.iata, r.id]));
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
const hf = `${Math.min(ids.HND, ids.FUK)}-${Math.max(ids.HND, ids.FUK)}`;
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values ('${A}', ${ids.HND}, ${ids.FUK}, now() - interval '3 days', now() - interval '3 days' + interval '2 hours', 880)`);
const nb = Number(await q1(`insert into aircraft (user_id, type, paid, reg, icao) values ('${A}', 'nb', 1000, 'JA73AB', 'B738') returning id`));
const set = (legs) => as(A, `select public.co3_set_schedule(${nb}, '${JSON.stringify(legs)}'::jsonb)`);
const km = async (a, b) => Number(await q1(`select km from co_routes('${A}') where (a, b) in (('${a}', '${b}'), ('${b}', '${a}'))`));
const blkC = Math.round((await km('HND', 'CTS')) / 820 * 60) + 20, blkF = Math.round((await km('HND', 'FUK')) / 820 * 60) + 20;
const L4 = [{ dep: 'HND', arr: 'CTS', t: 420 }, { dep: 'CTS', arr: 'HND', t: 420 + blkC + 35 }, { dep: 'HND', arr: 'FUK', t: 420 + 2 * (blkC + 35) }, { dep: 'FUK', arr: 'HND', t: 420 + 2 * (blkC + 35) + blkF + 35 }];
await db.exec(`update companies set rating = 1 where user_id = '${A}'`);
check('格付け1：自分で組めない', String(await set(L4)).includes('rating required 2'), null);
await db.exec(`update companies set rating = 2 where user_id = '${A}'`);
check('つながっていない', String(await set([L4[0], L4[2]])).includes('not connected'), null);
check('折り返しが短い（B737 は35分）', String(await set([L4[0], { ...L4[1], t: L4[1].t - 1 }])).includes('turn too short'), null);
check('運用時間の外（ほかの空港は8時から）', String(await set([{ dep: 'CTS', arr: 'HND', t: 450 }, { dep: 'HND', arr: 'CTS', t: 700 }])).includes('outside hours'), null);
check('1日の最後は最初の空港へ', String(await set([L4[0]])).includes('must end at HND'), null);
check('自社の路線でない区間は入れられない', String(await set([{ dep: 'HND', arr: 'OKA', t: 600 }])).includes('route not found'), null);
s = await set(L4);
check('4便を組む：飛ぶ時間 ＝ 距離÷820＋20分', !String(s).startsWith('ERROR') && s.scheds[nb].length === 4 && s.scheds[nb][0].ta === 420 + blkC, String(s).slice(0, 200));
const e1 = s.econ.find((x) => x.k === hc), e2 = s.econ.find((x) => x.k === hf);
check('羽田⇄新千歳：おまかせ 6便 ＋ 自分で組んだ 2便 ＝ 8便', e1.flights === 8, e1);
check('羽田⇄福岡：自分で組んだ 2便だけで飛ぶ・収益がある', e2.flights === 2 && Number(e2.revenue) > 0 && Number(e2.carried) > 0, e2);
const LC = s.legs[hc], LF = s.legs[hf];
check('便ごと：羽田⇄新千歳 8便（2便は JA73AB）・客の合計 ＝ 運んだ客', LC.length === 8 && LC.filter((x) => x.ac === nb).length === 2
  && near(LC.reduce((a, x) => a + Number(x.biz) + Number(x.lei), 0), Number(e1.carried), 0.5), LC.map((x) => [x.t, x.ac]));
check('便ごと：自分で組んだ便の時刻のまま・出発順に番号', LF.length === 2 && LF[0].t === L4[2].t && LF[1].t === L4[3].t && LC.every((x, i) => i === 0 || x.t >= LC[i - 1].t), LF);
check('JA73AB は路線から外れる（おまかせでない）', (await q1(`select route_key from aircraft where id = ${nb}`)) === null, null);
// 遅れは同じ機体の前の便から続く
const today = await q1(`select ((now() at time zone 'Asia/Tokyo')::date)::text`);
const at = (hm) => `('${today}'::date + time '${hm}') at time zone 'Asia/Tokyo'`;
await db.exec(`insert into flight_schedule (svc_date, flight, dep, arr, std, sta, source, etd) values ('${today}', 'JL900', 'HND', 'CTS', ${at('07:05')}, ${at('08:35')}, 'test', ${at('08:15')})`);
await q1(`select public.co3_legs_check(${at('04:05')})`); await q1(`select public.co3_legs_check(${at('06:00')})`);
const r = (await db.query(`select dep_at, status, delay_min, carried, aircraft_id from co3_leg_status where user_id = '${A}' and aircraft_id = ${nb} order by dep_at`)).rows;
check('JA73AB 7:00 の便：本物の遅れ 70分', r[0] && r[0].status === 'delay' && r[0].delay_min === 70, r);
check('JA73AB の次の便（折り返し35分ぎりぎり）に遅れが続く', r[1] && r[1].carried > 0 && r[1].delay_min === r[1].carried, r);
// おまかせに戻す
s = await as(A, `select public.co3_clear_schedule(${nb})`);
check('おまかせに戻すと、組んだ便は消える', !s.scheds[nb] && !(s.econ.find((x) => x.k === hf) || {}).flights, s.scheds);
check('スケジュールの表：自分の分だけ読める・直接は書けない', Number(await as(B, `select count(*) from co3_sched`)) === 0
  && String(await as(A, `insert into co3_sched (user_id, aircraft_id, seq, route_key, dep, arr, dep_min, arr_min) values ('${A}', ${nb}, 1, '${hc}', 'HND', 'CTS', 400, 500)`)).startsWith('ERROR'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
