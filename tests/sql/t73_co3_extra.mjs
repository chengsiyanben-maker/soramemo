// エアライン経営 co-v3：臨時便（繁忙期だけ・予備機・増えた旅行の客だけ稼ぐ・期間の終わり・予備機にならない）
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
// 予備機：A350 をもう1機（路線に入れない）
await db.exec(`insert into aircraft (user_id, type, reg, paid, bought_at) values ('${A}', 'lg', 'JA02ZZ', 40000, now())`);
const sp = Number(await q1(`select id from aircraft where reg = 'JA02ZZ'`));
check('繁忙期でなければ組めない', String(await as(A, `select public.co3_set_extra(${sp}, '${hc}', 4)`)).includes('not peak'), null);
await db.exec(`set co3.season_day = '2026-12-30'`);
check('年末年始の終わりは 1/4', (await q1(`select co3.peak_end('2026-12-30')::text`)) === '2027-01-04' && (await q1(`select co3.peak_end('2026-08-25')::text`)) === '2026-08-31' && (await q1(`select co3.peak_end('2026-08-10')::text`)) === '2026-08-18', null);
check('路線に入れている機体は使えない', String(await as(A, `select public.co3_set_extra(${s.fleet[0].id}, '${hc}', 4)`)).includes('not a spare'), null);
check('便数は 2・4・6・8', String(await as(A, `select public.co3_set_extra(${sp}, '${hc}', 5)`)).includes('invalid flights'), null);
s = await as(A, `select public.co3_set_extra(${sp}, '${hc}', 4)`);
const ex = s.extra.list[0], e2 = s.econ.find((x) => x.k === hc);
check('臨時便を組む：1/4まで', s.extra.list.length === 1 && ex.end === '2027-01-04' && s.extra.peak_end === '2027-01-04', s.extra);
// 手計算：客 ＝ 路線の客 × 旅行の割合 0.4 ×（旅行の倍率 1.5×1.4 − 1）× 自社の取り分、席の85%まで
const lei = 1.5 * 1.4, want = Math.min(4 * 369 * 0.85, Number(e2.demand) * 0.4 * (lei - 1) * Math.min(1, Number(e2.carried) / Number(e2.demand)));
check('臨時便の客 ＝ 増えた旅行の客 × 取り分（席の85%まで）', near(Number(ex.pax), want, 0.1), { ex, want, d: e2.demand, c: e2.carried });
const rev = Number(ex.pax) * (0.25 + 819.6 * 0.0003) * 1.2;
check('収益 ＝ 客 × 運賃 × 繁忙期の運賃 1.2（FSC 1.0）', Math.abs(Number(ex.revenue) - rev) / rev < 0.02, { r: ex.revenue, rev });
const g0 = Number(s.gross);
check('1日の稼ぎに足される', near(Number(await q1(`select public.co3_gross('${A}')`)), Number(await q1(`select round(sum(profit)) from co3_route_econ('${A}')`)) + Math.round(Number(ex.profit)), 2), { g0 });
check('同じ機体で2つは組めない', String(await as(A, `select public.co3_set_extra(${sp}, '${hc}', 2)`)).includes('already extra'), null);
// 臨時便の機体は予備機にならない：路線の機体を故障させる
await db.exec(`update ops.flags set value = 'true' where key = 'co_v3'`);
const today = await q1(`select ((now() at time zone 'Asia/Tokyo')::date)::text`);
await db.exec(`update co3_extra set start_day = '${today}', end_day = '${today}'::date + 3000`);
const spareOf = async () => { await db.exec(`delete from co3_breakdowns`); for (let i = 0; i < 3000; i++) { await q1(`select public.co3_breakdown_draw('${today}'::date + ${i})`); const r = (await db.query(`select spare_id from co3_breakdowns limit 1`)).rows[0]; if (r) return r; } return null; };
const b1 = await spareOf();
check('臨時便の間は予備機にならない', b1 && b1.spare_id === null, b1);
s = await as(A, `select public.co3_stop_extra(${ex.id})`);
check('やめる', s.extra.list.length === 0, s.extra);
await db.exec(`set co3.season_day = '2027-01-05'`);
check('期間が終わると消える', (await as(A, `select public.co_state()`)).extra.list.length === 0, null);
check('ほかの会社には見えない', Number(await as(B, `select count(*) from co3_extra`)) === 0 && Number(await as(A, `select count(*) from co3_extra`)) === 1, null);
await db.exec(`update companies set rating = 2 where user_id = '${A}'; set co3.season_day = '2026-12-30'`);
check('格付け2：組めない', String(await as(A, `select public.co3_set_extra(${sp}, '${hc}', 2)`)).includes('rating required 3'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
