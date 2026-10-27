// 古い記録をファイル置き場へ：候補は古い順（航跡は便の実績より先）、行数が合うときだけ消す、新しすぎる日は消さない、運営だけ
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`set co3.season_day = '2026-05-20'`);   // 季節の需要のない日で手計算する（季節は t72）
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const old = `'2025-01-10'::date`;
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta) values (${old}, 'JL1', 'HND', 'ITM', '2025-01-10 00:00+00', '2025-01-10 01:00+00');
  insert into public.flight_tracks (svc_date, flight, dep, pts) values (${old}, 'JL1', 'HND', 'abc');
  insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values ('HND', ${old}, 'JAL1', '2025-01-10 00:10+00', 1, 'xyz');
  insert into public.reg_legs (reg, callsign, day, first_at, last_at) values ('JA01XJ', 'JAL1', ${old}, '2025-01-10 00:00+00', '2025-01-10 01:00+00');
  insert into public.reg_legs (reg, callsign, day, first_at, last_at) values ('JA01XJ', 'JAL3', (now() at time zone 'Asia/Tokyo')::date, now(), now());`);
const c = (await db.query(`select * from public.cold_candidates('2025-06-01', 10)`)).rows;
check('候補は古い日だけ・航跡は便の実績より先', c.length === 4 && c.findIndex((x) => x.tbl === 'flight_tracks') < c.findIndex((x) => x.tbl === 'flight_history'), c);
const ft = (await db.query(`select public.cold_rows('flight_tracks', ${old}) as r`)).rows[0].r;
check('便の航跡に到着の空港を付ける', ft.length === 1 && ft[0].arr === 'ITM' && ft[0].pts === 'abc', ft);
let e = ''; try { await db.query(`select public.cold_done('reg_legs', ${old}, 'p', 5, 1)`); } catch (x) { e = x.message; }
check('行数が合わなければ消さない', /row count/.test(e) && (await db.query(`select count(*)::int as n from public.reg_legs`)).rows[0].n === 2, e);
const n = (await db.query(`select public.cold_done('reg_legs', ${old}, 'reg_legs/2025/2025-01-10.json.gz', 1, 100) as n`)).rows[0].n;
check('行数が合えば控えて消す', n === 1 && (await db.query(`select count(*)::int as n from public.reg_legs`)).rows[0].n === 1 && (await db.query(`select count(*)::int as n from public.cold_days`)).rows[0].n === 1);
e = ''; try { await db.query(`select public.cold_done('reg_legs', (now() at time zone 'Asia/Tokyo')::date, 'p', 1, 1)`); } catch (x) { e = x.message; }
check('新しすぎる日は消さない', /too new/.test(e), e);
let denied = false; await db.exec('set role anon'); try { await db.query(`select public.cold_rows('reg_legs', ${old})`); } catch { denied = true; }
const l = (await db.query(`select public.cold_days_list('reg_legs') as l`)).rows[0].l; await db.exec('reset role');
check('記録の中身は運営だけ・移した日の一覧はだれでも', denied && l.n === 1 && l.first === '2025-01-10', l);
if (bad) process.exit(1);
