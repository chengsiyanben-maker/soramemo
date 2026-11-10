// 図鑑の1空港のデータ欄（airport_facts）：供用開始の年と滑走路。出典は国土交通省「空港一覧」（令和8年9月1日現在）
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
const q = async (s, p) => (await db.query(s, p)).rows;

// 1. 行のある空港・ない空港
const cnt = (await q(`select count(*)::int as n, count(opened_year)::int as y,
  count(*) filter (where a.extra_kind is not null)::int as extra, count(*) filter (where a.category like '%会社管理%')::int as company
  from public.airport_facts f join public.airports a on a.id = f.airport_id`))[0];
check('82空港に行（番外編・会社管理の4空港はなし）', cnt.n === 82 && cnt.extra === 0 && cnt.company === 0, cnt);
const none = (await q(`select array_agg(a.id order by a.id) as ids from public.airports a where a.extra_kind is null and not exists (select 1 from public.airport_facts f where f.airport_id = a.id)`))[0].ids;
check('行がないのは成田・中部・関西・伊丹・千歳だけ', JSON.stringify(none) === JSON.stringify([1, 2, 3, 4, 91]), none);
check('供用開始の年がないのは羽田・三沢・岩国の3つだけ', cnt.y === 79 && JSON.stringify((await q(`select array_agg(airport_id order by airport_id) as a from public.airport_facts where opened_year is null`))[0].a) === JSON.stringify([5, 92, 96]));

// 2. 中身の見本（PDF と照らした値）
const get = async (id) => (await q(`select opened_year, runways, source, source_ref from public.airport_facts where airport_id = $1`, [id]))[0];
const hnd = await get(5);
check('羽田：滑走路4本（C は 3,360m×60m）', hnd.runways.length === 4 && hnd.runways.map((r) => r.name).join('') === 'ABCD' && hnd.runways[2].length_m === 3360 && hnd.runways[2].width_m === 60, hnd);
const cts = await get(6), ngo = await get(84), ishigaki = await get(80), shonai = await get(38), fuk = await get(16);
check('和暦を西暦に：新千歳 昭和63→1988・小牧 平成17→2005・庄内 平成3→1991・石垣 昭和47→1972', cts.opened_year === 1988 && ngo.opened_year === 2005 && shonai.opened_year === 1991 && ishigaki.opened_year === 1972, [cts.opened_year, ngo.opened_year, shonai.opened_year, ishigaki.opened_year]);
check('1本だけの空港は名前が null', ngo.runways.length === 1 && ngo.runways[0].name === null && ngo.runways[0].length_m === 2740);
check('福岡の C・D はヘリポートと書いてある', fuk.runways.filter((r) => /ヘリポート/.test(r.note ?? '')).length === 2 && fuk.runways.find((r) => r.name === 'B').length_m === 2500, fuk.runways);
check('出典：国交省の PDF の URL と基準日', hnd.source === 'mlit_airport_list' && hnd.source_ref === 'https://www.mlit.go.jp/koku/content/002021263.pdf（令和8年9月1日現在）' && /002021265\.pdf/.test(shonai.source_ref), hnd.source_ref);
const sane = (await q(`select count(*)::int as n from public.airport_facts, jsonb_array_elements(runways) r where (r->>'length_m')::int not between 30 and 4000 or (r->>'width_m')::int not between 20 and 60`))[0].n;
check('長さ・幅はどれも見込みの範囲', sane === 0, sane);

// 3. 決まり（形の違う中身は入らない）
const bads = [
  [`update public.airport_facts set opened_year = 1800 where airport_id = 6`, '年が古すぎる'],
  [`update public.airport_facts set runways = '{"a":1}' where airport_id = 6`, '配列でない'],
  [`update public.airport_facts set runways = '[{"name":"A","length_m":"3000","width_m":60}]' where airport_id = 6`, '長さが字'],
  [`update public.airport_facts set runways = '[{"name":"A","width_m":60}]' where airport_id = 6`, '長さがない'],
  [`update public.airport_facts set runways = '[{"name":"A","length_m":9000,"width_m":60}]' where airport_id = 6`, '長すぎる'],
  [`update public.airport_facts set source = 'wikipedia' where airport_id = 6`, '知らない出典'],
  [`insert into public.airport_facts (airport_id, source_ref) values (999999, 'x')`, '空港にない番号'],
];
let refused = 0; for (const [s] of bads) { try { await db.exec(s); } catch { refused++; } }
check('形の違う中身（7通り）はどれも断る', refused === bads.length, refused);

// 4. 直すと updated_at が新しくなる・もう一度流しても同じ
await db.exec(`update public.airport_facts set updated_at = '2020-01-01' where airport_id = 6`);
await db.exec(`update public.airport_facts set opened_year = opened_year where airport_id = 6`);
check('直すと updated_at が今に', (await q(`select updated_at > now() - interval '1 minute' as ok from public.airport_facts where airport_id = 6`))[0].ok);
const before = JSON.stringify(await q(`select airport_id, opened_year, runways, source_ref from public.airport_facts order by 1`));
await db.exec(fs.readFileSync(dir + files.find((f) => /_airport_facts\.sql$/.test(f)), 'utf8'));
check('もう一度流しても同じ', JSON.stringify(await q(`select airport_id, opened_year, runways, source_ref from public.airport_facts order by 1`)) === before);

// 5. RLS：誰でも読める・誰も書けない
for (const role of ['anon', 'authenticated']) {
  await db.exec(`set role ${role}`);
  const n = (await q(`select count(*)::int as n from public.airport_facts`))[0].n;
  let w = 0;
  for (const s of [`update public.airport_facts set opened_year = 2000 where airport_id = 6`, `delete from public.airport_facts where airport_id = 6`, `insert into public.airport_facts (airport_id, source_ref) values (1, 'x')`]) { try { await db.exec(s); } catch { w++; } }
  await db.exec('reset role');
  check(`${role} は読めて（82行）、書けない`, n === 82 && w === 3, { n, w });
}
const rls = (await q(`select relrowsecurity from pg_class where oid = 'public.airport_facts'::regclass`))[0].relrowsecurity;
check('RLS が有効', rls === true);

// 6. 空港が消えたら一緒に消える
await db.exec(`delete from public.airports where id = 97 and not exists (select 1 from public.checkins where airport_id = 97)`);
const left = (await q(`select (select count(*)::int from public.airports where id = 97) as a, (select count(*)::int from public.airport_facts where airport_id = 97) as f`))[0];
check('空港の行を消すと、データ欄の行も消える', left.a === 0 && left.f === 0, left);
if (bad) process.exit(1);
