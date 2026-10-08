import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir=new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth; create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated; grant execute on function auth.uid() to anon, authenticated;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir+f,'utf8'));
console.log('applied', fs.readdirSync(dir).length);
const ADM='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', U='11111111-1111-1111-1111-111111111111', U2='22222222-2222-2222-2222-222222222222';
const hnd = (await db.query(`select id, lat, lon from airports where iata='HND'`)).rows[0];
await db.exec(`insert into auth.users (id, email, created_at) values ('${ADM}','a@x', now() - interval '60 days'),('${U}','u@x', now() - interval '40 days'),('${U2}','v@x', now());
 insert into ops.admins values ('${ADM}');
 insert into checkins (user_id, airport_id, terminal_id, lat, lon, accuracy_m, position_at, created_at) values
   ('${U}', ${hnd.id}, 'HND-T1', ${hnd.lat}+0.003, ${hnd.lon}, 20, now(), now() - interval '2 days'),
   ('${U}', ${hnd.id}, null, ${hnd.lat}+0.015, ${hnd.lon}, 80, now(), now() - interval '1 day'),
   ('${U2}', ${hnd.id}, 'HND-T2', ${hnd.lat}, ${hnd.lon}+0.002, 15, now(), now());
 insert into ops.checkin_rejections (reason, airport_id, dist_km, accuracy_m) values ('out_of_range', ${hnd.id}, 2.4, 30), ('out_of_range', ${hnd.id}, 9.0, 30), ('low_accuracy', ${hnd.id}, 0.5, 1500);`);
const as = async (role, uid, sql) => { try { await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch(e){ return 'ERROR: '+e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const ev = JSON.stringify([{e:'open',p:'rally'},{e:'tab',p:'book'},{e:'tab',p:'book'},{e:'BAD NAME',p:'x'},{e:'checkin_fail',p:'out_of_range'}]);
console.log('anon log_events:', await as('anon','', `select public.log_events('abcd1234efgh', 'ios', '2026.10', '${ev}'::jsonb)`));
console.log('bad session:', await as('anon','', `select public.log_events('x', 'ios', '2026.10', '${ev}'::jsonb)`));
console.log('too many:', await as('anon','', `select public.log_events('abcd1234efgh', 'ios', '2026.10', '${JSON.stringify(Array.from({length:51},()=>({e:'tab'})))}'::jsonb)`));
console.log('anon log_error:', await as('anon','', `select public.log_error('abcd1234efgh', 'ios', '2026.10', 'js', 'TypeError: x is undefined', '{"line":12}'::jsonb)`));
console.log('anon reads events:', await as('anon','', `select count(*) from ops.usage_events`));
console.log('user admin_metrics:', await as('authenticated', U, `select public.admin_metrics(30)`));
const m = await as('authenticated', ADM, `select public.admin_metrics(30)`); console.log('metrics:', JSON.stringify({a7:m.active7, a30:m.active30, ret:m.retention30, last:m.daily.at(-1), top:m.top_airports, plus:m.plus}));
const u = await as('authenticated', ADM, `select public.admin_usage(30)`); console.log('usage:', JSON.stringify(u));
const e = await as('authenticated', ADM, `select public.admin_errors(30)`); console.log('errors:', JSON.stringify(e));
const q = await as('authenticated', ADM, `select public.admin_quality(90)`); console.log('quality:', JSON.stringify(q));
console.log('cleanup by user:', await as('authenticated', U, `select public.insights_cleanup()`));
