// エアライン経営 co-v3：上級席と、運賃での取り合い
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`update ops.flags set value = 'true' where key in ('game_released', 'co_v3')`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id) values ('${A}'), ('${B}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const n = async (sql) => Number(await q1(sql));
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('HND','CTS')`)).rows.map((r) => [r.iata, r.id]));

// 席の配置
check('A350（350席）FSC 上級席20%：上級席50・普通席200（1席3席分）', await q1(`select (co3.cabin(350, 'fsc', 20, true))::text`) === '(50,200)', await q1(`select (co3.cabin(350, 'fsc', 20, true))::text`));
check('B737（170席）ミドルコスト10%：上級席15・普通席140（1席2席分）', await q1(`select (co3.cabin(170, 'mcc', 10, false))::text`) === '(15,140)', await q1(`select (co3.cabin(170, 'mcc', 10, false))::text`));
check('LCC は詰めて 170 → 190.4席・上級席なし', await q1(`select (co3.cabin(170, 'lcc', 0, false))::text`) === '(0,190.40)', await q1(`select (co3.cabin(170, 'lcc', 0, false))::text`));
check('選べる割合：LCC は0%だけ・ミドルコストは10%まで・FSC は30%まで',
  (await q1(`select co3.premium_ok('lcc', 10)`)) === false && (await q1(`select co3.premium_ok('mcc', 20)`)) === false && (await q1(`select co3.premium_ok('fsc', 30)`)) === true, null);
check('上級席の運賃：小型 4.5倍・中型以上 5.6倍', await n(`select co3.premium_fare(false)`) === 4.5 && await n(`select co3.premium_fare(true)`) === 5.6, null);

// 羽田⇄新千歳：本物の便 1日20便×170席
await db.exec(`insert into flight_history (svc_date, flight, dep, arr, std, sta, type)
  select (now() at time zone 'Asia/Tokyo')::date - d, 'JL' || (500 + i * 2 + s), case s when 0 then 'HND' else 'CTS' end, case s when 0 then 'CTS' else 'HND' end,
         now() - d * interval '1 day', now() - d * interval '1 day' + interval '90 minutes', 'B738'
    from generate_series(1, 28) d, generate_series(0, 9) i, generate_series(0, 1) s`);
await q1(`select public.co3_route_real_refresh()`);
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no, airline) values
    ('${A}', ${ids.HND}, ${ids.CTS}, now() - interval '1 day', now() - interval '1 day' + interval '90 minutes', 819.6, 'JL601', 'JL');
  insert into flight_history (svc_date, flight, dep, arr, std, sta, type, reg, aircraft) values
    (((now() - interval '1 day') at time zone 'Asia/Tokyo')::date, 'JL601', 'HND', 'CTS', now() - interval '1 day', now() - interval '1 day' + interval '90 minutes', 'A359', 'JA01XJ', '359')`);
await as(A, `select public.co_state()`);
await db.exec(`update companies set cash = 500000 where user_id = '${A}'`);
// 手計算は満足度の倍率なし（満足度60）で確かめる。満足度は t47
await db.exec(`update companies set satisfaction = 60`).catch(() => {});
let s = await as(A, `select public.co_buy('r:JA01XJ')`);
const hc = `${Math.min(ids.HND, ids.CTS)}-${Math.max(ids.HND, ids.CTS)}`;
s = await as(A, `select public.co_assign(${s.fleet[0].id}, '${hc}')`);
check('FSC のはじめの上級席は20%', s.premium === 20, s.premium);
let e = s.econ.find((x) => x.k === hc);
// 手計算：A350-900 は機種の表で369席 → 上級席20%で上級席52・普通席213。
//   客 1,190人 × 0.94 ＝ 1,118.6人。上級席の客 ＝ 1,190 × 仕事の客 0.6 × 12% ＝ 85.68人（上級席 52席×6便×0.85 ＝ 265席に収まる）
//   普通席 ＝ min(1,118.6 − 85.68, 213席×6便×0.85 ＝ 1,086.3) ＝ 1,032.9人
//   収益 ＝（1,020 ＋ 85.68 × 5.6）× 運賃 0.496 × はじめの上乗せ 1.5
const fare = 0.25 + 820 * 0.0003, pp = 1190 * 0.6 * 0.12, ep = Math.min(1190 * 0.94 - pp, 213 * 6 * 0.85);
// 仕事の客の運賃 +20%（10/27）：上級席の客は全員、普通席は仕事の客 714人 − 上級席 85.68人 ＝ 628.32人の分
const rev = (ep + 0.2 * (1190 * 0.6 - pp) + pp * 5.6 * 1.2) * fare * 1.5, cost = 6 * 369 * 0.5 * fare, land = 6 * (((ep + pp) / 6) * 0.027 + 1.0);
check('上級席52席・上級席の客 85.7人・普通席の客 1,032.9人', near(Number(e.p_pax), pp, 0.1) && near(Number(e.e_pax), ep, 0.1) && Number(e.p_seats) === 52, e);
check('収益 ＝（普通席 ＋ 上級席 × 5.6）× 運賃 × 1.5、仕事の客は +20%', near(Number(e.revenue), rev, 0.05), { got: e.revenue, want: rev });
check('1日の収益 ＝ 手計算のもうけ', Number(s.gross) === Math.round(rev - cost - land), { got: s.gross, want: Math.round(rev - cost - land) });
const g20 = Number(s.gross);
s = await as(A, `select public.co3_set_premium(0)`);
check('上級席0%より20%のほうが、この路線ではもうかる', Number(s.gross) < g20, { g0: s.gross, g20 });
check('FSC は上級席40%は選べない', String(await as(A, `select public.co3_set_premium(40)`)).includes('premium not allowed'), null);
s = await as(A, `select public.co3_set_premium(30)`);
s = await as(A, `select public.co3_set_policy('mcc')`);
check('ミドルコストに変えると、選べない30%ははじめの10%に戻る', s.premium === 10, s.premium);
await as(A, `select public.co3_set_policy('fsc')`);
await as(A, `select public.co3_set_premium(0)`);

// 運賃での取り合い：B（LCC、運賃 0.72）が同じ路線に入る
await db.exec(`insert into companies (user_id, policy) values ('${B}', 'lcc') on conflict (user_id) do update set policy = 'lcc';
  insert into aircraft (user_id, type, route_key, paid) values ('${B}', 'nb', '${hc}', 1000);
  update companies set satisfaction = 60 where user_id = '${B}';
  insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values
    ('${B}', ${ids.HND}, ${ids.CTS}, now() - interval '3 day', now() - interval '3 day' + interval '90 minutes', 819.6)`);
s = await as(A, `select public.co_state()`);
e = s.econ.find((x) => x.k === hc);
// 客の総数 1,190 × 1.5（2社）＝ 1,785人。仕事の客：A は 1/1 ÷（1/1 ＋ 1/0.72）＝ 41.9%、旅行の客：1 ÷（1 ＋ 1/0.72³）＝ 27.2%
const wb = 1 / (1 + 1 / 0.72), wl = 1 / (1 + 1 / 0.72 ** 3);
const own = 1785 * (0.6 * 1.0 * wb + 0.4 * 0.85 * wl);
check('FSC と LCC の2社：A（FSC）の客は運賃の重みで 613人', e.n === 2 && near(Number(e.own), own, 0.2), { got: e.own, want: own });
const sb = await as(B, `select public.co_state()`);
const eb = sb.econ.find((x) => x.k === hc);
const ownB = 1785 * (0.6 * 0.4 * (1 - wb) + 0.4 * 1.7 * (1 - wl));
check('B（LCC）の客は旅行の客を多く取る', near(Number(eb.own), ownB, 0.2), { got: eb.own, want: ownB });
await db.exec(`update companies set policy = 'fsc' where user_id = '${B}'`);
s = await as(A, `select public.co_state()`);
e = s.econ.find((x) => x.k === hc);
check('同じ方針どうしなら前と同じ75%ずつ', near(Number(e.own), 1190 * 0.94 * 0.75, 0.2), e);

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('すべて OK');
