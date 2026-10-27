// データの使い方と統計レポート：既定は統計オン。統計をオフにした人は数えない。10人未満の区切りは出さない。レポートは運営者だけ
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
const ADM = '00000000-0000-0000-0000-0000000000ad';
const users = Array.from({ length: 12 }, (_, i) => `00000000-0000-0000-0000-0000000001${String(i).padStart(2, '0')}`);
await db.exec(`insert into auth.users (id, email) values ('${ADM}', 'adm@example.com'), ${users.map((u, i) => `('${u}', 'u${i}@example.com')`).join(',')};
  insert into ops.admins values ('${ADM}');`);
try { await db.exec(`insert into ops.flags (key, value) values ('admin_mfa_required', 'false') on conflict (key) do update set value = 'false'`); } catch (e) { }
const as = async (uid, sql) => { try { await db.exec(`set request.jwt.claim.sub = '${uid ?? ''}'; set role ${uid ? 'authenticated' : 'anon'}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec(`reset role; reset request.jwt.claim.sub`); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const p0 = await as(users[0], `select public.my_data_prefs()`);
check('はじめは統計オン・案内と調査はオフ', p0.stats === true && p0.offers === false && p0.research === false, p0);
const p1 = await as(users[0], `select public.set_data_prefs(false, true, false)`);
check('変えられる', p1.stats === false && p1.offers === true, p1);
check('ログインしないと変えられない', String(await as(null, `select public.set_data_prefs(true, true, true)`)).startsWith('ERROR'));
check('表は直接読めない', String(await as(users[1], `select count(*) from public.user_data_prefs`)).startsWith('ERROR'));
const ap = (await db.query(`select id from public.airports where iata = 'HND' limit 1`)).rows[0]?.id;
if (ap) {
  // 12人が10時にチェックイン（うち1人は統計オフ）→ 11人で10人以上なので出る。15時は3人だけ → 出さない
  for (const u of users) await db.exec(`insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values ('${u}', ${ap}, 35.55, 139.78, 10, '2026-10-20 01:00:00+00', '2026-10-20 01:00:00+00')`);
  for (const u of users.slice(0, 3)) await db.exec(`insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values ('${u}', ${ap}, 35.55, 139.78, 10, '2026-10-20 06:00:00+00', '2026-10-20 06:00:00+00')`);
  check('レポートは運営者だけ', String(await as(users[1], `select public.admin_stats_report('HND', '2026-10-01', '2026-10-31')`)).startsWith('ERROR'));
  const r = await as(ADM, `select public.admin_stats_report('HND', '2026-10-01', '2026-10-31')`);
  console.log(JSON.stringify(r));
  check('10人以上の区切りだけ数を出す（統計オフの人は数えない）', r && r.by_hour && r.by_hour['10'] === 11 && r.by_hour['15'] === null && r.checkins.users === 11, r);
} else console.log('（空港の表が空なので、チェックインの集計は飛ばす）');
if (bad) process.exit(1);
