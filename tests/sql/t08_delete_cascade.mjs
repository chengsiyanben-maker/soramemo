// auth.users を消すと、利用者のすべての表の行が消えることを確かめる
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir=new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth; create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated; grant execute on function auth.uid() to anon, authenticated;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir+f,'utf8'));
const A='11111111-1111-1111-1111-111111111111', B='22222222-2222-2222-2222-222222222222';
await db.exec(`insert into auth.users (id) values ('${A}'),('${B}');`);
for (const u of [A,B]) await db.exec(`
 insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${u}',5,0,0,10,now());
 insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values ('${u}',5,6,now()-interval '2 hours',now(),820);
 insert into manual_flights (user_id, from_airport, to_airport, flown_on) values ('${u}',5,6,'2025-01-01');
 insert into companies (user_id) values ('${u}'); insert into route_levels (user_id, route_key, level) values ('${u}','5-6',2);
 insert into aircraft (user_id, type) values ('${u}','prop'); insert into facilities (user_id, airport_id) values ('${u}',5);
 insert into subscriptions (user_id, status) values ('${u}','active');`);
const tables = ['checkins','flights','manual_flights','companies','route_levels','aircraft','facilities','subscriptions'];
const count = async u => Object.fromEntries(await Promise.all(tables.map(async t => [t, (await db.query(`select count(*)::int n from ${t} where user_id='${u}'`)).rows[0].n])));
console.log('before A:', JSON.stringify(await count(A)));
await db.exec(`delete from auth.users where id='${A}'`);
console.log('after  A:', JSON.stringify(await count(A)));
console.log('B kept  :', JSON.stringify(await count(B)));
