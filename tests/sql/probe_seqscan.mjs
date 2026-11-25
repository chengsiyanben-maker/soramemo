// 全部読みの洗い出し（データ担当の定期の手入れの道具。テストではない：npm test では流れない）
//   移行をすべて流した模擬のデータベースで、public・ops の SQL と plpgsql の関数を「全部読みを禁じて」実際に呼び、
//   その取引の中で全部読みになった表を pg_stat_xact_user_tables の差で出す（引数は型ごとの仮の値。呼べない関数は ERR と出る）
//   使い方（tests/sql で）：
//     node probe_seqscan.mjs [関数名の正規表現] > out.tsv           … 関数をまとめて呼ぶ
//     SEED=種.sql CALLS=呼ぶ文.sql node probe_seqscan.mjs             … 種（; と改行で区切る）をまいて、1行1文を呼ぶ
//   見方：4列目に出た表のうち、行の数が増える表があれば索引を足すか文の形を直す。よく呼ばれるものは t141 に足して見張る
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const U = '00000000-0000-0000-0000-0000000000a1';
await db.exec(`insert into auth.users (id, email) values ('${U}', 'a@example.com'); select set_config('request.jwt.claim.sub', '${U}', false);`);
if (process.env.SEED) for (const st of fs.readFileSync(process.env.SEED, 'utf8').split(/;\n/)) { if (!st.trim()) continue; try { await db.exec(st); } catch (e) { console.error('SEED NG', e.message, st.slice(0, 60)); } }
const fns = (await db.query(`select p.oid, n.nspname, p.proname, l.lanname, p.proargtypes::regtype[]::text[] types, p.pronargs, p.pronargdefaults, p.prokind, p.prorettype::regtype::text rt
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace join pg_language l on l.oid = p.prolang
  where n.nspname in ('public','ops') and l.lanname in ('plpgsql','sql') and p.prokind = 'f' and p.prorettype <> 'trigger'::regtype order by 2,3`)).rows;
const val = t => ({ text: `'HND'`, 'character varying': `'HND'`, date: `current_date`, integer: '10', bigint: '1', smallint: '1', numeric: '1', 'double precision': '1', real: '1',
  uuid: `'${U}'::uuid`, jsonb: `'[]'::jsonb`, json: `'[]'::json`, 'text[]': `array['HND']`, 'timestamp with time zone': 'now()', boolean: 'false', 'integer[]': 'array[1]', 'bigint[]': 'array[1]', interval: `'1 day'::interval`, 'time without time zone': `'12:00'::time` }[t]);
const only = process.argv[2] ? new RegExp(process.argv[2]) : null;
const snap = async () => { await db.exec('select pg_stat_clear_snapshot()'); const r = await db.query(`select schemaname||'.'||relname t, seq_scan from pg_stat_user_tables`); return Object.fromEntries(r.rows.map(x => [x.t, x.seq_scan])); };
const extra = process.env.CALLS ? fs.readFileSync(process.env.CALLS, 'utf8').split('\n').filter(l => l.trim()).map(c => ({ call: c })) : null;
for (const f of (extra || fns)) {
  if (f.call) { const call = f.call; let err = '', d = [];
    try { await db.exec('begin; set local enable_seqscan = off; set local statement_timeout = 5000');
      const X = `select schemaname||'.'||relname t, seq_scan n from pg_stat_xact_user_tables`;
      const a = Object.fromEntries((await db.query(X)).rows.map(r => [r.t, r.n]));
      const out = await db.query(call);
      d = (await db.query(X)).rows.filter(r => r.n - (a[r.t] || 0) > 0).map(r => r.t + '×' + (r.n - (a[r.t] || 0)));
      d.push('→ ' + JSON.stringify(out.rows[0] ?? null).slice(0, 120));
    } catch (e) { err = e.message.split('\n')[0].slice(0, 90); }
    await db.exec('rollback').catch(()=>{}); console.log(call.slice(0, 80), err ? 'ERR ' + err : '', d.join(' ')); continue; }
  if (only && !only.test(f.proname)) continue;
  if (/^(emergency_stop|cold_|archive_)/.test(f.proname)) continue;
  const args = f.types.map(val); if (args.some(a => a === undefined)) { console.log(`${f.lanname}\t${f.nspname}.${f.proname}\tSKIP ${f.types}`); continue; }
  const call = `select ${f.nspname}.${f.proname}(${args.join(',')})`;
  let err = '', d = [];
  try { await db.exec('begin; set local enable_seqscan = off; set local statement_timeout = 5000');
    const X = `select schemaname||'.'||relname t, seq_scan n from pg_stat_xact_user_tables`;
    const a = Object.fromEntries((await db.query(X)).rows.map(r => [r.t, r.n]));
    await db.query(call);
    d = (await db.query(X)).rows.filter(r => r.n - (a[r.t] || 0) > 0).map(r => r.t + '×' + (r.n - (a[r.t] || 0)));
  } catch (e) { err = e.message.split('\n')[0].slice(0, 70); }
  await db.exec('rollback').catch(()=>{});
  console.log(`${f.lanname}\t${f.nspname}.${f.proname}\t${err ? 'ERR ' + err : 'ok'}\t${d.join(' ')}`);
}
