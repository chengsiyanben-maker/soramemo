// エアライン経営 co-v3：満足度（始まり40・目標値・毎日の動き・お客さんの倍率）
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
await db.exec(`update ops.flags set value = 'true' where key in ('game_released', 'co_v3')`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const A = '00000000-0000-0000-0000-00000000000a';
await db.exec(`insert into auth.users (id) values ('${A}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const n = async (sql) => Number(await q1(sql));
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('HND','CTS')`)).rows.map((r) => [r.iata, r.id]));

let s = await as(A, `select public.co_state()`);
check('満足度の始まりは40', Number(s.satisfaction) === 40, s.satisfaction);
check('目標値：FSC・機体なし・機内食なしは 50 − 5 − 8 ＝ 37', Number(s.sat_parts.target) === 37 && Number(s.sat_parts.meal) === -8, s.sat_parts);
check('満足度40のお客さんの倍率は −4%', near(Number(s.sat_mult), 0.96, 1e-9), s.sat_mult);
const m = await q1(`select string_agg(co3.satisfaction_mult(x)::text, ',') from unnest(array[40, 59, 60, 64, 65, 100, 0]::numeric[]) x`);
check('倍率：40 −4%・59 0・60 0・64 0・65 +1%・100 +8%（上限）・0 −8%（上限）', m === '0.96,1.00,1.00,1.00,1.01,1.08,0.92', m);
check('1日の動き：(目標 − 今) × 0.1、±3まで', await n(`select co3.satisfaction_step(40, 45)`) === 40.5 && await n(`select co3.satisfaction_step(40, 100)`) === 43 && await n(`select co3.satisfaction_step(90, 0)`) === 87, null);

// 毎日の処理：同じ日に2回動かしても1回分
await q1(`select public.co3_satisfaction_refresh()`);
await q1(`select public.co3_satisfaction_refresh()`);
check('毎日の処理で 40 → 39.7（2回動かしても1回分）', await n(`select satisfaction from companies where user_id = '${A}'`) === 39.7, null);

// LCC：席を詰める −4・方針 +5・機内食なし −8 → 43
s = await as(A, `select public.co3_set_policy('lcc')`);
check('目標値：LCC は 50 − 4 ＋ 5 − 8 ＝ 43', Number(s.sat_parts.target) === 43 && Number(s.sat_parts.packed) === -4, s.sat_parts);
// 新しい機体の割合 ×6（会社に入れて90日まで）と、古さ（ac_age 0.8 で −8）
await db.exec(`insert into aircraft (user_id, type, paid, bought_at) values ('${A}', 'nb', 1000, now()), ('${A}', 'nb', 1000, now() - interval '400 days')`);
s = await as(A, `select public.co_state()`);
// 1機は新しい（割合 0.5 × 6 ＝ +3）、古さの平均 (1 + 0.8) / 2 ＝ 0.9 → −8 × 0.1 / 0.2 ＝ −4
check('新しい機体の半分で +3、古さの平均 0.9 で −4 → 目標値 42', Number(s.sat_parts.new_share) === 3 && Number(s.sat_parts.aging) === -4 && Number(s.sat_parts.target) === 42, s.sat_parts);

// お客さんに倍率が効く：羽田⇄新千歳（本物の便 1日20便×170席）に機体を入れる
await db.exec(`insert into flight_history (svc_date, flight, dep, arr, std, sta, type)
  select (now() at time zone 'Asia/Tokyo')::date - d, 'JL' || (500 + i * 2 + s), case s when 0 then 'HND' else 'CTS' end, case s when 0 then 'CTS' else 'HND' end,
         now() - d * interval '1 day', now() - d * interval '1 day' + interval '90 minutes', 'B738'
    from generate_series(1, 28) d, generate_series(0, 9) i, generate_series(0, 1) s;
  insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values
    ('${A}', ${ids.HND}, ${ids.CTS}, now() - interval '1 day', now() - interval '1 day' + interval '90 minutes', 819.6)`);
await q1(`select public.co3_route_real_refresh()`);
const hc = `${Math.min(ids.HND, ids.CTS)}-${Math.max(ids.HND, ids.CTS)}`;
await db.exec(`update aircraft set route_key = '${hc}' where user_id = '${A}' and bought_at > now() - interval '1 day'`);
const pax = 1190 * (0.6 * 0.4 + 0.4 * 1.7);   // LCC
await db.exec(`update companies set satisfaction = 60 where user_id = '${A}'`);
let e = (await as(A, `select public.co_state()`)).econ.find((x) => x.k === hc);
check('満足度60：倍率なし', near(Number(e.own), pax, 0.1), e);
await db.exec(`update companies set satisfaction = 80 where user_id = '${A}'`);
e = (await as(A, `select public.co_state()`)).econ.find((x) => x.k === hc);
check('満足度80：お客さん +4%', near(Number(e.own), pax * 1.04, 0.1), e);
await db.exec(`update companies set satisfaction = 40 where user_id = '${A}'`);
e = (await as(A, `select public.co_state()`)).econ.find((x) => x.k === hc);
check('満足度40：お客さん −4%', near(Number(e.own), pax * 0.96, 0.1), e);
check('満足度はアプリから書き換えられない', String(await as(A, `update companies set satisfaction = 100`)).startsWith('ERROR') || await n(`select satisfaction from companies where user_id = '${A}'`) === 40, null);

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('すべて OK');
