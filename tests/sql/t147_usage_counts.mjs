// 使われ方を個人を特定しない回数だけで見る（移行 usage_counts）
//   1. 日ごとの表 ops.usage_daily に、利用者ID・IP・位置・session の列がない
//   2. 1日分を作ると、印の数・断った理由・端末に保存・画面の失敗・位置が取れない・エラーの種類・タブ・起動・はじめての流れが数わる
//      日本時間の日の境目（0時ちょうどは入る・次の0時は入らない）で正しく分ける（流す所の時間帯によらない）
//   3. 作り直しても数は同じ（二重にならない）。元の表（usage_events など）は減らない
//   4. 毎晩の処理：前の日・前の前の日と、まだの古い日を p_max 日ずつ。cron に上限（statement_timeout）付き
//   5. admin_usage_counts：管理者だけ。返す中身に利用者ID・session の値が出ない。indoor の目安
//   6. RLS：anon・authenticated は表を読めない。関数は anon が呼べない
//   7. 全部読みなしで作れる（索引で範囲を引く）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
const files = fs.readdirSync(dir).filter(f => f.endsWith('.sql')).sort();
const mine = files.find(f => f.endsWith('_usage_counts.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 400)); if (!ok) bad++; };
check('移行がある', !!mine);
const db = new PGlite();
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select coalesce(nullif(current_setting('request.jwt.claims', true), '')::jsonb, '{}'::jsonb) $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;
-- pg_cron の代わり
create extension if not exists plpgsql; create schema cron;
create table cron.job (jobid serial primary key, jobname text unique, schedule text, command text);
create function cron.schedule(n text, s text, c text) returns bigint language sql as $$
  insert into cron.job (jobname, schedule, command) values (n, s, c) on conflict (jobname) do update set schedule = excluded.schedule, command = excluded.command returning jobid::bigint $$;
create function cron.unschedule(n text) returns boolean language sql as $$ delete from cron.job where jobname = n returning true $$;`);
// pg_extension に pg_cron がある環境のふり：移行は pg_extension を見るので、見えないときは cron の登録をあとで直接確かめる
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));

const cols = (await db.query(`select string_agg(column_name, ',' order by ordinal_position) c from information_schema.columns where table_schema = 'ops' and table_name = 'usage_daily'`)).rows[0].c;
check('表の列は day・metric・key・n・sessions だけ', cols === 'day,metric,key,n,sessions', cols);
check('利用者ID・IP・位置・session の列がない', !/user|ip|lat|lon|session\b/.test(cols.replace('sessions', '')), cols);

// 種：日本時間の「きのう」の0時ちょうど・23時59分59秒・きょうの0時（入らない）
const J = (days, hm) => `((((now() at time zone 'Asia/Tokyo')::date - ${days})::timestamp + time '${hm}') at time zone 'Asia/Tokyo')`;
const U = '00000000-0000-0000-0000-0000000000a1', ADM = '00000000-0000-0000-0000-0000000000ad';
await db.exec(`insert into auth.users (id, email) values ('${U}', 'u@x'), ('${ADM}', 'a@x'); insert into ops.admins values ('${ADM}');`);
await db.exec(`insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values
  ('${U}', 1, 35.5, 139.7, 10, now(), ${J(1, '00:00')}), ('${U}', 2, 35.5, 139.7, 10, now(), ${J(1, '23:59:59')}), ('${U}', 3, 35.5, 139.7, 10, now(), ${J(0, '00:00')});
insert into ops.checkin_rejections (reason, airport_id, dist_km, accuracy_m, created_at) values
  ('out_of_range', 1, 3.2, 20, ${J(1, '10:00')}), ('out_of_range', 1, 2.1, 20, ${J(1, '11:00')}), ('low_accuracy', 1, 0.5, 1200, ${J(1, '12:00')}), ('too_soon', 1, 0.1, 10, ${J(2, '23:59:59')});
insert into ops.usage_events (session, event, prop, created_at) values
  ('s1aaaaaaaa', 'open', 'live', ${J(1, '08:00')}), ('s2aaaaaaaa', 'open', 'live', ${J(1, '09:00')}), ('s2aaaaaaaa', 'open', 'demo', ${J(1, '09:01')}),
  ('s1aaaaaaaa', 'tab', 'ops', ${J(1, '08:01')}), ('s1aaaaaaaa', 'tab', 'ops', ${J(1, '08:02')}), ('s2aaaaaaaa', 'tab', 'book', ${J(1, '09:02')}),
  ('s1aaaaaaaa', 'checkin_queued', null, ${J(1, '08:03')}), ('s1aaaaaaaa', 'checkin_fail', 'server', ${J(1, '08:04')}),
  ('s1aaaaaaaa', 'geo_fail', '1', ${J(1, '08:05')}), ('s2aaaaaaaa', 'geo_fail', '2', ${J(1, '09:05')}), ('s2aaaaaaaa', 'geo_fail', '3', ${J(1, '09:06')}),
  ('s1aaaaaaaa', 'guide', 'done', ${J(1, '08:06')}), ('s2aaaaaaaa', 'guide', 'skip', ${J(1, '09:07')}), ('s2aaaaaaaa', 'signup', 'done:casual', ${J(1, '09:08')}),
  ('s3aaaaaaaa', 'pin', 'x', ${J(1, '10:00')}), ('s3aaaaaaaa', 'open', 'live', ${J(0, '00:00')});
insert into ops.client_errors (session, kind, message, created_at) values ('s1aaaaaaaa', 'js', 'TypeError', ${J(1, '08:07')}), ('s2aaaaaaaa', 'js', 'x', ${J(1, '09:09')}), ('s2aaaaaaaa', 'checkin', 'y', ${J(1, '09:10')});`);
const before = (await db.query(`select (select count(*) from ops.usage_events)::int e, (select count(*) from public.checkins)::int c, (select count(*) from ops.client_errors)::int r`)).rows[0];

// 7. 全部読みなしで作れる
await db.exec('begin; set local enable_seqscan = off');
const T = `select relname t, seq_scan n from pg_stat_xact_user_tables where relname in ('checkins','checkin_rejections','usage_events','client_errors')`;
const a0 = Object.fromEntries((await db.query(T)).rows.map(r => [r.t, Number(r.n)]));
await db.query(`select ops.usage_daily_build((now() at time zone 'Asia/Tokyo')::date - 1)`);
const a1 = (await db.query(T)).rows.filter(r => Number(r.n) - (a0[r.t] || 0) > 0).map(r => r.t);
await db.exec('rollback');
check('元の表を全部読みせずに作れる（索引で日の範囲を引く）', a1.length === 0, a1);

const n1 = (await db.query(`select ops.usage_daily_build((now() at time zone 'Asia/Tokyo')::date - 1) n`)).rows[0].n;
const rows = async () => Object.fromEntries((await db.query(`select metric || '/' || key k, n, sessions from ops.usage_daily where day = (now() at time zone 'Asia/Tokyo')::date - 1`)).rows.map(r => [r.k, [r.n, r.sessions]]));
const R = await rows();
const eq = (k, n, s) => check(`${k} = ${n}${s !== undefined ? '（起動 ' + s + '）' : ''}`, R[k] && R[k][0] === n && (s === undefined || R[k][1] === s), R[k]);
eq('checkin/ok', 2);            // 0時ちょうどと23時59分59秒。きょうの0時は入らない
eq('checkin/out_of_range', 2); eq('checkin/low_accuracy', 1);
check('前の日の23時59分59秒の断り（too_soon）は入らない', !R['checkin/too_soon'], R['checkin/too_soon']);
eq('checkin/queued', 1, 1); eq('client_fail/server', 1, 1);
eq('geo/1', 1, 1); eq('geo/2', 1, 1); eq('geo/3', 1, 1);
eq('tab/ops', 2, 1); eq('tab/book', 1, 1);
eq('open/live', 2, 2); eq('open/demo', 1, 1);
eq('onboard/guide:done', 1, 1); eq('onboard/guide:skip', 1, 1); eq('onboard/signup:done:casual', 1, 1);
check('ほかの記録（pin）は数えない', !Object.keys(R).some(k => k.includes('pin')), Object.keys(R));
eq('error/js', 2); eq('error/checkin', 1);
check('作った行の数を返す', n1 === Object.keys(R).length, [n1, Object.keys(R).length]);
const n2 = (await db.query(`select ops.usage_daily_build((now() at time zone 'Asia/Tokyo')::date - 1) n`)).rows[0].n;
check('作り直しても同じ（二重にならない）', n2 === n1 && JSON.stringify(await rows()) === JSON.stringify(R));
const after = (await db.query(`select (select count(*) from ops.usage_events)::int e, (select count(*) from public.checkins)::int c, (select count(*) from ops.client_errors)::int r`)).rows[0];
check('元の表は減らない', JSON.stringify(before) === JSON.stringify(after), { before, after });

// 4. 毎晩の処理
await db.exec(`delete from ops.usage_daily; delete from ops.usage_daily_runs;`);
const f1 = (await db.query(`select ops.usage_daily_fill(5) n`)).rows[0].n;
const runs1 = (await db.query(`select count(*)::int n, min((now() at time zone 'Asia/Tokyo')::date - day) lo, max((now() at time zone 'Asia/Tokyo')::date - day) hi from ops.usage_daily_runs`)).rows[0];
check('1回目：前の日・前の前の日＋古い日5日＝7日', f1 === 7 && runs1.n === 7 && runs1.lo === 1 && runs1.hi === 7, { f1, runs1 });
const f2 = (await db.query(`select ops.usage_daily_fill(5) n`)).rows[0].n;
const runs2 = (await db.query(`select count(*)::int n, max((now() at time zone 'Asia/Tokyo')::date - day) hi from ops.usage_daily_runs`)).rows[0];
check('2回目：作った日は飛ばして、その先の5日', f2 === 7 && runs2.n === 12 && runs2.hi === 12, { f2, runs2 });
await db.query(`select ops.usage_daily_fill(1000)`);
check('180日前より古い日は作らない', (await db.query(`select max((now() at time zone 'Asia/Tokyo')::date - day)::int hi from ops.usage_daily_runs`)).rows[0].hi === 180);
const fsrc = (await db.query(`select string_agg(array_to_string(proconfig, ','), ' | ') c from pg_proc where proname in ('usage_daily_build', 'usage_daily_fill')`)).rows[0].c;
check('作る関数に上限（statement_timeout）', /statement_timeout=60s/.test(fsrc) && /statement_timeout=110s/.test(fsrc), fsrc);
const sql = fs.readFileSync(dir + mine, 'utf8');
check('cron（usage-daily）の文に上限2分・ロック待ち5秒', /cron\.schedule\('usage-daily', '37 18 \* \* \*', \$job\$ set statement_timeout = '2min'; set lock_timeout = '5s';/.test(sql));

// 5. 運営の関数
const asU = async (uid, q) => { await db.exec(`select set_config('request.jwt.claim.sub', '${uid}', false); select set_config('request.jwt.claims', '${JSON.stringify({ sub: uid, aal: 'aal2' })}', false);`); return db.query(q); };
const out = (await asU(ADM, `select public.admin_usage_counts(3) r`)).rows[0].r;
const y = out.days[0];
check('3日分・新しい日から', out.days.length === 3 && y.made === true, out.days.map(d => [d.day, d.made]));
check('きのうの印 ok 2・範囲外 2', y.checkin.ok === 2 && y.checkin.out_of_range === 2, y.checkin);
check('indoor の目安＝low_accuracy 1＋geo 2・3 で 3', y.indoor === 3, y.indoor);
check('タブは回数と起動の数', y.tab.ops.n === 2 && y.tab.ops.sessions === 1, y.tab);
check('返す中身に利用者ID・session の値が出ない', !/s1aaaaaaaa|s2aaaaaaaa|0000000000a1/.test(JSON.stringify(out)));
let e = ''; try { await asU(U, `select public.admin_usage_counts(3)`); } catch (x) { e = x.message; }
check('管理者でなければ admin only', /admin only/.test(e), e);
await db.exec(`select set_config('request.jwt.claim.sub', '', false)`);

// 6. 権限
const p = (await db.query(`select has_function_privilege('anon', 'public.admin_usage_counts(integer)', 'execute') a, has_function_privilege('authenticated', 'public.admin_usage_counts(integer)', 'execute') u,
  has_function_privilege('authenticated', 'ops.usage_daily_build(date)', 'execute') b, has_function_privilege('anon', 'ops.usage_daily_fill(integer)', 'execute') f,
  has_table_privilege('authenticated', 'ops.usage_daily', 'select') t, has_table_privilege('anon', 'ops.usage_daily', 'select') t2,
  (select relrowsecurity from pg_class where oid = 'ops.usage_daily'::regclass) rls`)).rows[0];
check('anon は関数を呼べない・authenticated は呼べる（中で is_admin）', p.a === false && p.u === true, p);
check('作る関数は anon・authenticated から呼べない', p.b === false && p.f === false, p);
check('表は anon・authenticated から読めない・RLS 有効', p.t === false && p.t2 === false && p.rls === true, p);
check('checkins に created_at の索引', (await db.query(`select count(*)::int n from pg_indexes where tablename = 'checkins' and indexname = 'checkins_time'`)).rows[0].n === 1);
console.log(bad ? `NG ${bad}` : 'すべて OK'); process.exit(bad ? 1 : 0);
