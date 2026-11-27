// PM の読むだけの役割 pm_reader（移行212・data/pm-reader）
//   1 役割の形：ログインなし・強い力なし・既定は読むだけの取引・60秒・止まった取引を切る
//   2 権限：読めるのは一覧の表だけ（全部の表を調べ、一覧の外は1つも読めない）。どの表にも書けない
//   3 実際に pm_reader になって：一覧の表は読め、RLS の表の行も見える。利用者の表・auth・ops は読めない。書けない
//   4 read only の取引の中では、書く関数を呼んでも書けない（tools/pm_query.mjs の包みの守り）
//   5 例の問い合わせ（promo_day・reg_week）が pm_reader で流れ、大きい表を全部読みしない
//   6 流す前の確かめ（select / with の1文だけ・psql の命令や書く言葉を断る）・変数・20万行で切る
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
import { checkSql, checkName, parseParams, capCsv, wrap, MAX_ROWS } from '../../tools/pm_query.mjs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));

let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const ALLOW = ['flight_history', 'flight_tracks', 'track_points', 'reg_legs', 'flight_schedule', 'flight_changes', 'timetable',
  'foreign_legs', 'foreign_usual', 'airport_daily', 'airports', 'terminals', 'airline_codes', 'airport_facts', 'airport_yomi',
  'world_airport_status', 'ops_log', 'rwy_samples', 'rwy_learned_days', 'ground_moves', 'arr_watch', 'wx_obs', 'wx_taf',
  'wx_taf_hours', 'livery_extra', 'livery_sightings', 'livery_plans', 'rot_pairs', 'rot_eval', 'rotation_obs'];
// 利用者のデータ（読めてはいけない代表）。ないものは飛ばす
const USER = ['public.checkins', 'public.flights', 'public.manual_flights', 'public.intl_flights', 'public.user_profiles', 'public.user_pins',
  'public.user_view_prefs', 'public.user_data_prefs', 'public.shugyo_prefs', 'public.push_subs', 'public.subscriptions', 'public.companies',
  'public.aircraft', 'public.co3_daily', 'public.co3_market', 'public.atc_feeders', 'public.atc_msgs', 'public.track_quota', 'public.feedback',
  'ops.usage_events', 'ops.client_errors', 'ops.admins', 'ops.flags', 'auth.users'];

// 1. 役割の形
const role = (await db.query(`select rolcanlogin, rolsuper, rolinherit, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls from pg_roles where rolname = 'pm_reader'`)).rows[0];
check('役割 pm_reader があり、ログインなし・強い力なし', role && !role.rolcanlogin && !role.rolsuper && !role.rolinherit && !role.rolcreatedb && !role.rolcreaterole && !role.rolreplication && !role.rolbypassrls, role);
const conf = (await db.query(`select unnest(setconfig) c from pg_db_role_setting where setrole = 'pm_reader'::regrole and setdatabase = 0`)).rows.map(r => r.c);
check('既定：読むだけの取引・1文60秒・止まった取引2分・つなぎっぱなし10分', ['default_transaction_read_only=on', 'statement_timeout=60s', 'idle_in_transaction_session_timeout=120s', 'idle_session_timeout=600s'].every(x => conf.includes(x)), conf);
const members = (await db.query(`select count(*)::int n from pg_auth_members where member = 'pm_reader'::regrole`)).rows[0].n;
check('pm_reader はほかの役割の権限を受け継がない（どの役割にも入っていない）', members === 0, members);

// 2. 権限（全部の表・ビューを調べる）
const rels = (await db.query(`select n.nspname s, c.relname t,
    has_table_privilege('pm_reader', c.oid, 'select') sel,
    has_table_privilege('pm_reader', c.oid, 'insert') or has_table_privilege('pm_reader', c.oid, 'update')
      or has_table_privilege('pm_reader', c.oid, 'delete') or has_table_privilege('pm_reader', c.oid, 'truncate') wr
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where c.relkind in ('r', 'v', 'm', 'p', 'f') and n.nspname not in ('pg_catalog', 'information_schema', 'pg_toast')`)).rows;
const readable = rels.filter(r => r.sel).map(r => `${r.s}.${r.t}`).sort();
const want = ALLOW.map(t => 'public.' + t).sort();
check(`読めるのは一覧の ${ALLOW.length} 表だけ（全 ${rels.length} 表を調べた）`, JSON.stringify(readable) === JSON.stringify(want),
  { extra: readable.filter(x => !want.includes(x)), missing: want.filter(x => !readable.includes(x)) });
check('どの表にも書けない（insert・update・delete・truncate）', rels.every(r => !r.wr), rels.filter(r => r.wr).map(r => r.t));
const pol = (await db.query(`select c.relname t from pg_policy p join pg_class c on c.oid = p.polrelid where p.polname = 'pm_reader_read'`)).rows.map(r => r.t);
const rlsOn = (await db.query(`select relname from pg_class where relnamespace = 'public'::regnamespace and relname = any($1) and relrowsecurity`, [ALLOW])).rows.map(r => r.relname);
check('RLS が有効な一覧の表すべてに読むだけのポリシー（一覧の外には足していない）', pol.length === rlsOn.length && rlsOn.every(t => pol.includes(t)) && pol.every(t => ALLOW.includes(t)), { pol, rlsOn });
const polKinds = (await db.query(`select distinct polcmd::text k from pg_policy where polname = 'pm_reader_read'`)).rows.map(r => r.k);
check('足したポリシーは select だけ', JSON.stringify(polKinds) === '["r"]', polKinds);
const opsUse = (await db.query(`select has_schema_privilege('pm_reader', 'ops', 'usage') o, has_schema_privilege('pm_reader', 'auth', 'usage') a, has_schema_privilege('pm_reader', 'public', 'create') c`)).rows[0];
check('ops・auth の中は使えない・public に作れない', !opsUse.o && !opsUse.a && !opsUse.c, opsUse);

// 3. 実際に pm_reader になって
const U1 = '00000000-0000-0000-0000-0000000000c1';
await db.exec(`insert into auth.users (id, email) values ('${U1}', 'c1@example.com');
insert into public.flight_history (svc_date, flight, dep, arr, std, sta, reg, type, callsign)
  values ('2026-11-20', 'JL0101', 'HND', 'ITM', '2026-11-20 06:00+09', '2026-11-20 07:05+09', null, null, null),
         ('2026-11-20', 'JL0103', 'HND', 'ITM', '2026-11-20 07:00+09', '2026-11-20 08:05+09', 'JA8089', 'B763', 'JAL103');
insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr)
  values ('JA602J', 'JAL101', '2026-11-20', 'B763', '2026-11-20 06:05+09', '2026-11-20 07:00+09', 'HND', 'ITM'),
         ('JA8089', 'JAL110', '2026-11-19', 'B763', '2026-11-19 18:00+09', '2026-11-19 19:10+09', 'ITM', 'HND');`);
await db.exec(`insert into public.airline_codes (icao, iata, odpt) values ('JAL', 'JL', null) on conflict do nothing`).catch(() => {});
await db.exec('set role pm_reader');
const errs = [];
for (const t of ALLOW) { try { await db.query(`select count(*) from public.${t}`); } catch (e) { errs.push(`${t}: ${e.message}`); } }
check('一覧の表はどれも pm_reader で読める', errs.length === 0, errs);
const seen = (await db.query(`select count(*)::int n from public.flight_history`)).rows[0].n;
const aps = (await db.query(`select count(*)::int n from public.airports`)).rows[0].n;
check('RLS の表の行が見える（便2行・空港86以上）', seen === 2 && aps >= 86, { seen, aps });
const denied = [], leaked = [];
for (const t of USER) {
  const exists = await db.query(`select to_regclass($1) r`, [t]).then(r => r.rows[0].r).catch(() => 'deny');
  if (exists === null) continue;
  try { await db.query(`select 1 from ${t} limit 1`); leaked.push(t); } catch (e) { denied.push(t); }
}
check(`利用者の表・ops・auth は読めない（${denied.length}表を試した）`, leaked.length === 0 && denied.length >= 20, { leaked, denied: denied.length });
let wrote = null;
try { await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr) values ('2026-11-21', 'JL0001', 'HND', 'ITM')`); wrote = 'insert'; } catch {}
try { await db.exec(`update public.airports set name = name where id = (select id from public.airports limit 1)`); wrote = 'update'; } catch {}
try { await db.exec(`delete from public.track_points`); wrote = 'delete'; } catch {}
try { await db.exec(`create table public.pm_x (a int)`); wrote = 'create'; } catch {}
check('pm_reader は書けない・作れない（insert・update・delete・create）', wrote === null, wrote);
await db.exec('reset role');

// 4. read only の取引の中では、書く関数（作った人の権限で動く）を呼んでも書けない
await db.exec(`create function public.pm_t_write() returns int language sql security definer as $$ insert into public.flight_history (svc_date, flight, dep, arr) values ('2026-11-22', 'JL9999', 'HND', 'ITM') returning 1 $$;
grant execute on function public.pm_t_write() to pm_reader;`);
await db.exec('set role pm_reader');
let ro = '';
try { await db.exec(`begin transaction isolation level repeatable read read only; select public.pm_t_write();`); ro = 'wrote'; } catch (e) { ro = e.message; }
await db.exec('rollback').catch(() => {});
await db.exec('reset role');
const n9999 = (await db.query(`select count(*)::int n from public.flight_history where flight = 'JL9999'`)).rows[0].n;
check('read only の取引では、書く関数を通しても書けない', /read-only/.test(ro) && n9999 === 0, { ro, n9999 });
await db.exec('drop function public.pm_t_write()');
const w = wrap('select 1');
check('包みは read only の取引・60秒・COPY の1文・最後に rollback', /begin transaction isolation level repeatable read read only;/.test(w) && /set local statement_timeout = '60s';/.test(w) && /limit 200001\) to stdout with \(format csv, header\);\nrollback;/.test(w) && /^\\set ON_ERROR_STOP on/.test(w), w);

// 5. 例の問い合わせ
const qdir = new URL('../../tools/pm-queries/', import.meta.url).pathname;
const sub = (sql, vars) => sql.replace(/:'([a-z_]+)'/g, (_, k) => `'${vars[k]}'`);
const runQ = async (name, vars) => {
  const raw = fs.readFileSync(qdir + name, 'utf8'); const c = checkSql(raw);
  if (!c.ok) return { why: c.why };
  await db.exec('set role pm_reader');
  try {
    const rows = (await db.query(`select * from (\n${sub(c.sql, vars)}\n) pm_q limit ${MAX_ROWS + 1}`)).rows;
    await db.exec('set enable_seqscan = off');
    const plan = (await db.query(`explain select * from (\n${sub(c.sql, vars)}\n) pm_q`)).rows.map(r => r['QUERY PLAN']).join('\n');
    return { rows, plan };
  } finally { await db.exec('reset enable_seqscan; reset role'); }
};
const files = fs.readdirSync(qdir).filter(f => f.endsWith('.sql'));
check('tools/pm-queries の .sql はどれも確かめを通る', files.length >= 2 && files.every(f => checkSql(fs.readFileSync(qdir + f, 'utf8')).ok && !checkName(f)), files.map(f => [f, checkSql(fs.readFileSync(qdir + f, 'utf8')).why]));
const pd = await runQ('promo_day.sql', { airline: 'JL', day: '2026-11-20' });
const r101 = pd.rows?.find(r => r.flight === 'JL0101'), r103 = pd.rows?.find(r => r.flight === 'JL0103');
check('promo_day：その日の JL の便が2行・記録にない機体は全機の記録から補う', pd.rows?.length === 2 && r101?.reg === 'JA602J' && r101?.callsign === 'JAL101' && r103?.reg === 'JA8089' && r101.std_jst === '06:00', pd.why ?? pd.rows);
check('promo_day：大きい表（flight_history・reg_legs）を全部読みしない', pd.plan && !/Seq Scan on (flight_history|reg_legs)/.test(pd.plan), pd.plan);
const rw = await runQ('reg_week.sql', { reg: 'ja8089', from: '2026-11-14', to: '2026-11-20' });
check('reg_week：登録記号の区間（便と全機の記録）が日付順に2行', rw.rows?.length === 2 && rw.rows[0].src === '全機' && rw.rows[0].dep === 'ITM' && rw.rows[1].src === '便' && rw.rows[1].flight === 'JL0103', rw.why ?? rw.rows);
check('reg_week：大きい表を全部読みしない', rw.plan && !/Seq Scan on (flight_history|reg_legs)/.test(rw.plan), rw.plan);
const rw2 = await runQ('reg_week.sql', { reg: 'JA8089', from: '2026-01-01', to: '2026-12-31' });
check('reg_week：期間は31日まで（長く頼んでも最初の31日だけ）', rw2.rows?.length === 0, rw2.rows);

// 6. 流す前の確かめ・変数・行数
const good = [
  'select 1', 'SELECT 1;', 'with a as (select 1 x) select * from a;\n-- おわり\n', "select 'delete; drop' as s", 'select 1 -- delete\n',
  'select /* update */ 1', "select :'day'::date", 'select "updated_at" from public.airports', 'select updated_at, starts from public.world_airport_status',
  "select $$a;b$$ as s",
];
const badSql = [
  ['insert into public.airports default values', 'select か'], ['select 1; delete from public.airports', '1つ'], ['\\! ls', 'バックスラッシュ'],
  ["select 1 \\g", 'バックスラッシュ'], ['with d as (delete from public.track_points returning 1) select * from d', '言葉'],
  ['select 1 /* 閉じない', '閉じて'], ["select 'abc", '閉じて'], ['select pg_sleep(100)', '言葉'], ["select set_config('a','b',false)", '言葉'],
  ['select * from public.airports for update', '言葉'], ['copy public.airports to stdout', 'select か'], ['set role postgres', 'select か'],
  ['select 1); commit; (select 1', '1つ'], ['select (1', 'かっこ'], ['', '空'], ['select nextval(\'x\')', '言葉'], ['begin', 'select か'],
  ['select 1;; select 2', '1つ'],
];
const gOk = good.filter(s => !checkSql(s).ok);
check(`良い文 ${good.length}本は通る`, gOk.length === 0, gOk.map(s => [s, checkSql(s).why]));
const bOk = badSql.filter(([s, w]) => { const c = checkSql(s); return c.ok || !c.why.includes(w); });
check(`だめな文 ${badSql.length}本はどれも断る（理由も合う）`, bOk.length === 0, bOk.map(([s]) => [s, checkSql(s)]));
check('末尾の ; とコメントを外す', checkSql('select 1;\n-- おわり\n').sql === 'select 1' && checkSql("select ';'").sql === "select ';'", [checkSql('select 1;\n-- おわり\n').sql]);
const pOk = parseParams('airline=JL day=2026-11-20');
check('変数：名前=値 を読む', pOk.ok && JSON.stringify(pOk.params) === '[["airline","JL"],["day","2026-11-20"]]', pOk);
const pBad = ["day=2026'--", 'a=b;c', 'A=1', 'x=' + 'a'.repeat(41), 'x', 'x=a\\b', 'x=$(id)'].filter(s => parseParams(s).ok);
check('変数：引用・; ・大文字の名前・長すぎ・= なし・\\・$ は断る', pBad.length === 0, pBad);
check('変数：空なら0個', parseParams('').ok && parseParams('').params.length === 0);
const nBad = ['../x.sql', 'x.txt', 'X.sql', '/etc/p.sql', 'a/b.sql', 'nai.sql', '.sql'].filter(s => !checkName(s));
check('ファイル名：フォルダ・ほかの拡張子・大文字・ないファイルは断る', nBad.length === 0 && !checkName('promo_day.sql'), nBad);
const csv = 'a,b\n' + Array.from({ length: MAX_ROWS + 1 }, (_, i) => i === 5 ? `"x\ny",${i}` : `x,${i}`).join('\n') + '\n';
const cc = capCsv(csv);
check('20万行を超えたら20万行で切る（引用の中の改行は行にしない）', cc.cut && cc.rows === MAX_ROWS && cc.text.endsWith(`x,${MAX_ROWS - 1}\n`), { rows: cc.rows, cut: cc.cut, tail: cc.text.slice(-20) });
const c2 = capCsv('a\n1\n2\n');
check('20万行までは切らない', !c2.cut && c2.rows === 2 && c2.text === 'a\n1\n2\n', c2);

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('t151 すべて OK');
