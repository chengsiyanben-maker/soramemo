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
// 毎日の記録：空港のまとめ・機体のつながり・運用の予想
const today = `(now() at time zone 'Asia/Tokyo')::date`;
// 過去3日、JA8980 が JL100(HND→ITM) → JL105(ITM→HND) → JL110(HND→FUK) と飛んだ（1日だけ JL100 → JL107）
for (let d = 1; d <= 3; d++) {
  const nx = d === 2 ? 'JL107' : 'JL105';
  await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, reg, atd, ata, arr_delay, dep_delay) values
    (${today} - ${d}, 'JL100', 'HND', 'ITM', now() - interval '${d} days 6 hours', now() - interval '${d} days 5 hours', 'JA8980', null, now() - interval '${d} days 5 hours' + interval '20 minutes', 20, 0),
    (${today} - ${d}, '${nx}', 'ITM', 'HND', now() - interval '${d} days 4 hours', now() - interval '${d} days 3 hours', 'JA8980', null, null, 0, 0),
    (${today} - ${d}, 'JL110', 'HND', 'FUK', now() - interval '${d} days 2 hours', now() - interval '${d} days', 'JA8980', null, null, 0, 0)`);
  const day = await as('postgres', `select (${today} - ${d})::text`);
  await db.exec(`select public.archive_rotations('${day}'::date)`);
}
let r = await as('postgres', `select count(*)::int from public.rotation_obs where prev_flight = 'JL100'`);
check('機体のつながりを日ごとに残す（作り直しても増えない）', r === 3, r);
const d1 = await as('postgres', `select (${today} - 1)::text`);
await db.exec(`select public.archive_rotations('${d1}'::date)`);
r = await as('postgres', `select count(*)::int from public.rotation_obs`);
check('同じ日を作り直しても重ならない', r === 6, r);
await db.exec(`update public.flight_history set ata_src = 'odpt' where ata is not null`);
r = await as('postgres', `select public.archive_airport_daily('${d1}'::date)`);
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, atd, atd_src, dep_delay) values ('${d1}', 'JL999', 'ITM', 'HND', now() - interval '1 day', now() - interval '23 hours', now() - interval '1 day' + interval '25 minutes', 'adsb', 25)`);
const again = await as('postgres', `select public.archive_airport_daily('${d1}'::date)`);
const itm2 = await as('postgres', `select row_to_json(a) from public.airport_daily a where day = '${d1}' and iata = 'ITM'`);
check('機体の位置からの推定の遅れは、遅れに数えない', itm2 && itm2.dep === 2 && itm2.late === 1, itm2);
const hnd = await as('postgres', `select row_to_json(a) from public.airport_daily a where day = '${d1}' and iata = 'ITM'`);
check('空港のまとめ：到着・出発と15分以上の遅れを数える', hnd && hnd.arr === 1 && hnd.dep >= 1 && hnd.late === 1, hnd);
// 今日：JA8980 が JL100 に乗っているのを見つけた。今日の時刻表に JL105・JL107・JL110 がある
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
  (${today}, 'JL100', 'HND', 'ITM', now() - interval '30 minutes', now() + interval '35 minutes', 'ODPT'),
  (${today}, 'JL105', 'ITM', 'HND', now() + interval '80 minutes', now() + interval '145 minutes', 'ODPT'),
  (${today}, 'JL107', 'ITM', 'HND', now() + interval '100 minutes', now() + interval '165 minutes', 'ODPT'),
  (${today}, 'JL110', 'HND', 'FUK', now() + interval '200 minutes', now() + interval '320 minutes', 'ODPT')`);
await db.exec(`insert into public.flight_watch (schedule_id, state) select id, jsonb_build_object('phase','air','reg','JA8980','cs','JAL100') from public.flight_schedule where flight = 'JL100' and svc_date = ${today}`);
r = await as('anon', `select public.predict_rotation('JA8980')`);
const nx = (r?.next ?? []).map((x) => x.flight);
check('運用の予想：よく続く便をたどる', r?.known?.flight === 'JL100' && nx.join(',') === 'JL105,JL110', r);
check('運用の予想：記録の数と割合を返す', r?.next?.[0]?.of > 0 && Number(r.next[0].share) > 0.5, r?.next?.[0]);
r = await as('anon', `select public.predict_rotation('JA0000')`);
check('今日見つけていない機体は、予想を出さない', r && r.known === null && r.next.length === 0, r);
r = await as('anon', `select count(*) from public.flight_history`);
check('記録の表は利用者から読めない', String(r).startsWith('ERROR'), r);
r = await as('anon', `select public.archive_rotations(current_date)`);
check('記録を作る関数は利用者から呼べない', String(r).startsWith('ERROR'), r);
if (bad) process.exit(1);
