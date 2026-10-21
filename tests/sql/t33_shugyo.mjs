// 修行の保存（shugyo_prefs）は本人だけが読み書きでき、大きすぎる中身は入らない。運賃の金額は本人だけが入れられる。バックアップに入り、アカウントを消すと消える
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
check('自分の行を入れられる', (await as(A, `insert into public.shugyo_prefs (data) values ('{"budget": 600000}')`)) === 'ok');
check('2行目は入らない', String(await as(A, `insert into public.shugyo_prefs (data) values ('{}')`)).startsWith('ERROR'));
check('ほかの人の行としては入れられない', String(await as(A, `insert into public.shugyo_prefs (user_id, data) values ('${B}', '{}')`)).startsWith('ERROR'));
check('配列は入らない', String(await as(B, `insert into public.shugyo_prefs (data) values ('[]')`)).startsWith('ERROR'));
check('大きすぎる中身は入らない', String(await as(B, `insert into public.shugyo_prefs (data) values (jsonb_build_object('x', repeat(md5(random()::text), 4000)))`)).startsWith('ERROR'));
check('自分の行は読める', Number(await as(A, `select (data->>'budget')::int from public.shugyo_prefs`)) === 600000);
check('ほかの人の行は読めない', Number(await as(B, `select count(*) from public.shugyo_prefs`)) === 0);
await as(B, `update public.shugyo_prefs set data = '{"budget": 1}'`);
check('ほかの人の行は書き換えられない', Number(await as(A, `select (data->>'budget')::int from public.shugyo_prefs`)) === 600000);
check('自分の行は書き換えられる', (await as(A, `update public.shugyo_prefs set data = '{"budget": 500000}'`)) === 'ok' && Number(await as(A, `select (data->>'budget')::int from public.shugyo_prefs`)) === 500000);
check('ログインしていなければ読めない', String(await as(null, `select count(*) from public.shugyo_prefs`)).startsWith('ERROR'));
// 運賃の金額
const ap = (await db.query(`select id from public.airports limit 2`)).rows.map(r => r.id);
await db.exec(`insert into public.flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values ('${A}', ${ap[0]}, ${ap[1] ?? ap[0]}, now() - interval '3 hours', now() - interval '1 hour', 500)`);
const fid = (await db.query(`select id from public.flights limit 1`)).rows[0].id;
check('自分のフライトに金額を入れられる', (await as(A, `select public.set_flight_price(${fid}, 38900)`)) !== undefined && Number((await db.query(`select price from public.flights where id = ${fid}`)).rows[0].price) === 38900);
check('ほかの人のフライトには入れられない', String(await as(B, `select public.set_flight_price(${fid}, 1)`)).startsWith('ERROR'));
check('おかしな金額は入らない', String(await as(A, `select public.set_flight_price(${fid}, -5)`)).startsWith('ERROR'));
check('バックアップに入る（関数の中身）', /'shugyo_prefs'/.test((await db.query(`select prosrc from pg_proc where proname = 'admin_backup'`)).rows[0].prosrc));
await db.exec(`delete from public.flights; delete from auth.users where id = '${A}'`);
check('アカウントを消すと一緒に消える', Number((await db.query(`select count(*) as n from public.shugyo_prefs`)).rows[0].n) === 0);
// 路線の今日の便
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
  ((now() at time zone 'Asia/Tokyo')::date, 'NH469', 'HND', 'OKA', now(), now() + interval '2 hours 40 minutes', 'test'),
  ((now() at time zone 'Asia/Tokyo')::date, 'NH470', 'OKA', 'HND', now(), now() + interval '2 hours', 'test')`);
const rt = await as(null, `select public.route_today('HND', 'OKA')`);
check('路線の今日の便（片方向だけ・ログインなしで読める）', Array.isArray(rt) && rt.length === 1 && rt[0].flight === 'NH469' && rt[0].cancelled === false, rt);
if (bad) process.exit(1);
