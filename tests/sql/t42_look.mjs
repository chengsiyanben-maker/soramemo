// 見る・遊ぶ：特別塗装機を見た（チェックインの前後45分）、あの日の空港、空港の傾向
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
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id, email) values ('${A}', 'a@x'), ('${B}', 'b@x')`);
const ap = (await db.query(`select id from public.airports where iata = 'HND' limit 1`)).rows[0]?.id;
const as = async (uid, sql) => { await db.exec(`set request.jwt.claim.sub = '${uid ?? ''}'; set role ${uid ? 'authenticated' : 'anon'}`); try { return Object.values((await db.query(sql)).rows[0])[0]; } finally { await db.exec(`reset role; reset request.jwt.claim.sub`); } };
if (ap) {
  await db.exec(`insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values ('${A}', ${ap}, 35.55, 139.78, 10, now() - interval '2 hours', now() - interval '2 hours'), ('${B}', ${ap}, 35.55, 139.78, 10, now() - interval '9 hours', now() - interval '9 hours');
    insert into public.reg_legs (reg, callsign, day, first_at, last_at, dep, arr) values ('JA01XJ', 'JAL1', ((now() - interval '110 minutes') at time zone 'Asia/Tokyo')::date, now() - interval '3 hours', now() - interval '110 minutes', 'ITM', 'HND'),
      ('JA02XJ', 'JAL2', ((now() - interval '5 hours') at time zone 'Asia/Tokyo')::date, now() - interval '6 hours', now() - interval '5 hours', 'HND', 'CTS')`);
  const a = await as(A, `select public.my_livery_seen(array['JA01XJ','JA02XJ'])`), b = await as(B, `select public.my_livery_seen(array['JA01XJ','JA02XJ'])`);
  check('見た：自分のチェックインの前後45分に着いた機体だけ', a.length === 1 && a[0].reg === 'JA01XJ' && a[0].iata === 'HND' && b.length === 0, { a, b });
  // 日付の境目：流す時刻に頼らず、決めた時刻で試す。C は日本時間 11/21 23時58分にチェックイン。
  //   JA03XJ は 11/22 0時8分に着いた（便の日付は次の日）→ 見える。JA04XJ は 11/21 23時15分に出た（便の日付はその日）→ 見える。
  //   JA05XJ は 11/22 0時53分に着いた（55分後）→ 見えない。D は 11/22 0時5分にチェックイン、JA06XJ は 11/21 23時40分に着いた（便の日付は前の日）→ 見える
  const C = '00000000-0000-0000-0000-00000000000c', D = '00000000-0000-0000-0000-00000000000d';
  await db.exec(`insert into auth.users (id, email) values ('${C}', 'c@x'), ('${D}', 'd@x');
    insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values
      ('${C}', ${ap}, 35.55, 139.78, 10, '2026-11-21 23:58+09', '2026-11-21 23:58+09'), ('${D}', ${ap}, 35.55, 139.78, 10, '2026-11-22 00:05+09', '2026-11-22 00:05+09');
    insert into public.reg_legs (reg, callsign, day, first_at, last_at, dep, arr) values
      ('JA03XJ', 'JAL3', '2026-11-22', '2026-11-21 22:40+09', '2026-11-22 00:08+09', 'CTS', 'HND'),
      ('JA04XJ', 'JAL4', '2026-11-21', '2026-11-21 23:15+09', '2026-11-22 00:50+09', 'HND', 'FUK'),
      ('JA05XJ', 'JAL5', '2026-11-22', '2026-11-21 23:10+09', '2026-11-22 00:53+09', 'OKA', 'HND'),
      ('JA06XJ', 'JAL6', '2026-11-21', '2026-11-21 22:00+09', '2026-11-21 23:40+09', 'ITM', 'HND')`);
  const c = await as(C, `select public.my_livery_seen(array['JA03XJ','JA04XJ','JA05XJ','JA06XJ'])`), dd = await as(D, `select public.my_livery_seen(array['JA03XJ','JA04XJ','JA05XJ','JA06XJ'])`);
  const regs = (x) => x.map((r) => r.reg).sort().join(',');
  check('見た：23時58分のチェックインで、0時をまたいで着いた便・その前に出た便が見える（55分後の便は見えない）', regs(c) === 'JA03XJ,JA04XJ,JA06XJ', c);
  check('見た：0時5分のチェックインで、前の日の23時40分に着いた便が見える', regs(dd) === 'JA03XJ,JA06XJ', dd);
} else console.log('（空港の表が空なので、見たの確かめは飛ばす）');
await db.exec(`insert into public.airport_daily (day, iata, flights, arr, dep, modes, max_wind) values ('2026-10-20', 'HND', 1200, 600, 600, '{"south": 900}', 18);
  insert into public.rwy_samples (iata, dir, at, rwy, src) values ('HND', 'arr', '2026-10-20 03:00+00', '22', 'live'), ('HND', 'arr', '2026-10-20 03:10+00', '22', 'live'), ('HND', 'dep', '2026-10-20 03:00+00', '16R', 'live'), ('HND', 'arr', '2026-10-20 03:00+00', '22', 'track')`);
const d = await as(null, `select public.airport_day('HND', '2026-10-20')`);
check('あの日の空港（羽田は見張りの記録だけ数える）', d.daily.flights === 1200 && d.rwy['arr:22'] === 2 && d.rwy['dep:16R'] === 1, d);
await db.exec(`insert into public.ops_log (at, iata, wdir, wspd, est_mode, obs_mode) values (now(), 'CTS', 180, 12, 'a', 'a'), (now(), 'CTS', 190, 14, 'a', null), (now(), 'CTS', 350, 10, 'b', 'b'), (now(), 'CTS', null, 2, 'a', null);
  insert into public.rwy_samples (iata, dir, at, rwy, src) values ('CTS', 'arr', ((((now() at time zone 'Asia/Tokyo')::date - 1) + time '12:00') at time zone 'Asia/Tokyo'), '01R', 'track'), ('CTS', 'arr', ((((now() at time zone 'Asia/Tokyo')::date - 1) + time '12:00') at time zone 'Asia/Tokyo') - interval '5 minutes', '01R', 'track')`);
// 着陸は前の日の日本時間12時ごろに置く（今の1時間前だと、日本時間1時〜1時5分は0時をまたいで2日に分かれ、1日あたりの数が半分になる）
const t = await as(null, `select public.airport_trend('CTS', 30)`);
check('風の向きごとの運用・時間帯ごとの着陸', t.wind.S.a === 2 && t.wind.N.b === 1 && t.wind.calm.a === 1 && Object.values(t.hours).reduce((x, y) => x + Number(y), 0) === 2 && t.ga.n === 0, t);
if (bad) process.exit(1);
