// 遅れの通知を1つの便につき1件に（移行 168）：お知らせの書き直し（推定→公式・遅れの変化）・送った記録で二度送らない・
// 30分ふえたら送り直す・画面の一覧は60分以上のまま・急増の見張りも60分以上だけ・RLS（関数だけが読み書き）・退会（購読の削除）で記録も消える
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

await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
  ('2026-11-13','JL503','HND','CTS', now(), now() + interval '90 minutes', 'ODPT（JAL）'),
  ('2026-11-13','NH55','HND','CTS', now() + interval '1 hour', now() + interval '150 minutes', 'ODPT（ANA）')`);
const [{ id: s1 }, { id: s2 }] = await rows(`select id from public.flight_schedule order by id`);
const put = async (list) => (await rows(`select * from public.flight_alerts_put($1::jsonb)`, [JSON.stringify(list)])).map((r) => `${r.schedule_id}|${r.kind}`);
const A = (sid, kind, late, official, message) => ({ schedule_id: sid, kind, flight: 'JL503', dep: 'HND', arr: 'CTS', iata: ['HND', 'CTS'], message, late, official });

let r = await put([A(s1, 'delay_dep', 20, false, '出発が約20分遅れました（推定）')]);
check('新しいお知らせは入り、返る', r.length === 1 && r[0] === `${s1}|delay_dep`, r);
r = await put([A(s1, 'delay_dep', 20, false, '出発が約20分遅れました（推定）')]);
check('同じ中身の繰り返しは何も返さない', r.length === 0, r);
r = await put([A(s1, 'delay_dep', 25, true, '出発が約25分遅れる見込みです（航空会社の運航情報）')]);
let row = (await rows(`select late, official, message, updated_at from public.flight_alerts where schedule_id = ${s1} and kind = 'delay_dep'`))[0];
check('航空会社の運航情報は推定を上書きする', r.length === 1 && row.official === true && row.late === 25 && row.updated_at != null, row);
r = await put([A(s1, 'delay_dep', 80, false, '出発が約80分遅れました（推定）')]);
row = (await rows(`select late, official from public.flight_alerts where schedule_id = ${s1} and kind = 'delay_dep'`))[0];
check('推定は運航情報を上書きしない', r.length === 0 && row.official === true && row.late === 25, row);
r = await put([A(s1, 'delay_dep', 55, true, '出発が約55分遅れる見込みです（航空会社の運航情報）')]);
check('運航情報の遅れが変われば書き直す', r.length === 1, r);
r = await put([A(s1, 'delay_arr', 50, true, '到着が約50分遅れる見込みです（航空会社の運航情報）'), A(s2, 'delay_dep', 70, true, 'NH55 70分')]);
check('別の種類・別の便は別の行', r.length === 2, r);

// 画面の一覧は今までどおり60分以上（と遅れ以外）だけ。返す形も同じ
await db.exec('set role anon');
const list = (await rows(`select public.flight_alerts('HND') a`))[0].a;
await db.exec('reset role');
check('画面の一覧：15〜59分の遅れは出さず、60分以上は出す・鍵は今のまま', list.length === 1 && list[0].flight === 'JL503' && /70分/.test(list[0].message)
  && JSON.stringify(Object.keys(list[0]).sort()) === JSON.stringify(['arr', 'at', 'dep', 'flight', 'iata', 'id', 'kind', 'message']), list);

// 送った記録
await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, airports, flights) values ('https://push.example/a', 'k', 'a', '{}', '{JL503@2026-11-13}'), ('https://push.example/b', 'k', 'a', '{HND}', '{}')`);
const [{ id: u1 }, { id: u2 }] = await rows(`select id from public.push_subs order by id`);
const claim = async (list) => (await rows(`select * from public.alert_push_claim($1::jsonb)`, [JSON.stringify(list)])).map((x) => `${x.sub_id}|${x.gkey}|${x.again}`);
const C = (sub, rank, late, official, body = 'b') => ({ sub_id: sub, gkey: 'JL503@2026-11-13@HND', svc_date: '2026-11-13', rank, late, official, body });
r = await claim([C(u1, 1, 20, false)]);
check('はじめての便は送る（again は false）', r.length === 1 && r[0] === `${u1}|JL503@2026-11-13@HND|false`, r);
r = await claim([C(u1, 1, 20, false)]);
check('同じ遅れの繰り返しは送らない', r.length === 0, r);
r = await claim([C(u1, 1, 49, false)]);
check('29分ふえただけでは送らない', r.length === 0, r);
r = await claim([C(u1, 1, 45, true)]);
check('航空会社の運航情報がはじめて届いたら送る（更新）', r.length === 1 && r[0].endsWith('|true'), r);
r = await claim([C(u1, 1, 60, true)]);
check('運航情報のあと15分ふえただけでは送らない', r.length === 0, r);
r = await claim([C(u1, 1, 75, true)]);
check('送った遅れから30分ふえたら送る（上書き）', r.length === 1, r);
r = await claim([C(u1, 5, null, true, '欠航')]);
check('欠航になったら送る', r.length === 1, r);
r = await claim([C(u1, 1, 200, true)]);
check('欠航のあとに遅れが来ても送らない', r.length === 0, r);
r = await claim([C(u2, 1, 70, true), C(999999, 1, 70, true)]);
check('ほかの購読は別に数える・ない購読は記録しない', r.length === 1 && r[0].startsWith(`${u2}|`), r);
r = await claim([C(u2, 2, 80, true, '門限に間に合わないおそれ')]);
check('門限・0時前後（rank 2）になったら送り直す', r.length === 1 && r[0].endsWith('|true'), r);
r = await claim([C(u2, 2, 100, true)]);
check('rank 2 のまま20分ふえただけでは送らない', r.length === 0, r);
r = await claim([C(u2, 2, 110, true)]);
check('rank 2 のまま30分ふえたら送る', r.length === 1, r);
const n = (await rows(`select n, rank from public.alert_push_log where sub_id = ${u1}`))[0];
check('送った回数と重さを残す', n.n === 4 && n.rank === 5, n);
await db.exec(`delete from public.push_subs where id = ${u1}`);
check('購読を消すと送った記録も消える', (await rows(`select count(*)::int c from public.alert_push_log where sub_id = ${u1}`))[0].c === 0);
// 主要でない空港を選んだ人への欠航（11/14 本人：欠航・ダイバート・引き返しは主要でない空港の人にも届ける。宛先は関数の eligible が選び、記録は同じ決まり）
await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, airports, flights) values ('https://push.example/c', 'k', 'a', '{KMJ}', '{}')`);
const u3 = (await rows(`select id from public.push_subs where endpoint = 'https://push.example/c'`))[0].id;
const K = (rank, body) => ({ sub_id: u3, gkey: 'JL631@2026-11-14@HND', svc_date: '2026-11-14', rank, late: null, official: true, body });
r = await claim([K(4, 'ダイバート')]);
check('主要でない空港の人へのダイバートを送る', r.length === 1 && r[0] === `${u3}|JL631@2026-11-14@HND|false`, r);
r = await claim([K(5, '欠航')]);
check('そのあと欠航になったら送り直す（更新）', r.length === 1 && r[0].endsWith('|true'), r);
r = await claim([K(5, '欠航')]);
check('同じ欠航は二度送らない', r.length === 0, r);

// 急増の見張り：60分以上の遅れと遅れ以外だけを数える
await db.exec(`insert into public.flight_alerts (kind, flight, dep, arr, iata, message, late) select 'delay_dep', 'NH' || g, 'HND', 'OKA', '{HND}', 'x', 20 from generate_series(1, 30) g`);
check('15〜59分の遅れが多くても、急増の見張りは鳴らない', (await rows(`select ops.alert_watchdog() n`))[0].n === 0);
await db.exec(`insert into public.flight_alerts (kind, flight, dep, arr, iata, message, late) select 'delay_dep', 'JL' || g, 'HND', 'OKA', '{HND}', 'x', 90 from generate_series(1, 20) g`);
check('60分以上が20件で鳴る（今までどおり）', (await rows(`select ops.alert_watchdog() n`))[0].n === 1);

// RLS と権限
let denied = 0;
for (const role of ['anon', 'authenticated']) {
  await db.exec(`set role ${role}`);
  for (const sql of [`select 1 from public.alert_push_log`, `select public.alert_push_claim('[]'::jsonb)`, `select public.flight_alerts_put('[]'::jsonb)`]) { try { await db.query(sql); } catch { denied++; } }
  await db.exec('reset role');
}
check('送った記録・書き込みの関数は利用者から使えない', denied === 6, denied);
const rls = (await rows(`select relrowsecurity r from pg_class where relname = 'alert_push_log'`))[0].r;
const sr = (await rows(`select has_function_privilege('service_role', 'public.alert_push_claim(jsonb)', 'execute') a, has_function_privilege('service_role', 'public.flight_alerts_put(jsonb)', 'execute') b`))[0];
check('RLS は有効・service_role だけが関数を使える', rls && sr.a && sr.b, { rls, sr });
const runs = (await rows(`select array_agg(id order by id) ids from public.odpt_status_runs`))[0].ids;
check('乗る便を毎分見る回の行（id 2）がある', JSON.stringify(runs) === '[1,2]', runs);
const mig = fs.readFileSync(dir + files.find((f) => f.endsWith('_alert_merge.sql')), 'utf8');
check('移行の先頭に lock_timeout・掃除の仕事に statement_timeout', /^set lock_timeout/m.test(mig) && /statement_timeout = '30s'/.test(mig));
if (bad) process.exit(1);
