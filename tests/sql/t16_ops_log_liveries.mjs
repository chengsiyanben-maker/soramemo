// 運用の判定の記録と、特別塗装機：表は利用者から読めない・特別塗装機は直近15分のものだけ関数で読める・まとめは運営者だけ
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
await db.exec(`insert into public.ops_log (iata, est_mode, obs_mode) values ('FUK','b','a'),('FUK','a','a'),('HND','north',null);
insert into public.livery_sightings (reg, name, airline, lat, lon, src, iata, phase) values ('JA819A','ポケモンジェット 赤','ANA',35.5,139.8,'https://example','HND','arr');
insert into public.livery_sightings (reg, name, airline, lat, lon, src, seen_at) values ('JA05RK','ジンベエジェット','JTA',26.2,127.6,'https://example', now() - interval '20 minutes');`);
for (const t of ['ops_log', 'livery_sightings']) {
  const r = await as('anon', `select count(*) from public.${t}`);
  check(`${t} は利用者から直接読めない`, String(r).startsWith('ERROR'), r);
}
let r = await as('anon', `select public.special_now()`);
check('特別塗装機は直近15分に見えたものだけ読める', Array.isArray(r) && r.length === 1 && r[0].reg === 'JA819A' && r[0].iata === 'HND', r);
r = await as('anon', `select * from public.ops_log_summary(7)`);
check('運用の記録のまとめは利用者から呼べない', String(r).startsWith('ERROR'), r);
r = (await db.query(`select * from public.ops_log_summary(7) where iata = 'FUK'`)).rows[0];
check('まとめ：福岡は2件中、一致1・食い違い1', r && Number(r.samples) === 2 && Number(r.agree) === 1 && Number(r.disagree) === 1, r);
r = await as('anon', `select count(*) from public.livery_notified`);
check('特別塗装機の通知の記録は利用者から読めない', String(r).startsWith('ERROR'), r);
await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, sp_airports) values ('https://fcm.googleapis.com/sp','k','a','{HND,FUK}')`);
r = (await db.query(`select count(*)::int n from public.push_subs where sp_airports @> array['HND']`)).rows[0].n;
check('特別塗装機の通知を空港で選べる', r === 1, r);
if (bad) process.exit(1);
