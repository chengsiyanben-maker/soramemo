// 国際線の記録：本人だけが読み書きでき、日本の空港をどちらか一方に含む便だけ入る。アカウントを消すと一緒に消える。バックアップに入る
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id, email) values ('${A}', 'a@example.com'), ('${B}', 'b@example.com')`);
const as = async (uid, sql) => { try { await db.exec(`set request.jwt.claim.sub = '${uid ?? ''}'; set role ${uid ? 'authenticated' : 'anon'}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec(`reset role; reset request.jwt.claim.sub`); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const ins = (uid, dep, arr, more = '') => as(uid, `insert into public.intl_flights (flown_on, dep, arr, flight_no, distance_km${more ? ', dep_at, arr_at' : ''}) values (current_date, '${dep}', '${arr}', 'NH106', 8800${more})`);

check('日本 → 海外は入る', (await ins(A, 'HND', 'LAX')) === 'ok');
check('海外 → 日本も入る（時刻つき）', (await ins(A, 'ICN', 'NRT', `, now() - interval '3 hours', now() - interval '1 hour'`)) === 'ok');
check('国内線どうしは入らない（記録帳へ）', String(await ins(A, 'HND', 'CTS')).startsWith('ERROR'));
check('海外どうしは入らない', String(await ins(A, 'ICN', 'LAX')).startsWith('ERROR'));
check('到着が出発より前は入らない', String(await ins(A, 'HND', 'LAX', `, now(), now() - interval '1 hour'`)).startsWith('ERROR'));
check('ほかの人の行としては入れられない', String(await as(A, `insert into public.intl_flights (user_id, flown_on, dep, arr) values ('${B}', current_date, 'HND', 'LAX')`)).startsWith('ERROR'));
check('ログインしていなければ入れられない', String(await ins(null, 'HND', 'LAX')).startsWith('ERROR'));
check('自分の行は読める', Number(await as(A, `select count(*) from public.intl_flights`)) === 2);
check('ほかの人の行は読めない', Number(await as(B, `select count(*) from public.intl_flights`)) === 0);
await as(B, `delete from public.intl_flights`);
check('ほかの人の行は消せない', Number(await as(A, `select count(*) from public.intl_flights`)) === 2);
await as(A, `delete from public.intl_flights where dep = 'ICN'`);
check('自分の行は消せる', Number(await as(A, `select count(*) from public.intl_flights`)) === 1);
check('バックアップに入る（関数の中身）', /'intl_flights'/.test((await db.query(`select prosrc from pg_proc where proname = 'admin_backup'`)).rows[0].prosrc));
await db.exec(`delete from auth.users where id = '${A}'`);
check('アカウントを消すと一緒に消える', Number((await db.query(`select count(*) as n from public.intl_flights`)).rows[0].n) === 0);
if (bad) process.exit(1);
