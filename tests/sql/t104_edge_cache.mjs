// 関数どうしで使い回す置き場（edge_cache、移行 164）：形・鍵の決まり・上書きで増えない・RLS（anon と authenticated は読めも書けもしない）・もう一度流しても同じ
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const mine = files.find(f => f.endsWith('_edge_cache.sql'));
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));
// 本番の Supabase は public の表に select を既定で渡している。移行の revoke がそれを取り上げることを確かめるため、先に渡してからもう一度流す
await db.exec(`grant select, insert, update, delete on public.edge_cache to anon, authenticated`);
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const q = async (sql) => (await db.query(sql)).rows;
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const as = async (role, sql) => {
  try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; }
  finally { await db.exec(`reset role`); }
};
const isErr = (v) => String(v).startsWith('ERROR');

// 1. 形
check('移行は 164 番', /^\d{8}000164_edge_cache\.sql$/.test(mine), mine);
const cols = await q(`select column_name c, data_type t, is_nullable n from information_schema.columns where table_schema = 'public' and table_name = 'edge_cache' order by ordinal_position`);
check('列は key（text）・body（jsonb）・at（timestamptz）で、どれも空にできない', JSON.stringify(cols) === JSON.stringify([{ c: 'key', t: 'text', n: 'NO' }, { c: 'body', t: 'jsonb', n: 'NO' }, { c: 'at', t: 'timestamp with time zone', n: 'NO' }]), cols);
check('fillfactor 70（上書きを同じページで）', JSON.stringify(await q1(`select reloptions from pg_class where oid = 'public.edge_cache'::regclass`)) === JSON.stringify(['fillfactor=70']), null);

// 2. 鍵の決まり
for (const k of ['now:fl:HND', 'now:wx:RJTT', 'now:taf:ROAH', 'metar:RJTT'])
  check(`鍵 ${k} は入る`, !isErr(await as('service_role', `insert into public.edge_cache (key, body) values ('${k}', '{}')`)), k);
for (const k of ['', 'NOW:fl:HND', 'now', 'now:fl:HND;drop', 'now:fl:' + 'A'.repeat(40)])
  check(`鍵 "${k.slice(0, 20)}" は断る`, isErr(await as('service_role', `insert into public.edge_cache (key, body) values ('${k}', '{}')`)), k);
check('「通報がない」は JSON の null として入る', !isErr(await as('service_role', `insert into public.edge_cache (key, body) values ('now:wx:RJFK', 'null')`)), null);

// 3. 上書きで増えない（関数の upsert と同じ形）
await db.exec(`insert into public.edge_cache (key, body, at) values ('now:fl:HND', '{"arr":[1]}', now()) on conflict (key) do update set body = excluded.body, at = excluded.at`);
check('同じ鍵は1行のまま中身だけ変わる', await q1(`select count(*)::int from public.edge_cache where key = 'now:fl:HND'`) === 1 && (await q1(`select body->'arr'->>0 from public.edge_cache where key = 'now:fl:HND'`)) === '1', null);
check('合わせて5行（入れた鍵の数）', await q1(`select count(*)::int from public.edge_cache`) === 5, await q(`select key from public.edge_cache`));

// 4. RLS
check('RLS は有効', await q1(`select relrowsecurity from pg_class where oid = 'public.edge_cache'::regclass`) === true, null);
check('ポリシーはない（service_role だけが使う）', await q1(`select count(*)::int from pg_policies where tablename = 'edge_cache'`) === 0, null);
for (const role of ['anon', 'authenticated']) {
  check(`${role} は読めない`, isErr(await as(role, `select count(*) from public.edge_cache`)), null);
  check(`${role} は足せない`, isErr(await as(role, `insert into public.edge_cache (key, body) values ('now:fl:ITM', '{}')`)), null);
  check(`${role} は直せない`, isErr(await as(role, `update public.edge_cache set body = '{}' where key = 'now:fl:HND'`)), null);
  check(`${role} は消せない`, isErr(await as(role, `delete from public.edge_cache`)), null);
}
check('service_role は読み書きできる', await as('service_role', `select count(*)::int from public.edge_cache`) === 5, null);

// 5. もう一度流しても同じ（行も残る）
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流しても行は残る', await q1(`select count(*)::int from public.edge_cache`) === 5, null);

console.log(bad ? `\n${bad} 件 NG` : '\nすべて OK'); process.exit(bad ? 1 : 0);
