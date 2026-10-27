// 到着予想の学習：空港ごとに地上走行と寄り道を決め直す。10便より少なければ変えない。寄り道は前に変えた後の記録だけで決める（10/26 から：2日分・40便そろってから3割だけ。くわしくは t45）
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
const d0 = `(now() at time zone 'Asia/Tokyo')::date`;
const add = async (fl, arr, src, early, n, ago = '1 hour') => { for (let i = 0; i < n; i++) await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, ata, ata_src, eta30)
  values (${d0}, '${fl}${i}', 'XXX', '${arr}', now() - interval '3 hours', now() - interval '2 hours', now() - interval '${ago}', '${src}', now() - interval '${ago}' - interval '${early} minutes')`); };
// 熊本（記録の少ない空港）：搭乗口とのずれ −6分が12便 → 地上走行 6
await add('JL1', 'KMJ', 'odpt', 6, 12);
// 宮崎：9便だけ → 変えない（表にない）
await add('JL2', 'KMI', 'odpt', 9, 9);
// 羽田：着陸とのずれ −4分（前に変えた後）が12便、搭乗口とのずれ −14分が12便 → 地上走行 10。寄り道は12便（1日分）なので、まだ変えない
await add('NH1', 'HND', 'adsb', 4, 12);
await add('NH2', 'HND', 'odpt', 14, 12);
// 羽田の古い記録（前に変える前）は寄り道に使わない
await db.exec(`update public.eta_calib set extra_at = now() - interval '2 hours' where iata = 'HND'`);
await add('NH3', 'HND', 'adsb', 30, 5, '5 hours');
const n = (await db.query(`select public.refresh_eta_calib() as n`)).rows[0].n;
const row = async (k) => (await db.query(`select taxi, extra from public.eta_calib where iata = '${k}'`)).rows[0];
const kmj = await row('KMJ'), hnd = await row('HND'), kmi = await row('KMI');
check('記録の少ない空港も、搭乗口とのずれから地上走行を学ぶ', kmj && Number(kmj.taxi) === 6, kmj);
check('10便より少なければ変えない', Number(kmi.taxi) === 2, kmi);
check('羽田：地上走行は2つの差', Number(hnd.taxi) === 10, hnd);
check('羽田：寄り道は、2日分・40便そろうまで変えない', Number(hnd.extra) === 10, hnd);
check('地上走行の目安の関数も学んだ値を使う', (await db.query(`select public.taxi_in_min('KMJ') as t`)).rows[0].t === 6);
await db.exec('set role anon'); const l = (await db.query(`select public.eta_calib_list() as l`)).rows[0].l; await db.exec('reset role');
check('学んだ値はだれでも見られる', Array.isArray(l) && l.some((x) => x.iata === 'KMJ'), l);
if (bad) process.exit(1);
