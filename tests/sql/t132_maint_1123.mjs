// 定期の手入れ 11/23（移行 194）：関数の中の「表を全部読む文」を索引で引ける形にする
//   1. airport_day：日付の絞り込みを時刻の幅に直しても、日本時間の0時の前後の行の数え方が前と同じか。(iata, at) の索引で引けるか
//   2. flights_track_todo_dep：毎晩の flights_track_todo・archive_user_flights の形で索引が使われ、前と同じ便を返すか
//   3. rot_predict：本文は1か所の置き換えだけで、設定・権限は同じ。0時の前後の特別塗装機の予定で前と同じ答えか
//   4. 表・列・RLS・権限は変わらず、索引は1本増えるだけ。2回流しても壊れない
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const NEW = '20261123000194_maint_1123.sql';
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const rows = async (sql, p) => (await db.query(sql, p)).rows;
const SHAPE = `select (select json_agg(x order by x) from (select table_name || '.' || column_name || ':' || data_type x from information_schema.columns where table_schema = 'public') s) cols,
  (select json_agg(x order by x) from (select tablename || ':' || policyname || ':' || qual x from pg_policies where schemaname = 'public') s) pol,
  (select json_agg(x order by x) from (select table_name || ':' || grantee || ':' || privilege_type x from information_schema.role_table_grants where table_schema = 'public') s) grants,
  (select count(*)::int from pg_indexes where schemaname = 'public') nidx`;
const FN = `select p.proname, pg_get_functiondef(p.oid) def, p.proconfig, p.proacl::text acl, p.prosecdef
  from pg_proc p where p.oid in ('public.airport_day(text, date)'::regprocedure, 'public.rot_predict(text, text, date, text, text, time, int)'::regprocedure) order by 1`;

for (const f of files) if (f < NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));

// 日本時間の0時の前後に行を置く（11/22 23:59:59.999・11/23 0:00・11/23 23:59:59・11/24 0:00）
const EDGES = ['2026-11-22 23:59:59.999+09', '2026-11-23 00:00:00+09', '2026-11-23 12:00:00+09', '2026-11-23 23:59:59.999+09', '2026-11-24 00:00:00+09', '2026-11-22 15:00:00+00'];
let k = 0;
for (const iata of ['HND', 'KMQ']) for (const src of ['live', 'track']) for (const at of EDGES) for (const dirn of ['arr', 'dep']) {
  k++;
  await db.query(`insert into public.rwy_samples (iata, at, callsign, rwy, dir, src) values ($1, $2, $3, $4, $5, $6)`, [iata, at, 'CS' + k, k % 2 ? '34L' : '16R', dirn, src]);
}
for (const iata of ['HND', 'KMQ']) for (const at of EDGES) await db.query(`insert into public.ga_events (iata, at, hex, low_ft) values ($1, $2, $3, 800)`, [iata, at, 'h' + (k++)]);
const DAYS = ['2026-11-22', '2026-11-23', '2026-11-24'];
const dayOut = async () => { const o = []; for (const iata of ['HND', 'KMQ', 'NRT']) for (const d of DAYS) o.push((await rows(`select public.airport_day($1, $2::date) v`, [iata, d]))[0].v); return o; };

// 特別塗装機の予定：11/23 0:00 ちょうど と 11/22 23:59 の便（日本時間）
await db.exec(`insert into public.livery_sightings (reg, name, airline, lat, lon, src) values ('JA8001', 'テスト塗装', 'ANA', 35, 139, 'test')`);
const PLANS = [['NH101', 'HND', 'ITM', '2026-11-22 23:59:00+09'], ['NH103', 'HND', 'CTS', '2026-11-23 00:00:00+09'], ['NH105', 'CTS', 'HND', '2026-11-23 23:59:59+09'], ['NH107', 'HND', 'FUK', '2026-11-24 00:00:00+09']];
for (const [fl, dep, arr, std] of PLANS) {
  const id = (await rows(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values ((($4)::timestamptz at time zone 'Asia/Tokyo')::date, $1, $2, $3, $4, ($4)::timestamptz + interval '90 minutes', 'test') returning id`, [fl, dep, arr, std]))[0].id;
  await db.query(`insert into public.livery_plans (schedule_id, flight, dep, arr, std, livery) values ($1, $2, $3, $4, $5, 'テスト塗装')`, [id, fl, dep, arr, std]);
}
const rotOut = async () => { const o = []; for (const d of DAYS) for (const a of [null, 'HND', 'CTS']) o.push((await rows(`select public.rot_predict('learn', 'JA8001', $1::date, 'ANA9', $2, null, 4) v`, [d, a]))[0].v); return o; };

// 毎晩の flights_track_todo・archive_user_flights と同じ形
const uid = '00000000-0000-0000-0000-000000000001';
await db.exec(`insert into auth.users (id) values ('${uid}')`);
const ap = (await rows(`select id from public.airports where iata in ('HND', 'ITM') order by iata`)).map(r => r.id);
const TODO = `select f.id from public.flights f where f.track is null and f.flight_no is not null and f.dep_at >= now() - interval '32 days' order by f.dep_at desc limit 300`;
const ARCH = `select f.id from public.flights f where f.track is null and f.flight_no is not null and f.dep_at >= ('2026-11-22'::date::timestamp at time zone 'Asia/Tokyo') and f.dep_at < (('2026-11-22'::date + 1)::timestamp at time zone 'Asia/Tokyo') order by 1`;
const flOut = async () => [(await rows(TODO)).map(r => r.id), (await rows(ARCH)).map(r => r.id)];
if (ap.length === 2) {
  await db.exec(`set session_replication_role = replica`); // 便の入力の確かめ（チェックインの決まり）は今回の対象外なので外して入れる
  let n = 0;
  for (const [fno, track, dep] of [['NH1', null, `now() - interval '1 day'`], [null, null, `now() - interval '2 days'`], ['NH3', `'[[35,139],[34,135]]'::jsonb`, `now() - interval '3 days'`], ['NH5', null, `now() - interval '40 days'`], ['NH7', null, `'2026-11-22 10:00+09'::timestamptz`], ['NH9', null, `'2026-11-23 00:00+09'::timestamptz`]]) {
    n++;
    await db.exec(`insert into public.flights (user_id, from_airport, to_airport, distance_km, dep_at, arr_at, flight_no, track, status) values ('${uid}', '${ap[0]}', '${ap[1]}', 400, ${dep}, ${dep} + interval '1 hour', ${fno ? `'${fno}'` : 'null'}, ${track ?? 'null'}, 'verified')`);
  }
  await db.exec(`set session_replication_role = origin`);
}

const before = (await rows(SHAPE))[0];
const fnBefore = await rows(FN);
const dayBefore = await dayOut(), rotBefore = await rotOut(), flBefore = await flOut();

await db.exec(fs.readFileSync(dir + NEW, 'utf8'));
const after = (await rows(SHAPE))[0];
const fnAfter = await rows(FN);

// 1. airport_day
const dayAfter = await dayOut();
check('1 airport_day の答えが前と同じ（0時の前後・羽田の live だけ・KMQ・行のない NRT）', JSON.stringify(dayAfter) === JSON.stringify(dayBefore), { dayBefore, dayAfter });
const hnd23 = dayAfter[1];
check('1 羽田の11/23は live の4行×arr/dep を数える（0:00 ちょうど2行は入り、前の日の 23:59:59.999 と 11/24 0:00 は入らない。track は数えない）', hnd23.rwy && Object.values(hnd23.rwy).reduce((a, b) => a + b, 0) === 8 && hnd23.ga === 4, hnd23);
const daySrc = fnAfter.find(r => r.proname === 'airport_day').def;
check('1 airport_day に「::date = p_day」が残っていない', !/::date\s*=\s*p_day/.test(daySrc), daySrc);
await db.exec(`set enable_seqscan = off`);
const planRwy = (await rows(`explain select count(*) from public.rwy_samples where iata = 'HND' and (src = 'live' or iata not in ('HND', 'NRT')) and at >= ('2026-11-23'::date::timestamp at time zone 'Asia/Tokyo') and at < (('2026-11-23'::date + 1)::timestamp at time zone 'Asia/Tokyo')`)).map(r => r['QUERY PLAN']).join('\n');
check('1 rwy_samples を (iata, at) の索引で時刻の幅まで引ける', /rwy_samples_iata_at/.test(planRwy) && /Index Cond:.*at >=/.test(planRwy.replace(/\n/g, ' ')), planRwy);
const planGa = (await rows(`explain select count(*) from public.ga_events where iata = 'HND' and at >= ('2026-11-23'::date::timestamp at time zone 'Asia/Tokyo') and at < (('2026-11-23'::date + 1)::timestamp at time zone 'Asia/Tokyo')`)).map(r => r['QUERY PLAN']).join('\n');
check('1 ga_events を (iata, at) の索引で引ける', /ga_events_iata_at/.test(planGa), planGa);

// 2. flights の部分索引
const flAfter = await flOut();
check('2 毎晩の2つの形が前と同じ便を返す', ap.length === 2 && JSON.stringify(flAfter) === JSON.stringify(flBefore) && flAfter[0].length === 3 && flAfter[1].includes(5) && !flAfter[1].includes(6), { flBefore, flAfter });
const planTodo = (await rows(`explain ${TODO}`)).map(r => r['QUERY PLAN']).join('\n');
check('2 flights_track_todo の形で flights_track_todo_dep を使う', /flights_track_todo_dep/.test(planTodo), planTodo);
const planArch = (await rows(`explain ${ARCH}`)).map(r => r['QUERY PLAN']).join('\n');
check('2 archive_user_flights の形で flights_track_todo_dep を使う', /flights_track_todo_dep/.test(planArch), planArch);
await db.exec(`reset enable_seqscan`);
const idx = (await rows(`select pg_get_indexdef(indexrelid) d from pg_index where indexrelid = 'public.flights_track_todo_dep'::regclass`))[0]?.d ?? '';
check('2 索引は航跡のない・便名のある便だけ（部分索引）', /WHERE \(\(track IS NULL\) AND \(flight_no IS NOT NULL\)\)/.test(idx), idx);

// 3. rot_predict
const OLD = `(lp.std at time zone 'Asia/Tokyo')::date = p_day`;
const NEWP = `lp.std >= (p_day::timestamp at time zone 'Asia/Tokyo') and lp.std < ((p_day + 1)::timestamp at time zone 'Asia/Tokyo')`;
const rb = fnBefore.find(r => r.proname === 'rot_predict'), ra = fnAfter.find(r => r.proname === 'rot_predict');
check('3 rot_predict の本文は1か所の置き換えだけ', rb.def.split(OLD).length === 2 && ra.def === rb.def.replace(OLD, NEWP), { len: [rb.def.length, ra.def.length] });
check('3 rot_predict の設定・権限・security definer は同じ', JSON.stringify([ra.proconfig, ra.acl, ra.prosecdef]) === JSON.stringify([rb.proconfig, rb.acl, rb.prosecdef]), [rb, ra].map(r => [r.proconfig, r.acl, r.prosecdef]));
const rotAfter = await rotOut();
check('3 rot_predict の答えが前と同じ（0時の前後の予定）', JSON.stringify(rotAfter) === JSON.stringify(rotBefore), { rotBefore, rotAfter });
check('3 11/23 は 0:00 の NH103 から（前の日の 23:59 と次の日の 0:00 は入らない）', rotAfter[3]?.[0]?.callsign === 'ANA103' && rotAfter[3].every(s => !['ANA101', 'ANA107'].includes(s.callsign)), rotAfter[3]);
const da = fnAfter.find(r => r.proname === 'airport_day'), db0 = fnBefore.find(r => r.proname === 'airport_day');
check('3 airport_day の設定・権限・security definer は同じ', JSON.stringify([da.proconfig, da.acl, da.prosecdef]) === JSON.stringify([db0.proconfig, db0.acl, db0.prosecdef]), [db0, da].map(r => [r.proconfig, r.acl]));

// 4. 形
check('4 列・RLS・表の権限は同じ', JSON.stringify([after.cols, after.pol, after.grants]) === JSON.stringify([before.cols, before.pol, before.grants]));
check('4 索引は1本だけ増える', after.nidx === before.nidx + 1, [before.nidx, after.nidx]);
let again = true; try { await db.exec(fs.readFileSync(dir + NEW, 'utf8')); } catch (e) { again = e.message; }
const fnAgain = await rows(FN);
check('4 2回流しても壊れず、関数も同じ', again === true && JSON.stringify(fnAgain) === JSON.stringify(fnAfter), again);
const lt = (await rows(`select current_setting('lock_timeout') v`))[0].v;
check('4 移行のあと lock_timeout は元に戻る', lt === '0', lt);

console.log(bad ? `NG ${bad}` : 'ALL OK');
process.exit(bad ? 1 : 0);
