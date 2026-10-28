// 空の道すじの線を入れる（airport_tracks_put）：食い違う古い線は入れ替え、何度入れても同じ。ほかの機体・離れた時刻の線は残す。匿名では呼べない
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
const rows = async () => (await db.query(`select iata, callsign, to_char(at at time zone 'UTC', 'HH24:MI') as at, dep_here, pts from public.airport_tracks_all order by iata, callsign, at`)).rows;
// 古い判定：成田の出発 UAL32 を到着として入れていた（時刻は最後の点の 03:06）。ほかに、別の機体と、同じ機体の6時間あとの到着
await db.exec(`insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values
  ('NRT', '2026-10-24', 'UAL32', '2026-10-24 03:06+00', 0, 'old'),
  ('NRT', '2026-10-24', 'JAL5', '2026-10-24 03:10+00', 0, 'jal'),
  ('NRT', '2026-10-24', 'UAL32', '2026-10-24 09:30+00', 0, 'later')`);
const put = (r) => db.query(`select public.airport_tracks_put($1::jsonb) as n`, [JSON.stringify(r)]);
const fresh = [{ iata: 'NRT', day: '2026-10-24', callsign: 'UAL32', at: '2026-10-24T03:00:00Z', dep_here: 1, pts: 'new' }];
await put(fresh);
let r = await rows();
check('食い違う古い線（到着としていた）は入れ替わる', r.filter((x) => x.callsign === 'UAL32' && x.pts === 'old').length === 0 && r.some((x) => x.callsign === 'UAL32' && x.dep_here === 1 && x.pts === 'new'), r);
check('ほかの機体と、離れた時刻の線は残る', r.some((x) => x.callsign === 'JAL5') && r.some((x) => x.pts === 'later'), r);
await put(fresh); const r2 = await rows();
check('何度入れても同じ', JSON.stringify(r2) === JSON.stringify(r), r2);
// 同じ機体が出てすぐ戻った（出発と到着の2本）は、どちらも残る
const two = [{ iata: 'KMJ', day: '2026-10-24', callsign: 'SNJ1', at: '2026-10-24T01:00:00Z', dep_here: 1, pts: 'd' }, { iata: 'KMJ', day: '2026-10-24', callsign: 'SNJ1', at: '2026-10-24T01:50:00Z', dep_here: 0, pts: 'a' }];
await put(two); await put(two);
check('出てすぐ戻った便は、出発と到着の2本', (await rows()).filter((x) => x.callsign === 'SNJ1').length === 2);
let denied = false; await db.exec('set role anon'); try { await put(fresh); } catch { denied = true; } await db.exec('reset role');
check('匿名では呼べない', denied);
if (bad) process.exit(1);
