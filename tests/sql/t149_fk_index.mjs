// 定期の手入れ 11/26 の5回目（移行210）：消すときに連動する外部キー（cascade・set null）は、どれも索引で探せることの見張り
//   退会や協力者を外すとき、つながった表を「その列 = 消した行の id」で探す。その形を全部読み禁止の計画にかけ、
//   全部読みになる外部キーが1つもないことを確かめる。新しい表で索引を忘れたら、ここで落ちて気づける。
//   あわせて、移行210 で足した索引の表の RLS が今のまま（有効）であること、退会の削除が実際に通ることを確かめる。
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

// 1. 連動する外部キーを全部、全部読み禁止の計画にかける
const fks = (await db.query(`
select c.conrelid::regclass::text tbl, c.confrelid::regclass::text ref, c.confdeltype del,
       array(select a.attname::text from unnest(c.conkey) with ordinality k(n, ord) join pg_attribute a on a.attrelid = c.conrelid and a.attnum = k.n order by k.ord) cols,
       array(select format_type(a.atttypid, a.atttypmod) from unnest(c.conkey) with ordinality k(n, ord) join pg_attribute a on a.attrelid = c.conrelid and a.attnum = k.n order by k.ord) types
  from pg_constraint c
 where c.contype = 'f' and c.connamespace in ('public'::regnamespace, 'ops'::regnamespace) and c.confdeltype in ('c', 'n', 'd')
 order by 1, 2`)).rows;
const lit = t => t === 'uuid' ? `'00000000-0000-0000-0000-000000000001'::uuid` : /int/.test(t) ? `1::${t}` : `'x'::${t}`;
await db.exec('set enable_seqscan = off');
const seq = [];
for (const f of fks) {
  const where = f.cols.map((c, i) => `"${c}" = ${lit(f.types[i])}`).join(' and ');
  const plan = (await db.query(`explain select 1 from ${f.tbl} where ${where}`)).rows.map(r => r['QUERY PLAN']).join(' ');
  if (/Seq Scan/.test(plan)) seq.push(`${f.tbl}.${f.cols.join(',')} → ${f.ref}`);
}
await db.exec('reset enable_seqscan');
check(`連動する外部キー ${fks.length}本がすべて索引で探せる`, fks.length > 50 && seq.length === 0, seq);

// 2. 足した6つの索引がある・RLS は今のまま
const idx = (await db.query(`select indexname from pg_indexes where indexname = any($1)`,
  [['atc_msgs_feeder', 'co3_invest_investor', 'co3_invest_target', 'co3_market_seller', 'co3_market_buyer', 'co3_alliances_leader']])).rows.map(r => r.indexname);
check('移行210 の索引が6つある', idx.length === 6, idx);
const rls = (await db.query(`select relname, relrowsecurity from pg_class where oid = any(array['public.atc_msgs','public.co3_invest','public.co3_market','public.co3_alliances']::regclass[])`)).rows;
check('4つの表の RLS は有効のまま', rls.length === 4 && rls.every(r => r.relrowsecurity), rls);

// 3. 退会の削除が通る（つながった行は消える／空になる。全機の記録の表には触らない）
const U1 = '00000000-0000-0000-0000-0000000000b1', U2 = '00000000-0000-0000-0000-0000000000b2';
await db.exec(`insert into auth.users (id, email) values ('${U1}', 'b1@example.com'), ('${U2}', 'b2@example.com');
insert into public.atc_feeders (id, user_id, kind, token_hash, iata, consent_at) values ('00000000-0000-0000-0000-0000000000f1', '${U1}', 'pc', 'h1', 'HND', now());
insert into public.atc_msgs (iata, ch, at, feeder, text_en) values ('HND', 'twr', now(), '00000000-0000-0000-0000-0000000000f1', 'x')`);
const before = (await db.query(`select count(*)::int n from public.atc_feeders where user_id = '${U1}'`)).rows[0].n;
await db.exec(`delete from auth.users where id = '${U1}'`);
const after = (await db.query(`select count(*)::int n from public.atc_feeders where user_id = '${U1}'`)).rows[0].n;
const msg = (await db.query(`select count(*)::int n, count(feeder)::int f from public.atc_msgs`)).rows[0];
check('退会の削除が通り、協力者の行は消え、交信は残って協力者の欄だけ空になる', before === 1 && after === 0 && msg.n === 1 && msg.f === 0, { before, after, msg });

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('t149 すべて OK');
