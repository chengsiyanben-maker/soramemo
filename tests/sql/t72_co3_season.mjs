// エアライン経営 co-v3：季節の需要（全国の時期・地域のシーズン・客の総数と仕事の客の割合・運賃・次の繁忙期）
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
const S = async (a, b, d) => (await db.query(`select * from co3.season('${a}', '${b}', '${d}')`)).rows[0];
const eq = (r, l, b, f) => near(Number(r.lei), l, 1e-9) && near(Number(r.biz), b, 1e-9) && near(Number(r.fare), f, 1e-9);
check('年末年始（12/30）：羽田⇄福岡 旅行 ×1.5・仕事 ×0.5・運賃 ×1.2', eq(await S('HND', 'FUK', '2026-12-30'), 1.5, 0.5, 1.2), await S('HND', 'FUK', '2026-12-30'));
check('年末年始の羽田⇄新千歳：北海道の冬 ×1.4 をかける', eq(await S('HND', 'CTS', '2026-12-30'), 1.5 * 1.4, 0.5, 1.2), null);
check('雪まつりのころ（2/5）：閑散期 0.85 × 1.6', eq(await S('HND', 'CTS', '2027-02-05'), 0.85 * 1.6, 1, 0.9), null);
check('GW（5/3）：仕事 ×0.6', eq(await S('HND', 'FUK', '2027-05-03'), 1.5, 0.6, 1.2), null);
check('お盆（8/12）と夏休み（8/25）', eq(await S('HND', 'FUK', '2026-08-12'), 1.5, 0.5, 1.2) && eq(await S('HND', 'FUK', '2026-08-25'), 1.2, 0.9, 1.1), null);
check('那覇⇄石垣の夏（8/25）：どちらも沖縄 ×1.5', eq(await S('OKA', 'ISG', '2026-08-25'), 1.2 * 1.5, 0.9, 1.1), null);
check('那覇⇄奄美の冬（2/20）：沖縄 1.1 と奄美 0.8 の平均', eq(await S('OKA', 'ASJ', '2027-02-20'), 0.85 * 0.95, 1, 0.9), null);
check('羽田⇄山形の10月：東北 ×1.1', eq(await S('HND', 'GAJ', '2026-10-15'), 1.1, 1, 1), null);
check('伊丹⇄羽田の11月：閑散期 0.85 × 京都の紅葉 1.15', eq(await S('ITM', 'HND', '2026-11-15'), 0.85 * 1.15, 1, 0.9), null);
check('季節のない日（5/20）はすべて1', eq(await S('HND', 'CTS', '2026-05-20'), 1, 1, 1), null);
// 仕事の客の割合と総数
const sb = Number(await q1(`select co3.season_biz(0.6, 'HND', 'FUK')`)), sp = Number(await q1(`select co3.season_pool(0.6, 'HND', 'FUK')`));
check('季節のない日：割合と総数はそのまま', near(sb, 0.6, 1e-9) && near(sp, 1, 1e-9), { sb, sp });
await db.exec(`set co3.season_day = '2026-12-30'`);
const sb2 = Number(await q1(`select co3.season_biz(0.6, 'HND', 'FUK')`)), sp2 = Number(await q1(`select co3.season_pool(0.6, 'HND', 'FUK')`));
check('年末年始：総数 0.6×0.5＋0.4×1.5 ＝ 0.9 倍・仕事の割合 0.3 ÷ 0.9', near(sp2, 0.9, 1e-9) && near(sb2, 0.3 / 0.9, 1e-9), { sb2, sp2 });
s = await as(A, `select public.co_state()`);
const e2 = s.econ.find((x) => x.k === hc);
check('会社の状態：いまは年末年始（旅行 ×1.5）・次の繁忙期', s.season.name === '年末年始' && Number(s.season.lei) === 1.5 && s.season.next.name === '春休み', s.season);
check('年末年始の羽田⇄新千歳：収益は変わる（運賃 ×1.2・客が増える）', Number(e2.revenue) !== Number(e.revenue), { a: e2.revenue, b: e.revenue });
await db.exec(`set co3.season_day = '2026-05-20'`);
s = await as(A, `select public.co_state()`);
check('季節のない日：次は夏休み（61日後）', s.season.name === null && s.season.next.name === '夏休み' && s.season.next.days === 61, s.season);
check('もとの日に戻すと収益も戻る', Number(s.econ.find((x) => x.k === hc).revenue) === Number(e.revenue), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
