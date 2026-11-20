// 空の道すじの上限（移行190）：今日と前の7日はだれでも・それより前はログインした人だけ・1人1時間に空港×日60組まで
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
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id) values ('${A}'), ('${B}')`);
const as = async (role, uid, sql) => {
  try { await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub', '${uid ?? ''}', false)`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; }
  finally { await db.exec(`reset role; select set_config('request.jwt.claim.sub', '', false)`); }
};
const isErr = (v) => String(v).startsWith('ERROR');
const T = `(now() at time zone 'Asia/Tokyo')::date`;
// HND の線を、今日・前の日・7日前・8日前・40日前に1本ずつ
for (const d of [0, 1, 7, 8, 40]) await db.exec(`insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values ('HND', ${T} - ${d}, 'JAL${d}', now() - interval '${d} days', 1, 'p${d}')`);
const tr = (role, uid, d, iata = 'HND') => as(role, uid, `select public.airport_tracks('${iata}', ${T} - ${d})`);

for (const d of [0, 1, 7]) { const r = await tr('anon', null, d); check(`ログインなしでも ${d}日前は読める`, Array.isArray(r) && r.length === 1 && r[0].p === 'p' + d, r); }
let r = await tr('anon', null, 8);
check('ログインなしの8日前は login_required', r?.error === 'login_required', r);
r = await tr('anon', null, 40);
check('ログインなしの40日前も login_required', r?.error === 'login_required', r);
r = await tr('authenticated', A, 40);
check('ログインした人は40日前も読める（記録はずっと見られる）', Array.isArray(r) && r.length === 1 && r[0].p === 'p40', r);
check('7日以内は数えない', Number(await q1(`select count(*) from public.track_quota where user_id = '${A}'`)) === 1, null);
r = await tr('authenticated', A, 40);
check('同じ組を読み直しても数えない', Array.isArray(r) && Number(await q1(`select count(*) from public.track_quota where user_id = '${A}'`)) === 1, r);
r = await as('authenticated', A, `select public.airport_tracks('HND', ${T} + 1)`);
check('先の日は空の配列', Array.isArray(r) && r.length === 0, r);
r = await as('authenticated', A, `select public.airport_tracks('hnd', ${T} - 40)`);
check('空港の形がちがうと空の配列（数えない）', Array.isArray(r) && r.length === 0 && Number(await q1(`select count(*) from public.track_quota where user_id = '${A}'`)) === 1, r);

// 上限：60組まで
await db.exec(`insert into public.track_quota (user_id, hr, iata, day) select '${A}', date_trunc('hour', now()), 'HND', ${T} - 100 - g from generate_series(1, 59) g`);
r = await tr('authenticated', A, 40, 'NRT');
check('60組を超えると rate_limited', r?.error === 'rate_limited' && r.retry_after_min >= 1 && r.retry_after_min <= 60, r);
r = await tr('authenticated', A, 40);
check('上限でも、もう数えた組は読める', Array.isArray(r) && r.length === 1, r);
r = await tr('authenticated', A, 1);
check('上限でも7日以内は読める', Array.isArray(r) && r.length === 1, r);
r = await tr('authenticated', B, 40);
check('ほかの人は別に数える', Array.isArray(r) && r.length === 1, r);
await db.exec(`update public.track_quota set hr = hr - interval '3 hours' where user_id = '${A}'`);
r = await tr('authenticated', A, 40, 'NRT');
check('次の時間は読める', Array.isArray(r), r);
check('2時間より前の行は消える', Number(await q1(`select count(*) from public.track_quota where user_id = '${A}'`)) === 1, null);

// 運営の呼び出しは数えない
r = await q1(`select public.airport_tracks('HND', ${T} - 40)`);
check('運営（役なし）は数えずに読める', Array.isArray(r) && r.length === 1, r);
check('track_quota_take は service_role だけ', isErr(await as('authenticated', A, `select public.track_quota_take('${A}', 'HND', ${T})`)) && isErr(await as('anon', null, `select public.track_quota_take('${A}', 'HND', ${T})`)) && await as('service_role', null, `select public.track_quota_take('${B}', 'HND', ${T} - 9)`) === true, null);
check('track_quota_take は uid なしなら false', await as('service_role', null, `select public.track_quota_take(null, 'HND', ${T} - 9)`) === false, null);
check('airport_tracks_raw は直接呼べない', isErr(await as('anon', null, `select public.airport_tracks_raw('HND', ${T} - 40)`)) && isErr(await as('authenticated', A, `select public.airport_tracks_raw('HND', ${T} - 40)`)), null);

// 表の守り
check('track_quota は RLS 有効', await q1(`select relrowsecurity from pg_class where relname = 'track_quota'`) === true, null);
check('本人も track_quota を読めない・書けない', isErr(await as('authenticated', A, `select count(*) from public.track_quota`)) && isErr(await as('authenticated', A, `insert into public.track_quota (user_id, hr, iata, day) values ('${A}', now(), 'HND', ${T})`)) && isErr(await as('anon', null, `delete from public.track_quota`)), null);
await db.exec(`delete from auth.users where id = '${A}'`);
check('退会で数えた行も消える', Number(await q1(`select count(*) from public.track_quota where user_id = '${A}'`)) === 0, null);
check('航跡の記録は消えない', Number(await q1(`select count(*) from public.airport_tracks_all`)) === 5, null);
check('満足度の初期値は 40 のまま', Number(await q1(`select column_default from information_schema.columns where table_name = 'companies' and column_name = 'satisfaction'`)) === 40, null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
