// 機体の位置に進行方向（trk）を足す（移行 156）：列・範囲の確かめ・前の列での書き込みはそのまま・RLS は今のまま
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const mig = fs.readFileSync(dir + files.find((f) => f.endsWith('_live_positions_trk.sql')), 'utf8');

const col = (await db.query(`select data_type, is_nullable from information_schema.columns where table_schema = 'public' and table_name = 'live_positions' and column_name = 'trk'`)).rows[0];
check('trk の列（smallint・空でよい）', col && col.data_type === 'smallint' && col.is_nullable === 'YES', col);
await db.exec(`insert into public.live_positions (callsign, hex, lat, lon, alt_ft, ground, fpm, kt, type, reg, seen_at) values ('JAL123', '84abcd', 35.5, 139.8, 3000, false, -800, 180, 'B738', 'JA301J', now())`);
check('前の列だけの書き込みはそのまま（trk は空）', (await db.query(`select trk from public.live_positions where callsign = 'JAL123'`)).rows[0].trk === null);
await db.exec(`insert into public.live_positions (callsign, lat, lon, seen_at, trk) values ('ANA45', 35.6, 139.9, now(), 359) on conflict (callsign) do update set trk = excluded.trk`);
check('0〜359 は入る', (await db.query(`select trk from public.live_positions where callsign = 'ANA45'`)).rows[0].trk === 359);
let e = ''; try { await db.exec(`update public.live_positions set trk = 360 where callsign = 'ANA45'`); } catch (x) { e = x.message; }
check('360 は断る', /check/i.test(e), e);
const rls = (await db.query(`select relrowsecurity from pg_class where oid = 'public.live_positions'::regclass`)).rows[0].relrowsecurity;
let denied = 0;
for (const role of ['anon', 'authenticated']) { await db.exec(`set role ${role}`); try { await db.query(`select trk from public.live_positions`); } catch { denied++; } await db.exec('reset role'); }
check('RLS は有効のまま・anon と authenticated は読めない', rls === true && denied === 2, { rls, denied });
check('移行は列を足すだけ（消す・書き換える文がない）', !/\b(delete|drop|truncate|update)\b/i.test(mig.replace(/--.*$/gm, '')), mig);
check('行は消えない', (await db.query(`select count(*)::int as n from public.live_positions`)).rows[0].n === 2);
if (bad) process.exit(1);
