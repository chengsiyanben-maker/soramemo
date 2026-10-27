// エアライン経営 co-v3：混雑空港の発着枠（毎月の申し込み・おまかせ・割合で分ける・最低4便・地方の枠・混雑料金の固定・RLS）
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
const nm = await q1(`select ((co3.month_now() + interval '1 month')::date)::text`), m0 = await q1(`select co3.month_now()::text`);
const use = async (u) => (await db.query(`select * from co3_slot_use('${u}')`)).rows;
const fl0 = e.flights;
check('いま組んでいる便：羽田（main）と新千歳は混雑空港ではない', (await use(A)).length === 1 && (await use(A))[0].iata === 'HND' && (await use(A))[0].pool === 'main', await use(A));
const u0 = (await use(A))[0].fl;
check('月が決まる前は今までどおり', s.slots.decided === false && s.slots.list.length === 6 && s.slots.auto === true, s.slots);
// ほかの会社（5社）：自分で申し込み、羽田に400便ずつ
const others = [1, 2, 3, 4, 5].map((i) => `00000000-0000-0000-0000-00000000010${i}`);
for (const u of others) {
  await db.exec(`insert into auth.users (id) values ('${u}'); insert into companies (user_id, name, slot_auto, rating, last_collect) values ('${u}', 'X${u.slice(-1)}', false, 5, now());
    insert into co3_slot_apps (user_id, month, iata, pool, flights) values ('${u}', '${m0}', 'HND', 'main', 400)`);
}
const act = Number(await q1(`select count(*) from companies where last_collect > now() - interval '30 days'`));
const cap = 80 * 17 * Math.max(1, act / 50) * 0.8;
check('決める：書いた行の数', Number(await q1(`select public.co3_slots_decide('${m0}')`)) === 6, null);
check('2回目は何もしない', Number(await q1(`select public.co3_slots_decide('${m0}')`)) === 0, null);
const mo = (await db.query(`select * from co3_slot_month where month = '${m0}' and iata = 'HND' and pool = 'main'`)).rows[0];
check('羽田（main）の枠 ＝ 80 × 17 × 0.8、申し込みの合計 ＝ 2000 ＋ A', near(Number(mo.capacity), cap, 0.1) && mo.total === 2000 + u0, { mo, cap, u0 });
const g = async (u) => (await db.query(`select * from co3_slot_grants where user_id = '${u}' and month = '${m0}' and iata = 'HND'`)).rows[0];
check('超えたら割合で分ける（400 × 枠 ÷ 合計）', (await g(others[0])).granted === Math.floor(400 * Number(mo.capacity) / mo.total), await g(others[0]));
const gA = await g(A);
check('A（おまかせ）：いまの便で申し込み、割合で分ける（最低4便）', gA.applied === u0 && gA.granted === Math.max(Math.min(4, u0), Math.floor(u0 * Number(mo.capacity) / mo.total)), gA);
s = await as(A, `select public.co_state()`);
const e2 = s.econ.find((x) => x.k === hc);
check('自社の便は もらった枠 ÷ いまの便 の割合まで', e2.flights === Math.min(fl0, Math.floor(fl0 * Math.min(1, gA.granted / u0))) && e2.flights < fl0, { f: e2.flights, fl0, gA, u0 });
const whole = mo.total / (Number(mo.capacity) / 0.8), cr = Math.min(0.2, (whole - 1) * 0.2);
check('混雑料金は決まった混み具合で：収益 × 0.5 × 割合', near(Number(e2.congestion), Number(e2.revenue) * 0.5 * cr, 0.5), { c: e2.congestion, r: e2.revenue, cr });
check('会社の状態：決まった・もらった枠・混み具合', s.slots.decided === true && s.slots.list[0].granted === gA.granted && near(s.slots.list[0].cong, whole, 0.01), s.slots.list[0]);
check('新聞：枠の結果', (await db.query(`select title from co3_news where user_id = '${A}' and kind = 'slots'`)).rows[0]?.title.includes('羽田の発着枠は 1日'), null);
// 来月の申し込み：おまかせのうちは出せない
check('おまかせのうちは申し込めない', String(await as(A, `select public.co3_slot_apply('HND', 'main', 10)`)).includes('slot auto'), null);
s = await as(A, `select public.co3_set_slot_auto(false)`);
s = await as(A, `select public.co3_slot_apply('HND', 'main', 10)`);
check('来月の分を申し込む（10便）', s.slots.auto === false && s.slots.list[0].apply === 10 && (await db.query(`select month::text from co3_slot_apps where user_id = '${A}'`)).rows[0].month === nm, s.slots.list[0]);
check('羽田のほかは地方の枠に申し込めない', String(await as(A, `select public.co3_slot_apply('NRT', 'regional', 4)`)).includes('invalid airport'), null);
s = await as(A, `select public.co3_slot_apply('HND', 'main', null)`);
check('取り消し', s.slots.list[0].apply === null, s.slots.list[0]);
check('自分の申し込みしか見えない', Number(await as(A, `select count(*) from co3_slot_apps`)) === 0 && Number(await as(A, `select count(*) from co3_slot_grants`)) === 1, null);
check('枠の表はだれでも見られる・書けない', Number(await as(A, `select count(*) from co3_slot_month`)) === 6 && String(await as(A, `insert into co3_slot_month values ('${nm}', 'HND', 'main', 1, 1)`)).startsWith('ERROR'), null);
check('申し込みを直接は書けない', String(await as(A, `insert into co3_slot_apps (user_id, month, iata, flights) values ('${A}', '${nm}', 'HND', 1)`)).startsWith('ERROR'), null);
// 月の途中で始めた空港：最低4便まで
await db.exec(`delete from co3_slot_grants where user_id = '${A}'`);
check('枠をもらっていない空港は4便まで', Number(await q1(`select public.co3_slot_fl('${A}', 12, 'HND', 'CTS')`)) === Math.floor(12 * Math.min(1, 4 / u0)), null);
check('混雑空港でない路線はそのまま', Number(await q1(`select public.co3_slot_fl('${A}', 12, 'CTS', 'HIJ')`)) === 12, null);
check('地方の枠：羽田⇄広島は regional', (await q1(`select co3.slot_pool('HND', 'HND', 'HIJ')`)) === 'regional' && (await q1(`select co3.slot_pool('HND', 'HND', 'CTS')`)) === 'main', null);
await db.exec(`update companies set rating = 2 where user_id = '${A}'`);
check('格付け2：おまかせを変えられない', String(await as(A, `select public.co3_set_slot_auto(false)`)).includes('rating required 3'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
