// 撮影の知らせを「表示する機体」と同じ選び方で：機種のまとまり・1機ずつ選んだ特別塗装機の名前を残せる。決まった形以外は入らない。利用者からは読めない
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
const run = async (sql) => { try { const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } };

const ok = async (sql) => { try { await db.exec(sql); return true; } catch { return false; } };
const base = (n, more) => `insert into public.push_subs (endpoint, p256dh, auth, spot_iata, spot_kinds, spot_fams, spot_livs) values ('https://fcm.googleapis.com/f${n}', 'k', 'a', 'HND', '{}', ${more})`;
check('機種のまとまりと塗装機の名前を残せる', await ok(base(1, `array['777','787','small'], array['ポケモンジェット','嵐ジェット']`)));
check('はじめは空', await ok(`insert into public.push_subs (endpoint, p256dh, auth) values ('https://fcm.googleapis.com/f2', 'k', 'a')`) &&
  (await db.query(`select cardinality(spot_fams) + cardinality(spot_livs) as n from public.push_subs where endpoint like '%/f2'`)).rows[0].n === 0);
check('決まっていない機種のまとまりは入らない', !(await ok(base(3, `array['DC10'], '{}'`))));
check('塗装機の名前は30まで', !(await ok(base(4, `'{}', array(select 'x' || g from generate_series(1, 31) g)`))));
let denied = false; await db.exec('set role anon'); try { await db.query('select spot_fams from public.push_subs'); } catch { denied = true; } await db.exec('reset role');
check('利用者からは読めない', denied);
if (bad) process.exit(1);
