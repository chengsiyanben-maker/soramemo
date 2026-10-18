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
// 到着予想の当たり具合（機種ごとのまとめ）
const d0 = `(now() at time zone 'Asia/Tokyo')::date - 1`;
for (let i = 0; i < 4; i++) await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, ata, ata_src, eta30, type)
  values (${d0}, 'JL10${i}', 'HND', 'ITM', now() - interval '3 hours', now() - interval '2 hours', now() - interval '2 hours', 'odpt', now() - interval '2 hours' - interval '${6 + i} minutes', 'B763')`);
let r = await as('anon', `select public.eta_accuracy(7)`);
const b = (r?.by_type ?? []).find((x) => x.type === 'B763');
check('機種ごとに、予想と実際の差をまとめる（早すぎると負）', b && b.n === 4 && Number(b.mean) === -7.5, r);
check('3便より少ない機種は出さない', (r?.by_type ?? []).length === 1, r);
if (bad) process.exit(1);
