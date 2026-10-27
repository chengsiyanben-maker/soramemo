// 門限チャレンジ：伊丹・福岡だけ、門限の前後の便を返す（遠い時間の便・ほかの空港の便は出さない）
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
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
// 運用タブの「昨日の〇〇」
const y = `(now() at time zone 'Asia/Tokyo')::date - 1`;
await db.exec(`insert into public.airport_daily (day, iata, flights, arr, dep, late, cancelled, diverted, avg_delay, modes, max_wind) values
  (${y}, 'HND', 1000, 500, 500, 80, 2, 1, 27.5, '{"north": 900, "south": 540}', 18),
  (${y} - 1, 'HND', 1000, 500, 500, 40, 0, 0, 20, null, 8), (${y} - 2, 'HND', 1000, 500, 500, 60, 4, 0, 22, null, 9)`);
let r = await as('anon', `select public.airport_yesterday('HND')`);
check('昨日のまとめを返す', r?.flights === 1000 && r?.late === 80 && r?.modes?.north === 900, r);
check('その前の7日の平均を添える', r?.ref?.days === 2 && Number(r.ref.late) === 50, r?.ref);
r = await as('anon', `select public.airport_yesterday('ZZZ')`);
check('記録のない空港は null', r === null || r === 'ok', r);
if (bad) process.exit(1);
