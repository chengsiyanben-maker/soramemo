// 門限チャレンジ：伊丹・福岡だけ、門限の前後の便を返す（遠い時間の便・ほかの空港の便は出さない）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
// 運用タブの「これから着く便」と「今日の遅れ・欠航」
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
  (current_date, 'JL101', 'ITM', 'HND', now() - interval '40 minutes', now() + interval '20 minutes', 'ODPT'),
  (current_date, 'NH201', 'CTS', 'HND', now() - interval '60 minutes', now() + interval '50 minutes', 'ODPT'),
  (current_date, 'JL103', 'FUK', 'HND', now() - interval '30 minutes', now() + interval '70 minutes', 'ODPT'),
  (current_date, 'JL900', 'OKA', 'HND', now() - interval '20 minutes', now() + interval '40 minutes', 'ODPT'),
  (current_date, 'JL555', 'HND', 'KIX', now() + interval '30 minutes', now() + interval '90 minutes', 'ODPT'),
  (current_date, 'NH999', 'HND', 'OKA', now() + interval '5 hours 10 minutes', now() + interval '7 hours', 'ODPT'),
  (current_date - 1, 'JL777', 'ITM', 'HND', now() - interval '1 day 1 hour', now() - interval '1 day', 'ODPT')`);
// NH201 は見込みが30分遅れ、JL900 は欠航、前日の JL777 は20分遅れて着いた
await db.exec(`update public.flight_schedule set eta = sta + interval '30 minutes' where flight = 'NH201'`);
await db.exec(`update public.flight_schedule set arr_status = 'Cancelled' where flight = 'JL900'`);
await db.exec(`update public.flight_schedule set ata = sta + interval '20 minutes' where flight = 'JL777'`);
let r = await as('anon', `select public.airport_board('HND')`);
const arr = (r?.next_arr ?? []).map((f) => f.flight);
check('これから着く便：早い順に並び、欠航の便は出さない', arr.join(',') === 'JL101,JL103,NH201', r?.next_arr);
check('これから出る便：3時間より先の便は出さない', (r?.next_dep ?? []).map((f) => f.flight).join(',') === 'JL555', r?.next_dep);
const hrs = r?.hours ?? [];
check('1時間ごとの表は24時間ぶん', hrs.length === 24, hrs.length);
const tot = (k) => hrs.reduce((x, h) => x + Number(h[k]), 0);
check('今日の遅れ（15分以上）と欠航を数える', tot('late') === 1 && tot('cancel') === 1, { late: tot('late'), cancel: tot('cancel') });
check('前の7日の目安に、前日の遅れが入る', hrs.some((h) => Number(h.ref) > 0), hrs.filter((h) => Number(h.ref) > 0));
r = await as('anon', `select public.airport_board('ZZZ')`);
check('便のない空港でも空の一覧を返す', r && Array.isArray(r.next_arr) && r.next_arr.length === 0, r);
if (bad) process.exit(1);
