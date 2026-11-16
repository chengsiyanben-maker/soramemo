// 定期の手入れ 11/10：毎晩・3時間ごとの記録の処理を軽く（結果は前の作りと同じか）
//   1. archive_airport_daily：運用の記録をその日の範囲で引く  2. airport_tracks_put：一時の表を使わない  3. rwy_learn_points：json で組み立てる
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

// ---- 1. 空港ごとの1日のまとめ：日本時間の日付の境目で、前の作りと同じ行を数える
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, cancelled) values
  ('2026-11-08', 'JL1', 'HND', 'ITM', '2026-11-08 00:00+00', '2026-11-08 01:00+00', false),
  ('2026-11-08', 'JL2', 'ITM', 'HND', '2026-11-08 02:00+00', '2026-11-08 03:00+00', false);
  insert into public.ops_log (at, iata, wspd, est_mode, obs_mode) values
  ('2026-11-07 14:59:59+00', 'HND', 30, 'N', null),   -- 日本時間 11/7 23:59:59（入らない）
  ('2026-11-07 15:00:00+00', 'HND', 12, 'S', null),   -- 日本時間 11/8 0:00（入る）
  ('2026-11-08 03:00:00+00', 'HND', 8, 'S', 'N'),
  ('2026-11-08 14:59:59+00', 'ITM', 20, 'N', null),   -- 日本時間 11/8 23:59:59（入る）
  ('2026-11-08 15:00:00+00', 'ITM', 25, 'S', null);   -- 日本時間 11/9 0:00（入らない）`);
const want = (await db.query(`select iata, jsonb_object_agg(mode, cnt * 5) as modes, max(wmax) as max_wind from (
  select iata, coalesce(obs_mode, est_mode) as mode, count(*) as cnt, max(wspd) as wmax
  from public.ops_log where (at at time zone 'Asia/Tokyo')::date = '2026-11-08' group by 1, 2) x group by iata order by iata`)).rows;
const n1 = (await db.query(`select public.archive_airport_daily('2026-11-08') as n`)).rows[0].n;
const got = (await db.query(`select iata, modes, max_wind from public.airport_daily where day = '2026-11-08' order by iata`)).rows;
check('まとめは前の作り（日付に直して比べる）と同じ運用・風', n1 === 2 && JSON.stringify(got) === JSON.stringify(want)
  && got[0].modes.S === 5 && got[0].modes.N === 5 && got[0].max_wind === 12 && got[1].max_wind === 20, { got, want });
const plan = (await db.query(`explain select 1 from public.ops_log where at >= ('2026-11-08'::date::timestamp at time zone 'Asia/Tokyo') and at < (('2026-11-08'::date + 1)::timestamp at time zone 'Asia/Tokyo')`)).rows.map((r) => r['QUERY PLAN']).join(' ');
await db.exec(`set enable_seqscan = off`);
const plan2 = (await db.query(`explain select 1 from public.ops_log where at >= ('2026-11-08'::date::timestamp at time zone 'Asia/Tokyo') and at < (('2026-11-08'::date + 1)::timestamp at time zone 'Asia/Tokyo')`)).rows.map((r) => r['QUERY PLAN']).join(' ');
await db.exec(`reset enable_seqscan`);
check('その日の範囲は索引 ops_log_at で引ける', /ops_log_at/.test(plan2), { plan, plan2 });

// ---- 2. 空の道すじの線を入れる：前の作り（一時の表）と同じ結果
await db.exec(`create function public.atp_old(p_rows jsonb) returns int language plpgsql as $f$
declare n int;
begin
  create temp table if not exists _atp (iata text, day date, callsign text, at timestamptz, dep_here smallint, pts text) on commit drop;
  truncate _atp;
  insert into _atp select x.iata, x.day, x.callsign, x.at, x.dep_here, x.pts
    from jsonb_to_recordset(p_rows) as x(iata text, day date, callsign text, at timestamptz, dep_here smallint, pts text)
    where x.iata ~ '^[A-Z]{3}$' and x.callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$' and x.at is not null and x.dep_here in (0, 1) and length(x.pts) <= 4000;
  delete from public.airport_tracks_all a using _atp r
    where a.iata = r.iata and a.callsign = r.callsign and a.day = r.day
      and a.at between r.at - interval '90 minutes' and r.at + interval '90 minutes'
      and not exists (select 1 from _atp q where q.iata = a.iata and q.callsign = a.callsign and q.day = a.day and q.at = a.at and q.dep_here = a.dep_here);
  insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) select iata, day, callsign, at, dep_here, pts from _atp
    on conflict (iata, day, callsign, at) do update set dep_here = excluded.dep_here, pts = excluded.pts;
  get diagnostics n = row_count;
  return n;
end $f$;`);
const seed = `delete from public.airport_tracks_all; insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values
  ('NRT', '2026-10-24', 'UAL32', '2026-10-24 03:06+00', 0, 'old'),     -- 食い違う古い線（消える）
  ('NRT', '2026-10-24', 'UAL32', '2026-10-24 09:30+00', 0, 'later'),   -- 90分より離れている（残る）
  ('NRT', '2026-10-24', 'UAL32', '2026-10-24 04:30+00', 0, 'edge'),    -- ちょうど90分（消える）
  ('NRT', '2026-10-24', 'JAL5', '2026-10-24 03:10+00', 0, 'jal'),      -- 別の機体（残る）
  ('NRT', '2026-10-25', 'UAL32', '2026-10-25 03:06+00', 0, 'nextday'), -- 別の日（残る）
  ('KMJ', '2026-10-24', 'SNJ1', '2026-10-24 01:00+00', 0, 'flip'),     -- 同じ時刻で出発・到着だけ違う（入れ替わる）
  ('KMJ', '2026-10-24', 'SNJ1', '2026-10-24 01:30+00', 0, 'mid');      -- 入れる2本の間（消える）`;
const input = [
  { iata: 'NRT', day: '2026-10-24', callsign: 'UAL32', at: '2026-10-24T03:00:00Z', dep_here: 1, pts: 'new' },
  { iata: 'KMJ', day: '2026-10-24', callsign: 'SNJ1', at: '2026-10-24T01:00:00Z', dep_here: 1, pts: 'd' },
  { iata: 'KMJ', day: '2026-10-24', callsign: 'SNJ1', at: '2026-10-24T01:50:00Z', dep_here: 0, pts: 'a' },
  { iata: 'nrt', day: '2026-10-24', callsign: 'UAL32', at: '2026-10-24T03:00:00Z', dep_here: 1, pts: 'bad' },   // 形が違う（入れない）
  { iata: 'NRT', day: '2026-10-24', callsign: 'ANA1', at: '2026-10-24T03:00:00Z', dep_here: 2, pts: 'bad' },
  { iata: 'NRT', day: '2026-10-24', callsign: 'ANA2', at: '2026-10-24T05:00:00Z', dep_here: 0, pts: 'x'.repeat(4001) },
];
const state = async () => (await db.query(`select iata, day::text, callsign, to_char(at at time zone 'UTC', 'MM-DD HH24:MI') as at, dep_here, pts from public.airport_tracks_all order by 1, 2, 3, 4`)).rows;
await db.exec(seed); const nOld = (await db.query(`select public.atp_old($1::jsonb) as n`, [JSON.stringify(input)])).rows[0].n; const sOld = await state();
await db.exec(seed); const nNew = (await db.query(`select public.airport_tracks_put($1::jsonb) as n`, [JSON.stringify(input)])).rows[0].n; const sNew = await state();
check('入れたあとの行は前の作りとまったく同じ', JSON.stringify(sNew) === JSON.stringify(sOld), { sNew, sOld });
check('返す数も同じ（入れた・上書きした線の数）', nNew === nOld && nNew === 3, { nNew, nOld });
check('食い違う線・ちょうど90分・間の線は消え、離れた線・別の機体・別の日は残る',
  !sNew.some((x) => ['old', 'edge', 'mid', 'flip'].includes(x.pts)) && ['later', 'jal', 'nextday', 'new', 'd', 'a'].every((p) => sNew.some((x) => x.pts === p)) && !sNew.some((x) => x.pts === 'bad'), sNew);
await db.query(`select public.airport_tracks_put($1::jsonb)`, [JSON.stringify(input)]);
check('何度入れても同じ', JSON.stringify(await state()) === JSON.stringify(sNew));
// くじで作った入力でも前の作りと同じ（時刻をずらして何回も入れ直す）
let same = true;
for (let k = 0; k < 6 && same; k++) {
  const rnd = (i) => ((i * 7919 + k * 104729) % 997);
  const rows = Array.from({ length: 120 }, (_, i) => ({ iata: ['HND', 'ITM', 'CTS'][rnd(i) % 3], day: '2026-11-09', callsign: 'JAL' + (rnd(i) % 25),
    at: new Date(Date.parse('2026-11-09T00:00:00Z') + (rnd(i * 3) % 600) * 60000).toISOString(), dep_here: rnd(i) % 2, pts: 'p' + k + '_' + i }));
  const uniq = [...new Map(rows.map((r) => [r.iata + r.callsign + r.at, r])).values()];   // 同じ線を1回に2本は入れない（前の作りもエラーになる）
  await db.exec(`delete from public.airport_tracks_all; insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts)
    select (array['HND','ITM','CTS'])[1 + i % 3], '2026-11-09', 'JAL' || (i % 25), '2026-11-09 00:00+00'::timestamptz + make_interval(mins => (i * 37) % 600), i % 2, 'seed' || i from generate_series(1, 150) i on conflict do nothing;
    create temp table _seed as select * from public.airport_tracks_all;`);
  const a = (await db.query(`select public.atp_old($1::jsonb) as n`, [JSON.stringify(uniq)])).rows[0].n; const sa = await state();
  await db.exec(`delete from public.airport_tracks_all; insert into public.airport_tracks_all select * from _seed; drop table _seed;`);
  const b = (await db.query(`select public.airport_tracks_put($1::jsonb) as n`, [JSON.stringify(uniq)])).rows[0].n; const sb = await state();
  same = a === b && JSON.stringify(sa) === JSON.stringify(sb);
  if (!same) console.log({ k, a, b, onlyOld: sa.filter((x) => !sb.some((y) => JSON.stringify(y) === JSON.stringify(x))).slice(0, 3), onlyNew: sb.filter((x) => !sa.some((y) => JSON.stringify(y) === JSON.stringify(x))).slice(0, 3) });
}
check('くじで作った6通りの入力で、前の作りと同じ行・同じ数', same);
await db.exec(`drop table if exists _atp`);
await db.exec('begin');
await db.query(`select public.airport_tracks_put($1::jsonb)`, [JSON.stringify(input)]);
const tmp = (await db.query(`select count(*)::int as n from pg_class where relname = '_atp'`)).rows[0].n;
await db.exec('commit');
check('呼んでも一時の表を作らない', tmp === 0, tmp);

// ---- 3. 航跡の点の取り出し：json で返し、中身は前の作り（jsonb）と同じ
await db.exec(`insert into public.track_points (callsign, t, lat, lon, alt)
  select cs, now() - make_interval(mins => m), 35.5523 + m * 0.0137, 139.78123 - m * 0.0211, case when m % 5 = 0 then null else (m * 13) % 400 end
  from unnest(array['JAL123', 'ANA45', 'SKY7', 'APJ1234A', 'N123AB']) cs, generate_series(0, 90) m`);
const oldPts = (p) => db.query(`select coalesce(jsonb_agg(jsonb_build_object('cs', callsign, 'p', pts)), '[]'::jsonb) as r from (
  select callsign, jsonb_agg(jsonb_build_array(extract(epoch from t)::bigint, lat, lon, alt) order by t) as pts from public.track_points
  where t >= now() - interval '2 hours' and t < now() + interval '1 minute' and callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$' and abs(hashtext(callsign)) % 2 = ${p} group by callsign) q`);
let eq = true, total = 0;
for (const p of [0, 1]) {
  const a = (await oldPts(p)).rows[0].r;
  const b = (await db.query(`select public.rwy_learn_points(now() - interval '2 hours', now() + interval '1 minute', ${p}, 2) as r`)).rows[0].r;
  const norm = (x) => JSON.stringify(x.map((o) => [o.cs, o.p]).sort((u, v) => u[0].localeCompare(v[0])));   // jsonb はキーを並べ替えるので値だけで比べる
  eq = eq && norm(a) === norm(b); total += b.length;
}
check('前の作り（jsonb）と同じ機体・同じ点・同じ値（形の違う呼び出し符号は入らない）', eq && total === 4, { eq, total });
const ty = (await db.query(`select pg_typeof(public.rwy_learn_points(now() - interval '1 hour', now(), 0, 1))::text as t,
  public.rwy_learn_points('2020-01-01', '2020-01-02', 0, 8)::text as e`)).rows[0];
check('返す型は json・点のない時間は空の配列', ty.t === 'json' && ty.e === '[]', ty);
let denied = 0;
for (const role of ['anon', 'authenticated']) {
  await db.exec(`set role ${role}`);
  for (const q of [`select public.rwy_learn_points(now() - interval '1 hour', now(), 0, 1)`, `select public.airport_tracks_put('[]'::jsonb)`, `select public.archive_airport_daily('2026-11-08')`]) { try { await db.query(q); } catch { denied++; } }
  await db.exec('reset role');
}
check('anon・authenticated は3つとも呼べない', denied === 6, denied);
if (bad) process.exit(1);
