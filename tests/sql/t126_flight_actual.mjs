// フライトの実際の出発・到着（移行 187・11/20 PM「空の上」を実際の飛行時間に）
//   1. 本人以外は読めない・利用者は書けない（新しい列も今の flights の決まりのまま）
//   2. 取り先の順：毎日の記録の ODPT → 機体の位置の推定（adsb）→ 時刻表。共同運航の便名・0つきの便名でも当たる
//   3. 未来の時刻は入らない（関数でも、直接書いても）。欠航の便・区間ちがい・時間ちがいは入れない
//   4. さかのぼり：400日前までの記録から入る・何度呼んでも同じ・確かな取り先に書き直す
//   5. 航跡のさかのぼり：flight_tracks のある便だけ返す
//   6. 権限：関数は service_role だけ
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.sql')).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const one = async (sql, p) => (await db.query(sql, p)).rows[0];
const as = async (role, sql, sub) => { try { await db.exec(`set role ${role}`); if (sub) await db.exec(`select set_config('request.jwt.claim.sub', '${sub}', false)`);
  const r = await db.query(sql); return r.rows; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec(`reset role; select set_config('request.jwt.claim.sub', '', false)`); } };

const U1 = '00000000-0000-0000-0000-000000000001', U2 = '00000000-0000-0000-0000-000000000002';
await db.exec(`insert into auth.users (id) values ('${U1}'), ('${U2}')`);
const ap = (c) => `(select id from public.airports where iata = '${c}' order by id limit 1)`;
// フライト（チェックインの時刻）。h は「いま」から何時間前か
const fl = async (user, no, dep, arr, depH, arrH) => (await one(`insert into public.flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no)
  values ($1, ${ap(dep)}, ${ap(arr)}, now() - make_interval(mins => $2::int), now() - make_interval(mins => $3::int), 800, $4) returning id`, [user, Math.round(depH * 60), Math.round(arrH * 60), no])).id;
const hist = (o) => db.query(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, atd, ata, atd_src, ata_src, cancelled, also)
  values (((now() - make_interval(mins => $1::int)) at time zone 'Asia/Tokyo')::date, $2, $3, $4, now() - make_interval(mins => $1::int), now() - make_interval(mins => $5::int),
          case when $6::int is null then null else now() - make_interval(mins => $6::int) end, case when $7::int is null then null else now() - make_interval(mins => $7::int) end,
          $8, $9, $10, $11::text[])`,
  [Math.round(o.std * 60), o.flight, o.dep, o.arr, Math.round(o.sta * 60), o.atd == null ? null : Math.round(o.atd * 60), o.ata == null ? null : Math.round(o.ata * 60),
   o.atd_src ?? null, o.ata_src ?? null, o.cancelled ?? false, o.also ?? []]);
const act = (id) => one(`select act_src, round(extract(epoch from now() - act_dep_at) / 60) dep_min, round(extract(epoch from now() - act_arr_at) / 60) arr_min from public.flights where id = $1`, [id]);
const fill = async (days = 3) => (await one(`select public.flights_fill_actual($1, 2000) r`, [days])).r;

// --- 便と記録 ---
// a: ODPT の実績（出発・到着とも）。チェックインは 5h前→2.5h前、定刻 4.5h前→3h前、実際 4.4h前→3.1h前
const a = await fl(U1, 'JL501', 'HND', 'CTS', 5, 2.5);
await hist({ flight: 'JL0501', dep: 'HND', arr: 'CTS', std: 4.5, sta: 3, atd: 4.4, ata: 3.1, atd_src: 'odpt', ata_src: 'odpt' });
// b: 共同運航（利用者は NH の便名、記録は JL の便。also に NH）。到着は adsb の推定
const b = await fl(U1, 'NH5501', 'HND', 'ITM', 10, 7);
await hist({ flight: 'JL101', dep: 'HND', arr: 'ITM', std: 9.5, sta: 8.3, atd: 9.4, ata: 8.2, atd_src: 'odpt', ata_src: 'adsb', also: ['NH5501'] });
// c: 実績が片方だけ → 時刻表の定刻（まぜない）
const c = await fl(U1, 'JL903', 'HND', 'OKA', 30, 25);
await hist({ flight: 'JL903', dep: 'HND', arr: 'OKA', std: 29, sta: 26, atd: 28.9, ata: null, atd_src: 'odpt' });
// d: 欠航の便だけ → 入れない
const d = await fl(U1, 'JL505', 'HND', 'CTS', 50, 46);
await hist({ flight: 'JL505', dep: 'HND', arr: 'CTS', std: 49, sta: 47.5, cancelled: true });
// e: 区間ちがい（記録は HND→FUK）→ 入れない
const e = await fl(U1, 'JL305', 'HND', 'KOJ', 60, 57);
await hist({ flight: 'JL305', dep: 'HND', arr: 'FUK', std: 59, sta: 57.5, atd: 58.9, ata: 57.6, atd_src: 'odpt', ata_src: 'odpt' });
// f: 時間ちがい（定刻がチェックインの1日前）→ 入れない
const f = await fl(U1, 'JL307', 'HND', 'FUK', 30, 27);
await hist({ flight: 'JL307', dep: 'HND', arr: 'FUK', std: 54, sta: 52, atd: 53.9, ata: 52.1, atd_src: 'odpt', ata_src: 'odpt' });
// g: さかのぼり（300日前）
const g = await fl(U2, 'NH17', 'HND', 'ITM', 300 * 24 + 5, 300 * 24 + 2);
await hist({ flight: 'NH017', dep: 'HND', arr: 'ITM', std: 300 * 24 + 4.5, sta: 300 * 24 + 3.3, atd: 300 * 24 + 4.4, ata: 300 * 24 + 3.2, atd_src: 'odpt', ata_src: 'odpt' });
// h: 時刻表（flight_schedule）だけにある、ODPT の実際の時刻つき（毎日の記録はまだ）
const h = await fl(U2, 'NH241', 'HND', 'FUK', 4, 1);
await db.query(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, atd, ata, source)
  values (((now() - interval '3.5 hours') at time zone 'Asia/Tokyo')::date, 'NH241', 'HND', 'FUK', now() - interval '3.5 hours', now() - interval '1.5 hours',
          now() - interval '3.4 hours', now() - interval '1.6 hours', 't')`);
// i: 時刻表だけ・到着の定刻がまだ来ていない（早くチェックインした）→ 入れない
const i = await fl(U2, 'NH243', 'HND', 'FUK', 2, 0.1);
await db.query(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source)
  values (((now() - interval '1.5 hours') at time zone 'Asia/Tokyo')::date, 'NH243', 'HND', 'FUK', now() - interval '1.5 hours', now() + interval '20 minutes', 't')`);

// --- 1回目（3日分）---
let r = await fill(3);
let x = await act(a);
check('2 ODPT の実績が入る', x.act_src === 'odpt' && Number(x.dep_min) === 264 && Number(x.arr_min) === 186, x);
x = await act(b);
check('2 共同運航の便名で当たり、片方が推定なら adsb', x.act_src === 'adsb' && Number(x.dep_min) === 564 && Number(x.arr_min) === 492, x);
x = await act(c);
check('2 実績が片方だけなら時刻表の定刻（まぜない）', x.act_src === 'timetable' && Number(x.dep_min) === 1740 && Number(x.arr_min) === 1560, x);
x = await act(h);
check('2 毎日の記録がまだでも、時刻表の ODPT の実績で入る', x.act_src === 'odpt' && Number(x.dep_min) === 204 && Number(x.arr_min) === 96, x);
check('3 欠航の便は入れない', (await act(d)).act_src === null);
check('3 区間ちがいは入れない', (await act(e)).act_src === null);
check('3 時間ちがいは入れない', (await act(f)).act_src === null);
check('3 到着の定刻がまだ来ていない便は入れない', (await act(i)).act_src === null);
check('4 3日分では300日前は入らない', (await act(g)).act_src === null);
check('4 返す数', r.updated === 4 && r.odpt === 2 && r.adsb === 1 && r.timetable === 1, r);

// --- さかのぼり（400日）・2回目は書き直さない ---
r = await fill(400);
x = await act(g);
check('4 400日分のさかのぼりで300日前も入る', x.act_src === 'odpt', x);
check('4 さかのぼりの数は1（入っていた便は書き直さない）', r.updated === 1, r);
r = await fill(400);
check('4 何度呼んでも同じ（書き直し0）', r.updated === 0, r);

// --- 確かな取り先への書き直し ---
await db.exec(`update public.flight_history set ata = atd + interval '2 hours', ata_src = 'odpt' where flight = 'JL903'`);
r = await fill(3);
x = await act(c);
check('4 実績がそろったら時刻表から ODPT に書き直す', x.act_src === 'odpt' && Number(x.arr_min) === 1614, { x, r });
await db.exec(`update public.flight_history set ata_src = 'odpt' where flight = 'JL101'`);
r = await fill(3);
check('4 adsb → odpt に書き直す', (await act(b)).act_src === 'odpt', r);

// --- 未来の時刻は直接書いても入らない・組がそろわないものは入らない ---
await db.exec(`update public.flights set act_dep_at = now() + interval '1 hour', act_arr_at = now() + interval '2 hours', act_src = 'odpt' where id = ${d}`);
x = await act(d);
check('3 未来の時刻は守り（trigger）で空になる', x.act_src === null, x);
let err = '';
try { await db.exec(`update public.flights set act_dep_at = now() - interval '2 hours' where id = ${d}`); } catch (e2) { err = e2.message; }
check('3 片方だけは入らない（組の決まり）', err.includes('flights_act_pair'), err);
err = '';
try { await db.exec(`update public.flights set act_dep_at = now() - interval '2 hours', act_arr_at = now() - interval '3 hours', act_src = 'odpt' where id = ${d}`); } catch (e2) { err = e2.message; }
check('3 到着が出発より前は入らない', err.includes('flights_act_pair'), err);

// --- 1. 読み書きの決まり ---
let rows = await as('authenticated', `select id, act_src from public.flights order by id`, U1);
check('1 本人は自分の便の実際の時刻を読める', Array.isArray(rows) && rows.length === 6 && rows.some((q) => q.id === a && q.act_src === 'odpt'), rows);
rows = await as('authenticated', `select id from public.flights where id in (${g}, ${h})`, U1);
check('1 ほかの人の便は読めない', Array.isArray(rows) && rows.length === 0, rows);
rows = await as('anon', `select id from public.flights`);
check('1 ログインしていない人は読めない', !Array.isArray(rows) || rows.length === 0, rows);
rows = await as('authenticated', `update public.flights set act_dep_at = now() - interval '5 hours', act_arr_at = now() - interval '4 hours', act_src = 'odpt' where id = ${d}`, U1);
check('1 本人も書けない', String(rows).startsWith('ERROR'), rows);

// --- 5. 航跡のさかのぼり ---
await db.exec(`insert into public.flight_tracks (svc_date, flight, dep, pts, alts)
  select svc_date, flight, dep, '_p~iF~ps|U_ulLnnqC_mqNvxq\`@', '{0,100,0}' from public.flight_history where flight in ('JL0501', 'JL101')`);
rows = (await db.query(`select id from public.flights_track_todo(300) order by id`)).rows.map((q) => q.id);
check('5 航跡のある便だけ返す（共同運航の便名でも）', JSON.stringify(rows) === JSON.stringify([a, b].sort((p, q) => p - q)), rows);
await db.exec(`update public.flights set track = '[[35.5,139.7],[42.7,141.6]]'::jsonb where id = ${a}`);
rows = (await db.query(`select id from public.flights_track_todo(300)`)).rows.map((q) => q.id);
check('5 航跡の入った便は返さない', JSON.stringify(rows) === JSON.stringify([b]), rows);

// --- 6. 権限 ---
for (const fn of ['public.flights_fill_actual(3, 10)', 'public.flights_track_todo(10)']) {
  check(`6 anon は ${fn.split('(')[0]} を実行できない`, String(await as('anon', `select ${fn}`)).startsWith('ERROR'));
  check(`6 authenticated は ${fn.split('(')[0]} を実行できない`, String(await as('authenticated', `select ${fn}`, U1)).startsWith('ERROR'));
}
const cfg = (await one(`select proconfig from pg_proc where proname = 'flights_fill_actual'`)).proconfig ?? [];
check('6 時間の上限がある（statement_timeout・lock_timeout）', cfg.includes('statement_timeout=60s') && cfg.includes('lock_timeout=5s'), cfg);

if (bad) { console.log(`NG ${bad}件`); process.exit(1); }
console.log('すべて通過');
