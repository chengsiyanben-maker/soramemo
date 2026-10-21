// 管制の交信：表は直接読めない。atc_recent は確かめたものだけ（英語・協力者は出さない）。協力の合言葉は1回だけ返し、ハッシュだけ残す
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id, email) values ('${A}', 'a@example.com'), ('${B}', 'b@example.com')`);
const as = async (uid, sql) => { try { await db.exec(`set request.jwt.claim.sub = '${uid ?? ''}'; set role ${uid ? 'authenticated' : 'anon'}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec(`reset role; reset request.jwt.claim.sub`); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
check('同意しないと始められない', String(await as(A, `select public.atc_new_feeder('phone', 'ota', false)`)).startsWith('ERROR'));
check('ログインしないと始められない', String(await as(null, `select public.atc_new_feeder('phone', 'ota', true)`)).startsWith('ERROR'));
const f = await as(A, `select public.atc_new_feeder('phone', 'ota', true)`);
check('合言葉を返す', f && /^[0-9a-f]{64}$/.test(f.token), f);
const h = (await db.query(`select token_hash from public.atc_feeders where id = '${f.id}'`)).rows[0].token_hash;
check('保存するのはハッシュだけ', h !== f.token && h.length === 64);
await db.exec(`insert into public.atc_msgs (iata, ch, at, feeder, text_en, callsign, flight, items, ja, tags, verified) values
  ('HND', 'twr', now() - interval '1 minute', '${f.id}', 'Japan Air 123 cleared to land', 'JAL123', 'JL123', '[{"k":"land","rwy":"22"}]', '22滑走路への着陸を許可。', '{着陸許可}', true),
  ('HND', 'twr', now() - interval '2 minute', '${f.id}', 'Japan Air 999 cleared to land', 'JAL999', 'JL999', '[{"k":"land"}]', 'x', '{}', false),
  ('NRT', 'gnd', now(), '${f.id}', 'x', 'ANA1', 'NH1', '[]', 'y', '{}', true)`);
const r = await as(null, `select public.atc_recent('HND', null, 30)`);
check('確かめたものだけ・英語と協力者は出さない', Array.isArray(r) && r.length === 1 && r[0].flight === 'JL123' && r[0].text_en === undefined && r[0].feeder === undefined, r);
check('表は直接読めない', String(await as(null, `select count(*) from public.atc_msgs`)).startsWith('ERROR') && String(await as(A, `select count(*) from public.atc_feeders`)).startsWith('ERROR'));
await db.exec(`update public.atc_feeders set iata = 'HND', ch = 'twr', last_seen = now()`);
const c = await as(null, `select public.atc_coverage()`);
const tw = c.ch.find((x) => x.iata === 'HND' && x.ch === 'twr');
check('受信のネットワーク', tw && tw.live === 1 && tw.today >= 1 && c.areas.ota === 1, c);
const mine = await as(A, `select public.atc_my_feeders()`);
check('自分の協力の記録', mine.length === 1 && mine[0].sent === 0 && mine[0].shown === 2, mine);
check('ほかの人の協力は見えない', (await as(B, `select public.atc_my_feeders()`)).length === 0);
await as(B, `select public.atc_delete_feeder('${f.id}')`);
check('ほかの人は消せない', (await db.query(`select count(*)::int as n from public.atc_feeders`)).rows[0].n === 1);
await as(A, `select public.atc_delete_feeder('${f.id}')`);
check('自分のは消せる（交信は残る）', (await db.query(`select count(*)::int as n from public.atc_feeders`)).rows[0].n === 0 && (await db.query(`select count(*)::int as n from public.atc_msgs`)).rows[0].n === 3);
if (bad) process.exit(1);
