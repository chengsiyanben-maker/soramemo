// 海外の会社の便の実績の180日より前をファイル置き場へ（移行 181）
//   1. cold_candidates：foreign_legs は180日より前の日が候補になる（ほかの表は今までどおり p_before＝400日より前だけ）
//   2. cold_rows・cold_count が foreign_legs の1日分を返す・数える。cold_done で控えを書いて表から外す（行数が違えば外さない）
//   3. ほかの表の動きは前と同じ・cold_done の lock_timeout 5s は残る・権限は運営だけ
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.sql')).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const one = async (sql, p) => (await db.query(sql, p)).rows[0];
const rows = async (sql, p) => (await db.query(sql, p)).rows;

const today = (await one(`select (now() at time zone 'Asia/Tokyo')::date::text d`)).d;
const D = async (k) => (await one(`select ($1::date + $2::int)::text d`, [today, k])).d;
const d200 = await D(-200), d181 = await D(-181), d179 = await D(-179), d100 = await D(-100), before = await D(-400);
const fl = (day, cs, hm) => `('${day}', '${cs}', 'NRT', 0, (('${day} ${hm}')::timestamp at time zone 'Asia/Tokyo'), 'KE703', 'KE', 'HL8001', 'A333')`;
await db.exec(`insert into public.foreign_legs (day, callsign, iata, dep_here, at, flight, airline, reg, type) values
  ${fl(d200, 'KAL703', '13:00')}, ${fl(d200, 'KAL705', '15:00')}, ${fl(d181, 'KAL703', '13:00')}, ${fl(d179, 'KAL703', '13:00')}, ${fl(d100, 'KAL703', '13:00')};
  insert into public.reg_legs (reg, callsign, day, first_at, last_at) values ('JA01XJ', 'JAL1', '${d200}', now() - interval '200 days', now() - interval '200 days');`);

// 1
const c = await rows(`select tbl, day::text from public.cold_candidates($1::date, 40)`, [before]);
const fc = c.filter((x) => x.tbl === 'foreign_legs').map((x) => x.day);
check('foreign_legs は180日より前の日だけが候補（古い順）', JSON.stringify(fc) === JSON.stringify([d200, d181]), c);
check('ほかの表（reg_legs）は今までどおり400日より前だけ', !c.some((x) => x.tbl === 'reg_legs'), c);
const c2 = await rows(`select tbl, day::text from public.cold_candidates($1::date, 1)`, [before]);
check('件数の上限は表をまたいで効く', c2.length === 1 && c2[0].day === d200, c2);

// 2
const r = (await one(`select public.cold_rows('foreign_legs', $1::date) r`, [d200])).r;
check('cold_rows：1日分の行（列はそのまま）', Array.isArray(r) && r.length === 2 && r.every((x) => x.flight === 'KE703' && x.reg === 'HL8001' && x.iata === 'NRT'), r);
check('cold_count：数が合う', (await one(`select public.cold_count('foreign_legs', $1::date) n`, [d200])).n === 2, null);
let e = ''; try { await db.query(`select public.cold_done('foreign_legs', $1::date, 'p', 3, 10)`, [d200]); } catch (x) { e = x.message; }
check('行数が違えば外さない', /row count changed/.test(e) && (await one(`select count(*)::int n from public.foreign_legs`)).n === 5, e);
const n = (await one(`select public.cold_done('foreign_legs', $1::date, 'foreign_legs/x.json.gz', 2, 10) n`, [d200])).n;
const left = await rows(`select day::text from public.foreign_legs order by day`);
const ctl = await rows(`select tbl, day::text, rows, path from public.cold_days where tbl = 'foreign_legs'`);
check('cold_done：控えを書いて、その日だけ表から外す', n === 2 && left.length === 3 && !left.some((x) => x.day === d200)
  && ctl.length === 1 && ctl[0].day === d200 && ctl[0].rows === 2 && ctl[0].path === 'foreign_legs/x.json.gz', { n, left, ctl });
e = ''; try { await db.query(`select public.cold_done('foreign_legs', $1::date, 'p', 1, 1)`, [await D(-10)]); } catch (x) { e = x.message; }
check('30日より新しい日は外さない（前と同じ決まり）', /too new/.test(e), e);
e = ''; try { await db.query(`insert into public.cold_days (tbl, day, path, rows) values ('nope', '2020-01-01', 'p', 0)`); } catch (x) { e = x.message; }
check('控えの表は知らない表の名前を断る', /check constraint/.test(e), e);

// 3
const cfg = (await one(`select proconfig from pg_proc where proname = 'cold_done'`)).proconfig ?? [];
check('cold_done の lock_timeout 5s は残る', cfg.includes('lock_timeout=5s'), cfg);
const tbls = ['airport_tracks_all', 'flight_tracks', 'flight_history', 'reg_legs', 'rotation_obs', 'rwy_samples', 'ops_log', 'ga_events', 'foreign_legs'];
const cnt = await rows(`select tbl, public.cold_count(tbl, $1::date) as n, json_array_length(public.cold_rows(tbl, $1::date)) as m from unnest($2::text[]) tbl`, [d181, tbls]);
check('9つの表で cold_count と行数が合う', cnt.length === 9 && cnt.every((x) => x.n === x.m), cnt);
for (const role of ['anon', 'authenticated']) {
  let msg = ''; try { await db.exec(`set role ${role}`); await db.query(`select public.cold_rows('foreign_legs', current_date)`); } catch (x) { msg = x.message; } finally { await db.exec('reset role'); }
  check(`${role} は cold_rows を呼べない`, /permission denied/.test(msg), msg);
}

console.log(bad ? `NG ${bad}` : 'すべて OK'); process.exit(bad ? 1 : 0);
