// 三沢・岩国の民間ターミナルの行（移行 term_misawa_iwakuni）
//   1. terminals に MSJ-T・IWK-T が1行ずつ。stamp_m は 0（ターミナルの印は出さない）。ほかの行の stamp_m は変わらない
//   2. stamp_m の制約は 0〜1500（負の値・1501 は入らない）
//   3. airports の radius_m は変えない（経営の数字を動かさない）
//   4. 判定（_shared/judge.ts の locate を、表の行でそのまま呼ぶ）：ターミナルビルの前は範囲の中・印はターミナルなし。ビルから 900m 先は今までどおり外
//   5. RLS：anon も読める・書けない
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
const files = fs.readdirSync(dir).filter(f => f.endsWith('.sql')).sort();
const mine = files.find(f => f.endsWith('_term_misawa_iwakuni.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
check('移行がある', !!mine);
const db = new PGlite();
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select null::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select '{}'::jsonb $$;
grant usage on schema public, auth to anon, authenticated, service_role;`);
for (const f of files) { if (f === mine) { var before = (await db.query(`select id, stamp_m from public.terminals order by id`)).rows; var rad = (await db.query(`select id, radius_m from public.airports order by id`)).rows; } await db.exec(fs.readFileSync(dir + f, 'utf8')); }
const T = (await db.query(`select * from public.terminals order by id`)).rows;
const msj = T.find(t => t.id === 'MSJ-T'), iwk = T.find(t => t.id === 'IWK-T');
check('MSJ-T（三沢・airport 92・stamp_m 0）', msj && msj.airport_id === 92 && msj.stamp_m === 0, msj);
check('IWK-T（岩国・airport 96・stamp_m 0）', iwk && iwk.airport_id === 96 && iwk.stamp_m === 0, iwk);
check('ほかの行の stamp_m は変わらない', JSON.stringify(before) === JSON.stringify(T.filter(t => !['MSJ-T', 'IWK-T'].includes(t.id)).map(t => ({ id: t.id, stamp_m: t.stamp_m }))));
check('airports の radius_m は変わらない', JSON.stringify(rad) === JSON.stringify((await db.query(`select id, radius_m from public.airports order by id`)).rows));
for (const v of [-1, 1501]) { let e = ''; try { await db.exec(`update public.terminals set stamp_m = ${v} where id = 'MSJ-T'`); } catch (x) { e = x.message; } check(`stamp_m = ${v} は入らない`, /check/.test(e), e); }
await db.exec(fs.readFileSync(dir + mine, 'utf8')); check('2回流しても行は増えない', (await db.query(`select count(*)::int n from public.terminals where id in ('MSJ-T','IWK-T')`)).rows[0].n === 2);

// 判定：judge.ts をそのまま読み込み、表の行で呼ぶ
const { locate, km } = await import('../../supabase/functions/_shared/judge.ts');
// 関数 checkin の loadMaster と同じ読み方（game_target か番外編の行・extra は game_target でない番外編）
const A = (await db.query(`select id, name, coalesce(iata, icao, '') iata, lat, lon, radius_m, rare, (not coalesce(game_target, false) and extra_kind is not null) extra
  from public.airports where game_target or extra_kind is not null`)).rows;
const off = (p, dn, de) => ({ lat: p.lat + dn / 111320, lon: p.lon + de / (111320 * Math.cos(p.lat * Math.PI / 180)) });
for (const [t, ap] of [[msj, 92], [iwk, 96]]) {
  const front = locate(off(t, 0, 50), A, T);
  check(`${t.short}：ビルの前（50m）は ${ap} の範囲の中・ターミナルの印なし`, front.within && front.airport.id === ap && front.terminal === null, { id: front.airport.id, within: front.within, term: front.terminal?.id });
  const at0 = locate(off(t, 0.5, 0.5), A, T);
  check(`${t.short}：ビルのほぼ真上でも印は出さない（stamp_m 0）`, at0.terminal === null, at0.terminal?.id);
  const airportPt = A.find(a => a.id === ap);
  // ビルから空港の点と反対向きに 900m：ターミナルからも空港の点からも外
  const dn = (t.lat - airportPt.lat) * 111320, de = (t.lon - airportPt.lon) * 111320 * Math.cos(t.lat * Math.PI / 180), n = Math.hypot(dn, de);
  const far = off(t, dn / n * 900, de / n * 900);
  const r = locate(far, A, T);
  check(`${t.short}：ビルから外向きに 900m は範囲の外（${Math.round(km(far, airportPt) * 1000)}m）`, !(r.within && r.airport.id === ap), { id: r.airport.id, within: r.within });
}
// RLS
await db.exec(`grant select on public.terminals to anon; set role anon`);
const n = (await db.query(`select count(*)::int n from public.terminals where id in ('MSJ-T','IWK-T')`)).rows[0].n;
let we = ''; try { await db.exec(`insert into public.terminals (id, airport_id, short, name, tag, lat, lon) values ('X', 92, 'x', 'x', 'x', 0, 0)`); } catch (x) { we = x.message; }
await db.exec('reset role');
check('anon は2行とも読める', n === 2, n);
check('anon は書けない', /denied|policy/.test(we), we);
console.log(bad ? `NG ${bad}` : 'すべて OK'); process.exit(bad ? 1 : 0);
