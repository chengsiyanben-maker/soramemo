// 離陸の時刻：出発＋空港の地上走行（毎晩決め直す）・機体の位置で見つけた離陸・出発してまだ離陸していない便も出る・離陸の知らせ用の便
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

// 便を足す（std・sta・etd・atd は「いまから何分」。takeoff があれば機体の位置で離陸を見つけたことにする）
async function fl(flight, dep, arr, std, sta, o = {}) {
  const m = (x) => x == null ? null : new Date(Date.now() + x * 60e3).toISOString();
  const r = await db.query(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, etd, atd, aircraft, source)
    values ((($4::timestamptz) at time zone 'Asia/Tokyo')::date, $1, $2, $3, $4, $5, $6, $7, $8, 'test') returning id`, [flight, dep, arr, m(std), m(sta), m(o.etd), m(o.atd), o.aircraft ?? 'B789']);
  if (o.takeoff != null) await db.query(`insert into public.flight_watch (schedule_id, state) values ($1, $2::jsonb)`, [r.rows[0].id, JSON.stringify({ phase: 'air', takeoff_at: Date.now() + o.takeoff * 60e3, takeoff_est: false })]);
  return r.rows[0].id;
}
const T = (iso) => Math.round((Date.parse(iso) - Date.now()) / 60e3);
await fl('NH1', 'HND', 'ITM', 30, 100);                       // 定刻30分後 → 離陸は 30+16
await fl('NH2', 'HND', 'CTS', 10, 100, { etd: 20 });           // 見込み20分後 → 36
await fl('NH3', 'HND', 'FUK', -25, 90, { atd: -12 });          // 12分前に出発、まだ離陸していない → 4分後
await fl('NH4', 'HND', 'OKA', -40, 100, { atd: -35, takeoff: -18 });   // 18分前に離陸
await fl('NH5', 'HND', 'KOJ', -60, 40, { atd: -55, takeoff: -40 });    // とうに離陸（出ない）
await db.exec('set role anon');
const b = (await db.query(`select public.airport_board('HND') as b`)).rows[0].b;
await db.exec('reset role');
const by = Object.fromEntries(b.next_dep.map((x) => [x.flight, x]));
console.log(b.next_dep.map((x) => `${x.flight}:${T(x.takeoff)}:${x.takeoff_src}`).join(' '));
check('定刻＋地上走行（羽田は16分）', by.NH1 && T(by.NH1.takeoff) === 46 && by.NH1.takeoff_src === 'calc' && Number(by.NH1.taxi) === 16, by.NH1);
check('出発の見込み＋地上走行', by.NH2 && T(by.NH2.takeoff) === 36, by.NH2);
check('出発してまだ離陸していない便も出る', by.NH3 && T(by.NH3.takeoff) === 4, by.NH3);
check('機体の位置で見つけた離陸', by.NH4 && T(by.NH4.takeoff) === -18 && by.NH4.takeoff_src === 'actual', by.NH4);
check('とうに離陸した便は出ない', !by.NH5, b.next_dep.map((x) => x.flight));
check('離陸の時刻の順', b.next_dep.map((x) => x.flight).join() === 'NH4,NH3,NH2,NH1', b.next_dep.map((x) => x.flight));
check('これまでの t（出発の時刻）はそのまま', by.NH3 && T(by.NH3.t) === -12, by.NH3);

// 毎晩の学習：伊丹の便12本、出発から離陸まで 11〜13分（中央値12）
for (let i = 0; i < 12; i++) await fl('JL' + (500 + i), 'ITM', 'HND', -300 - i * 10, -200, { atd: -300 - i * 10, takeoff: -300 - i * 10 + 11 + (i % 3) });
await fl('JL600', 'ITM', 'HND', -900, -800, { atd: -900, takeoff: -800 });   // 100分（外れ値として使わない）
await db.query(`select public.refresh_taxi_out()`);
const c = (await db.query(`select taxi_out, n_out from public.eta_calib where iata = 'ITM'`)).rows[0];
check('出発から離陸までの中央値で決め直す', Number(c.taxi_out) === 12 && c.n_out === 12, c);

// 離陸の知らせ用の便：これから15分のうちに離陸する、まだ離陸していない便
const d = (await db.query(`select public.spot_departures(array['HND']) as d`)).rows[0].d;
check('離陸の知らせ用の便（15分以内・まだ離陸していない）', d.map((x) => x.flight).join() === 'NH3', d);
let denied = false; await db.exec('set role anon'); try { await db.query(`select public.spot_departures(array['HND'])`); } catch { denied = true; } await db.exec('reset role');
check('離陸の知らせ用の便は運営だけ', denied);
let ok = true; try { await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, spot_iata, spot_kinds) values ('https://fcm.googleapis.com/d1', 'k', 'a', 'HND', array['big','dep'])`); } catch { ok = false; }
check('撮影の知らせに「離陸も知らせる」', ok);
let denied2 = false; await db.exec('set role anon'); try { await db.query('select taxi_out from public.eta_calib'); } catch { denied2 = true; } await db.exec('reset role');
check('地上走行の表は利用者から読めない', denied2);
if (bad) process.exit(1);
