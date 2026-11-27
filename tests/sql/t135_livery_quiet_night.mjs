// 特別塗装機の知らせを1便で1つに・夜の静かな時間（移行 197）
//   1. push_subs.quiet_night：今いる購読も新しい購読も true、false にもできる、null は入らない
//   2. livery_plans.quiet_push_at：はじめ null。「null のものだけ書き換える」で2回目は0行（朝の送り直しが1回だけになる）
//   3. 権限：利用者（anon・authenticated）は push_subs・livery_plans を読めない・書けない。RLS は ON のまま
//   4. もう一度流しても同じ・lock_timeout は元に戻る
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const mine = files.find(f => f.endsWith('_livery_quiet_night.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 600)); if (!ok) bad++; };
const q = async (sql) => (await db.query(sql)).rows;
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const fails = async (sql) => { try { await db.exec(sql); return false; } catch { return true; } };

for (const f of files) { if (f === mine) break; await db.exec(fs.readFileSync(dir + f, 'utf8')); }
check('移行は 197 番', /^\d{8}000197_livery_quiet_night\.sql$/.test(mine), mine);

// 前からいる購読と予定
await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, sp_airports) values ('https://fcm.googleapis.com/x/1', 'k', 'a', '{HND}');
insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values (current_date, 'JL123', 'HND', 'ITM', now() + interval '2 hours', now() + interval '3 hours', 'ODPT');
insert into public.livery_plans (schedule_id, flight, dep, arr, std, livery) select id, flight, dep, arr, std, 'ミッキー' from public.flight_schedule;`);
await db.exec(fs.readFileSync(dir + mine, 'utf8'));

// 1. quiet_night
check('今いる購読は quiet_night = true', await q1(`select quiet_night from public.push_subs where id = (select min(id) from public.push_subs)`) === true, null);
await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, sp_airports) values ('https://fcm.googleapis.com/x/2', 'k', 'a', '{NRT}')`);
check('新しい購読も quiet_night = true', await q1(`select quiet_night from public.push_subs where endpoint like '%/2'`) === true, null);
await db.exec(`update public.push_subs set quiet_night = false where endpoint like '%/2'`);
check('false にできる', await q1(`select quiet_night from public.push_subs where endpoint like '%/2'`) === false, null);
check('null は入らない', await fails(`update public.push_subs set quiet_night = null`), null);
// push-subscribe の上書き（列を渡さない upsert）では前の値のまま
await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, sp_airports) values ('https://fcm.googleapis.com/x/2', 'k2', 'a2', '{HND}')
  on conflict (endpoint) do update set p256dh = excluded.p256dh, auth = excluded.auth, sp_airports = excluded.sp_airports`);
check('列を渡さない上書きでは前の設定のまま（false）', await q1(`select quiet_night from public.push_subs where endpoint like '%/2'`) === false, null);

// 2. quiet_push_at
check('予定の quiet_push_at ははじめ null', await q1(`select count(*)::int from public.livery_plans where quiet_push_at is null`) === 1, null);
const once = async () => (await q(`update public.livery_plans set quiet_push_at = now() where quiet_push_at is null and std > now() returning schedule_id`)).length;
check('朝の送り直しは1回目だけ行が返る', (await once()) === 1 && (await once()) === 0, null);
check('livery_plans_upcoming は前のまま動く', JSON.parse(await q1(`select public.livery_plans_upcoming('HND')::text`)).length === 1, null);

// 3. 権限・RLS
for (const t of ['push_subs', 'livery_plans']) {
  check(`${t} の RLS は ON`, await q1(`select relrowsecurity from pg_class where oid = 'public.${t}'::regclass`) === true, null);
  for (const r of ['anon', 'authenticated']) {
    check(`${r} は ${t} を読めない`, await fails(`set role ${r}; select * from public.${t}; reset role;`), null); await db.exec('reset role');
    check(`${r} は ${t} の quiet の列を書けない`, await fails(`set role ${r}; update public.${t} set ${t === 'push_subs' ? 'quiet_night = false' : 'quiet_push_at = null'}; reset role;`), null); await db.exec('reset role');
  }
}

// 4. もう一度
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流しても列は1つずつ・値はそのまま', await q1(`select count(*)::int from information_schema.columns where table_schema = 'public' and column_name in ('quiet_night', 'quiet_push_at')`) === 2
  && await q1(`select quiet_night from public.push_subs where endpoint like '%/2'`) === false, null);
check('移行のあと lock_timeout は元に戻る', (await q1(`show lock_timeout`)) === '0', null);

console.log(bad ? `\n${bad} 件 NG` : '\nすべて OK'); process.exit(bad ? 1 : 0);
