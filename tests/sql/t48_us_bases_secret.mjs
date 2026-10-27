// 米軍が管理する横田・嘉手納・普天間は「一般の人が行けない飛行場」（secret）。基地の枠（mil）は自衛隊だけで、厚木は基地のまま。
// 移行は何度流しても同じ。空港の表の RLS は今のまま（だれでも読めて、書く決まりはない）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const kinds = async () => Object.fromEntries((await db.query(`select id, extra_kind from public.airports where id in (1015, 1016, 1029, 1030, 4001)`)).rows.map((r) => [r.id, r.extra_kind]));
let k = await kinds();
check('横田・嘉手納・普天間は秘密の枠', k[1015] === 'secret' && k[1029] === 'secret' && k[1030] === 'secret', k);
check('厚木は基地の枠のまま、硫黄島は秘密のまま', k[1016] === 'mil' && k[4001] === 'secret', k);
const n = async () => (await db.query(`select extra_kind, count(*)::int n from public.airports where extra_kind in ('mil', 'secret') group by 1`)).rows;
const before = JSON.stringify(await n());
check('基地は27か所、秘密は5か所', JSON.stringify((await n()).sort((a, b) => a.extra_kind.localeCompare(b.extra_kind))) === JSON.stringify([{ extra_kind: 'mil', n: 27 }, { extra_kind: 'secret', n: 5 }]), await n());
await db.exec(fs.readFileSync(dir + files.find((f) => f.endsWith('_fields.sql')), 'utf8'));
await db.exec(fs.readFileSync(dir + files.find((f) => f.endsWith('_us_bases_secret.sql')), 'utf8'));
check('前の移行を流し直しても戻らない・何度流しても同じ', JSON.stringify(await n()) === before && (await kinds())[1015] === 'secret');
// 空港の表の決まり（RLS）は今のまま：だれでも読めて、書く決まりはない
const pol = (await db.query(`select cmd, roles::text from pg_policies where schemaname = 'public' and tablename = 'airports'`)).rows;
const rls = (await db.query(`select relrowsecurity from pg_class where oid = 'public.airports'::regclass`)).rows[0].relrowsecurity;
check('RLS は有効で、読む決まりだけ（書く決まりはない）', rls && pol.length === 1 && pol[0].cmd === 'SELECT' && pol[0].roles.includes('anon'), pol);
if (bad) process.exit(1);
