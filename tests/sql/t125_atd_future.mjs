// 実際の出発・到着の時刻に、まだ来ていない時刻を残さない（移行 186・11/18 JL661）
//   1. まだ来ていない atd・ata は入れず、etd・eta が渡されていなければそちらに回す
//   2. 来た時刻の atd・ata は入れる。渡されなくても消さない（今までどおり）。新しい値が来たら書き直す
//   3. 前に入ってしまった、まだ来ていない atd・ata は次の書き直しで外す
//   4. 権限：anon・authenticated は実行できない。lock_timeout は 10s のまま
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

await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
  (current_date, 'JL661', 'HND', 'FUK', now() + interval '30 minutes', now() + interval '150 minutes', 't'),
  (current_date, 'JL663', 'HND', 'FUK', now() - interval '60 minutes', now() + interval '60 minutes', 't'),
  (current_date, 'JL665', 'HND', 'FUK', now() - interval '200 minutes', now() - interval '80 minutes', 't')`);
const id = async (f) => (await one(`select id from public.flight_schedule where flight = $1`, [f])).id;
const [a, b, c] = [await id('JL661'), await id('JL663'), await id('JL665')];
const apply = (rows) => one(`select public.apply_flight_status($1::jsonb) n`, [JSON.stringify(rows)]);
const row = (i) => one(`select atd, etd, ata, eta, (atd - now()) > interval '0' atd_future from public.flight_schedule where id = $1`, [i]);
const at = async (mins) => (await one(`select (now() + make_interval(mins => $1::int))::text t`, [mins])).t;
const same = async (x, y) => x != null && y != null && (await one(`select $1::timestamptz = $2::timestamptz ok`, [x, y])).ok;

// 1. まだ来ていない atd（33分後）→ atd に入れず etd に
const f33 = await at(33);
await apply([{ id: a, atd: f33, etd: null }]);
let r = await row(a);
check('1 まだ来ていない atd は入れない', r.atd === null, r);
check('1 etd に回す（etd が空のとき）', await same(r.etd, f33), r);
// 見込みが別に渡されていれば、そちらを使う
const f35 = await at(35);
await apply([{ id: a, atd: f33, etd: f35 }]);
r = await row(a);
check('1 etd が渡されていればそちら', r.atd === null && await same(r.etd, f35), r);
// 1分以内（時計のずれ）は入れる
const f0 = await at(0);
await apply([{ id: b, atd: f0 }]);
r = await row(b);
check('1 いまの時刻は atd に入れる', await same(r.atd, f0), r);

// 2. 来た時刻は入れる・渡されなくても消さない・新しい値で書き直す
const p58 = await at(-58), p55 = await at(-55);
await apply([{ id: b, atd: p58 }]);
await apply([{ id: b, atd: null, dep_status: 'Departed' }]);
r = await row(b);
check('2 来た atd は渡されなくても消さない', await same(r.atd, p58), r);
await apply([{ id: b, atd: p55 }]);
r = await row(b);
check('2 新しい atd で書き直す', await same(r.atd, p55), r);
// 到着も同じ
const f50 = await at(50);
await apply([{ id: b, ata: f50, eta: null }]);
r = await row(b);
check('2 まだ来ていない ata は eta に', r.ata === null && await same(r.eta, f50), r);
const p82 = await at(-82);
await apply([{ id: c, ata: p82 }]);
await apply([{ id: c, ata: null }]);
r = await row(c);
check('2 来た ata は消さない', await same(r.ata, p82), r);

// 3. 前の版で入ってしまった、まだ来ていない atd・ata は次の書き直しで外す
await db.exec(`update public.flight_schedule set atd = now() + interval '33 minutes', ata = now() + interval '150 minutes' where id = ${a}`);
await apply([{ id: a, dep_status: 'OnTime' }]);
r = await row(a);
check('3 残っていた未来の atd・ata を外す', r.atd === null && r.ata === null, r);
check('3 etd はそのまま', await same(r.etd, f35), r);

// 4. 権限と設定
check('4 anon は実行できない', String(await as('anon', `select public.apply_flight_status('[]'::jsonb)`)).startsWith('ERROR'));
check('4 authenticated は実行できない', String(await as('authenticated', `select public.apply_flight_status('[]'::jsonb)`)).startsWith('ERROR'));
const cfg = (await one(`select proconfig from pg_proc where proname = 'apply_flight_status'`)).proconfig;
check('4 lock_timeout は 10s のまま', (cfg ?? []).includes('lock_timeout=10s'), cfg);
check('4 返す数は書き直した行の数', (await apply([{ id: a }, { id: b }, { id: 999999 }])).n === 2);

console.log(bad ? `NG ${bad}` : 'すべてOK');
process.exit(bad ? 1 : 0);
