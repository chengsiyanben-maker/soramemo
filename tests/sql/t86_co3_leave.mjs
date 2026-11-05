// エアライン経営 co-v3：退会した人がいたときの扱い（co3_leave_settle → auth.users を消す）
//   共同運航は終わりにして知らせる（ブロック買い取りの今月の残りは返す）・出資は返す・アライアンスのリーダーは引き継ぐ
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`set co3.season_day = '2026-05-20'`);
await db.exec(`update ops.flags set value = 'true' where key in ('game_released', 'co_v3')`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b', C = '00000000-0000-0000-0000-00000000000c',
  D = '00000000-0000-0000-0000-00000000000d', E = '00000000-0000-0000-0000-00000000000e';
await db.exec(`insert into auth.users (id) values ('${A}'), ('${B}'), ('${C}'), ('${D}'), ('${E}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const cash = async (u) => Number(await q1(`select cash from companies where user_id = '${u}'`));
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('HND','CTS','HIJ')`)).rows.map((r) => [r.iata, r.id]));
const hc = `${Math.min(ids.HND, ids.CTS)}-${Math.max(ids.HND, ids.CTS)}`, hh = `${Math.min(ids.HND, ids.HIJ)}-${Math.max(ids.HND, ids.HIJ)}`;

// 本物の便：羽田⇄新千歳 前の28日、毎日 片道10便ずつ
await db.exec(`insert into flight_history (svc_date, flight, dep, arr, std, sta, type)
  select (now() at time zone 'Asia/Tokyo')::date - d, 'JL' || (500 + i * 2 + s), case s when 0 then 'HND' else 'CTS' end, case s when 0 then 'CTS' else 'HND' end,
         now() - d * interval '1 day', now() - d * interval '1 day' + interval '90 minutes', 'B738'
    from generate_series(1, 28) d, generate_series(0, 9) i, generate_series(0, 1) s`);
await q1(`select public.co3_route_real_refresh()`);

// 5社：A は羽田⇄新千歳（退会する人）。B・C・D は羽田⇄広島、E は会社だけ
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no, airline) values
  ('${A}', ${ids.HND}, ${ids.CTS}, now() - interval '1 day', now() - interval '1 day' + interval '90 minutes', 819.6, 'JL501', 'JL'),
  ('${B}', ${ids.HND}, ${ids.HIJ}, now() - interval '1 day', now() - interval '1 day' + interval '80 minutes', 674, 'NH671', 'NH'),
  ('${C}', ${ids.HND}, ${ids.HIJ}, now() - interval '1 day', now() - interval '1 day' + interval '80 minutes', 674, 'NH671', 'NH'),
  ('${D}', ${ids.HND}, ${ids.HIJ}, now() - interval '1 day', now() - interval '1 day' + interval '80 minutes', 674, 'NH671', 'NH')`);
for (const u of [A, B, C, D, E]) {
  await db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${u}', ${ids.HND}, 35.55, 139.78, 10, now())`);
  await as(u, `select public.co_state()`);
}
await db.exec(`update companies set rating = 5, safety = 'low', satisfaction = 60, cash = 500000, policy = 'fsc';
  insert into aircraft (user_id, type, reg, route_key, paid, bought_at) values
    ('${A}', 'nb', 'JA70AA', '${hc}', 20000, now()), ('${B}', 'nb', 'JA77BB', '${hh}', 20000, now()),
    ('${C}', 'nb', 'JA77CC', '${hh}', 30000, now()), ('${D}', 'nb', 'JA77DD', '${hh}', 20000, now())`);

check('アプリからは呼べない', String(await as(B, `select public.co3_leave_settle('${A}')`)).startsWith('ERROR'), null);
check('会社のない人は何もしない', (await q1(`select public.co3_leave_settle('00000000-0000-0000-0000-0000000000ff')`)).company === false, null);

// アライアンス：A がリーダー、B・C が仲間
const aid = Number(await q1(`insert into co3_alliances (name, leader) values ('みなみの空連合', '${A}') returning id`));
await db.exec(`insert into co3_alliance_members (user_id, alliance_id) values ('${A}', ${aid}), ('${B}', ${aid}), ('${C}', ${aid})`);
// 共同運航：B が A の羽田⇄新千歳をブロック買い取り（今月分を払った）、C が A の路線をフリーセール、A が D の路線をフリーセール、E の申し込みは保留
const rev = Number(await q1(`select public.co3_op_revenue('${A}', '${hc}')`));
check('A の路線に収益がある', rev > 0, rev);
const m = await q1(`select date_trunc('month', (now() at time zone 'Asia/Tokyo'))::date::text`);
const csB = Number(await q1(`insert into co3_codeshares (op_id, seller_id, route_key, kind, status, active_at, paid_month) values ('${A}', '${B}', '${hc}', 'block', 'active', now(), '${m}') returning id`));
await db.exec(`insert into co3_codeshares (op_id, seller_id, route_key, kind, status, active_at) values ('${A}', '${C}', '${hc}', 'free', 'active', now()), ('${D}', '${A}', '${hh}', 'free', 'active', now());
  insert into co3_codeshares (op_id, seller_id, route_key, kind) values ('${A}', '${E}', '${hc}', 'free')`);
// 出資：C → A（10%・40,000）、A → D（5%・10,000）、E → A は申し込みだけ
await db.exec(`insert into co3_invest (investor, target, amount, pct, status, accepted_at) values ('${C}', '${A}', 40000, 0.1, 'active', now() - interval '3 days'), ('${A}', '${D}', 10000, 0.05, 'active', now() - interval '3 days');
  insert into co3_invest (investor, target, amount) values ('${E}', '${A}', 5000)`);
// みんな 2時間前に締めたことにする（退会の前に、相手の稼ぎを締めるかを見る）
await db.exec(`update companies set last_collect = now() - interval '2 hours'`);

const ratio = Number(await q1(`select co3.month_left_ratio()`));
const revNow = Number(await q1(`select public.co3_op_revenue('${A}', '${hc}')`));
const vA = Number(await q1(`select public.co_value('${A}')`));
const expectRefund = Math.ceil(revNow * 5 * ratio), expectBack = Math.max(40000, Math.floor(vA * 0.1));
const pendB = Number(await q1(`select floor(public.co_daily('${B}') * 2 / 24.0)`));
const c0 = { B: await cash(B), C: await cash(C), D: await cash(D) };
const r = await q1(`select public.co3_leave_settle('${A}')`);
check('結果：共同運航4件・出資3件（申し込みも数える）', r.company === true && r.codeshares === 4 && r.invest === 3, r);
check('月の残りの割合は 0〜1', ratio > 0 && ratio <= 1, ratio);

// 共同運航
check('共同運航はすべて終わる', Number(await q1(`select count(*) from co3_codeshares where '${A}' in (op_id, seller_id) and status <> 'ended'`)) === 0, null);
check('ブロック買い取り：今月の残りを返す', r.refund === expectRefund && expectRefund > 0, { r: r.refund, expectRefund });
check('B の資金：それまでの稼ぎ＋返金', Math.abs((await cash(B)) - c0.B - expectRefund - pendB) <= 3, { d: (await cash(B)) - c0.B, expectRefund, pendB });
const nB = (await db.query(`select kind, title, meta from co3_news where user_id = '${B}' and ref = 'leave-cs-${csB}'`)).rows[0];
check('B に知らせる（相手の名前は書かない）', nB && nB.title.includes('共同運航が終わりました') && nB.meta.includes(String(expectRefund)) && !nB.title.includes('Airline'), nB);
check('ニュースの種類：表の決まりに partner が足されるまでは event', nB && nB.kind === 'event', nB);
check('D（運航会社）にも知らせる', Number(await q1(`select count(*) from co3_news where user_id = '${D}' and title like '%共同運航が終わりました%'`)) === 1, null);
check('保留の申し込みは知らせない', Number(await q1(`select count(*) from co3_news where user_id = '${E}'`)) === 0, null);

// 出資
const iC = (await db.query(`select status, returned from co3_invest where investor = '${C}'`)).rows[0];
check('C の出資は返る（出した額と価値×割合の大きいほう）', iC.status === 'withdrawn' && Number(iC.returned) === expectBack && r.invest_back === expectBack, { iC, expectBack });
check('C の資金が増える', (await cash(C)) - c0.C >= expectBack, { d: (await cash(C)) - c0.C, expectBack });
check('A から D への出資は返さない（D のお金のまま）', (await q1(`select returned from co3_invest where investor = '${A}'`)) == 0 && (await cash(D)) >= c0.D, null);
check('E の申し込みは断ったことに', (await q1(`select status from co3_invest where investor = '${E}'`)) === 'declined', null);
check('C・D に出資の知らせ', Number(await q1(`select count(*) from co3_news where user_id in ('${C}', '${D}') and title like '出資していた会社が退会%'`)) === 2, null);

// アライアンス
const al = (await db.query(`select leader from co3_alliances where id = ${aid}`)).rows[0];
const vB = Number(await q1(`select public.co_value('${B}')`)), vC = Number(await q1(`select public.co_value('${C}')`));
check('アライアンスは残る', !!al, al);
check('リーダーは価値のいちばん高い仲間に', al && al.leader === (vC >= vB ? C : B), { al, vB, vC });
check('新しいリーダーに知らせる', Number(await q1(`select count(*) from co3_news where user_id = '${al?.leader}' and title like '%リーダーを引き継ぎました%'`)) === 1, null);
check('仲間は2社', Number(await q1(`select count(*) from co3_alliance_members where alliance_id = ${aid}`)) === 2, null);

// 2回呼んでもお金は増えない
const c1 = { B: await cash(B), C: await cash(C) };
const r2 = await q1(`select public.co3_leave_settle('${A}')`);
check('2回目は何もしない', r2.codeshares === 0 && r2.invest === 0 && r2.alliance === null && (await cash(B)) === c1.B && (await cash(C)) === c1.C, r2);

// アカウントを消す（cascade）
await db.exec(`delete from auth.users where id = '${A}'`);
check('消したあともアライアンスは残る', Number(await q1(`select count(*) from co3_alliance_members where alliance_id = ${aid}`)) === 2, null);
check('残った人の状態が読める', (await as(B, `select public.co_state()`)).ally?.members?.length === 2, null);
check('残った人のニュースは残る', Number(await q1(`select count(*) from co3_news where user_id = '${B}' and ref like 'leave-%'`)) === 1, null);

// ひとりだけのアライアンスのリーダーが退会：消える
const aid2 = Number(await q1(`insert into co3_alliances (name, leader) values ('ひとりの空', '${E}') returning id`));
await db.exec(`insert into co3_alliance_members (user_id, alliance_id) values ('${E}', ${aid2})`);
const r3 = await q1(`select public.co3_leave_settle('${E}')`);
check('ひとりのアライアンスは消える', r3.new_leader === false && Number(await q1(`select count(*) from co3_alliances where id = ${aid2}`)) === 0, r3);

// ニュースの種類に partner が足されたら partner で書く（データ担当の変更のあと）
await db.exec(`alter table co3_news drop constraint co3_news_kind_check;
  alter table co3_news add constraint co3_news_kind_check check (kind in ('route', 'god', 'rating', 'value', 'slots', 'event', 'partner'))`);
await db.exec(`insert into co3_codeshares (op_id, seller_id, route_key, kind, status, active_at) values ('${D}', '${B}', '${hh}', 'free', 'active', now())`);
await q1(`select public.co3_leave_settle('${D}')`);
check('種類が足されたら partner', (await q1(`select kind from co3_news where user_id = '${B}' and title like '%共同運航が終わりました%' order by id desc limit 1`)) === 'partner', null);
check('満足度の初期値は 40 のまま', Number(await q1(`select column_default from information_schema.columns where table_name = 'companies' and column_name = 'satisfaction'`)) === 40, null);

console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
