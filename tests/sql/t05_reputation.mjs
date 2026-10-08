import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir=new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth; create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated; grant execute on function auth.uid() to anon, authenticated;
alter default privileges in schema public grant all on tables to anon, authenticated; alter default privileges in schema public grant all on sequences to anon, authenticated;`);
for (const f of fs.readdirSync(dir).sort()) { await db.exec(fs.readFileSync(dir+f,'utf8')); }
await db.exec(`update ops.flags set value = 'true' where key = 'game_released'`);   // 会社のテストは、エアライン経営の公開後の状態で行う
console.log('applied all');
const A='11111111-1111-1111-1111-111111111111';
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('HND','CTS','OKA','ISG','KIX')`)).rows.map(r=>[r.iata,r.id]));
await db.exec(`insert into auth.users (id) values ('${A}');`);
const fl = (a,b,km) => db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values ('${A}',${a},${b},now()-interval '3 hours',now()-interval '1 hour',${km})`);
const ci = a => db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${A}', ${a}, 0,0,10, now())`);
await fl(ids.HND, ids.CTS, 819.6); await fl(ids.OKA, ids.ISG, 395.4);
for (const k of ['HND','CTS','OKA','ISG']) await ci(ids[k]);
await db.exec(`insert into companies (user_id, cash) values ('${A}', 50000)`);
const as = async (sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${A}',false);`); const r = await db.query(sql); return Object.values(r.rows[0])[0]; } catch(e){ return 'ERROR: '+e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const brief = j => typeof j === 'string' ? j : JSON.stringify({cash:j.cash, daily:j.daily, pts:j.rep_points, stars:j.stars, rb:j.rep_bonus, fac:j.facilities, routes:j.routes.map(r=>`${r.k}:${r.base}x${r.hub}`)});
console.log('state:', brief(await as('select public.co_state()')));   // 4*10 + 2*20 = 80 -> ★1
console.log('build HND (1 slot at ★1):', brief(await as(`select public.co_build(${ids.HND})`)));   // +10 -> 90
console.log('build CTS (no slot):', await as(`select public.co_build(${ids.CTS})`));
console.log('upgrade HND -> 2:', brief(await as(`select public.co_build(${ids.HND})`)));  // 100 -> ★2, +5%
console.log('build CTS (★2 = 2 slots):', brief(await as(`select public.co_build(${ids.CTS})`)));
console.log('build unvisited KIX:', await as(`select public.co_build(${ids.KIX})`));
console.log('HND -> 3:', brief(await as(`select public.co_build(${ids.HND})`)));
console.log('HND -> 4 (max):', await as(`select public.co_build(${ids.HND})`));
console.log('direct insert:', await as(`insert into facilities (user_id, airport_id, level) values ('${A}', ${ids.OKA}, 3)`));
// JSでの期待値: HND-CTS base 344, hub = 1 + .3 + .1 = 1.4 ; OKA-ISG 179 ; stars? 
