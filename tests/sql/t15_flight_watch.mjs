// 遅れ・ダイバートのお知らせ：表は利用者から読めない・お知らせは関数で直近のものだけ読める・空港で絞れる
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
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values ('2026-10-26','JL509','HND','CTS','2026-10-26 01:00+00','2026-10-26 02:35+00','テスト');
insert into public.flight_alerts (kind, flight, dep, arr, iata, message) values ('divert','JL509','HND','CTS','{CTS,HKD,HND}','JL509は函館へ'),('delay_dep','NH1','HND','ITM','{HND,ITM}','NH1は遅れ');
insert into public.flight_alerts (kind, flight, dep, arr, iata, message, created_at) values ('delay_arr','BC1','HND','FUK','{FUK,HND}','古い', now() - interval '13 hours');`);
for (const t of ['flight_schedule', 'flight_watch', 'flight_alerts', 'push_subs']) {
  const r = await as('anon', `select count(*) from public.${t}`);
  check(`${t} は利用者から直接読めない`, String(r).startsWith('ERROR'), r);
}
let r = await as('anon', `select public.flight_alerts()`);
check('直近12時間のお知らせだけ読める', Array.isArray(r) && r.length === 2, r);
r = await as('anon', `select public.flight_alerts('hkd')`);
check('空港で絞れる（ダイバート先の函館でも出る）', Array.isArray(r) && r.length === 1 && r[0].flight === 'JL509', r);
r = await as('anon', `insert into public.push_subs (endpoint, p256dh, auth, airports) values ('https://fcm.googleapis.com/x','a','b','{HND}')`);
check('通知の宛先は利用者から書けない', String(r).startsWith('ERROR'), r);
r = await as('anon', `insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values ('2026-10-26','JL1','HND','ITM',now(),now(),'x')`);
check('ダイヤは利用者から書けない', String(r).startsWith('ERROR'), r);
await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, airports, flights) values ('https://fcm.googleapis.com/a','k','a','{}','{JL509@2026-10-26}')`);
r = (await db.query(`select count(*)::int n from public.push_subs where flights && array['JL509@2026-10-26']`)).rows[0].n;
check('便（便名@運航日）でも宛先を選べる', r === 1, r);
r = await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, flights) values ('https://fcm.googleapis.com/b','k','a','{a,b,c,d,e,f}')`).then(() => 'ok').catch((e) => 'ERROR');
check('便は5つまで', r === 'ERROR', r);
if (bad) process.exit(1);
