// 運用を開いたときの速さ（移行 165）：時刻表と記録の索引・airport_board の1時間ごとの数を1回で数える形
//   作り物の時刻表（8日半・5空港＋海外、欠航・遅れ・機体の位置で見つけた時刻あり）で、前の airport_board と全部同じ答えになるか、
//   索引が使われるか、権限が変わっていないか、もう一度流しても同じかを確かめる
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const mine = files.find(f => f.endsWith('_ops_speed.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 600)); if (!ok) bad++; };
const q = async (sql) => (await db.query(sql)).rows;
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];

// 165 の前まで流し、前の airport_board を別の名前で写しておく
for (const f of files) { if (f === mine) break; await db.exec(fs.readFileSync(dir + f, 'utf8')); }
const prev = await q1(`select pg_get_functiondef('public.airport_board(text, text)'::regprocedure)`);
await db.exec(prev.replace(/public\.airport_board\(/, 'public.airport_board_old('));
await db.exec(fs.readFileSync(dir + mine, 'utf8'));

// 1. 番号と索引
check('移行は 165 番', /^\d{8}000165_ops_speed\.sql$/.test(mine), mine);
const idx = await q(`select indexname n, indexdef d from pg_indexes where schemaname = 'public' and indexname in ('flight_schedule_dep_std', 'flight_schedule_arr_std', 'flight_history_dep_day') order by 1`);
check('索引3つ（時刻表の出発・到着の空港と時刻、記録の出発の空港と運航日）', idx.length === 3
  && /\(dep, svc_date\)/.test(idx[0].d) && /\(arr, std\)/.test(idx[1].d) && /\(dep, std\)/.test(idx[2].d), idx);

// 2. 作り物の時刻表：5空港＋海外（ICN）、今から 8日6時間前〜7時間後。決まった順の数で作る（毎回同じ）
await db.exec(`
insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, aircraft, source)
select ((t at time zone 'Asia/Tokyo')::date), 'JL' || (100 + i), d, a, t, t + interval '95 minutes', case when i % 3 = 0 then '763' end, 'ODPT'
from (select i, now() - interval '8 days 7 hours' + (i * interval '4 minutes 7 seconds') as t,
             (array['HND','ITM','CTS','FUK','OKA','HND','HND'])[1 + i % 7] as d,
             (array['ITM','HND','HND','HND','HND','CTS','ICN','FUK','OKA'])[1 + (i * 7) % 9] as a
      from generate_series(1, 3100) i) s where d <> a;
update public.flight_schedule set
  etd = case when id % 4 = 0 then std + ((id % 50) * interval '1 minute') end,
  eta = case when id % 5 <> 0 then sta + ((id % 40) * interval '1 minute') end,
  atd = case when std < now() - interval '30 minutes' and id % 6 <> 0 then std + ((id % 33) * interval '1 minute') end,
  ata = case when sta < now() - interval '10 minutes' and id % 7 <> 0 then sta + ((id % 29) * interval '1 minute') end,
  dep_status = case when id % 23 = 0 then 'Cancelled' when id % 11 = 0 then '遅延' end,
  arr_status = case when id % 31 = 0 then 'cancelled' end;
insert into public.flight_watch (schedule_id, state)
select id, case id % 3
  when 0 then jsonb_build_object('phase', 'air', 'takeoff_at', extract(epoch from std + interval '12 minutes') * 1000, 'takeoff_est', false, 'eta', extract(epoch from sta + interval '9 minutes') * 1000)
  when 1 then jsonb_build_object('phase', 'landed', 'takeoff_at', extract(epoch from std + interval '15 minutes') * 1000, 'takeoff_est', true,
                                 'landed_at', extract(epoch from sta + interval '4 minutes') * 1000, 'landed_iata', arr)
  else jsonb_build_object('phase', 'landed', 'landed_at', extract(epoch from sta) * 1000, 'landed_iata', 'XXX') end
from public.flight_schedule where id % 2 = 0;
insert into public.eta_calib (iata, taxi_out, n_out) values ('HND', 17.5, 40) on conflict (iata) do update set taxi_out = excluded.taxi_out;
analyze public.flight_schedule; analyze public.flight_watch;`);
check('作り物の便が入った（2,000便より多い）', await q1(`select count(*)::int from public.flight_schedule`) > 2000, null);

// 3. 前と全部同じ答え（同じトランザクションの中なので now() も同じ）
const pairs = [];
for (const ap of ['HND', 'ITM', 'CTS', 'FUK', 'OKA', 'KIX', 'ICN']) for (const k of ['all', 'intl', 'dom']) pairs.push([ap, k]);
await db.exec('begin');
let same = 0, nonEmpty = 0; const diff = [];
for (const [ap, k] of pairs) {
  const a = await q1(`select public.airport_board_old('${ap}', '${k}')::text`), b = await q1(`select public.airport_board('${ap}', '${k}')::text`);
  if (a === b) same++; else diff.push([ap, k]);
  const j = JSON.parse(b); if (j.hours.some((h) => h.flights || h.ref)) nonEmpty++;
}
const hnd = JSON.parse(await q1(`select public.airport_board('HND', 'all')::text`));
await db.exec('commit');
check(`7空港 × 3通り（21通り）で前と同じ答え`, same === pairs.length, diff);
check('数のある1時間ごとの表で比べている（空ばかりではない）', nonEmpty >= 10, nonEmpty);
check('羽田：24時間がそろい、遅れ・欠航・7日の目安が数えられている', hnd.hours.length === 24 && hnd.hours.map((h) => h.h).join() === [...Array(24).keys()].join()
  && hnd.hours.some((h) => h.late > 0) && hnd.hours.some((h) => h.cancel > 0) && hnd.hours.some((h) => Number(h.ref) > 0), hnd.hours);
check('羽田：次の到着・出発も前と同じ形（6件まで・離陸の時刻つき）', hnd.next_arr.length > 0 && hnd.next_arr.length <= 6 && hnd.next_dep.length > 0 && hnd.next_dep.every((x) => x.takeoff && x.taxi === 18), hnd.next_dep[0]);
check('便のない空港（関西）も24時間が0で返る', JSON.parse(await q1(`select public.airport_board('KIX', 'all')::text`)).hours.every((h) => h.flights === 0 && h.late === 0 && h.cancel === 0 && Number(h.ref) === 0), null);

// 4. 索引が使われる（作り物は小さいので、表をまるごと読む方を止めて形だけ見る）
//   本番に近い割合にするため、ほかの20空港どうしの便を14日分足す（時刻表は14日で消えるので、表の中身は14日分）
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source)
  select ((t at time zone 'Asia/Tokyo')::date), 'NH' || (1000 + i % 9000), d, a, t, t + interval '80 minutes', 'ODPT'
  from (select i, now() - interval '14 days' + (i * interval '50 seconds') as t,
               (array['KMQ','KOJ','KMJ','NGS','HIJ','MYJ','TAK','KCZ','OIT','KMI','SDJ','AOJ','AXT','HKD','OBO','KUH','MMB','ISG','MMY','NGO'])[1 + i % 20] as d,
               (array['KMQ','KOJ','KMJ','NGS','HIJ','MYJ','TAK','KCZ','OIT','KMI','SDJ','AOJ','AXT','HKD','OBO','KUH','MMB','ISG','MMY','NGO'])[1 + (i * 3 + 1) % 20] as a
        from generate_series(1, 24000) i) s where d <> a on conflict do nothing;
  analyze public.flight_schedule;`);
const plan1 = (await q(`explain select 1 from public.flight_schedule where (arr = 'HND' or dep = 'HND') and std > now() - interval '8 days 6 hours' and std < now() + interval '6 hours'`)).map((r) => r['QUERY PLAN']).join('\n');
check('時刻表：この空港の分を出発・到着の索引で引く（BitmapOr。ほかの空港の便を読まない）', /flight_schedule_dep_std/.test(plan1) && /flight_schedule_arr_std/.test(plan1), plan1);
await db.exec(`set enable_seqscan = off`);
const plan2 = (await q(`explain select 1 from public.flight_history where dep = 'HND' and svc_date >= current_date - 30 and svc_date < current_date`)).map((r) => r['QUERY PLAN']).join('\n');
check('記録：この空港を出た30日分を出発の空港・運航日の索引で引く', /flight_history_dep_day/.test(plan2) && /svc_date >=/.test(plan2), plan2);
await db.exec(`reset enable_seqscan`);

// 5. 権限と形は前のまま
const priv = await q(`select r, has_function_privilege(r, 'public.airport_board(text, text)', 'execute') e from unnest(array['anon','authenticated']) r`);
check('airport_board は anon・authenticated が呼べる（前と同じ）', priv.every((x) => x.e === true), priv);
const fn = await q(`select p.provolatile v, p.prosecdef s, pg_get_function_result(p.oid) r, array_to_string(p.proconfig, ',') c from pg_proc p where p.oid = 'public.airport_board(text, text)'::regprocedure`);
check('stable・security definer・jsonb を返す・search_path は public（前と同じ）', fn[0].v === 's' && fn[0].s === true && fn[0].r === 'jsonb' && fn[0].c === 'search_path=public', fn);
check('移行のあと lock_timeout は元に戻る', (await q1(`show lock_timeout`)) === '0', await q1(`show lock_timeout`));

// 6. もう一度流しても同じ
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流しても索引は3つのまま', await q1(`select count(*)::int from pg_indexes where indexname in ('flight_schedule_dep_std', 'flight_schedule_arr_std', 'flight_history_dep_day')`) === 3, null);

console.log(bad ? `\n${bad} 件 NG` : '\nすべて OK'); process.exit(bad ? 1 : 0);
