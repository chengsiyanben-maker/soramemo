// 欠航のお知らせ・同じ便の同じ種類は1つだけ・お知らせの急増の見張り
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
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values ('2026-10-15','JL501','HND','CTS', now(), now() + interval '90 minutes', 'ODPT')`);
const sid = (await db.query(`select id from public.flight_schedule`)).rows[0].id;
await db.exec(`insert into public.flight_alerts (schedule_id, kind, flight, dep, arr, iata, message) values (${sid}, 'cancel', 'JL501', 'HND', 'CTS', '{HND,CTS}', 'JL501は欠航です')`);
check('欠航（cancel）のお知らせを入れられる', true);
let r = await db.query(`insert into public.flight_alerts (schedule_id, kind, flight, dep, arr, iata, message) values (${sid}, 'cancel', 'JL501', 'HND', 'CTS', '{HND,CTS}', '二度目') on conflict (schedule_id, kind) do nothing returning id`);
check('同じ便・同じ種類は2つ目を入れない', r.rows.length === 0, r.rows);
r = (await db.query(`select ops.alert_watchdog() n`)).rows[0].n;
check('少ないうちは見張りは何もしない', r === 0, r);
await db.exec(`insert into public.flight_alerts (kind, flight, dep, arr, iata, message) select 'delay_arr', 'NH' || g, 'HND', 'OKA', '{HND}', 'x' from generate_series(1, 25) g`);
r = (await db.query(`select ops.alert_watchdog() n`)).rows[0].n;
const e = (await db.query(`select count(*)::int n, max(message) m from ops.client_errors where kind = 'alert_surge'`)).rows[0];
check('1時間に20件以上で、運営のエラーの一覧に載せる', r === 1 && e.n === 1 && /delay_arr 25/.test(e.m), e);
r = (await db.query(`select ops.alert_watchdog() n`)).rows[0].n;
check('3時間のうちは二度載せない', r === 0, r);
try { await db.exec(`set role anon`); await db.query(`select ops.alert_watchdog()`); check('見張りは利用者から呼べない', false); } catch { check('見張りは利用者から呼べない', true); } finally { await db.exec('reset role'); }
await db.query(`select public.apply_flight_status($1::jsonb)`, [JSON.stringify([{ id: sid, dep_status: 'Departed', atd: '2026-10-15T00:12:00Z', dep_gate: '10' }])]);
await db.query(`select public.apply_flight_status($1::jsonb)`, [JSON.stringify([{ id: sid, arr_status: 'Arrived', ata: '2026-10-15T01:40:00Z', atd: null }])]);
r = (await db.query(`select dep_status, atd, dep_gate, arr_status, ata from public.flight_schedule where id = ${sid}`)).rows[0];
check('実際の時刻・状態・搭乗口を残し、あとから届いた空の時刻で消さない', r.dep_status === 'Departed' && r.dep_gate === '10' && r.arr_status === 'Arrived' && new Date(r.atd).toISOString() === '2026-10-15T00:12:00.000Z' && new Date(r.ata).toISOString() === '2026-10-15T01:40:00.000Z', r);
try { await db.exec(`set role anon`); await db.query(`select public.apply_flight_status('[]'::jsonb)`); check('運航情報の書き込みは利用者から呼べない', false); } catch { check('運航情報の書き込みは利用者から呼べない', true); } finally { await db.exec('reset role'); }
if (bad) process.exit(1);
