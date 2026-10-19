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
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
// パスポート用：利用者のフライトに便ごとの実績を付ける（共同運航の便名でも引ける）
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, ata, ata_src, arr_delay, type, reg, also) values
  ('2026-10-10', 'HD15', 'HND', 'CTS', '2026-10-10T01:00:00Z', '2026-10-10T02:30:00Z', '2026-10-10T02:52:00Z', 'odpt', 22, 'B763', 'JA01HD', '{NH4715}'),
  ('2026-10-11', 'JL501', 'HND', 'CTS', '2026-10-11T01:00:00Z', '2026-10-11T02:30:00Z', null, null, null, 'B738', 'JA301J', '{}')`);
let r = await as('anon', `select public.flight_facts('[{"f":"NH4715","d":"2026-10-10","a":"HND"},{"f":"JL501","d":"2026-10-11","a":"HND"},{"f":"JL999","d":"2026-10-11","a":"HND"},{"f":"bad","d":"x","a":"HND"}]'::jsonb)`);
check('共同運航の便名でも実績が付く', r?.find?.((x) => x.f === 'NH4715')?.arr_delay === 22 && r.find((x) => x.f === 'NH4715').reg === 'JA01HD', r);
check('記録のない便・形の違う入力は返さない', r?.length === 2, r);
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, ata, ata_src, arr_delay, also) values
  ('2026-10-12', 'NH059', 'HND', 'CTS', '2026-10-12T01:00:00Z', '2026-10-12T02:30:00Z', '2026-10-12T02:40:00Z', 'odpt', 10, '{HD0059}')`);
r = await as('anon', `select public.flight_facts('[{"f":"NH59","d":"2026-10-12","a":"HND"},{"f":"HD59","d":"2026-10-12","a":"HND"},{"f":"NH590","d":"2026-10-12","a":"HND"}]'::jsonb)`);
check('時刻表の便名の0（NH059）と利用者の便名（NH59）を同じとみなす。共同運航の便名も', r?.length === 2 && r.every((x) => x.arr_delay === 10), r);
r = await as('anon', `select public.flight_facts('"oops"'::jsonb)`);
check('配列でない入力は空で返す', Array.isArray(r) && r.length === 0, r);
if (bad) process.exit(1);
