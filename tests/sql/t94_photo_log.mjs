// 撮影記録（photo_log・photo_candidates）：本人だけ読む・足す・消す（update なし）、同じ分は1行、1日200行まで、未来と2000年より前は断る、退会で消える
//   候補は前後20分・時刻の差の小さい順・20件まで・登録記号のない便は出さない・36時間以内は航跡の点から作る（全機の航跡と重ねない）・
//   上空を通り過ぎた便は出さない・14空港の外／31日より前／未来は断る・ログインしていないと使えない・バックアップに入る
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id, email) values ('${A}', 'a@example.com'), ('${B}', 'b@example.com')`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const as = async (uid, sql) => { try { await db.exec(`set request.jwt.claim.sub = '${uid ?? ''}'; set role ${uid ? 'authenticated' : 'anon'}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec(`reset role; reset request.jwt.claim.sub`); } };
const err = (v) => typeof v === 'string' && v.startsWith('ERROR');

// ---- 表 photo_log ----
check('RLS が有効', await q1(`select relrowsecurity from pg_class where oid = 'public.photo_log'::regclass`) === true);
const ins = (uid, vals) => as(uid, `insert into public.photo_log (taken_at, iata, reg, callsign, type, phase, src) values ${vals} returning id`);
const P0 = `(date_trunc('minute', now()) - interval '2 hours')`;
const id1 = await ins(A, `(${P0} + interval '17 seconds', 'HND', 'JA8089', 'JAL123', 'B738', 'arr', 'cand')`);
check('本人は足せる', !err(id1), id1);
check('撮影時刻は分に丸める', await q1(`select extract(second from taken_at)::int from public.photo_log where id = ${id1}`) === 0);
check('同じ人・同じ機体・同じ分は1行', err(await ins(A, `(${P0} + interval '40 seconds', 'HND', 'JA8089', null, null, null, 'manual')`)));
check('ほかの人は同じ機体・同じ分でも足せる', !err(await ins(B, `(${P0}, 'HND', 'JA8089', null, null, null, 'manual')`)));
check('ほかの人の分として足せない', err(await as(A, `insert into public.photo_log (user_id, taken_at, iata, reg, src) values ('${B}', now() - interval '1 hour', 'HND', 'JA01AN', 'manual')`)));
check('ログインしていないと足せない', err(await ins(null, `(now() - interval '1 hour', 'HND', 'JA01AN', null, null, null, 'manual')`)));
check('未来の時刻は断る', err(await ins(A, `(now() + interval '10 minutes', 'HND', 'JA01AN', null, null, null, 'manual')`)));
check('2000年より前は断る', err(await ins(A, `('1999-12-31 10:00+09', 'HND', 'JA01AN', null, null, null, 'manual')`)));
check('登録記号の形を確かめる', err(await ins(A, `(now() - interval '1 hour', 'HND', 'ja01an', null, null, null, 'manual')`)));
check('src は cand か manual', err(await ins(A, `(now() - interval '1 hour', 'HND', 'JA01AN', null, null, null, 'auto')`)));
check('phase は arr・dep・空', err(await ins(A, `(now() - interval '1 hour', 'HND', 'JA01AN', null, null, 'taxi', 'manual')`)));
check('自分の分だけ読める', Number(await as(A, `select count(*) from public.photo_log`)) === 1 && Number(await as(B, `select count(*) from public.photo_log`)) === 1);
check('ログインしていないと読めない', err(await as(null, `select count(*) from public.photo_log`)));
check('書き換えはできない', err(await as(A, `update public.photo_log set reg = 'JA01AN' where id = ${id1}`)));
await as(B, `delete from public.photo_log where id = ${id1}`);
check('ほかの人の分は消せない', Number(await q1(`select count(*) from public.photo_log where id = ${id1}`)) === 1);
await as(A, `delete from public.photo_log where id = ${id1}`);
check('自分の分は消せる', Number(await q1(`select count(*) from public.photo_log where id = ${id1}`)) === 0);
// 1日200行まで（作った日を今日に固定するので、ずらした撮影時刻で200行足す）
const many = Array.from({ length: 200 }, (_, i) => `(now() - interval '${i + 10} minutes', 'NRT', 'JA${String(100 + i)}A', null, null, null, 'manual')`).join(',');
check('200行までは足せる', !err(await as(A, `insert into public.photo_log (taken_at, iata, reg, callsign, type, phase, src) values ${many}`)));
check('201行目は断る', err(await ins(A, `(now() - interval '5 hours', 'NRT', 'JA999A', null, null, null, 'manual')`)));
check('created_at は手で入れても今になる', String(await as(B, `insert into public.photo_log (taken_at, iata, reg, src, created_at) values (now() - interval '3 hours', 'HND', 'JA02AN', 'manual', now() - interval '3 days') returning (created_at > now() - interval '1 minute')::text`)) === 'true');

// ---- 候補 photo_candidates ----
// 3日前の 10:00（日本時間）を撮影時刻にする。全機の航跡と reg_legs を作る
const T = `((now() at time zone 'Asia/Tokyo')::date - 3 + time '10:00') at time zone 'Asia/Tokyo'`;
const day = `((now() at time zone 'Asia/Tokyo')::date - 3)`;
await db.exec(`insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values
  ('HND', ${day}, 'JAL101', ${T} + interval '2 minutes', 0, 'x'),
  ('HND', ${day}, 'ANA201', ${T} - interval '5 minutes', 1, 'x'),
  ('HND', ${day}, 'SKY301', ${T} + interval '12 minutes', 0, 'x'),
  ('HND', ${day}, 'JAL999', ${T} + interval '25 minutes', 0, 'x'),
  ('HND', ${day}, 'APJ401', ${T} + interval '1 minute', 1, 'x'),
  ('NRT', ${day}, 'JAL777', ${T}, 0, 'x');
insert into public.reg_legs (reg, callsign, day, type, first_at, last_at) values
  ('JA301J', 'JAL101', ${day}, 'B738', ${T} - interval '90 minutes', ${T} + interval '2 minutes'),
  ('JA219A', 'ANA201', ${day}, 'B788', ${T} - interval '5 minutes', ${T} + interval '60 minutes'),
  ('JA73NA', 'SKY301', ${day}, 'B738', ${T} - interval '80 minutes', ${T} + interval '12 minutes'),
  ('JA999J', 'JAL999', ${day}, 'A359', ${T} - interval '60 minutes', ${T} + interval '25 minutes'),
  ('JA777J', 'JAL777', ${day}, 'B77W', ${T} - interval '60 minutes', ${T})`);
const cand = await as(A, `select public.photo_candidates('HND', ${T})`);
check('差の小さい順・前後20分・登録記号のない便は出さない', Array.isArray(cand) && cand.map((x) => x.reg).join() === 'JA301J,JA219A,JA73NA', cand);
check('機種・便名・着陸／離陸・分の差を返す', cand?.[0]?.type === 'B738' && cand[0].callsign === 'JAL101' && cand[0].phase === 'arr' && Number(cand[0].dmin) === 2 && cand[1].phase === 'dep' && Number(cand[1].dmin) === 5, cand);
check('航跡の点は返さない', cand?.[0] && !('pts' in cand[0]), cand?.[0]);
check('ほかの空港の便は出さない', !cand?.some((x) => x.reg === 'JA777J'), cand);
check('空港は小文字でもよい', (await as(A, `select jsonb_array_length(public.photo_candidates('hnd', ${T}))`)) === 3);
// 20件まで
await db.exec(`insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts)
  select 'KIX', ${day}, 'APJ' || (500 + i), ${T} + make_interval(secs => i * 30), 0, 'x' from generate_series(1, 30) i;
  insert into public.reg_legs (reg, callsign, day, type, first_at, last_at)
  select 'JA' || (500 + i) || 'P', 'APJ' || (500 + i), ${day}, 'A320', ${T} - interval '1 hour', ${T} + interval '1 hour' from generate_series(1, 30) i`);
check('20件まで', (await as(A, `select jsonb_array_length(public.photo_candidates('KIX', ${T}))`)) === 20);
// 断る
check('14空港の外は断る', String(await as(A, `select public.photo_candidates('UKB', ${T})`)).includes('not recorded'));
check('31日より前は断る', String(await as(A, `select public.photo_candidates('HND', now() - interval '32 days')`)).includes('too old'));
check('未来は断る', String(await as(A, `select public.photo_candidates('HND', now() + interval '1 hour')`)).includes('future'));
check('ログインしていないと使えない', err(await as(null, `select public.photo_candidates('HND', ${T})`)));
check('候補の元の表は直接読めない', err(await as(A, `select count(*) from public.airport_tracks_all`)) && err(await as(A, `select count(*) from public.reg_legs`)));

// 36時間以内：全機の航跡がまだない便を、航跡の点から作る（羽田の中心 35.5497, 139.7870）
const N = `(now() - interval '1 hour')`;
await db.exec(`insert into public.track_points (callsign, t, lat, lon, alt)
  select 'ANA61', ${N} - make_interval(mins => 10 - i), 35.65 - i * 0.01, 139.80, 40 - i * 4 from generate_series(0, 10) i;   -- 降りてくる（着陸）
  insert into public.track_points (callsign, t, lat, lon, alt)
  select 'JAL62', ${N} + make_interval(mins => i), 35.55 + i * 0.01, 139.78, 2 + i * 5 from generate_series(0, 10) i;       -- 上っていく（離陸）
  insert into public.track_points (callsign, t, lat, lon, alt)
  select 'UAL1', ${N} + make_interval(mins => i), 35.55, 139.70 + i * 0.01, 350 from generate_series(0, 10) i;              -- 上空を通り過ぎる
  insert into public.track_points (callsign, t, lat, lon, alt)
  select 'SKY63', ${N} + make_interval(mins => i), 35.56, 139.79, 10 from generate_series(0, 5) i;                          -- 全機の航跡にもある便
  insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values ('HND', (${N} at time zone 'Asia/Tokyo')::date, 'SKY63', ${N} + interval '3 minutes', 1, 'x');
  insert into public.reg_legs (reg, callsign, day, type, first_at, last_at) values
    ('JA61AN', 'ANA61', (${N} at time zone 'Asia/Tokyo')::date, 'B789', ${N} - interval '2 hours', ${N}),
    ('JA62JL', 'JAL62', (${N} at time zone 'Asia/Tokyo')::date, 'A350', ${N}, ${N} + interval '2 hours'),
    ('N12345', 'UAL1',  (${N} at time zone 'Asia/Tokyo')::date, 'B77W', ${N} - interval '5 hours', ${N} + interval '5 hours'),
    ('JA63SK', 'SKY63', (${N} at time zone 'Asia/Tokyo')::date, 'B738', ${N}, ${N} + interval '2 hours')`);
const live = await as(A, `select public.photo_candidates('HND', ${N})`);
const by = Object.fromEntries((live ?? []).map((x) => [x.reg, x]));
check('36時間以内は航跡の点から作る（着陸・離陸）', by.JA61AN?.phase === 'arr' && by.JA62JL?.phase === 'dep', live);
check('着陸はいちばん近い点の時刻', by.JA61AN && Math.abs(Date.parse(by.JA61AN.at) - (Date.parse(await q1(`select (${N})::text`)))) < 61_000, by.JA61AN);
check('上空を通り過ぎた便は出さない', !by.N12345, live);
check('全機の航跡にある便は1つだけ（全機の航跡のほう）', (live ?? []).filter((x) => x.reg === 'JA63SK').length === 1 && by.JA63SK.phase === 'dep', live);

// 退会で消える・バックアップに入る
const bk = await q1(`select pg_get_functiondef('public.admin_backup()'::regprocedure)`);
check('バックアップに photo_log が入る', bk.includes("'photo_log'"));
await db.exec(`delete from auth.users where id = '${A}'`);
check('退会で本人の撮影記録が消える', Number(await q1(`select count(*) from public.photo_log where user_id = '${A}'`)) === 0 && Number(await q1(`select count(*) from public.photo_log where user_id = '${B}'`)) === 2);
check('全機の航跡と機体の記録は残る', Number(await q1(`select count(*) from public.airport_tracks_all`)) > 0 && Number(await q1(`select count(*) from public.reg_legs`)) > 0);
if (bad) process.exit(1);
