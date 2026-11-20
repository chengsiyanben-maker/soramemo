// 乗る便の機体（移行 189）：前の便がないとき、前の日の夜に着いて泊まった「この日の最初の便」なら first_of_day: true
//   1. 今日の登録記号が分かり、前の日の最後の便がこの空港に着いていれば first_src 'reg'・overnight を返す
//   2. 今日この便より前に同じ機体の便があれば、泊まりでも true にしない
//   3. 前の60日の記録で「最初の便で、前の日にここに着いた」が3日以上・7割以上なら first_src 'history'。足りなければ false
//   4. 前の便が見つかるときは false で、今までの値（inbound・late）は同じ。形の違う便名は null のまま
//   5. 権限は今までどおり（anon・authenticated は実行だけ）。主キーの日付で引く（全部読みをしない）
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
const T = `(now() at time zone 'Asia/Tokyo')::date`;

// 今日の便：JL0101（羽田→伊丹、3時間後）・JL0103（羽田→伊丹、4時間後）・JL0201（羽田→福岡、5時間後）
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source, aircraft) values
  (${T}, 'JL0101', 'HND', 'ITM', now() + interval '3 hours', now() + interval '4 hours', 'ODPT', '738'),
  (${T}, 'JL0103', 'HND', 'ITM', now() + interval '4 hours', now() + interval '5 hours', 'ODPT', '738'),
  (${T}, 'JL0201', 'HND', 'FUK', now() + interval '5 hours', now() + interval '7 hours', 'ODPT', '738'),
  (${T}, 'JL0099', 'HND', 'KIX', now() + interval '1 hour', now() + interval '2 hours', 'ODPT', '738')`);
const hist = (day, flight, dep, arr, hhStd, reg, cancelled = false) =>
  `(${T} - ${day}, '${flight}', '${dep}', '${arr}', (${T} - ${day})::timestamp + interval '${hhStd} hours' - interval '9 hours',
    (${T} - ${day})::timestamp + interval '${hhStd + 1} hours' - interval '9 hours', ${cancelled}, '${reg}')`;

// 1. 今日 JL0101 の機体は JA101J。前の日の最後の便は伊丹→羽田（夜に羽田に着いた）
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, cancelled, reg) values
  ${hist(1, 'JL0110', 'HND', 'ITM', 15, 'JA101J')}, ${hist(1, 'JL0128', 'ITM', 'HND', 20, 'JA101J')}`);
await db.exec(`insert into public.flight_watch (schedule_id, state) select id, jsonb_build_object('phase', 'gate', 'reg', 'JA101J') from public.flight_schedule where flight = 'JL0101'`);
let r = await as('anon', `select public.inbound_aircraft('JL101', 'HND')`);
check('今日の登録記号と前の日の最後の便から first_of_day（reg）', r?.found && r.inbound === null && r.first_of_day === true && r.first_src === 'reg', r);
check('泊まった便（JL0128 伊丹→羽田）を overnight に返す', r?.overnight?.flight === 'JL0128' && r.overnight.arr === 'HND' && r.overnight.arr_src === 'sched', r);

// 2. 今日 JL0099（1時間後）に同じ機体が先に飛ぶなら、JL0101 は最初の便ではない
await db.exec(`insert into public.flight_watch (schedule_id, state) select id, jsonb_build_object('phase', 'gate', 'reg', 'JA101J') from public.flight_schedule where flight = 'JL0099'`);
r = await as('anon', `select public.inbound_aircraft('JL101', 'HND')`);
check('今日この便より前に同じ機体の便があれば false', r?.first_of_day === false && r.overnight === null, r);
await db.exec(`update public.flight_schedule set dep_status = 'Cancelled' where flight = 'JL0099'`);
r = await as('anon', `select public.inbound_aircraft('JL101', 'HND')`);
check('先の便が欠航なら、もう一度 first_of_day', r?.first_of_day === true && r.first_src === 'reg', r);
// 前の日の最後の便がほかの空港に着いていたら（reg の道では）true にしない
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, cancelled, reg) values ${hist(1, 'JL0131', 'HND', 'ITM', 22, 'JA101J')}`);
r = await as('anon', `select public.inbound_aircraft('JL101', 'HND')`);
check('前の日の最後の便が伊丹に着いていれば false', r?.first_of_day === false, r);

// 3. 記録から：JL0103 は前の60日で4日中3日、機体の最初の便で前の日に羽田に着いていた
const rows = [];
for (const [d, reg] of [[2, 'JA201J'], [3, 'JA202J'], [4, 'JA203J']]) rows.push(hist(d, 'JL0103', 'HND', 'ITM', 7, reg), hist(d + 1, 'JL0190', 'ITM', 'HND', 20, reg));
rows.push(hist(5, 'JL0103', 'HND', 'ITM', 7, 'JA204J'), hist(5, 'JL0102', 'ITM', 'HND', 5, 'JA204J'));   // この日は前に1便あった
rows.push(hist(6, 'JL0103', 'HND', 'ITM', 7, 'JA205J', true));   // 欠航の日は数えない
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, cancelled, reg) values ${rows.join(',')} on conflict do nothing`);
r = await as('anon', `select public.inbound_aircraft('JL103', 'HND')`);
check('記録の 4日中3日（7割以上）で first_of_day（history）', r?.first_of_day === true && r.first_src === 'history' && r.first_stay === 3 && r.first_of === 4 && r.overnight === null, r);
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, cancelled, reg) values
  ${hist(7, 'JL0103', 'HND', 'ITM', 7, 'JA206J')}, ${hist(7, 'JL0104', 'ITM', 'HND', 5, 'JA206J')}`);
r = await as('anon', `select public.inbound_aircraft('JL103', 'HND')`);
check('5日中3日（6割）なら false', r?.first_of_day === false && r.first_stay === 3 && r.first_of === 5, r);
r = await as('anon', `select public.inbound_aircraft('JL201', 'HND')`);
check('記録のない便は false（数は 0）', r?.found && r.first_of_day === false && r.first_of === 0, r);

// 4. 前の便があるときは今までどおり
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source, aircraft) values
  (${T}, 'JL0150', 'ITM', 'HND', now() + interval '1 hour', now() + interval '2 hours', 'ODPT', '738');
  insert into public.rotation_obs (svc_date, reg, prev_flight, next_flight, iata, turn_min) values (${T} - 8, 'JA301J', 'JL0150', 'JL0201', 'HND', 180)`);
r = await as('anon', `select public.inbound_aircraft('JL201', 'HND')`);
check('前の便があれば inbound を返し first_of_day は false', r?.inbound?.flight === 'JL0150' && r.first_of_day === false && Number(r.late) === 0 && r.arr_src === 'sched', r);
r = await as('anon', `select public.inbound_aircraft('bad', 'HND')`);
check('形の違う便名は null', r === null || r === 'ok', r);
r = await as('anon', `select public.inbound_aircraft('JL9', 'HND')`);
check('時刻表にない便は found=false', r?.found === false, r);

// 5. 権限と引き方
r = await as('authenticated', `select public.inbound_aircraft('JL103', 'HND') ->> 'first_src'`);
check('ログインした人も呼べる', r === null || typeof r === 'string', r);
r = await as('anon', `select count(*) from public.flight_history`);
check('anon は flight_history を直接読めない', String(r).startsWith('ERROR'), r);
await db.exec(`set enable_seqscan = off`);
const plan = (await db.query(`explain select 1 from public.flight_history h where h.svc_date = any (array(select (${T} - g)::date from generate_series(1, 60) g)) and h.flight = 'JL0103' and h.dep = 'HND'`)).rows.map((x) => x['QUERY PLAN']).join(' / ');
check('記録は日付の配列で索引を引く（全部読みをしない）', /Index (Only )?Scan using flight_history_(pkey|dep_day)/.test(plan) && /svc_date = ANY/.test(plan) && !/Seq Scan on flight_history/.test(plan), plan);
await db.exec(`reset enable_seqscan`);

if (bad) { console.log(`NG ${bad}件`); process.exit(1); }
console.log('すべて OK');
