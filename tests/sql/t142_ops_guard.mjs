// 裏側の守り（移行 203）
//   1. 死活の記録：ops.data_health() が取り込みごとの ok を返し、止まったものだけ ng。watch は ng のときだけ1行・同じ中身は6時間に1回。admin_data_health は管理者だけ
//   2. timetable_replace：空・極端に少ない返事では前の時刻表を残す（例外）。ふつうの入れ替えは前と同じ
//      foreign_usual_build：作り直しが前の半分未満なら前のまま。ふつうは作り直す
//   3. 表・列・RLS・表の権限・関数の権限は変わらない。全部読みしない。2回流しても壊れない
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const NEW = '20261126000203_ops_guard.sql';
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const rows = async (sql, p) => (await db.query(sql, p)).rows;
const one = async (sql, p) => Object.values((await rows(sql, p))[0] ?? {})[0];
const tryq = async (sql) => { try { return await one(sql); } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } };
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); return await one(sql); } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const SHAPE = `select (select json_agg(x order by x) from (select table_schema || '.' || table_name || '.' || column_name || ':' || data_type x from information_schema.columns where table_schema in ('public', 'ops')) s) cols,
  (select json_agg(x order by x) from (select tablename || ':' || policyname || ':' || coalesce(qual, '') || ':' || coalesce(with_check, '') x from pg_policies where schemaname in ('public', 'ops')) s) pol,
  (select json_agg(x order by x) from (select table_name || ':' || grantee || ':' || privilege_type x from information_schema.role_table_grants where table_schema in ('public', 'ops')) s) grants,
  (select json_agg(x order by x) from (select p.oid::regprocedure::text || ':' || coalesce(p.proacl::text, '') x from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname in ('public', 'ops') and p.proname not in ('data_health', 'data_health_watch', 'admin_data_health')) s) fnacl,
  (select count(*)::int from pg_indexes where schemaname in ('public', 'ops')) nidx`;

for (const f of files) if (f < NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const tt = (n, dep = 'HND', op = 'JAL') => JSON.stringify(Array.from({ length: n }, (_, i) => ({ operator: op, dep, arr: 'ITM', flight: 'JL' + (100 + i), days: 127,
  valid_from: '2026-10-25', valid_to: '2027-03-27', dep_time: '08:00', arr_time: '09:10' })));
// 前の形：空の返事で時刻表が消える（直す前の確かめ）
await db.query(`select public.timetable_replace('JAL', 'HND', $1::jsonb)`, [tt(30)]);
await db.query(`select public.timetable_replace('JAL', 'HND', '[]'::jsonb)`);
check('前：空の返事で時刻表が0行になっていた', await one(`select count(*)::int from public.timetable where operator = 'JAL' and dep = 'HND'`) === 0);
const before = (await rows(SHAPE))[0];

await db.exec(fs.readFileSync(dir + NEW, 'utf8'));
const after = (await rows(SHAPE))[0];
check('3 列・RLS・表の権限は同じ', JSON.stringify([after.cols, after.pol, after.grants]) === JSON.stringify([before.cols, before.pol, before.grants]));
check('3 ほかの関数の権限は同じ（timetable_replace・foreign_usual_build も）', JSON.stringify(after.fnacl) === JSON.stringify(before.fnacl));
check('3 索引は増えない', after.nidx === before.nidx, [before.nidx, after.nidx]);

// 2-1 時刻表
const cnt = () => one(`select count(*)::int from public.timetable where operator = 'JAL' and dep = 'HND'`);
check('2 はじめての取り込みは入る', await one(`select public.timetable_replace('JAL', 'HND', $1::jsonb)`, [tt(30)]) === 30 && await cnt() === 30);
check('2 空の返事は例外で、前の30行が残る', /kept previous timetable: 30 rows -> 0 rows/.test(await tryq(`select public.timetable_replace('JAL', 'HND', '[]'::jsonb)`)) && await cnt() === 30);
check('2 極端に少ない返事（30→10）も残す', /kept previous/.test(await tryq(`select public.timetable_replace('JAL', 'HND', '${tt(10)}'::jsonb)`)) && await cnt() === 30);
check('2 ふつうの減り（30→20）は入れ替える', await one(`select public.timetable_replace('JAL', 'HND', $1::jsonb)`, [tt(20)]) === 20 && await cnt() === 20);
check('2 ほかの空港・航空会社は巻き込まない', await one(`select public.timetable_replace('ANA', 'HND', $1::jsonb)`, [tt(5, 'HND', 'ANA')]) === 5 && await cnt() === 20);
check('2 前が少ない（5行）なら、2行への減りも入れ替える', await one(`select public.timetable_replace('ANA', 'HND', $1::jsonb)`, [tt(2, 'HND', 'ANA')]) === 2);
check('2 前が0行のときの空の返事はそのまま（0行）', await one(`select public.timetable_replace('JAL', 'ITM', '[]'::jsonb)`) === 0);
check('2 おかしな入力は今までどおり bad input', /bad input/.test(await tryq(`select public.timetable_replace('XXX', 'HND', '[]'::jsonb)`)));

// 2-2 いつもの時刻（種の日付と時刻は日本時間で作る。テストを流す所の時間帯（手元は日本・GitHub は UTC）に左右されないように）
await db.exec(`insert into public.foreign_legs (day, callsign, iata, dep_here, at)
  select d, 'BAW' || i, 'HND', 0, (d + time '10:00' + make_interval(mins => i)) at time zone 'Asia/Tokyo'
    from generate_series(0, 29) k, lateral (select (now() at time zone 'Asia/Tokyo')::date - 30 + k as d) x, generate_series(1, 10) i`);
const n1 = await one(`select public.foreign_usual_build()`);
const fu = () => one(`select count(*)::int from public.foreign_usual`);
check('2 いつもの時刻を作る', n1 >= 20 && await fu() === n1, [n1]);
await db.exec(`delete from public.foreign_legs where callsign <> 'BAW1'`);
check('2 記録が減って作り直しが半分未満なら前のまま', await one(`select public.foreign_usual_build()`) === 0 && await fu() === n1);
await db.exec(`insert into public.foreign_legs (day, callsign, iata, dep_here, at)
  select d, 'BAW' || i, 'HND', 0, (d + time '11:00' + make_interval(mins => i)) at time zone 'Asia/Tokyo'
    from generate_series(0, 29) k, lateral (select (now() at time zone 'Asia/Tokyo')::date - 30 + k as d) x, generate_series(2, 10) i`);
const n2 = await one(`select public.foreign_usual_build()`);
check('2 記録が戻れば作り直す（時刻も新しく）', n2 === n1 && await one(`select mins from public.foreign_usual where callsign = 'BAW2' and dow = -1`) === 11 * 60 + 2, [n2]);

// 1 死活の記録
const h0 = await one(`select ops.data_health()`);
const keys = h0.map((x) => x.key);
check('1 取り込みの項目がそろう', ['live_positions', 'track_points', 'odpt_status', 'flight_watch', 'timetable_sync', 'daily_archive', 'flight_history', 'timetable_rows', 'cron_failed', 'wx_obs'].every((k) => keys.includes(k)), keys);
check('1 何も届いていなければ位置は ng', h0.find((x) => x.key === 'live_positions').ok === false);
await db.exec(`insert into public.live_positions (callsign, lat, lon, seen_at) values ('ANA1', 35.5, 139.8, now() - interval '5 minutes')`);
await db.exec(`insert into public.timetable_sync_runs (iata, ran_at, result) values ('HND', now(), '{"iata":"HND","JAL":20,"ANA_error":"replace: kept previous timetable"}')`);
const h1 = await one(`select ops.data_health()`);
check('1 5分前に届いた位置は ok', h1.find((x) => x.key === 'live_positions').ok === true);
check('1 先の時刻表は届いた時刻では ok', h1.find((x) => x.key === 'timetable_sync').ok === true);
const tr = h1.find((x) => x.key === 'timetable_rows');
check('1 時刻表の失敗は ng で中身が分かる', tr.ok === false && /HND ANA_error/.test(JSON.stringify(tr.detail)), tr);
check('1 cron のない所では cron の失敗は ok', h1.find((x) => x.key === 'cron_failed').ok === true);

const nErr = () => one(`select count(*)::int from ops.client_errors where kind = 'data_stale'`);
check('1 ng があれば watch は1行書く', await one(`select ops.data_health_watch()`) === 1 && await nErr() === 1);
const det = await one(`select detail from ops.client_errors where kind = 'data_stale'`);
check('1 通知の下書きが入る（題・本文200字まで）', det.notify?.title && det.notify.body.length <= 200 && det.bad.length > 0, det.notify);
check('1 同じ中身は6時間に1回まで', await one(`select ops.data_health_watch()`) === 0 && await nErr() === 1);

// 権限
check('1 anon は data_health を呼べない', String(await as('anon', `select ops.data_health()`)).startsWith('ERROR'));
check('1 authenticated も watch を呼べない', String(await as('authenticated', `select ops.data_health_watch()`)).startsWith('ERROR'));
check('1 admin_data_health は anon から呼べない', String(await as('anon', `select public.admin_data_health()`)).startsWith('ERROR'));
await db.exec(`select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-0000000000b1', false)`);
check('1 管理者でない人は admin only', /admin only/.test(String(await as('authenticated', `select public.admin_data_health()`))));
await db.exec(`select set_config('request.jwt.claim.sub', '', false)`);

// 全部読みしない（大きくなる表）
const SMALL = new Set(['public.odpt_status_runs', 'public.flight_watch_runs', 'public.schedule_sync_runs', 'public.timetable_sync_runs', 'public.archive_runs', 'public.odpt_feed_dates', 'ops.client_errors', 'public.foreign_usual']);
await db.exec(`begin; set local enable_seqscan = off`);
const X = `select schemaname || '.' || relname t, seq_scan n from pg_stat_xact_user_tables`;
const a = Object.fromEntries((await rows(X)).map((r) => [r.t, r.n]));
await db.query(`select ops.data_health()`);
const scans = (await rows(X)).filter((r) => r.n - (a[r.t] || 0) > 0).map((r) => r.t).filter((t) => !SMALL.has(t));
await db.exec('rollback');
check('3 data_health は大きくなる表を全部読みしない', scans.length === 0, scans);

// 2回流しても壊れない・後の移行も流せる
await db.exec(fs.readFileSync(dir + NEW, 'utf8'));
check('3 2回流しても壊れない', Array.isArray(await one(`select ops.data_health()`)));
for (const f of files) if (f > NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));
check('3 後の移行も流せる', true);
if (bad) process.exit(1);
