// エアライン経営 co-v3：シーズン順位（伸び率・部門・上位10%の印・1位の称号・出さない設定）
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
const q0 = await q1(`select (date_trunc('quarter', (now() at time zone 'Asia/Tokyo'))::date)::text`);
// ほかの会社 12社（格付け3の部門は A と 11社、格付け1の会社が1社）
const U = Array.from({ length: 12 }, (_, i) => `00000000-0000-0000-0000-0000000002${String(i).padStart(2, '0')}`);
for (const [i, u] of U.entries()) {
  await db.exec(`insert into auth.users (id) values ('${u}'); insert into companies (user_id, name, rating, last_collect) values ('${u}', 'C${i}', ${i === 11 ? 1 : 3}, now());
    insert into co_rank_days (day, user_id, value, routes, fleet) values ('${q0}', '${u}', 10000, 1, 1), ('${q0}'::date + 20, '${u}', ${10000 + i * 1000}, 1, 1)`);
}
await db.exec(`update companies set rating = 3 where user_id = '${A}'`);
const v = Number(await q1(`select public.co_value('${A}')`));
await db.exec(`insert into co_rank_days (day, user_id, value, routes, fleet) values ('${q0}', '${A}', ${Math.round(v / 1.15)}, 1, 1)`);
let r = await as(A, `select public.co3_season_rank()`);
const gA = (v - Math.round(v / 1.15)) / Math.round(v / 1.15);
check('部門は格付け3・格付け1の会社は入らない（12社）', r.division === '3' && r.total === 12 && !r.rows.some((x) => x.name === 'C11'), { d: r.division, t: r.total });
check('自分の伸び率 ＝ いまの価値 ÷ はじめの記録 − 1', near(Number(r.growth), gA, 1e-3), { g: r.growth, gA });
// C10 が +100%（いちばん）、自分は約 +15% で C1（+10%）より上・C2（+20%）より下
check('順位：C10 が1位・自分は伸び率の順', r.rows[0].name === 'C10' && r.rank === Array.from({ length: 11 }, (_, i) => i * 0.1).filter((g) => g > gA).length + 1, r);
check('上位10%の境目（12社なら上位2社）', near(Number(r.top10_cut), 0.9, 1e-9), r.top10_cut);
check('シーズンの名前と残りの日数', /^20\d\d年(冬|春|夏|秋)シーズン$/.test(r.season) && r.days_left > 0, r);
await db.exec(`update companies set hide_rank = true where name = 'C10'`);
r = await as(A, `select public.co3_season_rank()`);
check('出さない設定の会社は出ない', !r.rows.some((x) => x.name === 'C10') && r.total === 11, r.total);
// 締める
check('締める：上位10%に印・1位に称号', Number(await q1(`select public.co3_season_close('${q0}')`)) === 2 + 1 + 1 + 1, null);
const aw = (await db.query(`select c.name, a.kind from co3_awards a join companies c on c.user_id = a.user_id order by c.name, a.kind`)).rows.map((x) => `${x.name}:${x.kind}`);
check('C9 と C8 が上位10%・C9 が1位・格付け1の部門は C11 だけで1位', aw.join(',') === 'C11:season_champ,C11:season_top10,C8:season_top10,C9:season_champ,C9:season_top10', aw);
check('2回締めても増えない', Number(await q1(`select public.co3_season_close('${q0}')`)) === 0, null);
check('印は自分の分しか見えない', Number(await as(A, `select count(*) from co3_awards`)) === 0 && Number(await as(U[9], `select count(*) from co3_awards`)) === 2, null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
