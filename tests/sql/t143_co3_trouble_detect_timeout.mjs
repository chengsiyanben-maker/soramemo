// 経営の毎日の仕事 co3-trouble-detect に時間の上限が付くか（移行 co3_trouble_detect_timeout）
//   1. pg_cron がない環境では何もしない（移行を全部流せる）
//   2. 仕事がない（119 で止めたまま）なら、新しく作らない
//   3. 仕事が残っていれば、同じ時刻・同じ中身のまま、文の先頭に statement_timeout 3分と lock_timeout 5秒が付く
//   4. 2回流しても上限は二重にならない。ほかの仕事は変わらない
//   5. 付け直した文は、そのまま流して通る（空のデータベースで）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
const files = fs.readdirSync(dir).filter(f => f.endsWith('.sql')).sort();
const mine = files.find(f => f.endsWith('_co3_trouble_detect_timeout.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
check('移行がある', !!mine);
const sql = fs.readFileSync(dir + mine, 'utf8');
check('仕事を消さない（unschedule を使わない）', !/cron\.unschedule/.test(sql));

// pg_cron の代わり：cron.job の表と cron.schedule（同じ名前なら上書き）
const FAKE = `create schema cron;
create table cron.job (jobid serial primary key, jobname text unique, schedule text, command text);
create function cron.schedule(n text, s text, c text) returns bigint language sql as $$
  insert into cron.job (jobname, schedule, command) values (n, s, c)
  on conflict (jobname) do update set schedule = excluded.schedule, command = excluded.command returning jobid::bigint $$;`;
const OLD = ' select public.co3_trouble_detect() ';
const jobs = async db => Object.fromEntries((await db.query(`select jobname, schedule, command from cron.job order by jobname`)).rows.map(r => [r.jobname, r]));

{ // 2. 仕事がないとき
  const db = new PGlite(); await db.exec(FAKE);
  await db.exec(`select cron.schedule('co3-legs-check', '*/15 * * * *', 'select 1')`);
  await db.exec(sql);
  const j = await jobs(db);
  check('仕事がないときは作らない', !j['co3-trouble-detect'], Object.keys(j));
  check('ほかの仕事はそのまま（なし）', j['co3-legs-check']?.command === 'select 1', j['co3-legs-check']);
}
{ // 3・4. 仕事が残っているとき
  const db = new PGlite(); await db.exec(FAKE);
  await db.query(`select cron.schedule('co3-trouble-detect', '0 22 * * *', $1)`, [OLD]);
  await db.exec(`select cron.schedule('co3-legs-check', '*/15 * * * *', 'select 1')`);
  await db.exec(sql);
  let j = await jobs(db); const t = j['co3-trouble-detect'];
  check('時刻は同じ（0 22 * * *）', t?.schedule === '0 22 * * *', t);
  check('文の先頭に statement_timeout 3分と lock_timeout 5秒', /^set statement_timeout = '3min'; set lock_timeout = '5s'; /.test(t?.command), t?.command);
  check('中身は同じ', t?.command.replace(/^set [^;]+; set [^;]+; /, '').trim() === OLD.trim(), t?.command);
  check('ほかの仕事は変わらない', j['co3-legs-check']?.command === 'select 1', j['co3-legs-check']);
  await db.exec(sql);
  const t2 = (await jobs(db))['co3-trouble-detect'];
  check('2回流しても二重にならない', t2.command === t.command, t2.command);
  // 前に別の上限が付いていたときも 3分にそろう
  await db.query(`update cron.job set command = $1 where jobname = 'co3-trouble-detect'`, [`set statement_timeout = '10min'; set lock_timeout = '1s';${OLD}`]);
  await db.exec(sql);
  const t3 = (await jobs(db))['co3-trouble-detect'];
  check('前の上限は置きかえる', t3.command === t.command, t3.command);
}

// 1・5. 空のデータベース（pg_cron なし）で移行を全部流し、付け直した文をそのまま流す
const db = new PGlite();
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
let applied = true;
try { for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8')); } catch (e) { applied = false; console.log(e.message); }
check('移行を全部流せる（pg_cron がないときは何もしない）', applied);
check('pg_cron がないときは cron の表を作らない', (await db.query(`select to_regclass('cron.job') r`)).rows[0].r === null);
let err = null; try { await db.exec(`set statement_timeout = '3min'; set lock_timeout = '5s';${OLD}`); } catch (e) { err = e.message; }
check('付け直した文をそのまま流して通る', !err, err);
console.log(bad ? `NG ${bad}件` : 'すべて通過'); process.exit(bad ? 1 : 0);
