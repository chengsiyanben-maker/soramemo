// エアライン経営 co-v3：共同運航（フリーセール・ブロック買い取り・乗り継ぎ・上限）とアライアンス（作る・入る・仲間は認めなし・施設の半分・対抗戦）
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
// B：羽田⇄広島を飛ぶ会社（友だち）
const hh = `${Math.min(ids.HND, ids.HIJ)}-${Math.max(ids.HND, ids.HIJ)}`;
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no, airline) values ('${B}', ${ids.HND}, ${ids.HIJ}, now() - interval '1 day', now() - interval '1 day' + interval '80 minutes', 674, 'NH671', 'NH');
  insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${B}', ${ids.HND}, 35.55, 139.78, 10, now());`);
await as(B, `select public.co_state()`);
await db.exec(`update companies set rating = 5, safety = 'low', satisfaction = 60, cash = 500000 where user_id = '${B}';
  insert into aircraft (user_id, type, reg, route_key, paid, bought_at) values ('${B}', 'nb', 'JA77BB', '${hh}', 20000, now())`);
const codeB = await q1(`select friend_code from companies where user_id = '${B}'`), codeA = await q1(`select friend_code from companies where user_id = '${A}'`);
check('友だちでなければ申し込めない', String(await as(A, `select public.co3_cs_request('${codeB}', '${hh}', 'free')`)).includes('not partner'), null);
await as(A, `select public.co_add_friend('${codeB}')`);
let L = await as(A, `select public.co3_cs_candidates()`);
check('売れる路線：B の羽田⇄広島（羽田が自分の路線の空港）', L.length === 1 && L[0].k === hh && L[0].mine === null, L);
const revB0 = Number((await as(B, `select public.co_state()`)).econ.find((x) => x.k === hh).revenue);
s = await as(A, `select public.co3_cs_request('${codeB}', '${hh}', 'free')`);
check('友だちには申し込み（認め待ち）', s.cs.list[0].status === 'pending' && s.cs.list[0].role === 'seller', s.cs);
let sb = await as(B, `select public.co_state()`);
check('運航会社に頼まれている', sb.cs.list[0].role === 'op' && sb.cs.list[0].status === 'pending', sb.cs);
const g0 = Number(await q1(`select public.co3_gross('${A}')`));
sb = await as(B, `select public.co3_cs_answer(${sb.cs.list[0].id}, true)`);
check('認める：運航会社の収益 +5%', near(Number(sb.econ.find((x) => x.k === hh).revenue), revB0 * 1.05, 0.05), { r: sb.econ.find((x) => x.k === hh).revenue, revB0 });
const revB1 = Number(sb.econ.find((x) => x.k === hh).revenue);
s = await as(A, `select public.co_state()`);
const eA = s.econ.find((x) => x.k === hc);
check('販売会社の取り分 ＝ 路線の収益の15%', near(Number(s.cs.income), revB1 * 0.15, 1) && near(Number(s.cs.list[0].share), revB1 * 0.15, 1), s.cs);
check('乗り継ぎ：羽田でつながる 羽田⇄新千歳 +5%', near(Number(eA.revenue), Number(e.revenue) * 1.05, 0.05), { a: eA.revenue, b: e.revenue });
check('1日の稼ぎに取り分が入る', Math.abs(Number(await q1(`select public.co3_gross('${A}')`)) - (Number(await q1(`select round(sum(profit)) from co3_route_econ('${A}')`)) + Math.round(revB1 * 0.15))) <= 2, null);
check('同じ路線に2回は申し込めない', String(await as(A, `select public.co3_cs_request('${codeB}', '${hh}', 'block')`)).includes('already requested'), null);
s = await as(A, `select public.co3_cs_end(${s.cs.list[0].id})`);
check('やめる', s.cs.list.length === 0 && Number(s.cs.income) === 0, s.cs);
// ブロック買い取り：認めたときに5日分を払う・35%
s = await as(A, `select public.co3_cs_request('${codeB}', '${hh}', 'block')`);
let cA = Number(await q1(`select cash from companies where user_id = '${A}'`)), cB = Number(await q1(`select cash from companies where user_id = '${B}'`));
sb = await as(B, `select public.co3_cs_answer(${s.cs.list[0].id}, true)`);
const revB2 = Number(sb.econ.find((x) => x.k === hh).revenue) / 1.05, pay = Math.ceil(revB2 * 5);
check('ブロック：5日分を運航会社へ', Math.abs(cA - Number(await q1(`select cash from companies where user_id = '${A}'`)) - pay) <= 2 && Math.abs(Number(await q1(`select cash from companies where user_id = '${B}'`)) - cB - pay) <= 2, { pay });
s = await as(A, `select public.co_state()`);
check('ブロック：取り分は 35%', near(Number(s.cs.income), Number(sb.econ.find((x) => x.k === hh).revenue) * 0.35, 1), s.cs);
check('今月はもう払わない', Number(await q1(`select public.co3_cs_daily()`)) === 0, null);
await db.exec(`update co3_codeshares set paid_month = paid_month - interval '1 month'`);
cA = Number(await q1(`select cash from companies where user_id = '${A}'`));
check('次の月の1日にまた払う', Number(await q1(`select public.co3_cs_daily()`)) === 1 && cA > Number(await q1(`select cash from companies where user_id = '${A}'`)), null);
await db.exec(`update companies set cash = 0 where user_id = '${A}'; update co3_codeshares set paid_month = paid_month - interval '1 month'`);
await q1(`select public.co3_cs_daily()`);
check('払えなければ終わる', (await q1(`select status from co3_codeshares where kind = 'block'`)) === 'ended', null);
await db.exec(`update companies set cash = 500000 where user_id = '${A}'`);
check('上限：格付け1なら3本', Number(await q1(`select co3.cs_limit(1)`)) === 3 && Number(await q1(`select co3.cs_limit(5)`)) === 20, null);
check('ほかの会社の共同運航は見えない', Number(await as('00000000-0000-0000-0000-0000000000cc', `select count(*) from co3_codeshares`)) === 0, null);
// アライアンス
await db.exec(`update companies set policy = 'mcc' where user_id = '${B}'`);
check('ミドルコストは作れない', String(await as(B, `select public.co3_ally_create('瀬戸内の空')`)).includes('fsc only'), null);
check('本物の名前は使えない', String(await as(A, `select public.co3_ally_create('スター アライアンス')`)).includes('real alliance name'), null);
s = await as(A, `select public.co3_ally_create('みなみの空連合')`);
check('作る：リーダー', s.ally.name === 'みなみの空連合' && s.ally.leader === true, s.ally);
const aid = s.ally.id;
await db.exec(`update companies set policy = 'lcc' where user_id = '${B}'`);
check('LCC は入れない', String(await as(B, `select public.co3_ally_join(${aid})`)).includes('lcc cannot join'), null);
await db.exec(`update companies set policy = 'mcc' where user_id = '${B}'; delete from co_friends`);
sb = await as(B, `select public.co3_ally_join(${aid})`);
check('入る', sb.ally.members.length === 2, sb.ally);
s = await as(A, `select public.co3_cs_request('${codeB}', '${hh}', 'free')`);
check('仲間のフリーセールは認めなしで始まる', s.cs.list[0].status === 'active', s.cs);
// 仲間の施設：B の羽田の施設1段が、施設のない A の路線に +3%
const revA0 = Number(s.econ.find((x) => x.k === hc).revenue);
await db.exec(`insert into facilities (user_id, airport_id, level) values ('${B}', ${ids.HND}, 1)`);
check('仲間の施設の半分（+3%）', near(Number((await as(A, `select public.co_state()`)).econ.find((x) => x.k === hc).revenue), revA0 * 1.03, 0.05), null);
L = await as(A, `select public.co3_ally_list()`);
check('アライアンスの一覧：2社・会社の価値の合計', L.length === 1 && Number(L[0].n) === 2 && L[0].mine === true, L);
// 抜ける：仲間のフリーセールは終わる・7日は入れない
sb = await as(B, `select public.co3_ally_leave()`);
check('抜けると仲間の共同運航は終わる', (await q1(`select status from co3_codeshares where kind = 'free' and status <> 'ended' limit 1`)) === undefined && sb.ally === null && sb.ally_cooldown !== null, sb.ally_cooldown);
check('抜けたら7日は入れない', String(await as(B, `select public.co3_ally_join(${aid})`)).includes('alliance cooldown'), null);
await db.exec(`update companies set alliance_left_at = now() - interval '8 days' where user_id = '${B}'`);
await as(B, `select public.co3_ally_join(${aid})`);
// リーダーが抜けると、価値がいちばん高い仲間がリーダー
await as(A, `select public.co3_ally_leave()`);
check('リーダーが抜けると仲間がリーダーに', (await q1(`select leader from co3_alliances where id = ${aid}`)) === B, null);
// 対抗戦
const q0 = await q1(`select (date_trunc('quarter', (now() at time zone 'Asia/Tokyo'))::date)::text`);
await db.exec(`insert into co_rank_days (day, user_id, value, routes, fleet) values ('${q0}', '${B}', 10000, 1, 1), ('${q0}'::date + 1, '${B}', 12000, 1, 1)`);
cB = Number(await q1(`select cash from companies where user_id = '${B}'`));
check('対抗戦：1位の仲間に 20,000 と称号', Number(await q1(`select public.co3_ally_season_close('${q0}')`)) === 1 && Number(await q1(`select cash from companies where user_id = '${B}'`)) - cB === 20000
  && Number(await q1(`select count(*) from co3_awards where user_id = '${B}' and kind in ('ally_top3', 'ally_champ')`)) === 2, null);
check('2回締めても増えない', Number(await q1(`select public.co3_ally_season_close('${q0}')`)) === 0, null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
