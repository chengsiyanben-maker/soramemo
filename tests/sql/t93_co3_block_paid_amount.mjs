// エアライン経営 co-v3：ブロック買い取りで払った額（paid_amount）を残し、退会のときの返金をその額から計算する
//   払う（co3_cs_pay_block）と paid_amount に払った額が入る・返金は払った額 × 月の残り・払った額がない行は前のとおりいまの収益から
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

const m = await q1(`select date_trunc('month', (now() at time zone 'Asia/Tokyo'))::date::text`);
const rev = Number(await q1(`select public.co3_op_revenue('${A}', '${hc}')`));
check('A の路線に収益がある', rev > 0, rev);
// B が A の羽田⇄新千歳をブロック買い取り（まだ払っていない）
const csB = Number(await q1(`insert into co3_codeshares (op_id, seller_id, route_key, kind, status, active_at) values ('${A}', '${B}', '${hc}', 'block', 'active', now()) returning id`));
const b0 = await cash(B), a0 = await cash(A);
const amt = Math.ceil(Number(await q1(`select public.co3_op_revenue('${A}', '${hc}')`)) * 5);
check('払える', (await q1(`select public.co3_cs_pay_block(${csB})`)) === true, null);
const row = (await db.query(`select paid_month::text pm, paid_amount from co3_codeshares where id = ${csB}`)).rows[0];
check('払った額を paid_amount に残す', Number(row.paid_amount) === amt && row.pm === m, { row, amt });
check('B から A へ払った額が動く', b0 - (await cash(B)) === amt && (await cash(A)) - a0 === amt, { dB: b0 - (await cash(B)), dA: (await cash(A)) - a0, amt });
check('アプリからは払えない', String(await as(B, `select public.co3_cs_pay_block(${csB})`)).startsWith('ERROR'), null);

// あとで収益が変わっても、返金は払った額から（払った額を 12,345 にして、いまの収益と違う数にする）
await db.exec(`update co3_codeshares set paid_amount = 12345 where id = ${csB}`);
// C も A の路線をブロック買い取りしたが、払った額の記録がない（前からある行）
const csC = Number(await q1(`insert into co3_codeshares (op_id, seller_id, route_key, kind, status, active_at, paid_month) values ('${A}', '${C}', '${hc}', 'block', 'active', now(), '${m}') returning id`));
const ratio = Number(await q1(`select co3.month_left_ratio()`));
const revNow = Number(await q1(`select public.co3_op_revenue('${A}', '${hc}')`));
const expB = Math.ceil(12345 * ratio), expC = Math.ceil(revNow * 5 * ratio);
const r = await q1(`select public.co3_leave_settle('${A}')`);
check('返金の合計＝払った額から＋いまの収益から', r.refund === expB + expC && expB !== expC, { r: r.refund, expB, expC });
const nB = (await db.query(`select meta from co3_news where user_id = '${B}' and ref = 'leave-cs-${csB}'`)).rows[0];
const nC = (await db.query(`select meta from co3_news where user_id = '${C}' and ref = 'leave-cs-${csC}'`)).rows[0];
check('B には払った額 × 月の残りを返す', nB && nB.meta.includes(String(expB)), { nB, expB });
check('C（払った額がない）は、前のとおりいまの収益から', nC && nC.meta.includes(String(expC)), { nC, expC });
check('満足度の初期値は 40 のまま', Number(await q1(`select column_default from information_schema.columns where table_name = 'companies' and column_name = 'satisfaction'`)) === 40, null);

console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
