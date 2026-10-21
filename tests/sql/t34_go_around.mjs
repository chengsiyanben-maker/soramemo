// ゴーアラウンド：見張りは誰からも読めない、見つけたものは ga_recent・ga_event でだれでも読める（hex は出さない）。知らせの設定は決まった値だけ
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
await db.exec(`insert into public.ga_events (iata, at, hex, callsign, flight, low_ft, low_km, rwy, pts) values ('HND', now() - interval '10 minutes', 'abc123', 'JAL123', 'JL123', 450, 2.1, '34L', '[[1,450,2.1]]'),
  ('HND', now() - interval '30 hours', 'abc124', 'ANA24', 'NH24', 600, 3, '34R', '[]'), ('NRT', now(), 'abc125', 'JAL5', 'JL5', 500, 3, null, '[]')`);
const rec = await as(null, `select public.ga_recent('HND', 24)`);
check('最近のゴーアラウンド（その空港・24時間）', Array.isArray(rec) && rec.length === 1 && rec[0].flight === 'JL123' && rec[0].low_ft === 450 && rec[0].hex === undefined, rec);
const id = (await db.query(`select id from public.ga_events where flight = 'JL123'`)).rows[0].id;
const ev = await as(null, `select public.ga_event(${id})`);
check('1件はだれでも読める（hex は出さない）', ev && ev.rwy === '34L' && ev.hex === undefined && Array.isArray(ev.pts), ev);
check('見張りの表は読めない', String(await as(A, `select count(*) from public.ga_watch`)).startsWith('ERROR'));
check('ゴーアラウンドの表は直接読めない', String(await as(null, `select count(*) from public.ga_events`)).startsWith('ERROR'));
await db.exec(`insert into public.push_subs (endpoint, p256dh, auth) values ('https://fcm.googleapis.com/x', 'k', 'a')`);
check('知らせの設定：決まった種類は入る', (await as(null, `select 1`)) && (await db.query(`update public.push_subs set ga_airports = '{HND,NRT}', ga_kinds = '{plane,wind}', ga_quiet = true where endpoint = 'https://fcm.googleapis.com/x' returning id`)).rows.length === 1);
let bad2 = false; try { await db.query(`update public.push_subs set ga_kinds = '{xxx}'`); } catch { bad2 = true; }
check('知らせの設定：知らない種類は入らない', bad2);
if (bad) process.exit(1);
