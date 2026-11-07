// 古い記録を移す日の候補（cold_candidates）を、索引で次の日を1件ずつ引く形にした（移行 155）。
// 前の作り（日ごとにまとめて並べ替える）と同じ結果になるか、作り物のデータでいろいろな日・件数で比べる。
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v).slice(0, 600)); if (!ok) bad++; };

// 前の作り（移行 078 のまま。同じ日・同じ順位は表の名前の順にそろえる）
await db.exec(`create function public.cold_candidates_old(p_before date, p_limit int default 6) returns table (tbl text, day date)
language sql stable as $$
  select t.tbl, t.day from (
    select 'airport_tracks_all' as tbl, day from public.airport_tracks_all where day < p_before group by day
    union all select 'flight_tracks', svc_date from public.flight_tracks where svc_date < p_before group by svc_date
    union all select 'flight_history', svc_date from public.flight_history where svc_date < p_before group by svc_date
    union all select 'reg_legs', day from public.reg_legs where day < p_before group by day
    union all select 'rotation_obs', svc_date from public.rotation_obs where svc_date < p_before group by svc_date
    union all select 'rwy_samples', (at at time zone 'Asia/Tokyo')::date from public.rwy_samples where at < (p_before::timestamp at time zone 'Asia/Tokyo') group by 2
    union all select 'ops_log', (at at time zone 'Asia/Tokyo')::date from public.ops_log where at < (p_before::timestamp at time zone 'Asia/Tokyo') group by 2
    union all select 'ga_events', (at at time zone 'Asia/Tokyo')::date from public.ga_events where at < (p_before::timestamp at time zone 'Asia/Tokyo') group by 2
  ) t
  order by t.day, case t.tbl when 'flight_tracks' then 0 when 'flight_history' then 2 else 1 end, t.tbl
  limit greatest(1, least(coalesce(p_limit, 6), 40))
$$;`);

const same = async (before, lim) => {
  const a = (await db.query(`select tbl, day::text from public.cold_candidates_old($1, $2)`, [before, lim])).rows;
  const b = (await db.query(`select tbl, day::text from public.cold_candidates($1, $2)`, [before, lim])).rows;
  return { ok: JSON.stringify(a) === JSON.stringify(b), a, b };
};

// 空のとき
let r = await same('2025-06-01', 6);
check('記録がないときは何も返さない', r.ok && r.b.length === 0, r);

// 日本時間の境目：15:00Z は次の日の 0時。14:59Z はその日
await db.exec(`insert into public.ops_log (at, iata, est_mode) values ('2025-01-10 14:59+00', 'HND', 'south'), ('2025-01-10 15:00+00', 'HND', 'south');
  insert into public.ga_events (iata, at, hex, low_ft) values ('KIX', '2025-01-11 14:59:59+00', 'a1', 1000), ('ITM', '2025-01-11 15:00+00', 'a2', 1000);
  insert into public.rwy_samples (iata, at, rwy, src, dir, callsign) values ('HND', '2025-01-12 15:00+00', '34L', 'track', 'arr', 'JAL1'), ('HND', '2025-01-12 14:00+00', '34R', 'live', 'dep', 'JAL2');`);
r = await same('2025-06-01', 40);
const days = (t) => r.b.filter((x) => x.tbl === t).map((x) => x.day).join(',');
check('日本時間で日を分ける（ops_log）', r.ok && days('ops_log') === '2025-01-10,2025-01-11', r);
check('空港をまたいでも同じ日は1回（ga_events）', r.ok && days('ga_events') === '2025-01-11,2025-01-12', r);
check('取り先をまたいで合わせる（rwy_samples）', r.ok && days('rwy_samples') === '2025-01-12,2025-01-13', r);
r = await same('2025-01-11', 40);
check('p_before の日本時間 0時より前だけ', r.ok && r.b.length === 1 && r.b[0].day === '2025-01-10', r);

// 作り物のデータ：表ごとに日をばらばらに抜き、空港や取り先も混ぜる
await db.exec(`
  insert into public.flight_history (svc_date, flight, dep, arr, std, sta)
    select d, 'JL' || f, 'HND', 'ITM', d::timestamptz, d::timestamptz + interval '1 hour'
    from generate_series('2024-09-01'::date, '2025-05-31'::date, interval '1 day') g(d), generate_series(1, 3) f where (extract(doy from d)::int * 7) % 5 <> 0;
  insert into public.flight_tracks (svc_date, flight, dep, pts)
    select d, 'JL' || f, 'HND', 'p' from generate_series('2024-09-01'::date, '2025-05-31'::date, interval '1 day') g(d), generate_series(1, 2) f where (extract(doy from d)::int * 3) % 4 <> 0;
  insert into public.reg_legs (reg, callsign, day, first_at, last_at)
    select 'JA' || lpad(r::text, 3, '0') || 'A', 'JAL' || r, d, d::timestamptz, d::timestamptz from generate_series('2024-10-15'::date, '2025-05-31'::date, interval '2 day') g(d), generate_series(1, 4) r;
  insert into public.rotation_obs (svc_date, reg, prev_flight, next_flight, iata)
    select d, 'JA' || r || 'A', 'JL' || r, 'JL' || (r + 1), 'HND' from generate_series('2024-11-03'::date, '2025-05-31'::date, interval '3 day') g(d), generate_series(1, 2) r;
  insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts)
    select ap, d, 'JAL' || c, d::timestamptz, 0, 'x' from generate_series('2024-08-20'::date, '2025-05-31'::date, interval '1 day') g(d),
      unnest(array['CTS', 'FUK', 'HND', 'ITM', 'NRT']) ap, generate_series(1, 2) c where (extract(doy from d)::int + length(ap) * ascii(ap)) % 6 = 0;
  insert into public.ops_log (at, iata, est_mode)
    select t, 'HND', 'north' from generate_series('2024-12-01 10:00+00'::timestamptz, '2025-05-31'::timestamptz, interval '17 hour') t;
  insert into public.ga_events (iata, at, hex, low_ft)
    select ap, t, 'h' || ap, 500 from generate_series('2024-09-10 03:00+00'::timestamptz, '2025-05-31'::timestamptz, interval '29 hour') t, unnest(array['KIX', 'NGO', 'OKA']) ap
    where (extract(epoch from t)::bigint / 3600 + ascii(ap)) % 4 = 0;
  insert into public.rwy_samples (iata, at, rwy, src, dir, callsign)
    select 'NRT', t, '16R', s, 'arr', 'ANA' || (extract(epoch from t)::bigint % 9000) from generate_series('2024-10-01 05:00+00'::timestamptz, '2025-05-31'::timestamptz, interval '31 hour') t, unnest(array['live', 'track']) s
    where (extract(epoch from t)::bigint / 3600 + ascii(s)) % 3 = 0;`);
let all = true, tried = 0, sample;
for (const before of ['2024-08-01', '2024-09-02', '2024-10-20', '2024-12-01', '2025-02-15', '2025-06-01', '2026-01-01'])
  for (const lim of [null, 1, 2, 6, 13, 40, 99]) {
    r = await same(before, lim); tried++;
    if (!r.ok) { all = false; sample = { before, lim, a: r.a.slice(0, 8), b: r.b.slice(0, 8) }; }
  }
check(`前の作りと同じ結果（${tried}通りの日・件数）`, all, sample);
r = await same('2026-01-01', 40);
check('件数は 40 まで・航跡は便の実績より先', r.b.length === 40 && r.b.findIndex((x) => x.tbl === 'flight_tracks') < r.b.findIndex((x) => x.tbl === 'flight_history'), r.b.slice(0, 6));

// 移したあと（消えた日）は候補から外れる
const first = (await db.query(`select tbl, day::text from public.cold_candidates('2026-01-01', 1)`)).rows[0];
const n = (await db.query(`select jsonb_array_length(public.cold_rows($1, $2::date)) as n`, [first.tbl, first.day])).rows[0].n;
await db.query(`select public.cold_done($1, $2::date, 'p', $3, 1)`, [first.tbl, first.day, n]);
r = await same('2026-01-01', 6);
check('移した日は候補から外れる', r.ok && !r.b.some((x) => x.tbl === first.tbl && x.day === first.day), r);

// 表の名前の誤り・運営だけ
let e = ''; try { await db.query(`select * from public.cold_days_of('users', '2025-01-01', 3)`); } catch (x) { e = x.message; }
check('知らない表は断る', /bad table/.test(e), e);
let denied = 0; await db.exec('set role anon');
try { await db.query(`select * from public.cold_days_of('reg_legs', '2025-06-01', 3)`); } catch { denied++; }
try { await db.query(`select * from public.cold_candidates('2025-06-01', 3)`); } catch { denied++; }
await db.exec('reset role'); await db.exec('set role authenticated');
try { await db.query(`select * from public.cold_days_of('reg_legs', '2025-06-01', 3)`); } catch { denied++; }
await db.exec('reset role');
check('候補を見られるのは運営だけ', denied === 3, denied);
if (bad) process.exit(1);
