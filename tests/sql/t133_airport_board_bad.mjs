// 運用の「遅れ」の絞り込み（移行 195）：airport_board に今日の遅れ・欠航の便 'bad' を足す
//   作り物の時刻表（t105 と同じ。8日半・5空港＋海外、欠航・遅れ・機体の位置で見つけた時刻あり）で、
//   bad の数が hours の遅れ＋欠航と同じか、1便の形、ほかのキーが前と全部同じか、権限が変わっていないか、もう一度流しても同じかを確かめる
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const mine = files.find(f => f.endsWith('_airport_board_bad.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 600)); if (!ok) bad++; };
const q = async (sql) => (await db.query(sql)).rows;
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];

// 195 の前まで流し、前の airport_board を別の名前で写しておく
for (const f of files) { if (f === mine) break; await db.exec(fs.readFileSync(dir + f, 'utf8')); }
const prev = await q1(`select pg_get_functiondef('public.airport_board(text, text)'::regprocedure)`);
await db.exec(prev.replace(/public\.airport_board\(/, 'public.airport_board_old('));
await db.exec(fs.readFileSync(dir + mine, 'utf8'));

// 1. 番号
check('移行は 195 番', /^\d{8}000195_airport_board_bad\.sql$/.test(mine), mine);

// 2. 作り物の時刻表：5空港＋海外（ICN）、今から 8日6時間前〜7時間後。決まった順の数で作る（毎回同じ）
await db.exec(`
insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, aircraft, source)
select ((t at time zone 'Asia/Tokyo')::date), 'JL' || (100 + i), d, a, t, t + interval '95 minutes', case when i % 3 = 0 then '763' end, 'ODPT'
from (select i, now() - interval '8 days 7 hours' + (i * interval '4 minutes 7 seconds') as t,
             (array['HND','ITM','CTS','FUK','OKA','HND','HND'])[1 + i % 7] as d,
             (array['ITM','HND','HND','HND','HND','CTS','ICN','FUK','OKA'])[1 + (i * 7) % 9] as a
      from generate_series(1, 3100) i) s where d <> a;
update public.flight_schedule set
  etd = case when id % 4 = 0 then std + ((id % 50) * interval '1 minute') end,
  eta = case when id % 5 <> 0 then sta + ((id % 40) * interval '1 minute') end,
  atd = case when std < now() - interval '30 minutes' and id % 6 <> 0 then std + ((id % 33) * interval '1 minute') end,
  ata = case when sta < now() - interval '10 minutes' and id % 7 <> 0 then sta + ((id % 29) * interval '1 minute') end,
  dep_status = case when id % 23 = 0 then 'Cancelled' when id % 11 = 0 then '遅延' end,
  arr_status = case when id % 31 = 0 then 'cancelled' end;
insert into public.flight_watch (schedule_id, state)
select id, case id % 3
  when 0 then jsonb_build_object('phase', 'air', 'takeoff_at', extract(epoch from std + interval '12 minutes') * 1000, 'takeoff_est', false, 'eta', extract(epoch from sta + interval '9 minutes') * 1000)
  when 1 then jsonb_build_object('phase', 'landed', 'takeoff_at', extract(epoch from std + interval '15 minutes') * 1000, 'takeoff_est', true,
                                 'landed_at', extract(epoch from sta + interval '4 minutes') * 1000, 'landed_iata', arr)
  else jsonb_build_object('phase', 'landed', 'landed_at', extract(epoch from sta) * 1000, 'landed_iata', 'XXX') end
from public.flight_schedule where id % 2 = 0;
insert into public.eta_calib (iata, taxi_out, n_out) values ('HND', 17.5, 40) on conflict (iata) do update set taxi_out = excluded.taxi_out;
analyze public.flight_schedule; analyze public.flight_watch;`);
check('作り物の便が入った（2,000便より多い）', await q1(`select count(*)::int from public.flight_schedule`) > 2000, null);

// 3. ほかのキーは前と全部同じ・bad の数は hours の遅れ＋欠航と同じ（同じトランザクションの中なので now() も同じ）
const pairs = [];
for (const ap of ['HND', 'ITM', 'CTS', 'FUK', 'OKA', 'KIX', 'ICN']) for (const k of ['all', 'intl', 'dom']) pairs.push([ap, k]);
await db.exec('begin');
let same = 0, sumOk = 0, withBad = 0; const diff = [], sumNg = [];
const boards = {};
for (const [ap, k] of pairs) {
  const a = JSON.parse(await q1(`select public.airport_board_old('${ap}', '${k}')::text`));
  const b = JSON.parse(await q1(`select public.airport_board('${ap}', '${k}')::text`));
  boards[ap + k] = b;
  const { bad: bb, ...rest } = b;
  if (JSON.stringify(rest) === JSON.stringify(a) && !('bad' in a)) same++; else diff.push([ap, k]);
  const want = b.hours.reduce((s, h) => s + h.late + h.cancel, 0);
  if (Array.isArray(bb) && bb.length === want) sumOk++; else sumNg.push([ap, k, bb?.length, want]);
  if (bb?.length) withBad++;
}
const today = await q1(`select ((now() at time zone 'Asia/Tokyo')::date)::text`);
const chk = (await q(`select count(*) filter (where cancelled)::int c, count(*) filter (where not cancelled)::int l from (
  select coalesce(dep_status ~* 'cancel' or arr_status ~* 'cancel', false) cancelled,
         case when arr = 'HND' then coalesce(ata, eta) else coalesce(atd, etd) end - case when arr = 'HND' then sta else std end as off
  from public.flight_schedule where (arr = 'HND' or dep = 'HND') and std > now() - interval '8 days 6 hours' and std < now() + interval '6 hours'
    and ((case when arr = 'HND' then sta else std end) at time zone 'Asia/Tokyo')::date = '${today}'::date) s
  where cancelled or off >= interval '15 minutes'`))[0];
const bk = await q1(`select count(*)::int from public.flight_schedule where std > now() - interval '8 days 6 hours' and std < now() + interval '6 hours'`);
await db.exec('commit');
check('7空港 × 3通り（21通り）で bad 以外は前と全部同じ答え（前の答えに bad はない）', same === pairs.length, diff);
check('21通りすべてで bad の数 ＝ hours の遅れ＋欠航の合計', sumOk === pairs.length, sumNg);
check('bad のある答えで比べている（空ばかりではない）', withBad >= 6, withBad);
check('作り物の便は見る幅に入っている', bk > 1000, bk);

const hb = boards.HNDall.bad;
check('羽田：bad の数が時刻表から直接数えた今日の遅れ＋欠航（関数の見る幅：定刻の出発が8日6時間前〜6時間後）と同じ', hb.length === chk.c + chk.l && hb.length > 0, [hb.length, chk]);
const keys = 'dir,flight,other,sched,est,actual,late,cancelled,intl,aircraft';
check('1便の形：10個のキー', hb.every((x) => Object.keys(x).sort().join() === keys.split(',').sort().join()), hb[0]);
check('dir は dep か arr・相手の空港は羽田でない', hb.every((x) => (x.dir === 'dep' || x.dir === 'arr') && x.other && x.other !== 'HND'), hb.find((x) => x.other === 'HND'));
check('欠航は late が null、遅れは late が15分以上', hb.every((x) => x.cancelled ? x.late === null : x.late >= 15), hb.find((x) => x.cancelled ? x.late !== null : !(x.late >= 15)));
check('欠航と遅れの両方がある', hb.some((x) => x.cancelled) && hb.some((x) => !x.cancelled), null);
check('late は（実際、なければ見込み）− 定刻の分', hb.filter((x) => !x.cancelled).every((x) => Math.round((Date.parse(x.actual ?? x.est) - Date.parse(x.sched)) / 60000) === x.late), hb.find((x) => !x.cancelled));
check('定刻の順に並ぶ', hb.every((x, i) => i === 0 || Date.parse(hb[i - 1].sched) <= Date.parse(x.sched)), null);
const dayOf = (t) => new Date(Date.parse(t) + 9 * 3600e3).toISOString().slice(0, 10);
check('すべて今日（日本時間）の定刻', hb.every((x) => dayOf(x.sched) === today), hb.find((x) => dayOf(x.sched) !== today));
check('海外（ICN）の便は intl が true', hb.filter((x) => x.other === 'ICN').every((x) => x.intl === true) && hb.filter((x) => x.other !== 'ICN').every((x) => x.intl === false), null);
check('bad は p_kind で変わらない（hours と同じ）', JSON.stringify(boards.HNDintl.bad) === JSON.stringify(hb) && JSON.stringify(boards.HNDdom.bad) === JSON.stringify(hb), null);
check('便のない空港（関西）は bad が空の配列', Array.isArray(boards.KIXall.bad) && boards.KIXall.bad.length === 0, boards.KIXall.bad);

// 4. 権限と形は前のまま
const priv = await q(`select r, has_function_privilege(r, 'public.airport_board(text, text)', 'execute') e from unnest(array['anon','authenticated']) r`);
check('airport_board は anon・authenticated が呼べる（前と同じ）', priv.every((x) => x.e === true), priv);
const pub = await q1(`select count(*)::int from information_schema.routine_privileges where routine_name = 'airport_board' and grantee = 'PUBLIC'`);
check('public には許していない（前と同じ）', pub === 0, pub);
const fn = await q(`select p.provolatile v, p.prosecdef s, pg_get_function_result(p.oid) r, array_to_string(p.proconfig, ',') c from pg_proc p where p.oid = 'public.airport_board(text, text)'::regprocedure`);
check('stable・security definer・jsonb を返す・search_path は public（前と同じ）', fn[0].v === 's' && fn[0].s === true && fn[0].r === 'jsonb' && fn[0].c === 'search_path=public', fn);
check('関数は1つだけ（引数の違う同じ名前を作っていない）', await q1(`select count(*)::int from pg_proc where proname = 'airport_board' and pronamespace = 'public'::regnamespace`) === 1, null);
check('移行のあと lock_timeout は元に戻る', (await q1(`show lock_timeout`)) === '0', await q1(`show lock_timeout`));
const anonRes = await (async () => { await db.exec(`set role anon`); try { return JSON.parse(await q1(`select public.airport_board('HND')::text`)); } finally { await db.exec(`reset role`); } })();
check('anon で呼んでも bad が返る', Array.isArray(anonRes.bad), Object.keys(anonRes));

// 5. もう一度流しても同じ
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流しても関数は1つ・bad を返す', await q1(`select count(*)::int from pg_proc where proname = 'airport_board' and pronamespace = 'public'::regnamespace`) === 1
  && Array.isArray(JSON.parse(await q1(`select public.airport_board('HND')::text`)).bad), null);

console.log(bad ? `\n${bad} 件 NG` : '\nすべて OK'); process.exit(bad ? 1 : 0);
