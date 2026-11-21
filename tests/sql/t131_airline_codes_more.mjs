// 呼び出し符号の記号の表に会社を足す（移行 192）：airline_codes
//   1. 足した会社が入る（TOK→BV・AHX→MZ・EOK→RF・APZ→YP など34社）。どれも odpt = false
//   2. 今ある行は変えない（JAL→JL・ANA→NH は odpt = true のまま、行の数は 86＋34）
//   3. Edge Functions の flight_watch.ts の PREFIX にある呼び出し符号の記号は、みな表にある（PREFIX と表をそろえる）
//   4. RLS は今までどおり：anon・authenticated は読めるが書けない
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
const rows = async (sql, p) => (await db.query(sql, p)).rows;
const as = async (role, sql, p) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql, p); return r.rows; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };

const m = Object.fromEntries((await rows(`select icao, iata, odpt from public.airline_codes`)).map((r) => [r.icao, r]));
for (const [icao, iata] of [['TOK', 'BV'], ['AHX', 'MZ'], ['EOK', 'RF'], ['APZ', 'YP'], ['FDX', 'FX'], ['CSS', 'O3']]) {
  check(`${icao} → ${iata}（odpt = false）`, m[icao]?.iata === iata && m[icao]?.odpt === false, m[icao]);
}
check('今ある行は変えない（JAL→JL・ANA→NH は odpt = true）', m.JAL?.iata === 'JL' && m.JAL.odpt === true && m.ANA?.iata === 'NH' && m.ANA.odpt === true, [m.JAL, m.ANA]);
check('今ある行は変えない（SKY→BC・ADO→HD・TGW→TR・TZP→ZG・NCA→KZ）',
  m.SKY?.iata === 'BC' && m.ADO?.iata === 'HD' && m.TGW?.iata === 'TR' && m.TZP?.iata === 'ZG' && m.NCA?.iata === 'KZ', [m.SKY, m.ADO, m.TGW, m.TZP, m.NCA]);
check('行の数は 86＋34 = 120', Object.keys(m).length === 120, Object.keys(m).length);

// flight_watch.ts の PREFIX の呼び出し符号の記号がみな表にある
const src = fs.readFileSync(new URL('../../supabase/functions/_shared/flight_watch.ts', import.meta.url), 'utf8');
const block = src.slice(src.indexOf('const PREFIX'), src.indexOf('};', src.indexOf('const PREFIX')));
const icaos = [...block.matchAll(/"([A-Z]{3})"/g)].map((x) => x[1]);
const missing = [...new Set(icaos)].filter((c) => !m[c]);
check(`PREFIX の呼び出し符号の記号（${new Set(icaos).size}）がみな表にある`, icaos.length > 100 && missing.length === 0, missing);

const r = await as('anon', `select count(*)::int c from public.airline_codes where icao = 'TOK'`);
check('anon は読める', Array.isArray(r) && r[0].c === 1, r);
for (const role of ['anon', 'authenticated']) {
  const w = await as(role, `insert into public.airline_codes (icao, iata) values ('ZZZ', 'ZZ')`);
  check(`${role} は書けない`, typeof w === 'string' && /permission denied|row-level security/.test(w), w);
}

console.log(bad ? `NG ${bad}` : 'すべて OK');
process.exit(bad ? 1 : 0);
