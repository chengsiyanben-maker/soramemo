// 特別塗装機の予定の便（livery_plans）は、時刻表（flight_schedule）が消えても残る
//   毎晩の掃除（14日より前の時刻表を消す）のあとも残る・同じ便は2行にならない・予定の一覧は時刻表がなくても出る・
//   flight_watch はいまのまま時刻表と一緒に消える・利用者は表を直接読めない（RLS はいまのまま）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };

check('外部キーがない', Number(await q1(`select count(*) from pg_constraint where conrelid = 'public.livery_plans'::regclass and contype = 'f'`)) === 0, null);
check('schedule_id は主キーのまま', await q1(`select count(*) from pg_constraint where conrelid = 'public.livery_plans'::regclass and contype = 'p'`) == 1, null);

// 20日前の便（もうすぐ掃除で消える）と、2時間後の便
await db.exec(`insert into flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
  ((now() - interval '20 days')::date, 'JL501', 'HND', 'CTS', now() - interval '20 days', now() - interval '20 days' + interval '90 minutes', 'test'),
  ((now() + interval '2 hours')::date, 'NH63', 'HND', 'CTS', now() + interval '2 hours', now() + interval '3 hours 30 minutes', 'test')`);
const oldId = await q1(`select id from flight_schedule where flight = 'JL501'`), newId = await q1(`select id from flight_schedule where flight = 'NH63'`);
await db.exec(`insert into flight_watch (schedule_id, state) values (${oldId}, '{}'::jsonb)`);
await db.exec(`insert into livery_plans (schedule_id, flight, dep, arr, std, livery, note) values
  (${oldId}, 'JL501', 'HND', 'CTS', now() - interval '20 days', 'テスト塗装A', 'テスト塗装Aで運航いたします'),
  (${newId}, 'NH63', 'HND', 'CTS', now() + interval '2 hours', 'テスト塗装B', null)`);

check('掃除の前は flight_watch がある', Number(await q1(`select count(*) from flight_watch where schedule_id = ${oldId}`)) === 1, null);
// 毎晩の掃除と同じ文
await db.exec(`delete from public.flight_schedule where std < now() - interval '14 days'`);
check('時刻表の古い行は消える（掃除は今のまま）', Number(await q1(`select count(*) from flight_schedule where id = ${oldId}`)) === 0, null);
const kept = (await db.query(`select flight, dep, arr, livery, note from livery_plans where schedule_id = ${oldId}`)).rows[0];
check('予定の便は消えずに残る（便名・空港・塗装名・お知らせの文）', kept && kept.flight === 'JL501' && kept.dep === 'HND' && kept.arr === 'CTS' && kept.livery === 'テスト塗装A' && kept.note, kept);
check('flight_watch はいまのまま時刻表と一緒に消える', Number(await q1(`select count(*) from flight_watch where schedule_id = ${oldId}`)) === 0, null);

// 同じ便がもう一度見つかっても2行にならない（odpt-status の upsert ignoreDuplicates と同じ）
await db.exec(`insert into livery_plans (schedule_id, flight, dep, arr, std, livery) values (${newId}, 'NH63', 'HND', 'CTS', now() + interval '2 hours', 'テスト塗装B') on conflict (schedule_id) do nothing`);
check('同じ便は1行', Number(await q1(`select count(*) from livery_plans where flight = 'NH63'`)) === 1, null);

// 予定の一覧（返す形は今までと同じ）
const up = await as('anon', `select public.livery_plans_upcoming('HND')`);
check('予定の一覧はだれでも読める', Array.isArray(up), up);
check('これから飛ぶ便は出る（到着の定刻つき）', up.length === 1 && up[0].flight === 'NH63' && up[0].sta && up[0].cancelled === false, up);
check('返す形は今までと同じ', up[0] && ['flight', 'dep', 'arr', 'std', 'sta', 'livery', 'note', 'atd', 'cancelled'].every((k) => k in up[0]) && Object.keys(up[0]).length === 9, up[0]);
// 時刻表が先に消えても（例外）、予定は出る
await db.exec(`delete from flight_schedule where id = ${newId}`);
const up2 = await as('anon', `select public.livery_plans_upcoming(null)`);
check('時刻表がなくても予定は出る（到着の定刻は空）', up2.length === 1 && up2[0].flight === 'NH63' && up2[0].sta === null && up2[0].cancelled === false, up2);
check('時刻表が消えても予定の行は残る', Number(await q1(`select count(*) from livery_plans`)) === 2, null);

// 実績とのつなぎ方（運航日＝定刻の日本時間の日付・便名・出発）
await db.exec(`insert into flight_history (svc_date, flight, dep, arr, std, sta, type) values (((now() - interval '20 days') at time zone 'Asia/Tokyo')::date, 'JL501', 'HND', 'CTS', now() - interval '20 days', now() - interval '20 days' + interval '90 minutes', 'B738')`);
check('残った予定は flight_history とつなげられる', Number(await q1(`select count(*) from livery_plans p join flight_history h on h.svc_date = (p.std at time zone 'Asia/Tokyo')::date and h.flight = p.flight and h.dep = p.dep`)) === 1, null);

// RLS はいまのまま
check('RLS は有効', await q1(`select relrowsecurity from pg_class where relname = 'livery_plans'`) === true, null);
check('利用者は表を直接読めない', String(await as('authenticated', `select count(*) from public.livery_plans`)).startsWith('ERROR: permission denied'), null);
check('ログインしていない人も読めない', String(await as('anon', `select count(*) from public.livery_plans`)).startsWith('ERROR: permission denied'), null);
check('満足度の初期値は 40 のまま', Number(await q1(`select column_default from information_schema.columns where table_name = 'companies' and column_name = 'satisfaction'`)) === 40, null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
