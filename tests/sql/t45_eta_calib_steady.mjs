// 到着予想の寄り道の補正（refresh_eta_calib）：2日分・40便がそろうまで直さない。直すのはずれの3割、1回に2分まで。
// 日ごとのずれ（eta_daily）は中央値と便数だけ返し、匿名でも呼べる。表は匿名から読めない
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
const extra = async () => Number((await db.query(`select extra from public.eta_calib where iata = 'HND'`)).rows[0].extra);
// 前に変えた時刻を2日前の0時にして、そのあとの記録だけで決める
await db.exec(`update public.eta_calib set extra = 6, extra_at = (now() at time zone 'Asia/Tokyo')::date - 3 where iata = 'HND'`);
// diff 分だけ早い／遅い予想（eta30 − ata）の便を、日ごとに n 便入れる
let k = 0;
const add = async (daysAgo, n, diff) => { for (let i = 0; i < n; i++) { k++;
  await db.query(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, ata, ata_src, eta30)
    values ((now() at time zone 'Asia/Tokyo')::date - $1::int, $2, 'CTS', 'HND', now() - ($1::int || ' days')::interval - interval '3 hours', now() - ($1::int || ' days')::interval,
            now() - ($1::int || ' days')::interval, 'adsb', now() - ($1::int || ' days')::interval + ($3::float || ' minutes')::interval)`, [daysAgo, `JL${k}`, diff]); } };
await add(1, 45, -4);
await db.query('select public.refresh_eta_calib()');
check('1日分だけ（45便）では直さない', await extra() === 6, await extra());
await add(2, 10, -4);
await db.query('select public.refresh_eta_calib()');
check('2日分・55便：ずれ −4分の3割（+1.2分）だけ直す', Math.abs(await extra() - 7.2) < 0.01, await extra());
// 直した後の記録だけで次を決める：大きくずれても1回に2分まで
await db.exec(`update public.eta_calib set extra_at = (now() at time zone 'Asia/Tokyo')::date - 3 where iata = 'HND'`);
await db.exec(`delete from public.flight_history`); await add(1, 30, 12); await add(2, 30, 12);
await db.query('select public.refresh_eta_calib()');
check('ずれ +12分でも、1回に動かすのは2分まで', Math.abs(await extra() - 5.2) < 0.01, await extra());
await db.exec('set role anon');
const d = (await db.query(`select public.eta_daily('hnd', 7) as j`)).rows[0].j;
let denied = false; try { await db.query('select * from public.flight_history'); } catch { denied = true; }
await db.exec('reset role');
check('日ごとのずれ（中央値と便数だけ、匿名でも呼べる）', d.length === 2 && d.every((x) => x.n === 30 && Number(x.median) === 12 && Object.keys(x).length === 3), d);
check('表は匿名から読めない', denied);
if (bad) process.exit(1);
