// エアライン経営 co-v3：運賃の5段階（自社と他社の運賃の重み、1日1回）
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
if (fs.existsSync(dir + '20261028000103_co3_cabin_fare.sql')) s = await as(A, `select public.co3_set_premium(0)`);
const v2gross = Number(s.gross);
check('スイッチがオフ：co-v2 の収益のまま・econ なし', s.v3 === false && s.econ === null && v2gross > 0, { v3: s.v3, g: v2gross });

// スイッチをオンにする
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
s = await as(A, `select public.co_state()`);
const e = s.econ.find((x) => x.k === hc);
// B が同じ路線に機体を入れる（2社とも FSC・普通）
await db.exec(`insert into companies (user_id) values ('${B}') on conflict do nothing;
  insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values ('${B}', ${ids.CTS}, ${ids.HND}, now() - interval '2 days', now() - interval '2 days' + interval '90 minutes', 819.6);
  insert into aircraft (user_id, type, route_key, paid) values ('${B}', 'nb', '${hc}', 1000);
  update companies set satisfaction = 60`);
s = await as(A, `select public.co_state()`);
const e0 = s.econ.find((x) => x.k === hc);
check('はじめは普通（段 0）・ほかの会社の段が見える', s.fares[hc].level === 0 && JSON.stringify(s.fares[hc].others) === '[0]', s.fares[hc]);
// 2社とも普通のとき：仕事の客も旅行の客も半分ずつ → 自社の客 ＝ 路線の客の総数 × 0.94 × 0.5
const pool = Number(e0.own) / (0.94 * 0.5);
// A を「安い」（×0.85）に：仕事の客は 1/運賃、旅行の客は 1/運賃³ の割合
s = await as(A, `select public.co3_set_fare('${hc}', -1)`);
const e1 = s.econ.find((x) => x.k === hc);
const sb = (1 / 0.85) / (1 / 0.85 + 1), sl = (1 / 0.85 ** 3) / (1 / 0.85 ** 3 + 1);
check('安い：自社の客 ＝ 総数 ×（0.6 × 仕事の取り分 54% ＋ 0.4 × 0.85 × 旅行の取り分 62%）', near(Number(e1.own), pool * (0.6 * sb + 0.34 * sl), 0.2), { got: e1.own, want: pool * (0.6 * sb + 0.34 * sl) });
check('安い：段 −1 と決めた日が出る', s.fares[hc].level === -1 && !!s.fares[hc].set_on, s.fares[hc]);
// 収益は ×0.85（運べる客が増えた分を除いて、1人あたり）
// 1人あたりの収益は ×0.85。ただし仕事の客の運賃（+20%）の分は、客のうち仕事の客の割合が変わった分だけ動く
const be0 = 0.6 * 0.5 / (0.94 * 0.5), be1 = 0.6 * sb / (0.6 * sb + 0.34 * sl), ratio = 0.85 * (1 + 0.2 * be1) / (1 + 0.2 * be0);
check('安い：1人あたりの収益は普通の 0.85倍（仕事の客の割合の分を直して）', near(Number(e1.revenue) / Number(e1.carried), Number(e0.revenue) / Number(e0.carried) * ratio, 0.002),
  { now: Number(e1.revenue) / Number(e1.carried), before: Number(e0.revenue) / Number(e0.carried) });
check('同じ日にもう一度変えられない', String(await as(A, `select public.co3_set_fare('${hc}', 1)`)).includes('fare once a day'), null);
check('同じ段にするのは数えない', !String(await as(A, `select public.co3_set_fare('${hc}', -1)`)).startsWith('ERROR'), null);
check('段は −2〜2 だけ', String(await as(A, `select public.co3_set_fare('${hc}', 3)`)).includes('invalid fare'), null);
check('路線がない区間は決められない', String(await as(A, `select public.co3_set_fare('1-2', 1)`)).includes('route not found'), null);
// 次の日なら変えられる。B から見ると、A の段が「ほかの会社」に出て、B の客が減る
await db.exec(`update co3_fares set set_on = set_on - 1`);
s = await as(A, `select public.co3_set_fare('${hc}', 2)`);
check('次の日なら変えられる（とても高い）', s.fares[hc].level === 2, s.fares[hc]);
await db.exec(`update co3_fares set set_on = set_on - 1`);
s = await as(A, `select public.co3_set_fare('${hc}', -2)`);
const sB = await as(B, `select public.co_state()`);
check('B から見ると、ほかの会社の段 −2', JSON.stringify(sB.fares[hc].others) === '[-2]', sB.fares[hc]);
// 表は自分の分だけ読める・直接は書けない
check('運賃の表：自分の分だけ読める', Number(await as(B, `select count(*) from co3_fares`)) === 0 && Number(await as(A, `select count(*) from co3_fares`)) === 1, null);
check('運賃の表：直接は書けない', String(await as(A, `insert into co3_fares (user_id, route_key, level) values ('${A}', '1-2', 1)`)).startsWith('ERROR'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
