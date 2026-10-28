// 滑走路の使い方ごとの到着予想の寄り道（eta_calib_mode）：始めの値は「その使い方の便が全体と比べて何分ずれやすいか」。
// 学び方は空港全体と同じ（2日分・40便、3割、1回に2分まで）で、その使い方の便だけで決める。表は匿名から読めない
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const mig = fs.readFileSync(dir + files.find((f) => f.endsWith('_eta_by_mode.sql')), 'utf8');
await db.exec(`update public.eta_calib set extra = 4 where iata = 'HND'`);
// 2〜3日前：北風の便（ずれ +1分）と南風の便（ずれ −11分）を30便ずつ。運用の記録は着陸の5分前
let k = 0;
const add = async (daysAgo, hour, n, diff, mode) => {
  for (let i = 0; i < n; i++) { k++;
    const ata = `(((now() at time zone 'Asia/Tokyo')::date - ${daysAgo})::timestamp + interval '${hour} hours' + interval '${i} minutes') at time zone 'Asia/Tokyo'`;
    await db.exec(`insert into public.ops_log (at, iata, est_mode, obs_mode) values (${ata} - interval '5 minutes', 'HND', '${mode}', '${mode}');
      insert into public.flight_history (svc_date, flight, dep, arr, std, sta, ata, ata_src, eta30)
      values ((now() at time zone 'Asia/Tokyo')::date - ${daysAgo}, 'JL${k}', 'CTS', 'HND', ${ata} - interval '2 hours', ${ata}, ${ata}, 'adsb', ${ata} + interval '${diff} minutes')`); } };
await add(3, 8, 30, 1, 'north'); await add(2, 14, 30, -11, 'south');
check('その時刻の使い方（20分より前の記録しかなければ分からない）', (await db.query(`select public.ops_mode_at('HND', now() - interval '2 days') a, public.ops_mode_at('HND', now() + interval '1 day') b`)).rows[0].b === null);
await db.exec(mig);   // 移行をもう一度流すと、記録から始めの値が入る（何度流しても同じ）
const rows = async () => Object.fromEntries((await db.query(`select mode, extra from public.eta_calib_mode where iata = 'HND'`)).rows.map((r) => [r.mode, Number(r.extra)]));
let r = await rows();
// 全体の中央値は (1 と −11 の間) → percentile_cont で −5。南風は −11 − (−5) = −6 → 4 + 6 = 10、北風は 1 − (−5) = 6 → 4 − 6 = −2 → 0
check('始めの値：南風は全体より遅れやすい分だけ多く、北風は少なく', r.south === 10 && r.north === 0, r);
await db.exec(mig); check('移行は何度流しても同じ', JSON.stringify(await rows()) === JSON.stringify(r));
// 学ぶ：変えた後の南風の便だけで決める。南風で −5分が2日分・40便 → +1.5
await db.exec(`update public.eta_calib_mode set extra_at = now() - interval '4 days'`);
await db.exec(`delete from public.flight_history; delete from public.ops_log`);
await add(2, 9, 20, -5, 'south'); await add(1, 9, 25, -5, 'south'); await add(1, 15, 45, 3, 'north');
await db.query('select public.refresh_eta_calib()');
r = await rows();
check('南風の便だけで、ずれの3割を直す（10 → 11.5）', Math.abs(r.south - 11.5) < 0.01, r);
check('北風は1日分なので、まだ変えない', r.north === 0, r);
await db.exec('set role anon');
const d = (await db.query(`select public.eta_daily_mode('HND', 7) as j`)).rows[0].j;
let denied = false; try { await db.query('select * from public.eta_calib_mode'); } catch { denied = true; }
let denied2 = false; try { await db.query(`select public.ops_mode_at('HND', now())`); } catch { denied2 = true; }
await db.exec('reset role');
check('使い方ごとの日ごとのずれ（中央値と便数だけ）', d.some((x) => x.mode === 'south' && x.n === 25 && Number(x.median) === -5) && d.every((x) => Object.keys(x).length === 4), d);
check('使い方ごとの寄り道の表は匿名から読めない', denied);
check('運用の記録を引く関数は匿名から呼べない', denied2);
if (bad) process.exit(1);
