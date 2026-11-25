// 定期の手入れ 11/26（移行 201）
//   1. rwy_sample_counts：anon・authenticated は呼べない。持ち主（SQL Editor）と service_role は今までどおり呼べ、答えも同じ。本文と設定は変わらない
//   2. airports (iata) の索引：airport_board の「相手の空港が国内か」と同じ形（iata = $1）で索引を使う。airport_board の答えは前と同じ
//   3. 表・列・RLS・表の権限は変わらず、索引は1本増えるだけ。ほかの関数の権限は変わらない。2回流しても壊れない
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const NEW = '20261126000201_maint_1126.sql';
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const rows = async (sql, p) => (await db.query(sql, p)).rows;
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec(`reset role`); } };
const SHAPE = `select (select json_agg(x order by x) from (select table_name || '.' || column_name || ':' || data_type x from information_schema.columns where table_schema = 'public') s) cols,
  (select json_agg(x order by x) from (select tablename || ':' || policyname || ':' || coalesce(qual, '') || ':' || coalesce(with_check, '') x from pg_policies where schemaname = 'public') s) pol,
  (select json_agg(x order by x) from (select table_name || ':' || grantee || ':' || privilege_type x from information_schema.role_table_grants where table_schema = 'public') s) grants,
  (select json_agg(x order by x) from (select p.oid::regprocedure::text || ':' || coalesce(p.proacl::text, '') x from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname <> 'rwy_sample_counts') s) fnacl,
  (select count(*)::int from pg_indexes where schemaname = 'public') nidx`;
const FN = `select pg_get_functiondef('public.rwy_sample_counts()'::regprocedure) def, (select proconfig from pg_proc where oid = 'public.rwy_sample_counts()'::regprocedure) cfg`;

for (const f of files) if (f < NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));

// 記録を少し入れる
await db.exec(`insert into public.rwy_samples (iata, at, callsign, flight, rwy, ent120, ent60, first_brg, pts, dir) values
  ('HND', now(), 'JAL510', 'JL510', '34L', 10, 20, 5, '[]', 'arr'), ('HND', now() - interval '1 day', 'ANA24', 'NH24', '34R', 200, 210, 205, '[]', 'arr'),
  ('HND', now(), 'ANA25', 'NH25', '05', null, null, null, '[]', 'dep'), ('NRT', now(), 'JAL5', 'JL5', '34L', 30, 30, 30, '[]', 'arr')`);
const ap = await rows(`select iata from public.airports where iata is not null order by iata limit 3`);
for (const [i, a] of ap.entries()) await db.query(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values ((now() at time zone 'Asia/Tokyo')::date, $1, 'HND', $2, now() + make_interval(mins => 30 + i * 10), now() + interval '2 hours', 'test')`.replace('i * 10', String(i * 10)), ['NH' + (900 + i), a.iata]);
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values ((now() at time zone 'Asia/Tokyo')::date, 'XX1', 'HND', 'LAX', now() + interval '40 minutes', now() + interval '10 hours', 'test')`);
const boardOut = async () => { const b = (await rows(`select public.airport_board('HND') v`))[0].v; delete b.now; return JSON.stringify(b); };

const before = (await rows(SHAPE))[0]; const fnBefore = (await rows(FN))[0];
const cntBefore = JSON.stringify((await rows(`select public.rwy_sample_counts() v`))[0].v);
const boardBefore = await boardOut();
check('前：anon は数を呼べた（直す前の形の確かめ）', !String(await as('anon', `select public.rwy_sample_counts()`)).startsWith('ERROR'));

await db.exec(fs.readFileSync(dir + NEW, 'utf8'));

// 1. rwy_sample_counts
check('1 anon は呼べない', String(await as('anon', `select public.rwy_sample_counts()`)).startsWith('ERROR'));
check('1 authenticated も呼べない', String(await as('authenticated', `select public.rwy_sample_counts()`)).startsWith('ERROR'));
const svc = await as('service_role', `select public.rwy_sample_counts()`);
check('1 service_role は呼べて答えが同じ', JSON.stringify(svc) === cntBefore, [svc, cntBefore]);
check('1 持ち主（SQL Editor）も答えが同じ', JSON.stringify((await rows(`select public.rwy_sample_counts() v`))[0].v) === cntBefore);
const fnAfter = (await rows(FN))[0];
check('1 本文と設定は同じ', fnAfter.def === fnBefore.def && JSON.stringify(fnAfter.cfg) === JSON.stringify(fnBefore.cfg));
check('1 rwy_samples_recent（画面の一覧）は anon のまま読める', Array.isArray(await as('anon', `select public.rwy_samples_recent('HND', 14)`)));

// 2. airports (iata)
await db.exec(`set enable_seqscan = off`);
const pl = (await db.exec(`explain (generic_plan) select 1 from public.airports a where a.iata = $1::text`))[0].rows.map(r => r['QUERY PLAN']).join('\n');
await db.exec(`reset enable_seqscan`);
check('2 iata = $1 で airports_iata を使う', /airports_iata/.test(pl) && !/Seq Scan/.test(pl), pl);
const def = (await rows(`select indexdef from pg_indexes where indexname = 'airports_iata'`))[0]?.indexdef || '';
check('2 iata のない行は入れない部分索引', /\(iata\)/.test(def) && /WHERE \(iata IS NOT NULL\)/.test(def), def);
check('2 airport_board の答えは前と同じ', (await boardOut()) === boardBefore);
check('2 国内・海外の判定もそのまま（LAX は海外）', JSON.parse(boardBefore).next_dep.some(x => x.flight === 'XX1' && x.intl === true) && JSON.parse(boardBefore).next_dep.some(x => x.flight === 'NH900' && x.intl === false), JSON.parse(boardBefore).next_dep);

// 3. 形
const after = (await rows(SHAPE))[0];
check('3 列は同じ', JSON.stringify(after.cols) === JSON.stringify(before.cols));
check('3 RLS の方針は同じ', JSON.stringify(after.pol) === JSON.stringify(before.pol));
check('3 表の権限は同じ', JSON.stringify(after.grants) === JSON.stringify(before.grants));
check('3 ほかの関数の権限は同じ', JSON.stringify(after.fnacl) === JSON.stringify(before.fnacl));
check('3 索引は1本だけ増える', after.nidx === before.nidx + 1, [before.nidx, after.nidx]);
let again = true; try { await db.exec(fs.readFileSync(dir + NEW, 'utf8')); } catch (e) { again = false; console.log(e.message); }
check('3 2回流しても壊れない', again && (await rows(SHAPE))[0].nidx === after.nidx);

// 後の移行も流せる
for (const f of files) if (f > NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));
check('3 後の移行も流せる', true);
if (bad) process.exit(1);
