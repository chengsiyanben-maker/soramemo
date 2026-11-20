// 定期の手入れ 11/16 の2回目（移行 188。もとは 183・PR #111）：引く索引のない外部キーとよく引く列に索引を足す
//   1. 188 のあと、public の外部キーで「先頭がその列の索引」がないものは、空港・端末・種類の表を指すもの（ほぼ消さない小さな表）と
//      auth.users を指す経営の数本（1人消すとき1回だけ読む）だけになったか（足した8本が効いているか）
//   2. 部分索引でも、外部キーの確かめと同じ形（列 = $1 の汎用の計画）で索引が使われるか
//   3. 退会（auth.users を消す）と機体を売る形（aircraft を消す）が今までどおり動き、set null・cascade の結果が同じか
//   4. 表・列・RLS・権限は変わらず、同じ表で重なる索引を増やしていないか
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const NEW = '20261120000188_maint_1116b.sql';
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const rows = async (sql, p) => (await db.query(sql, p)).rows;

// 外部キーのうち、先頭がその列の索引（部分索引なら「列 is not null」だけのもの）がないもの
const NOIDX = `select c.conrelid::regclass::text tbl,
    (select string_agg(a.attname, ',' order by k.o) from unnest(c.conkey) with ordinality k(n, o)
      join pg_attribute a on a.attrelid = c.conrelid and a.attnum = k.n) cols, c.confrelid::regclass::text ref
  from pg_constraint c join pg_class t on t.oid = c.conrelid join pg_namespace n on n.oid = t.relnamespace
  where c.contype = 'f' and n.nspname = 'public'
    and not exists (select 1 from pg_index i where i.indrelid = c.conrelid
      and (i.indpred is null or array_length(c.conkey, 1) = 1 and pg_get_expr(i.indpred, i.indrelid) in
        (select a.attname || ' IS NOT NULL' from pg_attribute a where a.attrelid = c.conrelid and a.attnum = c.conkey[1]
         union all select '(' || a.attname || ' IS NOT NULL)' from pg_attribute a where a.attrelid = c.conrelid and a.attnum = c.conkey[1]))
      and (i.indkey::int2[])[0:array_length(c.conkey, 1) - 1] @> c.conkey
      and (i.indkey::int2[])[0:array_length(c.conkey, 1) - 1] <@ c.conkey)
  order by 1, 2`;
const SHAPE = `select (select json_agg(x order by x) from (select table_name || '.' || column_name || ':' || data_type x from information_schema.columns where table_schema = 'public') s) cols,
  (select json_agg(x order by x) from (select tablename || ':' || policyname || ':' || qual x from pg_policies where schemaname = 'public') s) pol,
  (select json_agg(x order by x) from (select table_name || ':' || grantee || ':' || privilege_type x from information_schema.role_table_grants where table_schema = 'public') s) grants,
  (select count(*)::int from pg_indexes where schemaname = 'public') nidx`;

for (const f of files) if (f < NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const before = (await rows(SHAPE))[0];
const noBefore = await rows(NOIDX);
await db.exec(fs.readFileSync(dir + NEW, 'utf8'));
await db.exec(fs.readFileSync(dir + NEW, 'utf8'));   // 2回流しても困らない（if not exists）
const after = (await rows(SHAPE))[0];   // 188 だけの変化を比べる（あとの移行が表を足しても落ちないように・11/21 移行190）
for (const f of files) if (f > NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const noAfter = await rows(NOIDX);

// 1
const WANT = ['aircraft.user_id', 'flights.dep_checkin', 'flights.arr_checkin', 'co3_market.aircraft_id', 'co3_orders.aircraft_id',
  'co3_breakdowns.spare_id', 'co3_heavy.spare_id', 'co3_extra.aircraft_id'];
const has = (list, k) => list.some((r) => `${r.tbl}.${r.cols}` === k);
check('188 の前は8本とも引く索引がなかった', WANT.every((k) => has(noBefore, k)), WANT.filter((k) => !has(noBefore, k)));
check('188 のあとは8本とも引く索引がある', WANT.every((k) => !has(noAfter, k)), WANT.filter((k) => has(noAfter, k)));
const SMALL = ['public.airports', 'public.terminals', 'public.co3_types', 'public.game_events', 'public.atc_feeders', 'airports', 'terminals', 'co3_types', 'game_events', 'atc_feeders', 'auth.users'];
const left = noAfter.filter((r) => !SMALL.includes(r.ref));
check('残るのは空港・端末・種類などの小さな表と auth.users を指すものだけ', left.length === 0, left);
check('足した索引はちょうど8本', after.nidx - before.nidx === 8, [before.nidx, after.nidx]);

// 2
await db.exec(`set plan_cache_mode = force_generic_plan; set enable_seqscan = off`);
const plan = async (sql) => (await rows(`explain ${sql}`)).map((r) => r['QUERY PLAN']).join(' / ');
for (const [q, idx] of [
  ['update public.flights set dep_checkin = null where dep_checkin = 1', 'flights_dep_checkin'],
  ['update public.flights set arr_checkin = null where arr_checkin = 1', 'flights_arr_checkin'],
  ['select 1 from public.aircraft where user_id = \'00000000-0000-0000-0000-000000000001\'', 'aircraft_user'],
  ['update public.co3_heavy set spare_id = null where spare_id = 1', 'co3_heavy_spare'],
  ['delete from public.co3_extra where aircraft_id = 1', 'co3_extra_aircraft'],
]) {
  await db.exec(`deallocate all; prepare p as ${q.replace(/= 1$/, '= $1::bigint').replace(/'0{8}-0{4}-0{4}-0{4}-0{11}1'$/, '$1::uuid')}`);
  const p = await plan(`execute p(${q.includes('user_id') ? "'00000000-0000-0000-0000-000000000001'" : '1'})`);
  check(`汎用の計画で ${idx} を使う`, p.includes(idx), p);
}
await db.exec(`deallocate all; reset plan_cache_mode; reset enable_seqscan`);

// 3：退会と機体を売る形
const U = '00000000-0000-0000-0000-0000000000a1', V = '00000000-0000-0000-0000-0000000000b2';
await db.exec(`insert into auth.users (id) values ('${U}'), ('${V}')`);
const ap = (await rows(`select id from public.airports order by id limit 2`)).map((r) => r.id);
await db.exec(`insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at)
  values ('${U}', ${ap[0]}, 35, 139, 10, now()), ('${U}', ${ap[1]}, 34, 135, 10, now()), ('${V}', ${ap[0]}, 35, 139, 10, now())`);
const ck = (await rows(`select id, user_id from public.checkins order by id`));
await db.exec(`insert into public.flights (user_id, from_airport, to_airport, dep_checkin, arr_checkin, dep_at, arr_at, distance_km)
  values ('${V}', ${ap[0]}, ${ap[1]}, ${ck[0].id}, ${ck[2].id}, now() - interval '2 hours', now() - interval '1 hour', 400)`);
await db.exec(`delete from auth.users where id = '${U}'`);
const fl = (await rows(`select dep_checkin, arr_checkin from public.flights where user_id = '${V}'`))[0];
check('退会でチェックインが消え、ほかの人の便の dep_checkin は null・arr_checkin はそのまま', fl && fl.dep_checkin === null && Number(fl.arr_checkin) === Number(ck[2].id), fl);
check('退会した人のチェックインは残らない', (await rows(`select count(*)::int c from public.checkins where user_id = '${U}'`))[0].c === 0, null);
await db.exec(`insert into public.aircraft (user_id, type) values ('${V}', 'prop'), ('${V}', 'rj')`);
const ac = (await rows(`select id from public.aircraft where user_id = '${V}' order by id`)).map((r) => r.id);
await db.exec(`delete from public.aircraft where id = ${ac[0]}`);
check('機体を消しても動き、残りの機体はそのまま', (await rows(`select count(*)::int c from public.aircraft where user_id = '${V}'`))[0].c === 1, null);

// 4（before は 188 の前まで・after は 188 を流した直後）
check('列は変わらない', JSON.stringify(before.cols) === JSON.stringify(after.cols), null);
check('RLS のポリシーは変わらない', JSON.stringify(before.pol) === JSON.stringify(after.pol), null);
check('表の権限は変わらない', JSON.stringify(before.grants) === JSON.stringify(after.grants), null);
const dup = await rows(`select a.indexrelid::regclass::text a, b.indexrelid::regclass::text b from pg_index a join pg_index b
  on a.indrelid = b.indrelid and a.indexrelid <> b.indexrelid and a.indkey::text = b.indkey::text
  and coalesce(pg_get_expr(a.indpred, a.indrelid), '') = coalesce(pg_get_expr(b.indpred, b.indrelid), '')
  where a.indexrelid::regclass::text = any($1)`, [['aircraft_user', 'flights_dep_checkin', 'flights_arr_checkin', 'co3_market_aircraft', 'co3_orders_aircraft', 'co3_breakdowns_spare', 'co3_heavy_spare', 'co3_extra_aircraft']]);
check('足した索引と同じ形の索引はほかにない', dup.length === 0, dup);

if (bad) { console.log(`NG ${bad}件`); process.exit(1); }
console.log('すべて OK');
