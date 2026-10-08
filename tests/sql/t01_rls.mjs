import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite();
const dir=new URL('../../supabase/migrations/', import.meta.url).pathname;
// Supabase の最小限の模擬
await db.exec(`
create role anon nologin; create role authenticated nologin; create role service_role nologin;
create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated;
grant execute on function auth.uid() to anon, authenticated;
alter default privileges in schema public grant all on tables to anon, authenticated;
alter default privileges in schema public grant all on sequences to anon, authenticated;
`);
for (const f of fs.readdirSync(dir).sort()) { await db.exec(fs.readFileSync(dir+f,'utf8')); console.log('applied', f); }
const A='11111111-1111-1111-1111-111111111111', B='22222222-2222-2222-2222-222222222222';
await db.exec(`insert into auth.users (id) values ('${A}'),('${B}');
insert into public.checkins (user_id, airport_id, terminal_id, lat, lon, accuracy_m, position_at) values
 ('${A}', 4, 'HND-T1', 35.5489, 139.7844, 30, now()), ('${B}', 4, null, 35.55, 139.78, 30, now());`);
console.log((await db.query(`select count(*)::int n, sum(game_target::int)::int g from public.airports`)).rows, (await db.query(`select count(*)::int n from public.terminals`)).rows);
const asUser = async (uid, sql) => {
  try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`);
        const r = await db.query(sql); return r.rows ?? 'ok'; }
  catch(e){ return 'ERROR: '+e.message.split('\n')[0]; }
  finally { await db.exec('reset role'); }
};
console.log('A reads checkins:', await asUser(A, 'select user_id, terminal_id from public.checkins'));
console.log('A inserts checkin:', await asUser(A, `insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${A}',4,0,0,1,now())`));
console.log('A updates checkin:', await asUser(A, `update public.checkins set airport_id=5`));
console.log('A adds manual:', await asUser(A, `insert into public.manual_flights (from_airport,to_airport,flown_on) values (4,6,'2025-05-01') returning user_id`));
console.log('A adds manual for B:', await asUser(A, `insert into public.manual_flights (user_id,from_airport,to_airport,flown_on) values ('${B}',4,6,'2025-05-01')`));
console.log('B reads manual:', await asUser(B, 'select * from public.manual_flights'));
console.log('anon reads airports:', (await (async()=>{await db.exec('set role anon'); const r=await db.query('select count(*)::int n from public.airports'); await db.exec('reset role'); return r.rows;})()));
