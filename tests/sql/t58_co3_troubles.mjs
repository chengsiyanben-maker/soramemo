// エアライン経営 co-v3：トラブルの対応と神対応（1日まとめ：前の日の本物の欠航から、毎朝7時）
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
const fl = e.flights, rev = Number(e.revenue);
const today = await q1(`select ((now() at time zone 'Asia/Tokyo')::date)::text`);
const sky = async (back, n, cxl) => db.exec(`insert into co_sky (route_key, day, n, cxl, avg4, mult) values ('${hc}', '${today}'::date - ${back}, ${n}, ${cxl}, null, 1)
  on conflict (route_key, day) do update set n = excluded.n, cxl = excluded.cxl`);
const sat = async () => Number(await q1(`select satisfaction from companies where user_id = '${A}'`));
const cash = async () => Number(await q1(`select cash from companies where user_id = '${A}'`));
// 前の日：本物 18便が飛んで 2便が欠航（1割）→ 自社 6便 × 0.1 ＝ 0.6 → 1便が欠航
await sky(1, 18, 2);
check('スイッチがオフなら決めない', (await db.exec(`update ops.flags set value = 'false' where key = 'co_v3'`), Number(await q1(`select public.co3_trouble_detect()`))) === 0, null);
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
check('毎朝：トラブルが1件', Number(await q1(`select public.co3_trouble_detect()`)) === 1, null);
check('同じ日に2回動かしても1件', Number(await q1(`select public.co3_trouble_detect()`)) === 0, null);
s = await as(A, `select public.co_state()`);
let t1 = s.troubles[0];
check('欠航 1便・1便あたりの収益・6時間と1時間', fl === 6 && t1.cancelled === 1 && t1.flights === 6 && near(Number(t1.rev_flight), rev / 6, 0.01)
  && (Date.parse(t1.deadline) - Date.parse(t1.created_at)) === 6 * 3600e3 && (Date.parse(t1.god_until) - Date.parse(t1.created_at)) === 3600e3 && t1.result === null, t1);
// はじめの1時間に振替の手配 → 神対応：満足度 +8・費用 その便の収益の20%・評判 +15・目標値 +3
const sat0 = await sat(), cash0 = await cash(), rep0 = Number(await q1(`select public.co_rep_points('${A}')`));
s = await as(A, `select public.co3_trouble_respond(${t1.id}, 'transfer')`);
t1 = s.troubles[0];
check('神対応', t1.result === 'god' && t1.card === 'transfer', t1);
check('神対応：満足度その日 +8', near(await sat(), sat0 + 8, 0.001), { before: sat0, after: await sat() });
check('神対応：費用は その便の収益 × 20%（切り上げ。維持費の精算 ±2）', Math.abs(cash0 - Number(s.cash) - Math.ceil(0.2 * Number(t1.rev_flight))) <= 2, { cash0, cash: s.cash, want: Math.ceil(0.2 * Number(t1.rev_flight)) });
check('神対応：評判 +15', Number(await q1(`select public.co_rep_points('${A}')`)) - rep0 === 15, null);
check('神対応：目標値の「対応」 +3', Number(s.sat_parts.response) === 3, s.sat_parts);
check('もう対応したトラブルには使えない', String(await as(A, `select public.co3_trouble_respond(${t1.id}, 'hotel')`)).includes('already done'), null);
// 2日前：1時間を過ぎてからの対応、合わないカード → ふつうの対応
await sky(2, 10, 5);
check('2日前のトラブル（1日前の朝に決まった形）', Number(await q1(`select public.co3_trouble_detect(now() - interval '1 day')`)) === 1, null);
let id2 = Number(await q1(`select id from co3_troubles where user_id = '${A}' and day = '${today}'::date - 2`));
const g2 = await q1(`select (god_until + interval '1 minute')::text from co3_troubles where id = ${id2}`);
check('1時間を過ぎたら振替の手配でも「ふつう」', (await q1(`select public.co3_trouble_do('${A}', ${id2}, 'transfer', false, '${g2}')`)) === 'normal', null);
check('ふつうの対応で満足度は変わらない（前の +8 のまま）', near(await sat(), sat0 + 8, 0.001), null);
// 3日前：1時間以内でも合わないカード（軽食）→ ふつう
await sky(3, 10, 5);
await q1(`select public.co3_trouble_detect(now() - interval '2 days')`);
let id3 = Number(await q1(`select id from co3_troubles where user_id = '${A}' and day = '${today}'::date - 3`));
check('合わないカード（軽食とおわび）は1時間以内でも「ふつう」・欠航 6便 × 1/3 ＝ 2便',
  (await q1(`select public.co3_trouble_do('${A}', ${id3}, 'snack', false, (select created_at from co3_troubles where id = ${id3}))`)) === 'normal'
  && Number(await q1(`select cancelled from co3_troubles where id = ${id3}`)) === 2, null);

// 4日前：対応しないまま締め切り → 対応なし：満足度 −2・評判 −5・目標値 −2
await sky(4, 10, 5);
await q1(`select public.co3_trouble_detect(now() - interval '3 days')`);
const id4 = Number(await q1(`select id from co3_troubles where user_id = '${A}' and day = '${today}'::date - 4`));
let tl = 'ok'; try { await db.query(`select public.co3_trouble_do('${A}', ${id4}, 'transfer', false, (select deadline + interval '1 minute' from co3_troubles where id = ${id4}))`); } catch (err) { tl = err.message; }
check('6時間を過ぎたら対応できない', String(tl).includes('too late'), tl);
const sat1 = await sat(), rep1 = Number(await q1(`select public.co_rep_points('${A}')`));
check('毎時：締め切りを過ぎたものは「対応なし」', Number(await q1(`select public.co3_trouble_expire()`)) === 1 && (await q1(`select result from co3_troubles where day = '${today}'::date - 4`)) === 'none', null);
check('対応なし：満足度 −2・評判 −5', near(await sat(), sat1 - 2, 0.001) && Number(await q1(`select public.co_rep_points('${A}')`)) - rep1 === -5, null);
s = await as(A, `select public.co_state()`);
check('目標値の「対応」：神対応1回 +3、対応なし1回 −2 → +1', Number(s.sat_parts.response) === 1, s.sat_parts);
// 自動で対応する：決まったときに振替の手配でふつうの対応（神対応にはならない）
s = await as(A, `select public.co3_set_auto_trouble(true)`);
check('自動で対応する：オン', s.auto_trouble === true, null);
await sky(5, 10, 5);
await q1(`select public.co3_trouble_detect(now() - interval '4 days')`);
const t5 = (await db.query(`select result, card, auto from co3_troubles where day = '${today}'::date - 5`)).rows[0];
check('自動：振替の手配でふつうの対応', t5.result === 'normal' && t5.card === 'transfer' && t5.auto === true, t5);
// 本物の欠航が少なく、四捨五入で0便ならトラブルにしない
await sky(6, 100, 1);
check('本物の欠航 1% → 6便 × 0.01 ＝ 0.06 → トラブルなし', Number(await q1(`select public.co3_trouble_detect(now() - interval '5 days')`)) === 0, null);
// 表：自分の分だけ読める・直接は書けない
check('トラブルの表：自分の分だけ読める', Number(await as(B, `select count(*) from co3_troubles`)) === 0 && Number(await as(A, `select count(*) from co3_troubles`)) === 5, null);
check('トラブルの表：直接は書けない', String(await as(A, `update co3_troubles set result = 'god'`)).startsWith('ERROR'), null);
check('ほかの人のトラブルには対応できない', String(await as(B, `select public.co3_trouble_respond(${id2}, 'transfer')`)).startsWith('ERROR'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
