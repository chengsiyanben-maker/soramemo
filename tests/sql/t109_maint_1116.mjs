// 定期の手入れ 11/16（移行 170）：時間の上限のない処理をなくす
//   1. ops-log-cleanup の仕事の文に statement_timeout と lock_timeout が入っているか（pg_cron は手元にないので文を見る）
//   2. 裏の処理が呼ぶ書く関数12個に lock_timeout が付いたか・値は毎晩 5s／毎分 10s か
//   3. 付けたあとも関数は動き、呼んだあとに設定が残らないか（呼び出し元の lock_timeout は元のまま）
//   4. 中身（定義の本文）と権限は変わっていないか
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const NEW = '20261116000170_maint_1116.sql';
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const rows = async (sql, p) => (await db.query(sql, p)).rows;

const FNS = {
  archive_airport_daily: '5s', archive_rotations: '5s', archive_track_points: '5s', archive_user_flights: '5s', cold_done: '5s',
  airport_tracks_put: '5s', reg_legs_route: '5s', timetable_replace: '5s', world_status_put: '5s',
  apply_flight_status: '10s', flight_alerts_put: '10s', reg_legs_touch: '10s',
};
const info = async () => Object.fromEntries((await rows(`select p.proname, p.prosrc, p.proconfig, p.proacl::text acl, p.prosecdef
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname = any($1)`, [Object.keys(FNS)])).map((r) => [r.proname, r]));

// 170 の前まで入れて、前の形をとっておく
for (const f of files) if (f < NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const before = await info();
check('12個の関数がそろっている（名前が変わっていない）', Object.keys(before).length === 12, Object.keys(before));
check('前は lock_timeout が付いていない', Object.values(before).every((r) => !(r.proconfig ?? []).some((c) => c.startsWith('lock_timeout'))), null);
for (const f of files) if (f >= NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const after = await info();

// 2
const wrong = Object.entries(FNS).filter(([k, v]) => !(after[k]?.proconfig ?? []).includes(`lock_timeout=${v}`));
check('12個に lock_timeout（毎晩 5s・毎分と30秒ごと 10s）', wrong.length === 0, wrong.map(([k]) => [k, after[k]?.proconfig]));
// 4
const changed = Object.keys(FNS).filter((k) => before[k].prosrc !== after[k].prosrc || before[k].acl !== after[k].acl || before[k].prosecdef !== after[k].prosecdef);
check('本文・権限・security definer は変わっていない', changed.length === 0, changed);
const other = (after.flight_alerts_put.proconfig ?? []).filter((c) => !c.startsWith('lock_timeout'));
const otherBefore = (before.flight_alerts_put.proconfig ?? []);
check('前からある関数の設定（search_path など）は残る', JSON.stringify(other) === JSON.stringify(otherBefore), { other, otherBefore });

// 3
await db.exec(`set lock_timeout = '0'`);
const put = await rows(`select count(*)::int c from public.world_status_put('faa', now(), '[{"iata":"LAX","kind":"ground_stop","reason":"t"}]'::jsonb)`);
check('付けたあとも world_status_put は動く', put[0].c === 1, put);
const st = await rows(`select public.apply_flight_status('[]'::jsonb) is not distinct from public.apply_flight_status('[]'::jsonb) ok`);
check('付けたあとも apply_flight_status は動く（空の入力）', st[0].ok === true, st);
const lt = (await rows(`show lock_timeout`))[0].lock_timeout;
check('呼んだあと、呼び出し元の lock_timeout は元のまま（関数の中だけ）', lt === '0', lt);
const inside = (await rows(`select (select setting from pg_settings where name = 'lock_timeout') s
  from (select public.reg_legs_touch('[]'::jsonb)) x`))[0];
check('reg_legs_touch も空の入力で動く', inside !== undefined, inside);

// 1
const sql = fs.readFileSync(dir + NEW, 'utf8');
const job = sql.slice(sql.indexOf("cron.schedule('ops-log-cleanup'"), sql.indexOf('$job$)', sql.indexOf("cron.schedule('ops-log-cleanup'")));
check('ops-log-cleanup は時刻と中身が今のまま', job.includes("'35 19 * * *'") && job.includes("delete from public.ops_log where at < now() - interval '90 days'"), job);
check('ops-log-cleanup の文の先頭に statement_timeout と lock_timeout', /\$job\$\s*set statement_timeout = '2min'; set lock_timeout = '5s';/.test(job), job);
check('pg_cron がない所では仕事を作らない', sql.includes("where extname = 'pg_cron') then return"), null);
check('表・索引・RLS・権限を変える文がない', !/create table|alter table|create index|drop |grant |revoke |policy/i.test(sql.replace(/^--.*$/gm, '')), null);

console.log(bad ? `NG ${bad}件` : 'すべて OK');
process.exit(bad ? 1 : 0);
