// エアライン経営のアーリーアクセス公開：本番だけでスイッチを入れる（試験ではオフのまま）・運営は co_v3 も切り替えられる
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`set co3.season_day = '2026-05-20'`);   // 季節の需要のない日で手計算する（季節は t72）
const ADM = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', U = '11111111-1111-1111-1111-111111111111';
await db.exec(`insert into auth.users (id) values ('${ADM}'),('${U}'); insert into ops.admins values ('${ADM}');`);
const as = async (role, uid, sql) => { try { await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const flag = async (k) => (await db.query(`select value from ops.flags where key = '${k}'`)).rows[0].value;
check('試験のデータベースでは2つのスイッチはオフのまま', (await flag('game_released')) === false && (await flag('co_v3')) === false, null);
check('利用者は co_v3 を切り替えられない', String(await as('authenticated', U, `select public.admin_set_flag('co_v3','true'::jsonb)`)).includes('admin only'), null);
await as('authenticated', ADM, `select public.admin_set_flag('co_v3','true'::jsonb)`);
check('運営は co_v3 を切り替えられる', (await flag('co_v3')) === true, null);
await as('authenticated', ADM, `select public.admin_set_flag('co_v3','false'::jsonb)`);
check('運営は co_v3 を戻せる', (await flag('co_v3')) === false, null);
check('知らないスイッチは断る', String(await as('authenticated', ADM, `select public.admin_set_flag('nope','true'::jsonb)`)).includes('unknown flag'), null);
const n = Number((await db.query(`select count(*) as n from ops.admin_actions where target = 'co_v3'`)).rows[0].n);
check('切り替えは運営の記録に残る', n === 2, n);
console.log(bad ? `NG ${bad}` : 'ALL OK'); process.exit(bad ? 1 : 0);
