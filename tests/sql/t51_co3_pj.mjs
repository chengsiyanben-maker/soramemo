// エアライン経営 co-v3：プライベートジェットの会社
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
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('HND','OKA')`)).rows.map((r) => [r.iata, r.id]));

// 本物の便：羽田⇄那覇 1日20便×170席（前の28日）→ 路線の客 1,190人、リゾートなので VIP の客 20% ＝ 238人
await db.exec(`insert into flight_history (svc_date, flight, dep, arr, std, sta, type)
  select (now() at time zone 'Asia/Tokyo')::date - d, 'JL' || (900 + i * 2 + s), case s when 0 then 'HND' else 'OKA' end, case s when 0 then 'OKA' else 'HND' end,
         now() - d * interval '1 day', now() - d * interval '1 day' + interval '160 minutes', 'B738'
    from generate_series(1, 28) d, generate_series(0, 9) i, generate_series(0, 1) s`);
await q1(`select public.co3_route_real_refresh()`);
// A は羽田⇄那覇を飛び、羽田で G650ER（JA500G）を見る
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values
    ('${A}', ${ids.HND}, ${ids.OKA}, now() - interval '3 day', now() - interval '3 day' + interval '160 minutes', 1560);
  insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values
    ('${A}', ${ids.HND}, 35.55, 139.78, 10, now() - interval '2 hours', now() - interval '2 hours');
  insert into flight_history (svc_date, flight, dep, arr, std, sta, type, reg) values
    (((now() - interval '2 hours') at time zone 'Asia/Tokyo')::date, 'JA500G', 'HND', 'OKA', now() - interval '110 minutes', now() + interval '50 minutes', 'GLF6', 'JA500G')`);
await as(A, `select public.co_state()`);
await db.exec(`update companies set cash = 1000000, satisfaction = 60 where user_id = '${A}'`);
let s = await as(A, `select public.co3_set_policy('pj')`);
check('方針をプライベートジェットにできる', s.policy === 'pj', s.policy);
const seen = await as(A, `select public.co3_seen_list()`);
check('見た G650ER はビジネスジェット（乗ったのと同じ扱い）', seen.some((x) => x.reg === 'JA500G' && x.code === 'GLF6' && x.kind === 'bizjet' && x.as_ridden), seen);
s = await as(A, `select public.co3_buy_seen('JA500G')`);
const ac = (await db.query(`select id from aircraft where reg = 'JA500G'`)).rows[0].id;
const hk = `${Math.min(ids.HND, ids.OKA)}-${Math.max(ids.HND, ids.OKA)}`;
s = await as(A, `select public.co_assign(${ac}, '${hk}')`);
const e = s.pj.find((x) => x.k === hk);
// 手計算：VIP の客 238人、G650ER 14席。1,560km は1日4便まで → 2便でも4便でも埋まり方は上限の90% → もうかる4便
//   運賃 0.25 ＋ 1,560 × 0.0003 ＝ 0.718。収益 ＝ 4便 × 14席 × 25 × 0.9 × 0.718 × はじめの上乗せ 1.5
//   費用 ＝ 4便 × 14 × 25 × 0.45 × 0.718。着陸料 ＝ 4便 ×（14 × 0.9 人 × 0.027 ＋ ジェット 0.6）
const fare = 0.25 + 1560 * 0.0003;
const rev = 4 * 14 * 25 * 0.9 * fare * 1.5, cost = 4 * 14 * 25 * 0.45 * fare, land = 4 * (14 * 0.9 * 0.027 + 0.6);
check('リゾート：VIP の客 238人・4便・埋まり方 90%（上限）', e && near(Number(e.vip), 238, 0.1) && e.kind === 'resort' && e.flights === 4 && Number(e.fill) === 0.9, e);
check('収益（VIP 席1席 ＝ 25席分）', near(Number(e.revenue), rev, 0.05), { got: e.revenue, want: rev });
check('費用（埋まり方45%で赤字）', near(Number(e.cost), cost, 0.05), { got: e.cost, want: cost });
check('着陸料', near(Number(e.landing), land, 0.02), { got: e.landing, want: land });
check('1日の収益 ＝ 手計算のもうけ', Number(s.gross) === Math.round(rev - cost - land), { got: s.gross, want: Math.round(rev - cost - land) });
check('ビジネスジェットは旅客の路線では飛ばない', s.econ.every((x) => x.flights === 0), s.econ);

// VIP の客が少ないと、いちばんもうかる便数を選ぶ：客を 1/10 にすると（23.8人）、2便で 85% → 2便がもうかる
await db.exec(`update co3_route_real set flights = 2 where a = 'HND' and b = 'OKA'`);
s = await as(A, `select public.co_state()`);
const e2 = s.pj.find((x) => x.k === hk);
check('VIP の客 23.8人：2便（埋まり方 85%）を選ぶ', e2.flights === 2 && near(Number(e2.fill), 23.8 / 28, 0.001), e2);
s = await as(A, `select public.co3_set_flights('${hk}', 4)`);
const e3 = s.pj.find((x) => x.k === hk);
// はじめの上乗せ 1.5倍があるので赤字にはならないが、2便よりもうけは減る
check('便数を4便に決めると4便（埋まり方 42.5%）で、2便よりもうけが減る', e3.flights === 4 && near(Number(e3.fill), 0.425, 0.001) && Number(e3.profit) < Number(e2.profit), { e2: e2.profit, e3: e3.profit });

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('すべて OK');
