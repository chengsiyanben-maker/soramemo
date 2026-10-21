// 滑走路の学習の記録：表はだれからも読めない。数と、方角・滑走路だけの一覧は読める（便名・位置は出さない）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const as = async (sql) => { try { await db.exec(`set role anon`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec(`reset role`); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
await db.exec(`insert into public.rwy_samples (iata, at, callsign, flight, rwy, ent120, ent60, first_brg, pts) values ('HND', now(), 'JAL510', 'JL510', '34L', 10, 20, 5, '[[1,35.6,139.9,9000]]'), ('HND', now() - interval '1 day', 'ANA24', 'NH24', '34R', 200, 210, 205, '[]'), ('NRT', now(), 'JAL5', 'JL5', '34L', 30, 30, 30, '[]')`);
const c = await as(`select public.rwy_sample_counts()`);
check('数は読める', c['HND:arr:34L'] === 1 && c['NRT:arr:34L'] === 1, c);
const r = await as(`select public.rwy_samples_recent('HND', 14)`);
check('最近の記録：方角と滑走路だけ', Array.isArray(r) && r.length === 2 && r[0][1] === '34R' && r[1].length === 9 && r[1][6] === 'arr' && !JSON.stringify(r).includes('JL510'), r);
check('表は直接読めない', String(await as(`select count(*) from public.rwy_samples`)).startsWith('ERROR'));
check('見張りの表も読めない', String(await as(`select count(*) from public.arr_watch`)).startsWith('ERROR'));
let badRwy = false; try { await db.query(`insert into public.rwy_samples (iata, at, rwy) values ('HND', now(), 'X1')`); } catch { badRwy = true; }
check('おかしな滑走路の名前は入らない', badRwy);
if (bad) process.exit(1);
