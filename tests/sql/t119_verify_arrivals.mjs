// OpenSky の置き換えの1歩目（移行 180）：verify_arrivals が全機の記録（reg_legs）から OpenSky と同じ形の到着の一覧を返す
//   1. 到着の空港（ICAO）・時間帯（最後に見えた時刻）で絞る・出発の空港は ICAO に直す・出発の分からない行は返さない
//   2. 日をまたぐ（日本時間の前の日の行も見る）・窓は2日まで・知らない空港は空
//   3. 照合の決まり（match）にそのまま渡せる形（項目の名前・UNIX秒）
//   4. 権限：service_role だけ。表と RLS は変えない
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
const as = async (role, sql, p) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql, p); return r.rows; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const arr = async (icao, b, e) => { const r = await as('service_role', 'select public.verify_arrivals($1, $2::timestamptz, $3::timestamptz) j', [icao, b, e]); return Array.isArray(r) ? r[0].j : r; };

const ap = (await db.query(`select icao, iata from public.airports where iata in ('HND','CTS','FUK') order by iata`)).rows;
check('空港の表に羽田・新千歳・福岡がある（ICAO つき）', ap.length === 3 && ap.every((a) => /^[A-Z]{4}$/.test(a.icao)), ap);
const icao = Object.fromEntries(ap.map((a) => [a.iata, a.icao]));

await db.exec(`insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr) values
  ('JA01XJ', 'JAL501', '2026-10-03', 'B738', '2026-10-03 08:32+09', '2026-10-03 09:58+09', 'HND', 'CTS'),
  ('JA02XJ', 'JAL503', '2026-10-03', 'B738', '2026-10-03 09:30+09', '2026-10-03 11:00+09', 'HND', 'CTS'),
  ('JA03XJ', 'JAL505', '2026-10-03', 'B738', '2026-10-03 08:40+09', '2026-10-03 09:50+09', null, 'CTS'),
  ('JA04XJ', 'JAL305', '2026-10-03', 'B738', '2026-10-03 07:30+09', '2026-10-03 09:20+09', 'HND', 'FUK'),
  ('JA05XJ', 'JAL519', '2026-10-02', 'B738', '2026-10-02 22:40+09', '2026-10-03 00:20+09', 'HND', 'CTS')`);

let j = await arr(icao.CTS, '2026-10-03 07:40+09', '2026-10-03 10:25+09');
check('到着の空港と時間帯で絞る（出発の分からない行・別の空港・窓の外は返さない）', Array.isArray(j) && j.length === 1 && j[0].callsign === 'JAL501', j);
const one = j[0];
check('OpenSky と同じ項目の名前・出発は ICAO・UNIX秒', one && JSON.stringify(Object.keys(one).sort()) === JSON.stringify(['callsign', 'estArrivalAirport', 'estDepartureAirport', 'firstSeen', 'icao24', 'lastSeen'])
  && one.icao24 === 'JA01XJ' && one.estDepartureAirport === icao.HND && one.estArrivalAirport === icao.CTS
  && one.firstSeen === Date.parse('2026-10-03T08:32:00+09:00') / 1000 && one.lastSeen === Date.parse('2026-10-03T09:58:00+09:00') / 1000, one);
j = await arr(icao.CTS.toLowerCase(), '2026-10-03 00:00+09', '2026-10-03 12:00+09');
check('ICAO は小文字でもよい・日本時間の前の日の行（0時過ぎに着いた便）も見る・着いた順', Array.isArray(j) && j.map((x) => x.callsign).join(',') === 'JAL519,JAL501,JAL503', j);
j = await arr(icao.CTS, '2026-09-01 00:00+09', '2026-10-30 00:00+09');
check('窓は2日まで（それより先は見ない）', Array.isArray(j) && j.length === 0, j);
j = await arr('XXXX', '2026-10-03 00:00+09', '2026-10-03 12:00+09');
check('知らない空港は空の配列', Array.isArray(j) && j.length === 0, j);

// match（verify.ts）と同じ決まりで当てはまるか（窓は出発の30分前〜到着の20分後・出発空港の一致・便名の一致）
const begin = Date.parse('2026-10-03T07:40:00+09:00') / 1000, end = Date.parse('2026-10-03T10:25:00+09:00') / 1000;
const hit = (await arr(icao.CTS, '2026-10-03 07:40+09', '2026-10-03 10:25+09')).find((a) => a.estDepartureAirport === icao.HND && a.lastSeen >= begin && a.lastSeen <= end && a.firstSeen >= begin - 3600 && a.callsign.trim() === 'JAL501');
check('照合の決まりにそのまま当てはまる', !!hit, hit);

for (const role of ['anon', 'authenticated']) {
  const r = await as(role, `select public.verify_arrivals('RJCC', now() - interval '1 hour', now())`);
  check(`${role} は呼べない`, typeof r === 'string' && /permission denied/.test(r), r);
}
const rls = (await db.query(`select relrowsecurity from pg_class where relname = 'reg_legs'`)).rows[0];
check('reg_legs の RLS は有効のまま', rls.relrowsecurity === true, rls);
const n = (await db.query(`select count(*)::int c from public.reg_legs`)).rows[0].c;
check('記録は1行も消えない（読むだけ）', n === 5, n);

console.log(bad ? `NG ${bad}` : 'すべて OK'); process.exit(bad ? 1 : 0);
