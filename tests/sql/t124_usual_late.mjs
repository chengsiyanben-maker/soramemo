// 「いつもより○分遅い（推定）」の画面に要る読むだけの関数（移行 185）
//   1. 便名・登録記号から引く（先頭の0・空白・小文字を直す）。いつもの到着（曜日・回数・ばらつき）
//   2. 着く見込みの元の順：その日の実績（着いた）→ 画面が渡した land_pred → 見張り（10分以内）。どれもなければ null（U1n-v2）
//   3. いつもより○分：0時をまたいでも比べる・late／usual／early の幅・ダイバートでは比べない・次の日の同じ便を取らない
//   4. ODPT の会社は reason odpt・知らない記号は unknown・形のちがう値は null
//   5. 権限：anon・authenticated は関数を実行だけ。表は今までどおり読めない。誰が選んだかは返さない
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.sql')).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const one = async (sql, p) => (await db.query(sql, p)).rows[0];
const as = async (role, sql, p) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql, p); return r.rows; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const UL = async (args, role = 'anon') => {
  const r = await as(role, `select public.usual_late(p_flight => $1, p_reg => $2, p_day => $3::date, p_arr => $4, p_land => $5::timestamptz) j`,
    [args.flight ?? null, args.reg ?? null, args.day ?? null, args.arr ?? null, args.land ?? null]);
  return typeof r === 'string' ? r : r[0]?.j;
};

const today = (await one(`select (now() at time zone 'Asia/Tokyo')::date::text d`)).d;
const D = async (k) => (await one(`select ($1::date + $2::int)::text d`, [today, k])).d;
const dow = (await one(`select extract(dow from $1::date)::int d`, [today])).d;
// 日本時間の「その日の mins 分」の時刻
const T = async (mins, off = 0) => (await one(`select ((($1::date + $2::int)::timestamp + make_interval(mins => $3::int)) at time zone 'Asia/Tokyo')::text t`, [today, off, mins])).t;
// いまから k 分後の日本時間の分（0〜1439）
const nowMins = async (k) => (await one(`select ((extract(hour from (now() + make_interval(mins => $1::int)) at time zone 'Asia/Tokyo') * 60
  + extract(minute from (now() + make_interval(mins => $1::int)) at time zone 'Asia/Tokyo'))::int) m`, [k])).m;

const m60 = await nowMins(60);
const uBA5 = (m60 - 32 + 1440) % 1440;           // land_pred（いまから60分後）がいつもより32分遅くなる、いつもの時刻
await db.exec(`
  insert into public.foreign_usual (callsign, iata, dep_here, dow, mins, n, spread, last_day) values
    ('BAW5', 'HND', 0, ${dow}, ${uBA5}, 7, 16, '${today}'), ('BAW5', 'HND', 0, -1, ${(uBA5 + 5) % 1440}, 40, 20, '${today}'),
    ('BAW5', 'NRT', 0, -1, 600, 5, 10, '${today}'),
    ('QTR812', 'HND', 0, -1, 1430, 30, 12, '${today}'),
    ('SKY13', 'FUK', 0, -1, 1200, 25, 8, '${today}'),
    ('KAL703', 'NRT', 0, -1, 700, 20, 9, '${today}'),
    ('CPA500', 'NRT', 0, -1, 900, 20, 9, '${today}'),
    ('UAL837', 'HND', 0, -1, 960, 20, 9, '${today}');
  insert into public.reg_legs (reg, callsign, day, type, first_at, last_at) values
    ('G-XWBA', 'BAW5', '${today}', 'A35K', now() - interval '9 hours', now() - interval '1 minute'),
    ('G-XWBA', 'BAW8', '${await D(-1)}', 'A35K', now() - interval '30 hours', now() - interval '20 hours'),
    ('JA731J', 'JAL5', '${today}', 'B77W', now() - interval '2 hours', now());
  insert into public.live_positions (callsign, lat, lon, alt_ft, ground, seen_at) values ('BAW5', 40, 150, 35000, false, now() - interval '1 minute');
  insert into public.foreign_legs (day, callsign, iata, dep_here, at, flight, airline) values
    ('${today}', 'QTR812', 'HND', 0, '${await T(20, 1)}', 'QR812', 'QR'),                 -- 23:50 の便が次の日の 0:20 に着いた（30分遅い）
    ('${today}', 'SKY13', 'FUK', 0, '${await T(1200 - 20)}', 'BC13', 'BC'),               -- 20分早い
    ('${await D(1)}', 'KAL703', 'NRT', 0, '${await T(700, 1)}', 'KE703', 'KE'),          -- 次の日の同じ便（今日には取らない）
    ('${await D(-1)}', 'KAL703', 'NRT', 0, '${await T(705, -1)}', 'KE703', 'KE');         -- 前の日の同じ便（今日には取らない）
  insert into public.foreign_legs (day, callsign, iata, dep_here, at, flight, airline, event) values
    ('${today}', 'CPA500', 'KIX', 0, '${await T(950)}', 'CX500', 'CX', 'divert');
  insert into public.foreign_watch (flight, svc_date, callsign, arr, usual_arr, usual_n, state, late, eta, updated_at) values
    ('UA837', '${today}', 'UAL837', 'HND', 960, 20, '{"curfew_near": true}', 10, '${await T(970)}', now() - interval '2 minutes'),
    ('KE703', '${today}', 'KAL703', 'NRT', 700, 20, '{}', 5, '${await T(705)}', now() - interval '30 minutes');
  insert into public.push_subs (endpoint, p256dh, auth, flights) values ('https://e/secret', 'k', 'a', array['UA837@${today}']);`);

// 1
let j = await UL({ flight: 'BA5', land: (await one(`select (now() + interval '60 minutes')::text t`)).t });
check('便名と land_pred から「いつもより32分遅い」（late）', j?.late_min === 32 && j.kind === 'late' && j.eta?.src === 'live' && j.eta.landed === false, j);
check('いつもの到着はその曜日を先に（時刻・回数・曜日・ばらつき・8週）', j?.usual?.mins === uBA5 && j.usual.n === 7 && j.usual.dow === dow && j.usual.spread === 16 && j.usual.weeks === 8
  && j.usual.time === `${String(Math.floor(uBA5 / 60)).padStart(2, '0')}:${String(uBA5 % 60).padStart(2, '0')}`, j?.usual);
check('着く空港は回数の多いもの（HND）・呼び出し符号・出典と断り書き', j?.arr === 'HND' && j.callsign === 'BAW5' && j.source === 'adsb.lol（ODbL）' && /定刻や航空会社の発表ではありません/.test(j.note), j);
check('いまの位置を見た時刻と地上かどうか', j?.seen_at && j.ground === false, j);
const j2 = await UL({ flight: ' ba 005 ' });
check('先頭の0・空白・小文字を直す。見込みがなければ eta も ずれも null（U1n-v2）', j2?.flight === 'BA5' && j2.eta === null && j2.late_min === null && j2.kind === null && j2.usual?.n === 7, j2);
const j3 = await UL({ flight: 'BA5', arr: 'NRT' });
check('空港を渡すとその空港のいつも（曜日を問わない → dow は null）', j3?.arr === 'NRT' && j3.usual?.mins === 600 && j3.usual.dow === null, j3?.usual);
const j4 = await UL({ reg: 'g-xwba' });
check('登録記号から（その日のいちばん新しい呼び出し符号 → 便名）', j4?.callsign === 'BAW5' && j4.flight === 'BA5' && j4.reg === 'G-XWBA' && j4.usual?.n === 7, j4);

// 2
j = await UL({ flight: 'QR812', land: (await one(`select (now() + interval '60 minutes')::text t`)).t });
check('着いたあとは実績を先に（land_pred より）・0時をまたいで30分遅い', j?.eta?.src === 'track' && j.eta.landed === true && j.eta.iata === 'HND' && j.late_min === 30 && j.kind === 'late' && j.eta.time === '00:20', j);
j = await UL({ flight: 'UA837' });
check('見張りの見込み（10分以内に書かれたもの）・前後14分以内は usual・門限に近い', j?.eta?.src === 'watch' && j.late_min === 10 && j.kind === 'usual' && j.curfew_near === true, j);
j = await UL({ flight: 'UA837', land: '2000-01-01T00:00:00Z' });
check('ありえない land_pred は使わない（見張りの見込みのまま）', j?.eta?.src === 'watch', j?.eta);
j = await UL({ flight: 'KE703' });
check('古い見張りの見込みは使わない・前の日と次の日の同じ便の実績は取らない → null', j?.eta === null && j.late_min === null && j.usual?.mins === 700, j);
j = await UL({ flight: 'KE703', day: await D(1) });
check('次の日を聞けば次の日の実績', j?.eta?.src === 'track' && j.late_min === 0 && j.kind === 'usual', j);

// 3
j = await UL({ flight: 'BC13' });
check('ODPT にない日本の会社（スカイマーク）・20分早い（early）', j?.callsign === 'SKY13' && j.late_min === -20 && j.kind === 'early', j);
j = await UL({ flight: 'CX500' });
check('ダイバートは比べない（ずれ null・行き先の空港）', j?.event === 'divert' && j.divert_to === 'KIX' && j.late_min === null && j.kind === null && j.eta?.iata === 'KIX', j);

// 4
j = await UL({ flight: 'JL5' });
check('ODPT の会社は reason odpt だけ', j?.reason === 'odpt' && !('usual' in j), j);
j = await UL({ reg: 'JA731J' });
check('登録記号でも ODPT の会社の便なら odpt', j?.reason === 'odpt' && j.callsign === 'JAL5', j);
j = await UL({ flight: 'XX1' });
check('知らない記号は unknown（usual・eta は null）', j?.reason === 'unknown' && j.usual === null && j.eta === null, j);
j = await UL({ reg: 'N12345' });
check('見えていない登録記号は unknown', j?.reason === 'unknown', j);
for (const [a, label] of [[{}, '何もない'], [{ flight: 'BAD' }, '形のちがう便名'], [{ flight: 'BA5', arr: 'TOKYO' }, '形のちがう空港'], [{ flight: 'BA5', day: await D(-30) }, '遠い日'], [{ reg: '???' }, '形のちがう登録記号']]) {
  j = await UL(a);
  check(`形のちがう値は null：${label}`, j === null, j);
}

// 5
j = await UL({ flight: 'UA837' }, 'authenticated');
check('authenticated も実行できる', j?.callsign === 'UAL837', j);
check('誰が選んだかは返さない（申し込みの中身がない）', !JSON.stringify(j).includes('secret') && !('endpoint' in j), j);
for (const t of ['foreign_usual', 'foreign_legs', 'foreign_watch', 'reg_legs', 'live_positions']) {
  const r = await as('anon', `select * from public.${t} limit 1`);
  check(`anon は表 ${t} を読めない`, typeof r === 'string' && /permission denied/.test(r), r);
}
const f = await one(`select prosecdef, provolatile, proacl::text acl from pg_proc where proname = 'usual_late'`);
check('security definer・stable・public には許さない', f.prosecdef === true && f.provolatile === 's' && /anon=X/.test(f.acl) && /authenticated=X/.test(f.acl) && !/(^|[{,])=X/.test(f.acl), f);
const plan = (await db.query(`explain select public.usual_late('BA5')`)).rows.map((r) => r['QUERY PLAN']).join('\n');
check('呼び出しは1行（関数の中は主キーで引く）', /Result/.test(plan), plan);

console.log(bad ? `NG ${bad}` : 'すべて OK');
if (bad) process.exit(1);
