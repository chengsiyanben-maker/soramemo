// 全機の記録：機体の便を足す（最初と最後の時刻）・出発と到着の空港を入れる・この先の便の予想・空の道すじは全機の航跡を先に
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
const q = async (sql) => (await db.query(sql)).rows[0];
// 日本時間で日付が変わった直後は、「1時間前」と「30分前」が別の日になる。そのときは前の日の夜の時刻で作る
const jstMin = Math.floor((Date.now() + 9 * 3600e3) % 864e5 / 60e3), base = Date.now() - (jstMin < 70 ? (jstMin + 10) * 60e3 : 0);
await db.query(`select public.reg_legs_touch($1::jsonb)`, [JSON.stringify([{ reg: 'JA801A', cs: 'ANA21', type: 'B788', at: new Date(base - 3600e3).toISOString() }, { reg: 'JA801A', cs: 'ANA21', type: null, at: new Date(base - 1800e3).toISOString() },
  { reg: 'JA4123', cs: 'JA4123', type: 'C172', at: new Date().toISOString() }])]);
const l = await q(`select count(*)::int as n, min(type) as type, max(last_at) - min(first_at) as span from public.reg_legs`);
check('便を足す（自家用機は残さない・最初と最後の時刻）', l.n === 1 && l.type === 'B788', l);
await db.query(`select public.reg_legs_route($1::jsonb)`, [JSON.stringify([{ cs: 'ANA21', dir: 'dep', iata: 'HND', at: new Date(base - 3700e3).toISOString() }, { cs: 'ANA21', dir: 'arr', iata: 'ITM', at: new Date(base - 1700e3).toISOString() }])]);
const r = await q(`select dep, arr from public.reg_legs where reg = 'JA801A'`);
check('出発と到着の空港', r.dep === 'HND' && r.arr === 'ITM', r);
// 前の日々：ANA21 のあとに ANA30 が4回、ANA99 が1回
for (let d = 1; d <= 5; d++) {
  const nx = d === 5 ? 'ANA99' : 'ANA30';
  await db.exec(`insert into public.reg_legs (reg, callsign, day, first_at, last_at, dep, arr) values
    ('JA80${d}B', 'ANA21', (now() at time zone 'Asia/Tokyo')::date - ${d}, now() - interval '${d} days' - interval '1 hour', now() - interval '${d} days' - interval '30 minutes', 'HND', 'ITM'),
    ('JA80${d}B', '${nx}', (now() at time zone 'Asia/Tokyo')::date - ${d}, now() - interval '${d} days', now() - interval '${d} days' + interval '1 hour', 'ITM', 'HND')`);
}
await db.exec('set role anon'); const p = (await db.query(`select public.predict_rotation_reg('JA801A') as p`)).rows[0].p; await db.exec('reset role');
check('この先の便の予想（よく続く便）', p.known.callsign === 'ANA21' && p.next.length === 1 && p.next[0].callsign === 'ANA30' && p.next[0].dep === 'ITM' && Number(p.next[0].share) >= 0.6, p);
await db.exec(`insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values ('KMJ', (now() at time zone 'Asia/Tokyo')::date - 1, 'SNJ51', now() - interval '1 day', 0, 'abc')`);
await db.exec('set role anon'); const a = (await db.query(`select public.airport_tracks('KMJ', (now() at time zone 'Asia/Tokyo')::date - 1) as a`)).rows[0].a; await db.exec('reset role');
check('空の道すじは全機の航跡', Array.isArray(a) && a.length === 1 && a[0].p === 'abc', a);
check('線ごとに日本時間の「時」も返す', Number.isInteger(a?.[0]?.h) && a[0].h >= 0 && a[0].h <= 23, a);
await db.exec(`insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values ('KMJ', (now() at time zone 'Asia/Tokyo')::date, 'SNJ53', now(), 1, 'def')`);
await db.exec('set role anon'); const td = (await db.query(`select public.airport_tracks('KMJ', (now() at time zone 'Asia/Tokyo')::date) as a`)).rows[0].a; await db.exec('reset role');
check('今日の分も、まとめた所まで返す（3時間ごと）', Array.isArray(td) && td.length === 1 && td[0].p === 'def', td);
let denied = false; await db.exec('set role anon'); try { await db.query(`select public.reg_legs_touch('[]'::jsonb)`); } catch { denied = true; } await db.exec('reset role');
check('記録を足せるのは運営だけ', denied);
if (bad) process.exit(1);
