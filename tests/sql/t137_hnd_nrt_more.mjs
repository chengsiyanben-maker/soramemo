// 羽田・成田の細かいデータ（移行 199）
//   1. ground_watch・ground_moves ができる。形の決まり（mode・kind・滑走路・地上を走った時間の幅）
//   2. flight_changes：羽田・成田に関わる便のゲート・機材・状態・見込みの時刻（5分以上）が変わると1件ずつ残る。ほかの空港・5分未満・同じ値は残らない。便の行が消えても残る
//   3. 権限：利用者（anon・authenticated）は3つとも読めない・書けない。RLS は ON。service_role は書ける
//   4. 本人用の読むだけの SQL（docs/pm/hnd-nrt-more-check.sql）が全部流れる
//   5. もう一度流しても同じ・lock_timeout は元に戻る
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const mine = files.find(f => f.endsWith('_hnd_nrt_more.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 600)); if (!ok) bad++; };
const q = async (sql) => (await db.query(sql)).rows;
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const fails = async (sql) => { try { await db.exec(sql); return false; } catch { return true; } };

for (const f of files) { if (f === mine) break; await db.exec(fs.readFileSync(dir + f, 'utf8')); }
check('移行は 199 番', /^\d{8}000199_hnd_nrt_more\.sql$/.test(mine), mine);
// 前からある便（羽田発・伊丹発）
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, aircraft, source) values
  (current_date, 'JL123', 'HND', 'ITM', now() + interval '2 hours', now() + interval '3 hours', 'B738', 'ODPT'),
  (current_date, 'JL124', 'ITM', 'FUK', now() + interval '2 hours', now() + interval '3 hours', 'B738', 'ODPT')`);
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('lock_timeout は元に戻る', (await q1(`show lock_timeout`)) === '0', await q1(`show lock_timeout`));

// 1. 地上の動き
await db.exec(`insert into public.ground_watch (iata, hex, mode, last_at, last_lat, last_lon) values ('HND', '84a1b2', 'park', now(), 35.55, 139.78)`);
check('mode の形が違えば入らない', await fails(`insert into public.ground_watch (iata, hex, mode, last_at, last_lat, last_lon) values ('HND', 'x', 'fly', now(), 35, 139)`), null);
await db.exec(`insert into public.ground_moves (iata, hex, kind, rwy, t_rwy, t_block, taxi_sec, stand_lat, stand_lon) values
  ('HND', '84a1b2', 'arr', '34R', now() - interval '10 minutes', now() - interval '2 minutes', 480, 35.5495, 139.7855),
  ('NRT', '86c1d2', 'dep', '34L', now(), now() - interval '15 minutes', 900, 35.77, 140.38)`);
check('kind の形が違えば入らない', await fails(`insert into public.ground_moves (iata, hex, kind) values ('HND', 'x', 'taxi')`), null);
check('滑走路の形が違えば入らない', await fails(`insert into public.ground_moves (iata, hex, kind, rwy) values ('HND', 'x', 'arr', 'A')`), null);
check('6時間を超える地上の時間は入らない', await fails(`insert into public.ground_moves (iata, hex, kind, taxi_sec) values ('HND', 'x', 'arr', 30000)`), null);

// 2. 便の変わったこと
const n = async () => await q1(`select count(*)::int from public.flight_changes`);
await db.exec(`update public.flight_schedule set dep_gate = '12' where flight = 'JL123'`);
check('ゲートが決まると1件', await n() === 1, await q(`select * from public.flight_changes`));
await db.exec(`update public.flight_schedule set dep_gate = '12' where flight = 'JL123'`);
check('同じ値では残らない', await n() === 1, null);
await db.exec(`update public.flight_schedule set dep_gate = '15', aircraft = 'B788' where flight = 'JL123'`);
check('ゲートと機材が同時に変わると2件', await n() === 3, null);
const g = (await q(`select old_v, new_v from public.flight_changes where field = 'dep_gate' order by id desc limit 1`))[0];
check('前の値と新しい値が残る', g.old_v === '12' && g.new_v === '15', g);
await db.exec(`update public.flight_schedule set etd = std + interval '20 minutes' where flight = 'JL123'`);
check('見込みの時刻が入ると1件', await n() === 4, null);
await db.exec(`update public.flight_schedule set etd = etd + interval '3 minutes' where flight = 'JL123'`);
check('5分未満の動きは残らない', await n() === 4, null);
await db.exec(`update public.flight_schedule set etd = etd + interval '6 minutes', dep_status = 'Delayed' where flight = 'JL123'`);
check('5分以上の動きと状態は残る', await n() === 6, null);
await db.exec(`update public.flight_schedule set dep_gate = '3', dep_status = 'Delayed' where flight = 'JL124'`);
check('羽田・成田に関わらない便は残らない', await n() === 6, null);
await db.exec(`update public.flight_schedule set arr_gate = '7' where flight = 'JL123'`);
await db.exec(`delete from public.flight_schedule where flight = 'JL123'`);
check('便の行が消えても記録は残る', await n() === 7, null);

// 3. 権限
for (const t of ['ground_watch', 'ground_moves', 'flight_changes']) {
  check(`${t} の RLS は ON`, await q1(`select relrowsecurity from pg_class where oid = 'public.${t}'::regclass`) === true, null);
  for (const r of ['anon', 'authenticated']) {
    check(`${r} は ${t} を読めない`, await fails(`set role ${r}; select * from public.${t}; reset role;`), null); await db.exec('reset role');
    check(`${r} は ${t} を消せない`, await fails(`set role ${r}; delete from public.${t}; reset role;`), null); await db.exec('reset role');
  }
}
check('利用者はトリガーの関数を呼べない', !(await q1(`select has_function_privilege('anon', 'public.flight_changes_log()', 'execute')`)), null);
await db.exec(`set role service_role`);
check('service_role は地上の動きを書ける', (await q(`insert into public.ground_moves (iata, hex, kind) values ('HND', 'abc', 'dep') returning id`)).length === 1, null);
await db.exec(`reset role`);

// 4. 読むだけの SQL
await db.exec(`insert into public.rwy_samples (iata, at, rwy) values ('HND', now() - interval '10 minutes', '34L'), ('HND', now() - interval '8 minutes', '34L'), ('HND', now() - interval '6 minutes', '34L')`);
const sql = fs.readFileSync(new URL('../../docs/pm/hnd-nrt-more-check.sql', import.meta.url), 'utf8');
const stmts = sql.split(/;\s*\n/).map(s => s.replace(/^\s*--.*$/mg, '').trim()).filter(Boolean);
check('読むだけの SQL は5つ', stmts.length === 5, stmts.length);
const res = [];
for (const [i, s] of stmts.entries()) {
  check(`SQL ${i + 1} は select（読むだけ）`, /^(select|with)\b/i.test(s) && !/\b(insert|update|delete|create|drop|alter|truncate)\b/i.test(s), s.slice(0, 80));
  try { res.push((await db.query(s)).rows); check(`SQL ${i + 1} が流れる`, true); } catch (e) { res.push([]); check(`SQL ${i + 1} が流れる`, false, e.message); }
}
check('2：羽田の到着の地上の時間は8分', Number(res[1].find(r => r.iata === 'HND' && r.kind === 'arr')?.median_min) === 8, res[1]);
check('5：続けて降りる間隔は120秒', Number(res[4].find(r => r.rwy === '34L')?.median_sec) === 120, res[4]);

// 5. もう一度
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流してもトリガーは1つ・行はそのまま', await q1(`select count(*)::int from pg_trigger where tgname = 'flight_changes_log'`) === 1 && await n() === 7, null);

if (bad) { console.log(`NG ${bad}件`); process.exit(1); }
console.log('t137 すべて OK');
