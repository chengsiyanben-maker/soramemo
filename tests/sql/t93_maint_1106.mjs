// 定期の手入れ（11/6・移行 153）
//   毎日の処理に時間の上限を付けても、時刻と中身は今のまま（cron の記録だけ 1日 → 8日）・経営の処理には触らない・
//   BRIN 索引が付き、cold-archive の候補探しが索引を使い、結果は同じ・自動掃除の設定・記録は1行も消えない・RLS と権限は今のまま
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).filter((f) => f.endsWith('.sql')).sort();
const MIG = files.find((f) => f.endsWith('_maint_1106.sql'));
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const norm = (s) => s.replace(/\s+/g, ' ').trim().replace(/;$/, '').trim();

// ---- 1. 毎日の処理：時刻と中身は今のまま、上限だけ足す ----
const jobsIn = (text) => [...text.matchAll(/cron\.schedule\(\s*'([a-z0-9-]+)'\s*,\s*'([^']+)'\s*,\s*\$(job|\$)\$(.*?)\$(job|\$)\$/gs)].map((m) => ({ name: m[1], when: m[2], cmd: norm(m[4]) }));
const prev = new Map();
for (const f of files) {
  if (f === MIG) break;
  const t = fs.readFileSync(dir + f, 'utf8');
  for (const m of t.matchAll(/cron\.unschedule\(\s*'([a-z0-9-]+)'/g)) prev.delete(m[1]);
  for (const j of jobsIn(t)) prev.set(j.name, j);
}
const mig = fs.readFileSync(dir + MIG, 'utf8');
const jobs = jobsIn(mig);
check('11の処理を直す', jobs.length === 11, jobs.map((j) => j.name));
check('経営の処理（co-・co3-）には触らない', jobs.every((j) => !/^co3?-/.test(j.name)), jobs.map((j) => j.name));
check('どれも前からある処理（新しい処理は足さない）', jobs.every((j) => prev.has(j.name)), jobs.filter((j) => !prev.has(j.name)).map((j) => j.name));
check('時刻は今のまま', jobs.every((j) => prev.get(j.name)?.when === j.when), jobs.map((j) => [j.name, j.when, prev.get(j.name)?.when]));
const SET = /^set statement_timeout = '(\d+)(s|min)'; set lock_timeout = '5s'; /;
const secs = (j) => { const m = j.cmd.match(SET); return m ? Number(m[1]) * (m[2] === 'min' ? 60 : 1) : null; };
check('どれも先頭に statement_timeout と lock_timeout 5s', jobs.every((j) => SET.test(j.cmd)), jobs.filter((j) => !SET.test(j.cmd)).map((j) => j.cmd));
check('上限は30秒〜3分（ほかの処理を巻き込まない長さ）', jobs.every((j) => secs(j) >= 30 && secs(j) <= 180), jobs.map((j) => [j.name, secs(j)]));
check('10分ごと・15分ごとの処理は30秒', jobs.filter((j) => /^\*\/1[05] /.test(j.when)).every((j) => secs(j) === 30), null);
const body = (j) => norm(j.cmd.replace(SET, ''));
const same = jobs.filter((j) => j.name !== 'cron-history-cleanup');
check('中身は今のまま（cron の記録の掃除のほか）', same.every((j) => body(j) === norm(prev.get(j.name).cmd)), same.filter((j) => body(j) !== norm(prev.get(j.name).cmd)).map((j) => [j.name, body(j), norm(prev.get(j.name).cmd)]));
const ch = jobs.find((j) => j.name === 'cron-history-cleanup');
check('cron の記録は 1日 → 8日 残す（ほかは同じ）', ch && body(ch) === norm(prev.get('cron-history-cleanup').cmd).replace("'1 day'", "'8 days'") && body(ch).includes("interval '8 days'"), ch && body(ch));
// 消す先と範囲は今のまま（記録の表を消す文は1つも増えない）
const delTargets = (s) => [...s.matchAll(/delete from ([a-z_.]+)/g)].map((m) => m[1]).sort().join(',');
check('消す先の表は今のまま', jobs.every((j) => delTargets(body(j)) === delTargets(norm(prev.get(j.name).cmd))), null);
const KEEP = ['airport_tracks_all', 'flight_tracks', 'flight_history', 'reg_legs', 'rotation_obs', 'rwy_samples', 'ops_log', 'ga_events', 'rot_pairs', 'livery_plans', 'cold_days'];
check('航路と機体の記録の表を消す文はない', jobs.every((j) => KEEP.every((t) => !new RegExp(`delete from public\\.${t}\\b`).test(j.cmd))), null);
const outside = mig.replace(/\$job\$.*?\$job\$/gs, '').replace(/--.*$/gm, '');
check('移行の中に delete・drop・truncate・表やポリシー・権限の変更はない', !/\b(delete|drop|truncate|create table|policy|grant|revoke)\b/i.test(outside), outside.match(/\b(delete|drop|truncate|create table|policy|grant|revoke)\b/gi));
// 上限を足した文がそのまま流せ、上限がその処理の中で効く（pg_cron と同じく1つの文字列で流す）
await db.exec(`create schema if not exists cron; create table if not exists cron.job_run_details (runid bigint, end_time timestamptz)`);
let runErr = [];
for (const j of jobs) {
  try { await db.exec(j.cmd); const st = await q1(`show statement_timeout`); if (!st || st === '0') runErr.push([j.name, 'timeout ' + st]); }
  catch (e) { runErr.push([j.name, e.message.split('\n')[0]]); }
  finally { await db.exec(`reset statement_timeout; reset lock_timeout`); }
}
check('11の文はどれもエラーなく流れ、上限が効く', runErr.length === 0, runErr);
// 上限で止まること自体は PGlite では確かめられない（時計で止める仕組みがない）。本物の Postgres 16 で確かめる（報告に結果）

// ---- 2. BRIN 索引 ----
const brin = (await db.query(`select c.relname as idx, t.relname as tbl, a.attname as col, am.amname as am, c.reloptions as opt
  from pg_index i join pg_class c on c.oid = i.indexrelid join pg_class t on t.oid = i.indrelid join pg_am am on am.oid = c.relam
  join pg_attribute a on a.attrelid = t.oid and a.attnum = i.indkey[0] where am.amname = 'brin' order by 1`)).rows;
const want = [['airport_tracks_all', 'day'], ['atc_msgs', 'at'], ['ga_events', 'at'], ['rwy_samples', 'at']];
check('BRIN 索引が4つ（全機の航跡の日・管制の時刻・ゴーアラウンドの時刻・滑走路の記録の時刻）', want.every(([t, c]) => brin.some((b) => b.tbl === t && b.col === c && String(b.opt).includes('pages_per_range=32'))) && brin.length === 4, brin);

// 全機の航跡：400日より前の日がある状態で、cold-archive の候補探しが索引を使い、結果は索引なしと同じ
await db.exec(`insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts)
  select (array['HND','ITM','CTS','FUK'])[1 + (g % 4)], d::date, 'JAL' || (100 + g), d + make_interval(mins => g), (g % 2)::smallint, repeat('x', 300)
  from generate_series(current_date - 430, current_date - 1, interval '1 day') d, generate_series(1, 60) g`);
await db.exec(`insert into public.rwy_samples (iata, at, callsign, rwy, src, dir)
  select 'HND', now() - make_interval(hours => g), 'JAL' || (g % 900), '34L', 'live', case when g % 2 = 0 then 'arr' else 'dep' end
  from generate_series(1, 430 * 24 * 3) g order by 2`);
await db.exec(`analyze public.airport_tracks_all; analyze public.rwy_samples`);
const before = (await db.query(`select tbl, day from public.cold_candidates((now() at time zone 'Asia/Tokyo')::date - 400, 40)`)).rows.map((r) => r.tbl + ':' + r.day.toISOString().slice(0, 10)).join(',');
// 表が小さいうちは表を読むほうが速いと判断されるので、表を読む道を閉じて「この探し方に BRIN が使えるか」を見る（本物の大きさでの速さは本物の Postgres 16 で測る）
await db.exec(`set enable_seqscan = off`);
const plan = (await db.query(`explain select day from public.airport_tracks_all where day < current_date - 400 group by day`)).rows.map((r) => r['QUERY PLAN']).join('\n');
check('候補探し（日だけで探す）に BRIN 索引が使える', /airport_tracks_all_day_brin/.test(plan), plan);
const plan2 = (await db.query(`explain select * from public.airport_tracks_all where day = current_date - 420`)).rows.map((r) => r['QUERY PLAN']).join('\n');
await db.exec(`set enable_indexscan = off`);
const plan3 = (await db.query(`explain select * from public.airport_tracks_all where day = current_date - 420`)).rows.map((r) => r['QUERY PLAN']).join('\n');
await db.exec(`reset enable_seqscan; reset enable_indexscan`);
check('移す日の読み出し（cold_rows・cold_done と同じ条件）は、主キーか BRIN 索引で引ける（表を丸ごと読まない）', /airport_tracks_all_pkey|airport_tracks_all_day_brin/.test(plan2) && /airport_tracks_all_day_brin/.test(plan3), [plan2, plan3]);
const rp = async () => { await db.exec(`set enable_seqscan = off`); const r = (await db.query(`explain select (at at time zone 'Asia/Tokyo')::date from public.rwy_samples where at < now() - interval '400 days' group by 1`)).rows.map((r) => r['QUERY PLAN']).join('\n'); await db.exec(`reset enable_seqscan`); return r; };
const plan4 = await rp();
check('滑走路の記録も時刻だけの探し方に BRIN 索引が使える', /rwy_samples_at_brin/.test(plan4), plan4);
await db.exec(`set enable_bitmapscan = off; set enable_indexscan = off`);
const noidx = (await db.query(`select tbl, day from public.cold_candidates((now() at time zone 'Asia/Tokyo')::date - 400, 40)`)).rows.map((r) => r.tbl + ':' + r.day.toISOString().slice(0, 10)).join(',');
await db.exec(`reset enable_bitmapscan; reset enable_indexscan`);
check('候補の日は索引があってもなくても同じ', before === noidx && before.split(',').length >= 30, [before.slice(0, 120), noidx.slice(0, 120)]);
const sizes = (await db.query(`select pg_relation_size('public.airport_tracks_all') as t, pg_relation_size('public.airport_tracks_all_day_brin') as i`)).rows[0];
check('BRIN 索引は表の100分の1より小さい', Number(sizes.i) * 100 < Number(sizes.t), sizes);

// ---- 3. 自動掃除の設定 ----
const opts = (await db.query(`select relname, reloptions from pg_class where relname in ('track_points', 'live_positions') and relnamespace = 'public'::regnamespace order by 1`)).rows;
check('track_points・live_positions は 2%＋1000行で自動掃除', opts.length === 2 && opts.every((o) => ['autovacuum_vacuum_scale_factor=0.02', 'autovacuum_vacuum_threshold=1000', 'autovacuum_analyze_scale_factor=0.05'].every((x) => (o.reloptions || []).includes(x))), opts);

// ---- 4. 記録は1行も消えない・RLS と権限は今のまま ----
const count = async () => Object.fromEntries(await Promise.all(['airport_tracks_all', 'rwy_samples'].map(async (t) => [t, Number(await q1(`select count(*) from public.${t}`))])));
const c0 = await count();
for (const j of jobs) { try { await db.exec(j.cmd); } catch {} finally { await db.exec(`reset statement_timeout; reset lock_timeout`); } }
const c1 = await count();
check('毎日の処理を全部流しても、全機の航跡と滑走路の記録は1行も減らない', JSON.stringify(c0) === JSON.stringify(c1) && c0.airport_tracks_all > 0 && c0.rwy_samples > 0, [c0, c1]);
for (const t of ['airport_tracks_all', 'rwy_samples', 'ga_events', 'atc_msgs', 'track_points', 'live_positions']) {
  check(`${t} の RLS は有効のまま`, await q1(`select relrowsecurity from pg_class where oid = 'public.${t}'::regclass`) === true, null);
}
check('ログインしていない人は全機の航跡を読めないまま', String(await as('anon', `select count(*) from public.airport_tracks_all`)).startsWith('ERROR: permission denied'), null);
check('利用者も全機の航跡を読めないまま', String(await as('authenticated', `select count(*) from public.airport_tracks_all`)).startsWith('ERROR: permission denied'), null);

console.log(bad ? `\n${bad} 件 NG` : '\nすべて OK');
process.exit(bad ? 1 : 0);
