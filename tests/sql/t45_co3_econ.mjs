// エアライン経営 co-v3：1日の収益を仕様書の計算に切り替える（スイッチ co_v3）
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
// 手計算（仕様書の式）：客 20便×170席×0.7×0.5 ＝ 1,190人。大きい空港どうし（仕事の客6割）、FSC は仕事の客 1.0・旅行の客 0.85 → ×0.94
//   1社なので取り合いなし → 1,118.6人。A350-900（機種の表で369席）は 820km で1日6便 → 運べる 6×369×0.85 ＝ 1,882人 → 1,118.6人
//   運賃 0.25＋820×0.0003 ＝ 0.496、はじめの上乗せ 1.5 → 収益 832.3
//   費用 6便 × 369席 × 0.5 × 0.496 ＝ 549.0。着陸料 1便の客 186.4人 × 0.027 ＋ 大きいジェット 1.0 ＝ 6.03 × 6 ＝ 36.2
const pax = 1190 * (0.6 * 1.0 + 0.4 * 0.85), fare = 0.25 + 820 * 0.0003;
// 仕事の客の運賃（10/27）：大きい空港どうしの FSC は +20%。自社の仕事の客 1,190×0.6 ＝ 714人の分だけ上がる
const rev = (pax + 0.2 * 1190 * 0.6) * fare * 1.5, cost = 6 * 369 * 0.5 * fare, land = 6 * ((pax / 6) * 0.027 + 1.0);
check('路線の客：1,190人 → 方針で 1,118.6人', Number(e.demand) === 1190 && near(Number(e.own), pax, 0.1), e);
check('1日6便・A350-900 369席（機種の表）・全員運べる', e.flights === 6 && Number(e.seats) === 369 && near(Number(e.carried), pax, 0.1), e);
check('収益（運賃 × はじめの上乗せ 1.5、仕事の客は +20%）', near(Number(e.revenue), rev, 0.05), { got: e.revenue, want: rev });
check('運航の費用', near(Number(e.cost), cost, 0.05), { got: e.cost, want: cost });
check('着陸料', near(Number(e.landing), land, 0.05), { got: e.landing, want: land });
check('混雑料金：羽田の申し込みが枠に収まるので0', Number(e.congestion) === 0, e);
check('1日の収益（co_gross）＝ 手計算のもうけ', Number(s.gross) === Math.round(rev - cost - land), { got: s.gross, want: Math.round(rev - cost - land) });

// 便数を変える：2便にすると、運べるのが 2×350×0.85 ＝ 595人まで
s = await as(A, `select public.co3_set_flights('${hc}', 2)`);
const e2 = s.econ.find((x) => x.k === hc);
check('便数を2便に：運べる客は 2×369×0.85 ＝ 627.3人まで', e2.flights === 2 && near(Number(e2.carried), 627.3, 0.1), e2);
check('奇数の便数は入れられない', String(await as(A, `select public.co3_set_flights('${hc}', 3)`)).includes('invalid flights'), null);
check('持っていない路線は入れられない', String(await as(A, `select public.co3_set_flights('1-2', 4)`)).includes('route not found'), null);
check('ほかの人の便数は見えない', Number(await as(B, `select count(*) from co3_plans`)) === 0 && Number(await as(A, `select count(*) from co3_plans`)) === 1, null);
await as(A, `select public.co3_set_flights('${hc}', null)`);

// 方針を LCC に：運賃 0.72倍、旅行の客 1.7倍
s = await as(A, `select public.co3_set_policy('lcc')`);
const e3 = s.econ.find((x) => x.k === hc);
check('LCC：客は 1,190 ×（0.6×0.4＋0.4×1.7）', s.policy === 'lcc' && near(Number(e3.own), 1190 * (0.6 * 0.4 + 0.4 * 1.7), 0.1), e3);
check('方針の名前がおかしいと入れられない', String(await as(A, `select public.co3_set_policy('xyz')`)).includes('invalid policy'), null);
await as(A, `select public.co3_set_policy('fsc')`);

// ほかの会社 B が同じ路線に機体を入れると、客は 2社で 75%ずつ
await db.exec(`insert into companies (user_id) values ('${B}') on conflict do nothing;
  insert into aircraft (user_id, type, route_key, paid) values ('${B}', 'nb', '${hc}', 1000)`);
await db.exec(`update companies set satisfaction = 60`).catch(() => {});
s = await as(A, `select public.co_state()`);
const e4 = s.econ.find((x) => x.k === hc);
check('2社で取り合うと 75%', e4.n === 2 && near(Number(e4.own), pax * 0.75, 0.1), e4);

// 混雑料金：羽田の申し込みが枠の1.5倍（1,360便の枠に 2,040便）だと 10%（片側の着陸の分なので収益の5%）
await db.exec(`insert into auth.users (id) select gen_random_uuid() from generate_series(1, 339);
  insert into companies (user_id) select id from auth.users where id not in ('${A}', '${B}');
  insert into aircraft (user_id, type, route_key, paid) select id, 'nb', '${hc}', 1000 from auth.users where id not in ('${A}', '${B}');
  update companies set last_collect = now() - interval '60 days' where user_id not in ('${A}', '${B}');`);
s = await as(A, `select public.co_state()`);
const e5 = s.econ.find((x) => x.k === hc);
const total = 6 + 6 * 340; // A と 340社がそれぞれ 820km で6便
const rate = Math.min(0.2, Math.max(0, (total / 1360 - 1) * 0.2));
check('混雑料金：（混み具合−1）×20% の、羽田に着く片側の分', near(Number(e5.congestion), Number(e5.revenue) * 0.5 * rate, 0.05), { e5, rate });
check('申し込みが枠を超えたので、A の便は申し込みの割合で減る（最低4便）', e5.flights === Math.max(4, Math.floor(6 * 1360 / total)), e5);

// 本拠地と地元の応援：山形（小規模）を本拠地にして30日すぎ。山形⇄羽田（本物の便あり、1日4便×85席）
await db.exec(`insert into flight_history (svc_date, flight, dep, arr, std, sta, type)
  select (now() at time zone 'Asia/Tokyo')::date - d, 'JL' || (170 + s), case s when 0 then 'HND' else 'GAJ' end, case s when 0 then 'GAJ' else 'HND' end,
         now() - d * interval '1 day', now() - d * interval '1 day' + interval '60 minutes', 'B738'
    from generate_series(1, 28) d, generate_series(0, 3) s;
  insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values
    ('${A}', ${ids.HND}, ${ids.GAJ}, now() - interval '2 day', now() - interval '2 day' + interval '60 minutes', 300);
  update companies set home_airport = ${ids.GAJ}, home_since = (now() at time zone 'Asia/Tokyo')::date - 40 where user_id = '${A}';`);
await q1(`select public.co3_route_real_refresh()`);
s = await as(A, `select public.co_state()`);
const hg = `${Math.min(ids.HND, ids.GAJ)}-${Math.max(ids.HND, ids.GAJ)}`;
const e6 = s.econ.find((x) => x.k === hg);
// 客 4便×170席（B738）×0.35 ＝ 238人 × FSC（仕事の客45%）0.9175 ＝ 218.4人 → 小規模なので ×5 ＝ 1,092人（500人より多い）
check('本拠地（小規模）の路線は ×5（羽田⇄山形 218.4人 → 1,092人）', e6 && near(Number(e6.own), 238 * (0.45 + 0.55 * 0.85) * 5, 0.1), e6);
await db.exec(`update flight_history set type = 'DH8D' where flight in ('JL170', 'JL171', 'JL172', 'JL173')`);
await q1(`select public.co3_route_real_refresh()`);
s = await as(A, `select public.co_state()`);
const e7 = s.econ.find((x) => x.k === hg);
// Q400（機種の表で74席）なら 4×74×0.35 ＝ 103.6人 × 0.9175 × 5 ＝ 475.3人 → 最低500人
check('×5 しても500人に届かなければ500人（本物の便がある路線だけ）', e7 && near(Number(e7.own), 500, 0.1), e7);
check('機体のない路線は便が0で、もうけも0', e6 && e6.flights === 0 && Number(e6.profit) === 0, e6);
check('本拠地はチェックインした空港だけ', String(await as(A, `select public.co3_set_home(${ids.HIJ})`)).includes('not visited'), null);

// スイッチをオフに戻すと co-v2 の収益
await db.exec(`update ops.flags set value = 'false' where key = 'co_v3'`);
s = await as(A, `select public.co_state()`);
check('スイッチをオフに戻すと econ なし', s.v3 === false && s.econ === null, null);

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('すべて OK');
