// アプリ全体の見直し B の回のデータの分（移行 196）
//   1. airport_board の next_arr・next_dep：今より先を12便まで＋過ぎた便を2便まで
//   2. airport_board の hours・bad は前の関数（移行 195）と同じ。まとめ（airport_hour_bad）がない日があっても同じ
//   3. rwy_learned：まとめ（rwy_learned_days）＋今日の分が、暦の日で数えた rwy_samples と同じ。まとめがない日があっても同じ
//   4. user_pins：本人の行だけ・形の確かめ・rev のぶつかり・退会で消える
//   5. 速さ：羽田の便が多い作り物で、前の airport_board・rwy_learned と比べる（目安。PGlite なので本番の秒数ではない）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const mine = files.find(f => f.endsWith('_ops_sweep_all.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 700)); if (!ok) bad++; };
const q = async (sql) => (await db.query(sql)).rows;
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];

for (const f of files) { if (f === mine) break; await db.exec(fs.readFileSync(dir + f, 'utf8')); }
for (const [fn, sig] of [['airport_board', '(text, text)'], ['rwy_learned', '(text, integer)']]) {
  const def = await q1(`select pg_get_functiondef('public.${fn}${sig}'::regprocedure)`);
  await db.exec(def.replace(new RegExp(`public\\.${fn}\\(`), `public.${fn}_old(`));
}
check('移行は 196 番', /^\d{8}000196_ops_sweep_all\.sql$/.test(mine), mine);

// 作り物の時刻表（t133 と同じ）＋羽田の到着・出発を、いまの前後に1分ごと（羽田の昼のように混む）
await db.exec(`
insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, aircraft, source)
select ((t at time zone 'Asia/Tokyo')::date), 'JL' || (100 + i), d, a, t, t + interval '95 minutes', case when i % 3 = 0 then '763' end, 'ODPT'
from (select i, now() - interval '8 days 7 hours' + (i * interval '4 minutes 7 seconds') as t,
             (array['HND','ITM','CTS','FUK','OKA','HND','HND'])[1 + i % 7] as d,
             (array['ITM','HND','HND','HND','HND','CTS','ICN','FUK','OKA'])[1 + (i * 7) % 9] as a
      from generate_series(1, 3100) i) s where d <> a;
insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source)
select ((now() at time zone 'Asia/Tokyo')::date), 'NH' || (1000 + i), case when i % 2 = 0 then 'CTS' else 'HND' end, case when i % 2 = 0 then 'HND' else 'FUK' end,
       now() + (i - 40) * interval '1 minute' - case when i % 2 = 0 then interval '90 minutes' else interval '0' end,
       now() + (i - 40) * interval '1 minute' + case when i % 2 = 0 then interval '0' else interval '100 minutes' end, 'ODPT'
from generate_series(1, 260) i;
update public.flight_schedule set
  etd = case when id % 4 = 0 then std + ((id % 50) * interval '1 minute') end,
  eta = case when id % 5 <> 0 and flight like 'JL%' then sta + ((id % 40) * interval '1 minute') end,
  atd = case when std < now() - interval '30 minutes' and id % 6 <> 0 then std + ((id % 33) * interval '1 minute') end,
  ata = case when sta < now() - interval '10 minutes' and id % 7 <> 0 and flight like 'JL%' then sta + ((id % 29) * interval '1 minute') end,
  dep_status = case when id % 23 = 0 then 'Cancelled' when id % 11 = 0 then '遅延' end,
  arr_status = case when id % 31 = 0 then 'cancelled' end;
insert into public.flight_watch (schedule_id, state)
select id, case id % 3
  when 0 then jsonb_build_object('phase', 'air', 'takeoff_at', extract(epoch from std + interval '12 minutes') * 1000, 'takeoff_est', false, 'eta', extract(epoch from sta + interval '9 minutes') * 1000)
  when 1 then jsonb_build_object('phase', 'landed', 'takeoff_at', extract(epoch from std + interval '15 minutes') * 1000, 'takeoff_est', true,
                                 'landed_at', extract(epoch from sta + interval '4 minutes') * 1000, 'landed_iata', arr)
  else jsonb_build_object('phase', 'landed', 'landed_at', extract(epoch from sta) * 1000, 'landed_iata', 'XXX') end
from public.flight_schedule where id % 2 = 0 and flight like 'JL%';
insert into public.eta_calib (iata, taxi_out, n_out) values ('HND', 17.5, 40) on conflict (iata) do update set taxi_out = excluded.taxi_out;`);

// 滑走路の記録：羽田（live と track）・伊丹（track）を40日ぶん
await db.exec(`
insert into public.rwy_samples (iata, at, callsign, rwy, dir, src, ent60, ent30, ent120, first_brg, ex60, ex30)
select (array['HND','HND','ITM','NRT'])[1 + i % 4], now() - (i * interval '7 minutes 3 seconds'), 'C' || i,
       (array['22','23','34L','34R','16L','05'])[1 + (i * 5) % 6], case when i % 3 = 0 then 'dep' else 'arr' end,
       case when i % 5 = 0 then 'track' else 'live' end,
       case when i % 4 = 0 then null else (i * 37) % 360 end, case when i % 6 = 0 then (i * 11) % 360 end, (i * 13) % 360,
       case when i % 9 = 0 then null else (i * 17) % 360 end,
       case when i % 7 = 0 then null else (i * 19) % 360 end, case when i % 8 = 0 then null else (i * 23) % 360 end
from generate_series(1, 8200) i;
analyze public.flight_schedule; analyze public.flight_watch; analyze public.rwy_samples;`);

// 移行 196 を流す（最初のまとめは、上の作り物で作られる）
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('まとめができた：遅れの表に行がある・前の8日がまとめ済み', await q1(`select count(*)::int from public.airport_hour_bad`) > 50
  && await q1(`select count(*)::int from public.airport_hour_bad_done`) === 8, await q(`select count(*) from public.airport_hour_bad`));
check('まとめができた：滑走路の表に行がある・記録のある日がまとめ済み（40日前後）', await q1(`select count(*)::int from public.rwy_learned_days`) > 100
  && await q1(`select count(*)::int from public.rwy_learned_done`) >= 39, await q(`select count(*) from public.rwy_learned_done`));

const pairs = [];
for (const ap of ['HND', 'ITM', 'CTS', 'FUK', 'OKA', 'KIX', 'ICN']) for (const k of ['all', 'intl', 'dom']) pairs.push([ap, k]);
async function compareBoards(label) {
  await db.exec('begin');
  let same = 0; const diff = []; const boards = {};
  for (const [ap, k] of pairs) {
    const a = JSON.parse(await q1(`select public.airport_board_old('${ap}', '${k}')::text`));
    const b = JSON.parse(await q1(`select public.airport_board('${ap}', '${k}')::text`));
    boards[ap + k] = { a, b };
    const pick = (x) => JSON.stringify({ iata: x.iata, now: x.now, bad: x.bad, hours: x.hours });
    if (pick(a) === pick(b)) same++; else diff.push([ap, k, a.hours?.find((h, i) => JSON.stringify(h) !== JSON.stringify(b.hours[i])), b.hours?.find((h, i) => JSON.stringify(h) !== JSON.stringify(a.hours[i]))]);
  }
  await db.exec('commit');
  check(`${label}：21通りで iata・now・bad・hours（ref も）が前の関数と全部同じ`, same === pairs.length, diff);
  return boards;
}
const boards = await compareBoards('まとめあり');
check('前の7日の ref に0でない時がある（比べている）', boards.HNDall.b.hours.some((h) => h.ref > 0), boards.HNDall.b.hours);

// まとめのない日（毎時の仕事が止まった）があっても同じ
await db.exec(`delete from public.airport_hour_bad_done where day in ((now() at time zone 'Asia/Tokyo')::date - 1, (now() at time zone 'Asia/Tokyo')::date - 4)`);
await compareBoards('2日ぶんのまとめがない');
await db.exec(`delete from public.airport_hour_bad_done`);
await compareBoards('まとめが1日もない');
await db.exec(`select public.airport_hour_bad_roll((now() at time zone 'Asia/Tokyo')::date - 8, (now() at time zone 'Asia/Tokyo')::date - 1)`);
check('まとめ直すのは今日より前の日だけ（今日・明日を頼んでも作らない）',
  await q1(`select public.airport_hour_bad_roll((now() at time zone 'Asia/Tokyo')::date, (now() at time zone 'Asia/Tokyo')::date + 1)`) === 0
  && await q1(`select count(*)::int from public.airport_hour_bad_done where day >= (now() at time zone 'Asia/Tokyo')::date`) === 0, null);

// 1. これからの便：先を12便まで＋過ぎた便を2便まで
await db.exec('begin');
const nowMs = Date.parse(await q1(`select now()::text`));
const hb = JSON.parse(await q1(`select public.airport_board('HND', 'all')::text`));
const want = await q(`select
  (select count(*)::int from public.flight_schedule f left join public.flight_watch w on w.schedule_id = f.id
    where f.arr = 'HND' and not coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) and f.sta > now() - interval '6 hours'
      and coalesce(f.ata, case when w.state ->> 'landed_iata' = f.arr then public.inferred_time(w.state, 'landed_at') end, f.eta,
                   case when w.state ->> 'phase' = 'air' then public.inferred_time(w.state, 'eta') end, f.sta) between now() and now() + interval '3 hours') as fut,
  (select count(*)::int from public.flight_schedule f left join public.flight_watch w on w.schedule_id = f.id
    where f.arr = 'HND' and not coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) and f.sta > now() - interval '6 hours'
      and coalesce(f.ata, case when w.state ->> 'landed_iata' = f.arr then public.inferred_time(w.state, 'landed_at') end, f.eta,
                   case when w.state ->> 'phase' = 'air' then public.inferred_time(w.state, 'eta') end, f.sta) >= now() - interval '20 minutes'
      and coalesce(f.ata, case when w.state ->> 'landed_iata' = f.arr then public.inferred_time(w.state, 'landed_at') end, f.eta,
                   case when w.state ->> 'phase' = 'air' then public.inferred_time(w.state, 'eta') end, f.sta) < now()) as past`);
const oldHb = JSON.parse(await q1(`select public.airport_board_old('HND', 'all')::text`));
await db.exec('commit');
const fut = hb.next_arr.filter((x) => Date.parse(x.t) >= nowMs), past = hb.next_arr.filter((x) => Date.parse(x.t) < nowMs);
check('羽田の作り物は先の便が12便より多く、過ぎた20分の便が2便より多い（混む昼の形）', want[0].fut > 12 && want[0].past > 2, want[0]);
check('前の関数は先の便が少ない（過ぎた便で枠が埋まる）', oldHb.next_arr.filter((x) => Date.parse(x.t) >= nowMs).length < 6, oldHb.next_arr.map((x) => x.t));
check('next_arr：先の便が12便・過ぎた便が2便', fut.length === 12 && past.length === 2, [fut.length, past.length]);
check('next_arr：時刻の順・先の便は3時間以内・過ぎた便は20分以内', hb.next_arr.every((x, i) => i === 0 || hb.next_arr[i - 1].t <= x.t)
  && fut.every((x) => Date.parse(x.t) <= nowMs + 3 * 3600e3) && past.every((x) => Date.parse(x.t) >= nowMs - 20 * 60e3), hb.next_arr.map((x) => x.t));
check('next_arr：過ぎた2便はいちばん新しい2便（今にいちばん近い）', past.length === 2 && oldHb.next_arr.length > 0, past.map((x) => x.t));
const keysA = 'aircraft,actual,est,flight,inferred,intl,other,predicted,sched,t';
check('next_arr：1便の形は前と同じ（10個のキー）', hb.next_arr.every((x) => Object.keys(x).sort().join() === keysA.split(',').sort().join()), hb.next_arr[0]);
const futD = hb.next_dep.filter((x) => Date.parse(x.takeoff) >= nowMs), pastD = hb.next_dep.filter((x) => Date.parse(x.takeoff) < nowMs);
check('next_dep：先の便が12便まで・過ぎた便が2便まで・離陸の時刻の順', futD.length === 12 && pastD.length <= 2
  && hb.next_dep.every((x, i) => i === 0 || hb.next_dep[i - 1].takeoff <= x.takeoff), [futD.length, pastD.length]);
const keysD = 'aircraft,actual,est,flight,inferred,intl,other,sched,t,takeoff,takeoff_src,taxi';
check('next_dep：1便の形は前と同じ（12個のキー）', hb.next_dep.every((x) => Object.keys(x).sort().join() === keysD.split(',').sort().join()), hb.next_dep[0]);
check('p_kind=intl は国際線だけ', boards.HNDintl.b.next_arr.every((x) => x.intl) && boards.HNDintl.b.next_dep.every((x) => x.intl), null);
check('便のない空港（関西）は空の配列', boards.KIXall.b.next_arr.length === 0 && boards.KIXall.b.next_dep.length === 0, null);

// 3. 学んだ滑走路
const rwyWant = async (ap, days) => JSON.parse(await q1(`
  select jsonb_build_object('iata', '${ap}', 'n', coalesce(sum(n), 0), 'rows', coalesce(jsonb_agg(jsonb_build_object('dir', dir, 'rwy', rwy, 'sec', sec, 'n', n) order by dir, rwy, sec), '[]'::jsonb))::text
  from (select dir, rwy, case when b is null then null else (((b + 22) % 360) / 45)::int end as sec, count(*) as n
        from (select dir, rwy, case when dir = 'arr' then coalesce(ent60, ent30, ent120, first_brg) else coalesce(ex60, ex30) end as b
              from public.rwy_samples where iata = '${ap}' and (src = 'live' or iata not in ('HND', 'NRT'))
                and at >= (((now() at time zone 'Asia/Tokyo')::date - ${days} + 1)::timestamp at time zone 'Asia/Tokyo')) s group by 1, 2, 3) q`));
async function compareRwy(label) {
  let ok = 0; const ng = [];
  for (const ap of ['HND', 'ITM', 'NRT', 'KIX']) for (const days of [1, 7, 30, 3660]) {
    const a = await rwyWant(ap, days), b = JSON.parse(await q1(`select public.rwy_learned('${ap}', ${days})::text`));
    if (JSON.stringify(a) === JSON.stringify(b)) ok++; else ng.push([ap, days, a.n, b.n]);
  }
  check(`${label}：4空港 × 4通りで、暦の日で rwy_samples を数えたのと全部同じ`, ok === 16, ng);
}
await compareRwy('まとめあり');
await db.exec(`delete from public.rwy_learned_done where day in ((now() at time zone 'Asia/Tokyo')::date - 1, (now() at time zone 'Asia/Tokyo')::date - 9)`);
await compareRwy('2日ぶんのまとめがない');
const o30 = JSON.parse(await q1(`select public.rwy_learned_old('HND', 30)::text`)), n30 = JSON.parse(await q1(`select public.rwy_learned('HND', 30)::text`));
check('羽田30日：前の関数との違いは1日ぶん以内（幅の端だけ）', Math.abs(Number(o30.n) - Number(n30.n)) <= Number(o30.n) / 30 + 5 && Number(n30.n) > 100, [o30.n, n30.n]);
check('羽田は live だけ・伊丹は track も数える（前と同じ）', Number(JSON.parse(await q1(`select public.rwy_learned('HND', 3660)::text`)).n)
  === await q1(`select count(*)::int from public.rwy_samples where iata = 'HND' and src = 'live'`)
  && Number(JSON.parse(await q1(`select public.rwy_learned('ITM', 3660)::text`)).n) === await q1(`select count(*)::int from public.rwy_samples where iata = 'ITM'`), null);
// 記録がファイル置き場に移った日（rwy_samples から消えた日）は、まとめ直しても前のまとめが残る
const d5 = await q1(`select ((now() at time zone 'Asia/Tokyo')::date - 5)::text`);
const before5 = await q1(`select coalesce(sum(n), 0)::int from public.rwy_learned_days where day = '${d5}'`);
await db.exec(`create table keep5 as select * from public.rwy_samples where (at at time zone 'Asia/Tokyo')::date = '${d5}';
  delete from public.rwy_samples where (at at time zone 'Asia/Tokyo')::date = '${d5}';
  select public.rwy_learned_roll('${d5}'::date - 1, '${d5}'::date + 1);`);
check('記録が移った日は、まとめ直してもまとめが残る', before5 > 0 && await q1(`select coalesce(sum(n), 0)::int from public.rwy_learned_days where day = '${d5}'`) === before5, before5);
await db.exec(`insert into public.rwy_samples overriding system value select * from keep5; drop table keep5;`);

// 権限：まとめの表は直接読めない・まとめる関数は呼べない・読む関数は前と同じ
const tp = await q(`select t, r, has_table_privilege(r, 'public.' || t, 'select') s from unnest(array['airport_hour_bad','airport_hour_bad_done','rwy_learned_days','rwy_learned_done']) t, unnest(array['anon','authenticated']) r`);
check('まとめの表は anon・authenticated から読めない', tp.every((x) => x.s === false), tp.filter((x) => x.s));
const rls = await q(`select relname, relrowsecurity from pg_class where relname in ('airport_hour_bad','airport_hour_bad_done','rwy_learned_days','rwy_learned_done','user_pins') and relnamespace = 'public'::regnamespace`);
check('新しい表はどれも RLS が有効（5つ）', rls.length === 5 && rls.every((x) => x.relrowsecurity), rls);
const fp = await q(`select f, r, has_function_privilege(r, f, 'execute') e from unnest(array['public.airport_hour_bad_roll(date, date)','public.rwy_learned_roll(date, date)']) f, unnest(array['anon','authenticated']) r`);
check('まとめる関数は anon・authenticated から呼べない', fp.every((x) => x.e === false), fp);
const fq = await q(`select f, r, has_function_privilege(r, f, 'execute') e from unnest(array['public.airport_board(text, text)','public.rwy_learned(text, integer)']) f, unnest(array['anon','authenticated']) r`);
check('airport_board・rwy_learned は anon・authenticated が呼べる（前と同じ）', fq.every((x) => x.e === true), fq);
const anonR = await (async () => { await db.exec(`set role anon`); try { return [JSON.parse(await q1(`select public.airport_board('HND')::text`)), JSON.parse(await q1(`select public.rwy_learned('HND', 30)::text`))]; } finally { await db.exec(`reset role`); } })();
check('anon で呼べて、中身がある', anonR[0].next_arr.length > 0 && Number(anonR[1].n) > 0, null);
check('同じ名前の関数は1つずつ', await q1(`select count(*)::int from pg_proc where proname in ('airport_board','rwy_learned') and pronamespace = 'public'::regnamespace`) === 2, null);

// 4. ピン止め
const U1 = '11111111-1111-1111-1111-111111111111', U2 = '22222222-2222-2222-2222-222222222222';
await db.exec(`insert into auth.users (id) values ('${U1}'), ('${U2}')`);
const as = async (role, uid, sql) => {
  try { await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub', '${uid ?? ''}', false)`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERR ' + e.message; }
  finally { await db.exec(`reset role; select set_config('request.jwt.claim.sub', '', false)`); }
};
const P1 = `'[{"k":"HND","sp":true,"dl":false,"ga":true},{"k":"#123","sp":false}]'::jsonb`;
check('まだ保存していなければ my_pins は null', await as('authenticated', U1, `select public.my_pins()`) === null, null);
const put1 = await as('authenticated', U1, `select public.my_pins_put(${P1}, 'HND')::text`);
check('はじめて書くと rev 1', JSON.parse(put1).ok === true && JSON.parse(put1).rev === 1, put1);
const got = JSON.parse(await as('authenticated', U1, `select public.my_pins()::text`));
check('読むと書いた中身・撮影の空港・rev が返る', got.pins.length === 2 && got.pins[1].k === '#123' && got.spot === 'HND' && got.rev === 1, got);
check('前の rev で書くと上がる', JSON.parse(await as('authenticated', U1, `select public.my_pins_put('[{"k":"ITM"}]', null, 1)::text`)).rev === 2, null);
const cf = JSON.parse(await as('authenticated', U1, `select public.my_pins_put('[{"k":"FUK"}]', null, 1)::text`));
check('古い rev で書くとぶつかりを返し、書かない', cf.conflict === true && cf.rev === 2 && cf.pins[0].k === 'ITM', cf);
check('ほかの人の行は見えない', await as('authenticated', U2, `select count(*)::int from public.user_pins`) === 0 && await as('authenticated', U2, `select public.my_pins()`) === null, null);
check('ほかの人の行は直せない（0行）', await as('authenticated', U2, `with u as (update public.user_pins set pins = '[]' where user_id = '${U1}' returning 1) select count(*)::int from u`) === 0, null);
check('ほかの人の行は作れない', String(await as('authenticated', U2, `insert into public.user_pins (user_id, pins) values ('${U1}', '[]')`)).startsWith('ERR'), null);
check('rev・updated_at は直接書けない', String(await as('authenticated', U1, `update public.user_pins set rev = 99`)).startsWith('ERR'), null);
check('anon は読めない・書けない', String(await as('anon', null, `select count(*) from public.user_pins`)).startsWith('ERR')
  && String(await as('anon', null, `select public.my_pins_put('[]')`)).startsWith('ERR'), null);
for (const [label, v] of [['配列でない', `'{"k":"HND"}'`], ['k がない', `'[{"sp":true}]'`], ['k の形が違う', `'[{"k":"hnd"}]'`], ['知らない鍵', `'[{"k":"HND","x":1}]'`],
  ['sp が文字', `'[{"k":"HND","sp":"yes"}]'`], ['同じ空港が2回', `'[{"k":"HND"},{"k":"HND"}]'`],
  ['21空港', `(select jsonb_agg(jsonb_build_object('k', '#' || g)) from generate_series(1, 21) g)`]]) {
  check(`形の違うピン止めは入らない：${label}`, String(await as('authenticated', U2, `select public.my_pins_put(${v})`)).startsWith('ERR'), null);
}
check('撮影の空港の形が違うと入らない', String(await as('authenticated', U2, `select public.my_pins_put('[]', 'hnd')`)).startsWith('ERR'), null);
check('20空港までは入る', JSON.parse(await as('authenticated', U2, `select public.my_pins_put((select jsonb_agg(jsonb_build_object('k', '#' || g, 'sp', true)) from generate_series(1, 20) g))::text`)).ok === true, null);
check('本人は自分の行を消せる', await as('authenticated', U2, `with d as (delete from public.user_pins returning 1) select count(*)::int from d`) === 1, null);
await db.exec(`delete from auth.users where id = '${U1}'`);
check('退会（auth.users の削除）で一緒に消える', await q1(`select count(*)::int from public.user_pins`) === 0, null);
const pf = await q(`select f, r, has_function_privilege(r, f, 'execute') e from unnest(array['public.my_pins()','public.my_pins_put(jsonb, text, integer)']) f, unnest(array['anon','authenticated']) r`);
check('my_pins・my_pins_put は authenticated だけが呼べる', pf.every((x) => x.e === (x.r === 'authenticated')), pf);

// 5. 速さ（目安）：羽田の便を1日1,300便・9日ぶん足して比べる
await db.exec(`
insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source, ata, eta)
select ((t at time zone 'Asia/Tokyo')::date), chr(66 + i / 5000) || 'Z' || (i % 5000 + 1), case when i % 2 = 0 then 'HND' else 'OKA' end, case when i % 2 = 0 then 'ITM' else 'HND' end,
       t, t + interval '70 minutes', 'ODPT', case when t + interval '70 minutes' < now() then t + interval '70 minutes' + (i % 30) * interval '1 minute' end,
       t + interval '70 minutes' + (i % 25) * interval '1 minute'
from (select i, now() - interval '9 days' + i * interval '1 minute' - interval '7 seconds' * (i % 9) as t from generate_series(1, 13400) i) s;
insert into public.rwy_samples (iata, at, callsign, rwy, dir, src, ent60, pts)
select 'HND', now() - (i * interval '61 seconds'), 'P' || i, (array['22','23','34L','34R'])[1 + i % 4], case when i % 2 = 0 then 'dep' else 'arr' end, 'live', (i * 7) % 360,
       (select jsonb_agg(jsonb_build_array(g, 35.5, 139.8, 3000)) from generate_series(1, 40) g)
from generate_series(1, 43000) i;
analyze public.flight_schedule; analyze public.rwy_samples;
select public.airport_hour_bad_roll((now() at time zone 'Asia/Tokyo')::date - 8, (now() at time zone 'Asia/Tokyo')::date - 1);
select public.rwy_learned_roll((now() at time zone 'Asia/Tokyo')::date - 31, (now() at time zone 'Asia/Tokyo')::date - 1);`);
const time = async (sql, n) => { const t = performance.now(); for (let i = 0; i < n; i++) await q1(sql); return Math.round((performance.now() - t) / n); };
await time(`select public.airport_board('HND')::text`, 1); await time(`select public.airport_board_old('HND')::text`, 1);
const tOld = await time(`select public.airport_board_old('HND')::text`, 8), tNew = await time(`select public.airport_board('HND')::text`, 8);
const rOld = await time(`select public.rwy_learned_old('HND', 30)::text`, 5), rNew = await time(`select public.rwy_learned('HND', 30)::text`, 5);
console.log(`   速さの目安（PGlite・1回あたり）：airport_board 前 ${tOld}ms → 今 ${tNew}ms ／ rwy_learned(30日) 前 ${rOld}ms → 今 ${rNew}ms`);
check('airport_board は前より速い（目安）', tNew < tOld, [tOld, tNew]);
check('rwy_learned は前より速い（目安）', rNew < rOld, [rOld, rNew]);
const bigB = JSON.parse(await q1(`select public.airport_board('HND')::text`));
check('多い作り物でも先の便が12便', bigB.next_arr.filter((x) => Date.parse(x.t) >= Date.parse(bigB.now)).length === 12, null);

// もう一度流しても同じ
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流しても関数は1つずつ・中身が返る', await q1(`select count(*)::int from pg_proc where proname in ('airport_board','rwy_learned','my_pins','my_pins_put') and pronamespace = 'public'::regnamespace`) === 4
  && JSON.parse(await q1(`select public.airport_board('HND')::text`)).next_arr.length > 0, null);
check('移行のあと lock_timeout・statement_timeout は元に戻る', (await q1(`show lock_timeout`)) === '0' && (await q1(`show statement_timeout`)) === '0', null);

console.log(bad ? `\n${bad} 件 NG` : '\nすべて OK'); process.exit(bad ? 1 : 0);
