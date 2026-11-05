// 運用予想の毎晩の処理を軽くした仕組み：つながりは前の日の分だけ足す（まだない古い日は時間の上限まで埋める）・採点は300便まで・
// 一時ファイルを使わない（作業メモリ 64kB で測る）・前の作り方と同じ結果・pg_cron の仕事を分けて statement_timeout を付ける・片方が失敗しても止めない
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
const q = async (sql, args) => (await db.query(sql, args)).rows[0];
const T = `(now() at time zone 'Asia/Tokyo')::date`;

// 作り物の便：400機 × 1日5便 × 45日（約9万件）。10日に1回ほど、ちがう便が入る
await db.exec(`insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr)
  select 'JA' || lpad(r::text, 4, '0'),
         (array['JAL', 'ANA', 'SKY', 'APJ'])[1 + r % 4] || (100 + (r % 60) * 5 + leg + case when abs(hashint4(r * 1000 + dd)) % 10 = 0 then 300 else 0 end),
         ${T} - dd, (array['B738', 'A320', 'B789'])[1 + r % 3],
         ((${T} - dd) + time '07:00' + leg * interval '3 hours') at time zone 'Asia/Tokyo',
         ((${T} - dd) + time '09:00' + leg * interval '3 hours') at time zone 'Asia/Tokyo',
         case when leg % 2 = 0 then 'HND' else (array['CTS', 'FUK', 'ITM', 'OKA'])[1 + r % 4] end,
         case when leg % 2 = 0 then (array['CTS', 'FUK', 'ITM', 'OKA'])[1 + r % 4] else 'HND' end
  from generate_series(1, 400) r, generate_series(0, 4) leg, generate_series(1, 45) dd`);
const legs = (await q(`select count(*)::int as n from public.reg_legs`)).n;
console.log(`作り物の便 ${legs}件`);
await db.exec(`analyze public.reg_legs`);

const temp = async () => { await db.query(`select pg_stat_force_next_flush()`); return Number((await q(`select temp_bytes from pg_stat_database where datname = current_database()`)).temp_bytes); };
await db.exec(`set work_mem = '64kB'`);

// 前の作り方（1日分をまとめて並べ替える）は、作業メモリが小さいと一時ファイルを使う
const t0 = await temp();
const old = (await db.query(`select reg, callsign as prev_cs, lead(callsign) over w as next_cs, arr as prev_arr, lead(dep) over w as next_dep, lead(arr) over w as next_arr,
    lead(type) over w as next_type, lead(first_at) over w as nfirst, last_at from public.reg_legs where day = ${T} - 1 window w as (partition by reg order by first_at, callsign)`)).rows.filter(r => r.next_cs);
const oldTemp = (await temp()) - t0;

// 1. つながり：時間の上限 0 なら前の日の分だけ
const n0 = (await q(`select public.rot_pairs_nightly(interval '0 seconds', 60) as r`)).r;
check('つながり：前の日の分だけ足す（時間の上限 0 なら古い日は埋めない）', n0.pairs === 400 * 4 && n0.filled.length === 0 && n0.stopped === 'budget' && n0.left === 44, n0);
const newRows = (await db.query(`select reg, prev_cs, next_cs, prev_arr, next_dep, next_arr, next_type from public.rot_pairs where day = ${T} - 1 order by reg, prev_cs`)).rows;
const key = r => [r.reg, r.prev_cs, r.next_cs, r.prev_arr, r.next_dep, r.next_arr, r.next_type].join('|');
const oldKeys = old.map(key).sort(), newKeys = newRows.map(key).sort();
check('つながり：前の作り方（並べ替え）と同じ行', oldKeys.length === newKeys.length && oldKeys.every((k, i) => k === newKeys[i]), { old: oldKeys.length, new: newKeys.length });

// 2. 古い日を時間の上限まで埋める → 一時ファイルを使わない
const t1 = await temp();
const n1 = (await q(`select public.rot_pairs_nightly(interval '60 seconds', 60) as r`)).r;
const pairsTemp = (await temp()) - t1;
const pc = await q(`select count(*)::int as n, count(distinct day)::int as days from public.rot_pairs`);
const pd = await q(`select count(*)::int as n from public.rot_pairs_days`);
check('つながり：まだない古い日を新しい日から埋める', n1.filled.length === 44 && n1.left === 0 && n1.stopped === null && pc.days === 45 && pd.n === 45 && n1.filled[0] > n1.filled[43], { n1: { ...n1, filled: n1.filled.length }, pc, pd });
const n2 = (await q(`select public.rot_pairs_nightly(interval '60 seconds', 60) as r`)).r;
const pc2 = await q(`select count(*)::int as n from public.rot_pairs`);
check('つながり：次の夜は前の日の分だけ（作り直さない・増えない）', n2.filled.length === 0 && n2.left === 0 && pc2.n === pc.n, { n2, pc2 });
check('つながり：作業メモリ 64kB で一時ファイルを使わない', pairsTemp === 0, { pairsTemp });
console.log(`一時ファイル（バイト）：前の作り方 1日 ${oldTemp}／新しい作り方 45日分 ${pairsTemp}`);

// 3. 採点：300便まで・3通り・一時ファイルを使わない
const t2 = await temp(); const c0 = Date.now();
const e1 = (await q(`select public.rot_eval_nightly(300) as r`)).r;
const evalTemp = (await temp()) - t2; const evalMs = Date.now() - c0;
const ev = (await db.query(`select method, sum(n)::int as n, sum(predicted)::int as predicted, sum(hit)::int as hit from public.rot_eval where k = 1 group by 1 order by 1`)).rows;
check('採点：前の日の300便まで、3通りとも同じ便を採点', ev.length === 3 && ev.every(r => r.n === 300) && e1.eval_rows > 0 && e1.legs === 300, { e1, ev });
const lo = ev.find(r => r.method === 'learn'), hi = ev.find(r => r.method === 'learn_hi');
check('採点：厳しいしきい値（3回以上・4割以上）は出す数が今のしきい値以下', hi.predicted <= lo.predicted && lo.predicted > 0, ev);
check('採点：作業メモリ 64kB で一時ファイルを使わない', evalTemp === 0, { evalTemp });
console.log(`採点 300便×3通り：一時ファイル ${evalTemp} バイト・${evalMs}ms`);
const e2 = (await q(`select public.rot_eval_nightly(100) as r`)).r;
const ev2 = await q(`select count(distinct method)::int as m, sum(n) filter (where k = 1 and method = 'base')::int as n from public.rot_eval where day = ${T} - 1`);
check('採点：便の数は定数で変えられ、流し直しても同じ日が二重にならない', ev2.n === 100 && ev2.m === 3 && e2.legs === 100, { e2, ev2 });
const eb = (await q(`select public.rot_eval_day(${T} - 2, 300, interval '0 seconds') as n`)).n;
check('採点：時間の上限を過ぎたら、そこで止める（0秒なら1便も採点しない）', eb === 0, eb);

// 4. EXPLAIN：つながりを作る本体（1日分）は、索引で引き、一時ファイルを使わない
const plan = (await db.query(`explain (analyze, buffers, costs off) select a.reg, nl.callsign from public.reg_legs a
  cross join lateral (select b.callsign from public.reg_legs b where b.reg = a.reg and b.day = a.day and (b.first_at, b.callsign) > (a.first_at, a.callsign)
                      order by b.first_at, b.callsign limit 1) nl where a.day = ${T} - 1`)).rows.map(r => r['QUERY PLAN']).join('\n');
check('EXPLAIN：次の便は主キーの索引で引き、一時ファイルを使わない', /Index Scan using reg_legs_pkey|Index Scan using reg_legs_day|Bitmap Index Scan/.test(plan) && !/temp (read|written)/.test(plan) && !/external/.test(plan), plan);
const plan2 = (await db.query(`explain (analyze, buffers, costs off) select x.reg, x.callsign as cs from public.reg_legs x
  cross join lateral (select 1 from public.reg_legs b where b.reg = x.reg and b.day = x.day and (b.first_at, b.callsign) > (x.first_at, x.callsign) limit 1) nb
  where x.day = ${T} - 1 order by md5(x.reg || ':' || x.callsign) limit 300`)).rows.map(r => r['QUERY PLAN']).join('\n');
check('EXPLAIN：採点で測る便を選ぶところは、上位300件だけの並べ替えで、一時ファイルを使わない', /top-N heapsort/.test(plan2) && !/temp (read|written)/.test(plan2) && !/Hash/.test(plan2), plan2);
await db.exec(`reset work_mem`);

// 5. 片方が失敗しても、もう片方は流す
await db.exec(`alter table public.rot_pairs_days rename to rot_pairs_days_x`);
const nf = (await q(`select public.rot_nightly() as r`)).r;
await db.exec(`alter table public.rot_pairs_days_x rename to rot_pairs_days`);
check('手で流す rot_nightly：つながりが失敗しても採点は流す', nf.pairs_job?.error && nf.eval_rows > 0, nf);
const nok = (await q(`select public.rot_nightly() as r`)).r;
check('手で流す rot_nightly：ふだんは両方', nok.pairs === 1600 && nok.eval_rows > 0 && !nok.pairs_job.error && !nok.eval_job.error, nok);

// 6. pg_cron の仕事：2つに分け、それぞれ statement_timeout と lock_timeout を付け、ほかの毎晩の処理と時刻を重ねない
const mig = fs.readFileSync(dir + files.find(f => f.endsWith('_rotation_predict.sql')), 'utf8');
const jobs = [...mig.matchAll(/cron\.schedule\('([a-z-]+)', '([^']+)', \$job\$(.*?)\$job\$/g)].map(m => ({ name: m[1], when: m[2], cmd: m[3] }));
check('毎晩の仕事は rot-pairs と rot-eval の2つ（前の rot-learn は外す）', jobs.map(j => j.name).join(',') === 'rot-pairs,rot-eval' && /unschedule[^;]*'rot-learn'/.test(mig), jobs);
check('どちらにも statement_timeout と lock_timeout', jobs.every(j => /set statement_timeout = '\d+min'/.test(j.cmd) && /set lock_timeout = '\d+s'/.test(j.cmd)), jobs);
const others = new Set(); for (const f of files) if (!f.endsWith('_rotation_predict.sql')) for (const m of fs.readFileSync(dir + f, 'utf8').matchAll(/cron\.schedule\('[a-z0-9-]+', '([^']+)'/g)) others.add(m[1]);
check('ほかの毎晩の処理と同じ時刻にしない', jobs.every(j => !others.has(j.when)), { jobs: jobs.map(j => j.when), others: [...others] });
check('移行では、これまでの日をまとめて作らない', !/for d in select distinct day from public\.reg_legs/.test(mig));

// 7. 権限：新しい表と関数は運営だけ
const rls = await q(`select relrowsecurity from pg_class where relname = 'rot_pairs_days'`);
check('rot_pairs_days は行レベルセキュリティ', rls?.relrowsecurity === true, rls);
for (const [label, sql] of [['つながりを作った日の表', `select count(*) from public.rot_pairs_days`], ['つながりの毎晩', `select public.rot_pairs_nightly()`], ['採点の毎晩', `select public.rot_eval_nightly()`]]) {
  for (const role of ['anon', 'authenticated']) {
    let denied = false; await db.exec(`set role ${role}`); try { await db.query(sql); } catch { denied = true; } await db.exec('reset role');
    check(`${label}は ${role} から使えない`, denied);
  }
}
if (bad) process.exit(1);
console.log('すべて OK');
