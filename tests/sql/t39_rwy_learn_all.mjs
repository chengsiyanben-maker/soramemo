// 滑走路の学習（日本中）：航跡の読み出しは運営だけ。滑走路ごと・方角ごとの数はだれでも読める（羽田・成田は見張りの記録だけ）
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
await db.exec(`insert into public.track_points (callsign, t, lat, lon, alt) values ('JAL123', now() - interval '1 hour', 35.6, 139.9, 30), ('JAL123', now() - interval '59 minutes', 35.58, 139.85, 20), ('JA4123', now() - interval '1 hour', 35, 139, 10)`);
const pts = (await db.query(`select public.rwy_learn_points(now() - interval '2 hours', now(), 0, 1) as p`)).rows[0].p;
check('航跡を呼び出し符号ごとに（自家用機は除く）', pts.length === 1 && pts[0].cs === 'JAL123' && pts[0].p.length === 2, pts);
let denied = false; await db.exec('set role anon'); try { await db.query(`select public.rwy_learn_points(now() - interval '2 hours', now(), 0, 1)`); } catch { denied = true; } await db.exec('reset role');
check('航跡の読み出しは運営だけ', denied);
await db.exec(`insert into public.rwy_samples (iata, dir, at, rwy, ent60, src) values ('KMJ', 'arr', now(), '07', 250, 'track'), ('KMJ', 'arr', now(), '07', 260, 'track'), ('KMJ', 'dep', now(), '25', null, 'track'),
  ('HND', 'arr', now(), '22', 20, 'live'), ('HND', 'arr', now(), '22', 20, 'track')`);
await db.exec(`update public.rwy_samples set ex60 = 90 where dir = 'dep'`);
await db.exec('set role anon');
const k = (await db.query(`select public.rwy_learned('KMJ', 30) as r`)).rows[0].r, h = (await db.query(`select public.rwy_learned('HND', 30) as r`)).rows[0].r;
await db.exec('reset role');
check('滑走路ごと・方角ごとの数', k.n === 3 && k.rows.some((x) => x.dir === 'arr' && x.rwy === '07' && x.sec === 6 && x.n === 2) && k.rows.some((x) => x.dir === 'dep' && x.sec === 2), k);
check('羽田は見張りの記録だけ', h.n === 1, h);
if (bad) process.exit(1);
