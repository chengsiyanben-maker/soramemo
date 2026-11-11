// 定期の手入れ 11/11：到着空港の部分索引・毎晩の仕事の時間の上限
//   1. 索引を足したあとも refresh_eta_calib は前の作り（20261027000091）と同じ eta_calib・eta_calib_mode を作るか（いくつもの種で）
//   2. eta_daily・eta_daily_mode・使い方ごとの寄り道の読み方が、新しい索引 flight_history_arr_eta で引けるか
//   3. 移行に時間の上限の文が入っているか（pg_cron は手元にないので文を見る）
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

// 前の作りを名前を変えて置く
const src = fs.readFileSync(dir + '20261027000091_eta_by_mode.sql', 'utf8');
const a = src.indexOf('create or replace function public.refresh_eta_calib()');
const b = src.indexOf('revoke all on function public.refresh_eta_calib()');
await db.exec(src.slice(a, b).replace('public.refresh_eta_calib()', 'public.refresh_eta_calib_old()'));

// 種つきの乱数
let seed = 1; const rnd = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
const AIR = ['HND', 'ITM', 'CTS', 'FUK', 'OKA', 'KOJ', 'ISG'];

async function setup(s) {
  seed = s;
  await db.exec(`delete from public.flight_history; delete from public.eta_calib; delete from public.eta_calib_mode; delete from public.ops_log;`);
  const rows = []; const today = (await db.query(`select (now() at time zone 'Asia/Tokyo')::date as d`)).rows[0].d;
  for (let i = 0; i < 900; i++) {
    const arr = AIR[Math.floor(rnd() * AIR.length * (0.6 + 0.4 * rnd())) % AIR.length];
    const dep = arr === 'HND' ? 'ITM' : 'HND';
    const back = Math.floor(rnd() * 18);   // 14日より前の便も混ぜる
    const ataMin = Math.floor(rnd() * 1440);
    const diff = Math.round((rnd() * 30 - 12) * 10) / 10;
    const src = rnd() < 0.55 ? 'adsb' : 'odpt';
    const cancelled = rnd() < 0.04, div = rnd() < 0.03, noEta = rnd() < 0.05;
    rows.push(`(current_date - ${back}, 'JL${i}', '${dep}', '${arr}', now() - interval '${back} days', now() - interval '${back} days',
      now() - interval '${back} days' + interval '${ataMin} minutes', '${src}', ${cancelled}, ${div ? "'NGO'" : 'null'},
      ${noEta ? 'null' : `now() - interval '${back} days' + interval '${ataMin} minutes' + interval '${diff} minutes'`})`);
  }
  await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, ata, ata_src, cancelled, diverted_to, eta30) values ${rows.join(',')}`);
  // 前の寄り道の値（ある空港・ない空港・前に変えた時刻がいろいろ）
  await db.exec(`insert into public.eta_calib (iata, taxi, extra, n_odpt, n_adsb, extra_at) values
    ('HND', 9.5, 10, 0, 0, now() - interval '${Math.floor(rnd() * 10)} days'),
    ('ITM', 4, 3, 0, 0, now() - interval '${Math.floor(rnd() * 10)} days'),
    ('CTS', null, null, 0, 0, now() - interval '20 days')`);
  // 羽田の運用の記録（5分ごと、北と南）と、使い方ごとの寄り道
  await db.exec(`insert into public.ops_log (at, iata, wspd, est_mode, obs_mode)
    select g, 'HND', 10, case when extract(hour from g)::int % 3 = 0 then 'South' else 'North' end, null
    from generate_series(now() - interval '19 days', now(), interval '5 minutes') g;
    insert into public.eta_calib_mode (iata, mode, extra, extra_at) values ('HND', 'North', 8, now() - interval '${Math.floor(rnd() * 8)} days'), ('HND', 'South', 12, now() - interval '30 days');`);
}
const snap = async () => ({
  c: (await db.query(`select iata, taxi, extra, n_odpt, n_adsb, extra_at > now() - interval '1 minute' as moved, extra_at::text as ea from public.eta_calib order by iata`)).rows,
  m: (await db.query(`select iata, mode, extra, n, extra_at > now() - interval '1 minute' as moved from public.eta_calib_mode order by iata, mode`)).rows,
});
const norm = (s) => JSON.stringify({ c: s.c.map(({ ea, ...r }) => (r.moved ? r : { ...r, ea })), m: s.m });

let allSame = true, movedSome = false, diffs = [];
for (const s of [1, 7, 42, 99, 2026, 31337]) {
  await setup(s);
  await db.exec(`create temp table c0 as select * from public.eta_calib; create temp table m0 as select * from public.eta_calib_mode;`);
  const n0 = (await db.query(`select public.refresh_eta_calib_old() as n`)).rows[0].n; const s0 = await snap();
  await db.exec(`delete from public.eta_calib; insert into public.eta_calib select * from c0; delete from public.eta_calib_mode; insert into public.eta_calib_mode select * from m0; drop table c0; drop table m0;`);
  const n1 = (await db.query(`select public.refresh_eta_calib() as n`)).rows[0].n; const s1 = await snap();
  if (n0 !== n1 || norm(s0) !== norm(s1)) { allSame = false; diffs.push({ s, n0, n1, s0, s1 }); }
  if (s1.c.some((r) => r.moved)) movedSome = true;
}
check('6つの種で前の作りと同じ eta_calib・eta_calib_mode（数・地上走行・寄り道・便数・変えたかどうか）', allSame, diffs.slice(0, 1));
check('寄り道を変える空港がある種を含む（比べた意味がある）', movedSome, null);

// 2. 索引で引けるか
await db.exec(`analyze public.flight_history; set enable_seqscan = off; set enable_bitmapscan = on;`);
const plan = async (q) => (await db.query(`explain ${q}`)).rows.map((r) => r['QUERY PLAN']).join(' ');
const p1 = await plan(`select * from public.flight_history where arr = 'HND' and ata_src = 'adsb' and eta30 is not null and ata is not null and not cancelled and diverted_to is null and svc_date >= current_date - 14`);
check('到着空港ごとの読み方は索引 flight_history_arr_eta で引ける', /flight_history_arr_eta/.test(p1), p1);
await db.exec(`reset enable_seqscan`);
const d1 = (await db.query(`select public.eta_daily('HND', 14) as j`)).rows[0].j;
check('eta_daily は今までどおり動く（日ごとの行）', Array.isArray(d1) && d1.length > 0, d1);
const d2 = (await db.query(`select public.eta_daily_mode('HND', 14) as j`)).rows[0].j;
check('eta_daily_mode は今までどおり動く', Array.isArray(d2) && d2.length > 0, d2);

// 権限は前のまま
const priv = (await db.query(`select has_function_privilege('anon', 'public.refresh_eta_calib()', 'execute') as a, has_function_privilege('authenticated', 'public.refresh_eta_calib()', 'execute') as u`)).rows[0];
check('refresh_eta_calib は利用者から呼べない', !priv.a && !priv.u, priv);
const rls = (await db.query(`select relrowsecurity from pg_class where relname = 'flight_history'`)).rows[0];
check('flight_history の RLS は有効のまま', rls.relrowsecurity === true, rls);

// 3. 時間の上限
const mig = fs.readFileSync(dir + '20261111000162_maint_1111.sql', 'utf8');
for (const job of ['eta-calib', 'taxi-out', 'flight-watch-cleanup']) {
  const re = new RegExp(`cron\\.schedule\\('${job}'[^]*?\\$job\\$\\s*set statement_timeout = '\\d+min'; set lock_timeout = '5s';`);
  check(`仕事 ${job} の先頭に statement_timeout と lock_timeout`, re.test(mig), job);
}
check('flight-watch-cleanup の消す決まりは前と同じ（お知らせ2日・時刻表14日）', /flight_alerts where created_at < now\(\) - interval '2 days'/.test(mig) && /flight_schedule where std < now\(\) - interval '14 days'/.test(mig), null);

console.log(bad ? `NG ${bad}` : 'ALL OK'); process.exit(bad ? 1 : 0);
