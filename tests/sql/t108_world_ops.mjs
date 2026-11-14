// 海外の空港の止まり具合（移行 169）：FAA の取り込み（始まり・続き・終わり）・10分より古いものは出さない・国際線の欠航と遅れを海外の空港ごとに数える・
// 画面の関数の形と出典・通知の記録（止まり具合がはじめて分かったら送り直す・止まり具合だけの通知 rank 0）・RLS と権限・掃除の仕事
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
const rows = async (sql, p) => (await db.query(sql, p)).rows;

const put = async (list, feed = 'now()') => (await rows(`select iata, kind from public.world_status_put('faa', ${feed}, $1::jsonb) order by 1, 2`, [JSON.stringify(list)]))
  .map((r) => `${r.iata}|${r.kind}`);
const GS = { iata: 'LAX', kind: 'ground_stop', reason: 'equipment', ends: '2026-11-15T02:30:00Z' };
const GDP = { iata: 'sfo', kind: 'gdp', reason: 'low ceilings', avg_delay: 63, max_delay: 121 };

let r = await put([GS, GDP]);
check('はじめての取り込みは全部「始まった」として返る（記号は大文字に）', JSON.stringify(r) === '["LAX|ground_stop","SFO|gdp"]', r);
r = await put([GS, { ...GDP, avg_delay: 80 }]);
const sfo = (await rows(`select avg_delay, count(*) over () n from public.world_airport_status where iata = 'SFO'`))[0];
check('続いているものは返らず、同じ行を書き直す', r.length === 0 && sfo.avg_delay === 80 && Number(sfo.n) === 1, { r, sfo });
r = await put([GDP, { ...GS }, { iata: 'GUM', kind: 'closure', reason: 'typhoon' }, { iata: 'GUM', kind: 'closure', reason: '重なり' }, { iata: 'X1', kind: 'gdp' }]);
check('新しいものだけ返る・同じ空港と種類の重なりは1つ・読めない記号は捨てる', JSON.stringify(r) === '["GUM|closure"]', r);
r = await put([GDP]);
const ended = (await rows(`select iata, kind from public.world_airport_status where ended_at is not null order by 1`)).map((x) => `${x.iata}|${x.kind}`);
check('なくなったものは消さずに終わりにする', r.length === 0 && JSON.stringify(ended) === '["GUM|closure","LAX|ground_stop"]', ended);
r = await put([GDP, GS]);
check('終わったあとにまた始まれば、新しい行で「始まった」', JSON.stringify(r) === '["LAX|ground_stop"]'
  && (await rows(`select count(*)::int c from public.world_airport_status where iata = 'LAX'`))[0].c === 2, r);

// いま出してよいもの
let now = (await rows(`select iata, kind from public.world_status_now() order by 1, 2`)).map((x) => `${x.iata}|${x.kind}`);
check('いま出してよいのは終わっていないものだけ', JSON.stringify(now) === '["LAX|ground_stop","SFO|gdp"]', now);
now = (await rows(`select iata from public.world_status_now(array['LAX'])`));
check('空港を絞れる', now.length === 1 && now[0].iata === 'LAX', now);
await db.exec(`update public.world_airport_status set feed_at = now() - interval '11 minutes' where iata = 'SFO'`);
await db.exec(`update public.world_airport_status set fetched_at = now() - interval '11 minutes' where iata = 'LAX' and ended_at is null`);
check('FAA の Update_Time か取った時刻が10分より前なら出さない', (await rows(`select count(*)::int c from public.world_status_now()`))[0].c === 0);
await put([GDP, GS]);
check('次に取れれば、また出る', (await rows(`select count(*)::int c from public.world_status_now()`))[0].c === 2);

// 国際線の欠航・遅れを海外の空港ごとに数える
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source, dep_status, atd, ata) values
  ('2026-11-15','JL62','NRT','LAX','2026-11-15 08:00+00','2026-11-15 18:00+00','ODPT（JAL）', null, '2026-11-15 08:45+00', null),
  ('2026-11-15','AA8402','NRT','LAX','2026-11-15 08:00+00','2026-11-15 18:00+00','ODPT（JAL）', null, null, null),
  ('2026-11-15','NH6','NRT','LAX','2026-11-15 09:00+00','2026-11-15 19:00+00','ODPT（ANA）', 'odpt.FlightStatus:Cancelled', null, null),
  ('2026-11-15','NH105','LAX','HND','2026-11-15 03:00+00','2026-11-15 14:00+00','ODPT（ANA）', null, '2026-11-15 03:05+00', '2026-11-15 14:00+00'),
  ('2026-11-15','JL5','HND','JFK','2026-11-15 01:00+00','2026-11-15 13:00+00','ODPT（JAL）', null, null, null),
  ('2026-11-15','JL503','HND','CTS','2026-11-15 01:00+00','2026-11-15 02:30+00','ODPT（JAL）', 'odpt.FlightStatus:Cancelled', null, null),
  ('2026-11-14','JL61','LAX','NRT','2026-11-14 18:00+00','2026-11-15 05:00+00','ODPT（JAL）', 'odpt.FlightStatus:Cancelled', null, null)`);
const counts = Object.fromEntries((await rows(`select * from public.world_flight_counts('2026-11-15')`)).map((x) => [x.iata, [x.flights, x.cancelled, x.late30]]));
check('海外の空港ごと：共同運航は1便・欠航と30分以上の遅れ（欠航は遅れに数えない）・国内線と別の日は入らない',
  JSON.stringify(counts) === JSON.stringify({ JFK: [1, 0, 0], LAX: [3, 1, 1] }), counts);

// 画面で使う関数
await db.exec('set role anon');
const ops = (await rows(`select public.world_airport_ops() j`))[0].j;
const one = (await rows(`select public.world_airport_ops('lax') j`))[0].j;
await db.exec('reset role');
check('画面の関数：出典の文・止まり具合と便の数をまとめる', ops.source === 'FAA NAS Status' && /運航の判断には使えません/.test(ops.note) && /遅れることがあります/.test(ops.note)
  && Array.isArray(ops.airports) && ops.airports.some((a) => a.iata === 'SFO' && a.faa.length === 1 && a.faa[0].avg_delay === 63 && a.flights === 0), ops);
const lax = one.airports;
check('画面の関数：空港を絞れる・LAX は地上待機と便の数（今日の日付でないので0）', lax.length === 1 && lax[0].iata === 'LAX' && lax[0].faa[0].kind === 'ground_stop'
  && JSON.stringify(Object.keys(lax[0]).sort()) === '["cancelled","faa","flights","iata","late30"]', lax);

// 通知の記録：止まり具合
await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, airports, flights) values ('https://push.example/w', 'k', 'a', '{}', '{JL62@2026-11-15}')`);
const u = (await rows(`select id from public.push_subs where endpoint = 'https://push.example/w'`))[0].id;
const claim = async (list) => (await rows(`select * from public.alert_push_claim($1::jsonb)`, [JSON.stringify(list)])).map((x) => `${x.gkey}|${x.again}`);
const C = (rank, late, world, body = 'b') => ({ sub_id: u, gkey: 'JL62@2026-11-15@NRT', svc_date: '2026-11-15', rank, late, official: false, body, world });
r = await claim([C(0, null, 'arr:LAX:ground_stop', '止まり具合だけ')]);
check('止まり具合だけの通知（rank 0）を記録して送る', r.length === 1 && r[0].endsWith('|false'), r);
r = await claim([C(0, null, 'arr:LAX:ground_stop')]);
check('同じ止まり具合は二度送らない', r.length === 0, r);
r = await claim([C(1, 20, 'arr:LAX:ground_stop')]);
check('そのあと遅れが出たら送る（上書き）', r.length === 1 && r[0].endsWith('|true'), r);
r = await claim([C(0, null, 'arr:LAX:closure')]);
check('遅れの通知のあと、止まり具合だけの通知では上書きしない', r.length === 0, r);
r = await claim([C(1, 25, 'arr:LAX:closure')]);
check('遅れの通知に足した止まり具合が変われば送り直す', r.length === 1, r);
r = await claim([C(1, 30, null)]);
check('止まり具合が出なくなっただけでは送らない', r.length === 0, r);
r = await claim([C(1, 55, null)]);
check('今までの決まり（30分ふえたら送る）はそのまま', r.length === 1, r);
const log = (await rows(`select rank, late, world, n from public.alert_push_log where sub_id = ${u}`))[0];
check('記録：重さ・遅れ・止まり具合の印・回数', log.rank === 1 && log.late === 55 && log.world === 'arr:LAX:closure' && log.n === 4, log);

// RLS と権限
let denied = 0;
for (const role of ['anon', 'authenticated']) {
  await db.exec(`set role ${role}`);
  for (const sql of [`insert into public.world_airport_status (iata, kind, feed_at) values ('LAX', 'gdp', now())`, `update public.world_airport_status set reason = 'x'`,
    `delete from public.world_airport_status`, `select * from public.world_status_put('faa', now(), '[]'::jsonb)`, `select * from public.world_status_rows('[]'::jsonb)`]) {
    try { const q = await db.query(sql); if (/^(update|delete)/.test(sql) && q.affectedRows === 0) denied++; } catch { denied++; }
  }
  const sel = (await rows(`select count(*)::int c from public.world_airport_status`))[0].c;
  if (sel > 0) denied++;   // 読むのは誰でも
  await db.exec('reset role');
}
check('止まり具合の表は誰でも読めるが、書けるのは service_role だけ', denied === 12, denied);
const rls = (await rows(`select relrowsecurity r from pg_class where relname = 'world_airport_status'`))[0].r;
const sr = (await rows(`select has_function_privilege('service_role', 'public.world_status_put(text, timestamptz, jsonb)', 'execute') a,
  has_function_privilege('anon', 'public.world_flight_counts(date)', 'execute') b, has_function_privilege('anon', 'public.world_status_now(text[])', 'execute') c`))[0];
check('RLS は有効・service_role が取り込み・anon は数える関数と今の止まり具合を使える', rls && sr.a && sr.b && sr.c, { rls, sr });
const mig = fs.readFileSync(dir + files.find((f) => f.endsWith('_world_ops.sql')), 'utf8');
check('移行の先頭に lock_timeout・取り込みと掃除の仕事に statement_timeout・一時の表を使わない',
  /^set lock_timeout/m.test(mig) && /'world-status'[\s\S]*statement_timeout = '10s'/.test(mig) && /'world-status-cleanup'[\s\S]*statement_timeout = '30s'/.test(mig) && !/temp table/i.test(mig));
if (bad) process.exit(1);
