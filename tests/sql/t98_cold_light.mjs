// 定期の手入れ 11/9：古い記録を移す処理を軽く・安全に（cold_rows は json で作る・cold_done は数えるだけ・消した数が違えば取り消す）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const old = `'2025-01-10'::date`;
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta) values (${old}, 'JL1', 'HND', 'ITM', '2025-01-10 00:00+00', '2025-01-10 01:00+00');
  insert into public.flight_tracks (svc_date, flight, dep, pts) values (${old}, 'JL1', 'HND', 'abc'), (${old}, 'JL9', 'CTS', 'def');
  insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts)
    select 'HND', ${old}, 'JAL' || i, '2025-01-10 00:10+00'::timestamptz + make_interval(secs => i), i % 2, repeat('x', i) from generate_series(1, 50) i;
  insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values ('HND', '2025-01-11', 'JAL1', '2025-01-11 00:10+00', 1, 'next');
  insert into public.reg_legs (reg, callsign, day, first_at, last_at) values ('JA01XJ', 'JAL1', ${old}, '2025-01-10 00:00+00', '2025-01-10 01:00+00');`);

// 1. 中身は前（jsonb）と同じ
const rows = (await db.query(`select public.cold_rows('airport_tracks_all', ${old}) as r`)).rows[0].r;
const ref = (await db.query(`select jsonb_agg(to_jsonb(x)) as r from public.airport_tracks_all x where day = ${old}`)).rows[0].r;
const key = (o) => JSON.stringify(Object.keys(o).sort().map((k) => [k, o[k]]));
const same = Array.isArray(rows) && rows.length === 50 && JSON.stringify(rows.map(key).sort()) === JSON.stringify(ref.map(key).sort());
check('全機の航跡：前の作り（jsonb）と同じ行・同じ値', same, rows?.length);
const ft = (await db.query(`select public.cold_rows('flight_tracks', ${old}) as r`)).rows[0].r;
check('便の航跡には到着の空港（なければ null）', ft.length === 2 && ft.find((x) => x.flight === 'JL1').arr === 'ITM' && ft.find((x) => x.flight === 'JL9').arr === null, ft);
const t = (await db.query(`select pg_typeof(public.cold_rows('reg_legs', ${old}))::text as t, public.cold_rows('ops_log', ${old})::text as e`)).rows[0];
check('返す型は json・記録のない日は空の配列', t.t === 'json' && t.e === '[]', t);

// 2. 8つの表すべてで、数える関数と中身の行数が合う
const tbls = ['airport_tracks_all', 'flight_tracks', 'flight_history', 'reg_legs', 'rotation_obs', 'rwy_samples', 'ops_log', 'ga_events'];
const cnt = (await db.query(`select tbl, public.cold_count(tbl, ${old}) as n, json_array_length(public.cold_rows(tbl, ${old})) as m from unnest($1::text[]) tbl`, [tbls])).rows;
check('8つの表で cold_count と行数が合う', cnt.length === 8 && cnt.every((r) => r.n === r.m) && cnt.find((r) => r.tbl === 'airport_tracks_all').n === 50, cnt);
let e = ''; try { await db.query(`select public.cold_count('nope', ${old})`); } catch (x) { e = x.message; }
check('知らない表は断る', /bad table/.test(e), e);

// 3. 消すときの決まり（前と同じ）
e = ''; try { await db.query(`select public.cold_done('airport_tracks_all', ${old}, 'p', 49, 1)`); } catch (x) { e = x.message; }
check('行数が合わなければ消さない', /row count changed \(50 <> 49\)/.test(e) && (await db.query(`select count(*)::int as n from public.airport_tracks_all`)).rows[0].n === 51, e);
e = ''; try { await db.query(`select public.cold_done('reg_legs', (now() at time zone 'Asia/Tokyo')::date, 'p', 0, 1)`); } catch (x) { e = x.message; }
check('新しすぎる日は消さない', /too new/.test(e), e);

// 4. 数えたあとに行が増えた（数える関数が少なく返した）ときは、消した数が違うので全部取り消す
await db.exec(`alter function public.cold_count(text, date) rename to cold_count_real;
  create function public.cold_count(p_tbl text, p_day date) returns int language sql as $$ select public.cold_count_real(p_tbl, p_day) - 1 $$;`);
e = ''; try { await db.query(`select public.cold_done('airport_tracks_all', ${old}, 'p', 49, 1)`); } catch (x) { e = x.message; }
const left = (await db.query(`select (select count(*)::int from public.airport_tracks_all) as a, (select count(*)::int from public.cold_days) as c`)).rows[0];
check('消した数が控えと違えば取り消す（記録も控えも残る）', /while deleting \(50 <> 49\)/.test(e) && left.a === 51 && left.c === 0, { e, left });
await db.exec(`drop function public.cold_count(text, date); alter function public.cold_count_real(text, date) rename to cold_count;`);

// 5. 合えば控えて、その日だけ消す
const n = (await db.query(`select public.cold_done('airport_tracks_all', ${old}, 'airport_tracks_all/2025/2025-01-10.json.gz', 50, 100) as n`)).rows[0].n;
const after = (await db.query(`select (select count(*)::int from public.airport_tracks_all) as a, (select rows from public.cold_days where tbl = 'airport_tracks_all') as r`)).rows[0];
check('合えば控えて消す（次の日は残る）', n === 50 && after.a === 1 && after.r === 50, { n, after });

// 6. 運営だけ
let denied = 0;
for (const role of ['anon', 'authenticated']) {
  await db.exec(`set role ${role}`);
  for (const q of [`select public.cold_rows('reg_legs', ${old})`, `select public.cold_count('reg_legs', ${old})`, `select public.cold_done('reg_legs', ${old}, 'p', 1, 1)`]) { try { await db.query(q); } catch { denied++; } }
  await db.exec('reset role');
}
check('anon・authenticated は3つとも呼べない', denied === 6, denied);
if (bad) process.exit(1);
