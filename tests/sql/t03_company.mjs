import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir=new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth; create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated; grant execute on function auth.uid() to anon, authenticated;
alter default privileges in schema public grant all on tables to anon, authenticated; alter default privileges in schema public grant all on sequences to anon, authenticated;`);
for (const f of fs.readdirSync(dir).sort()) { await db.exec(fs.readFileSync(dir+f,'utf8')); console.log('applied', f); }
await db.exec(`update ops.flags set value = 'true' where key = 'game_released'`);   // 会社のテストは、エアライン経営の公開後の状態で行う
const A='11111111-1111-1111-1111-111111111111', B='22222222-2222-2222-2222-222222222222';
// HND=5, CTS=6, OKA? find ids
const ids = Object.fromEntries((await db.query(`select iata, id, radius_m from airports where iata in ('HND','CTS','OKA','ISG')`)).rows.map(r=>[r.iata,r]));
console.log(ids);
await db.exec(`insert into auth.users (id) values ('${A}'),('${B}');`);
const ins = (u,a,b,km) => db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values ('${u}',${a},${b},now()-interval '3 hours',now()-interval '1 hour',${km})`);
await ins(A, ids.HND.id, ids.CTS.id, 819.6); await ins(A, ids.CTS.id, ids.HND.id, 819.6); await ins(A, ids.OKA.id, ids.ISG.id, 395.4);
for (let i=0;i<20;i++) await db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${A}', ${ids.HND.id}, 0,0,10, now())`);
await db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at) values ('${A}', ${ids.CTS.id}, 0,0,10, now())`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows; } catch(e){ return 'ERROR: '+e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const st = r => typeof r === 'string' ? r : JSON.stringify((({name,cash,daily,bonus,pending,routes,roles})=>({name,cash,daily,bonus,pending,routes,roles}))(Object.values(r[0])[0]));
console.log('state:', st(await as(A, 'select public.co_state()')));
// JS式で期待値
const js = (km,s1,s2)=>Math.round(Math.sqrt(km)*(s1+s2)*2); const sz=r=>r>=2000?3:r>=1500?2:1.5;
console.log('js base HND-CTS', js(819.6, sz(ids.HND.radius_m), sz(ids.CTS.radius_m)), 'OKA-ISG', js(395.4, sz(ids.OKA.radius_m), sz(ids.ISG.radius_m)));
// 3日前に受け取ったことにする（管理者権限で）
await db.exec(`update companies set last_collect = now() - interval '3 days' where user_id='${A}'`);
console.log('collect:', st(await as(A, 'select public.co_collect()')));
console.log('collect again (0):', st(await as(A, 'select public.co_collect()')));
const key = `${Math.min(ids.HND.id,ids.CTS.id)}-${Math.max(ids.HND.id,ids.CTS.id)}`;
console.log('upgrade:', st(await as(A, `select public.co_upgrade('${key}')`)));
console.log('upgrade unknown route:', await as(A, `select public.co_upgrade('1-2')`));
console.log('upgrade broke:', await as(A, `select public.co_upgrade('${key}')`));
console.log('role sales HND:', st(await as(A, `select public.co_set_role('sales', ${ids.HND.id})`)));
console.log('role crew HND (moves):', st(await as(A, `select public.co_set_role('crew', ${ids.HND.id})`)));
console.log('role unmet OKA:', await as(A, `select public.co_set_role('maint', ${ids.OKA.id})`));
console.log('bad role:', await as(A, `select public.co_set_role('ceo', ${ids.HND.id})`));
console.log('rename:', st(await as(A, `select public.co_rename('  羽田エアライン ')`)), await as(A, `select public.co_rename('${'あ'.repeat(21)}')`));
console.log('direct cash edit:', await as(A, `update companies set cash = 999999999`));
console.log('call helper:', await as(A, `select * from public.co_routes('${A}')`));
console.log('B sees A company:', await as(B, `select * from companies`));
console.log('B state (own, empty):', st(await as(B, 'select public.co_state()')));
