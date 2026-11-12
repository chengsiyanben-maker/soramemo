// 番外編のヘリポート（extra_kind = 'heli'、移行 163）：公共用12か所・読みがある・ほかの空港と印の円が重ならない・誰でも読めて書けない・もう一度流しても同じ
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const mine = files.find(f => f.endsWith('_heliports.sql'));
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));
// 本番の Supabase は public の表に anon・authenticated の select を既定で渡している（init.sql は書く権限だけを取り上げる）。ここでは手で同じにする
await db.exec(`grant select on public.airports to anon, authenticated`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const q = async (sql) => (await db.query(sql)).rows;
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const as = async (role, sql) => {
  try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; }
  finally { await db.exec(`reset role`); }
};
const isErr = (v) => String(v).startsWith('ERROR');

// 1. 12か所・番外編の形
const h = await q(`select id, name, icao, iata, category, prefecture, lat, lon, radius_m, game_target, rare from public.airports where extra_kind = 'heli' order by id`);
check('ヘリポートは12か所（5001〜5012）', h.length === 12 && h[0].id === 5001 && h[11].id === 5012, h.map(r => r.id));
check('どれも番外編の形（ゲームの対象外・IATA なし・珍しいでない・分類 heliport）', h.every(r => !r.game_target && r.iata === null && !r.rare && r.category === 'heliport'), h);
check('名前はどれも「ヘリポート」で終わる', h.every(r => r.name.endsWith('ヘリポート')), h.map(r => r.name));
const pref = { 5001: '北海道', 5002: '山形県', 5003: '栃木県', 5004: '群馬県', 5005: '群馬県', 5006: '東京都', 5007: '静岡県', 5008: '福井県', 5009: '三重県', 5010: '奈良県', 5011: '広島県', 5012: '鹿児島県' };
check('都道府県は国の一覧の所在地どおり', h.every(r => pref[r.id] === r.prefecture), h.map(r => [r.id, r.prefecture]));
check('ICAO は東京（RJTI）と広島（RJBH）だけ', JSON.stringify(h.filter(r => r.icao).map(r => [r.id, r.icao])) === JSON.stringify([[5006, 'RJTI'], [5011, 'RJBH']]), null);
check('位置は日本の中、半径は 600m（広島だけ 800m）', h.every(r => r.lat > 24 && r.lat < 46 && r.lon > 122 && r.lon < 154 && r.radius_m === (r.id === 5011 ? 800 : 600)), h);

// 2. ほかの空港と印の円が重ならない（球面の距離。番外編を含む全部と比べる）
const ov = await q(`select h.id hid, a.id aid, round((6371000 * 2 * asin(sqrt(power(sin(radians(a.lat - h.lat) / 2), 2) + cos(radians(h.lat)) * cos(radians(a.lat)) * power(sin(radians(a.lon - h.lon) / 2), 2))))::numeric) d, h.radius_m + a.radius_m r
  from public.airports h join public.airports a on a.id <> h.id where h.extra_kind = 'heli'
  and 6371000 * 2 * asin(sqrt(power(sin(radians(a.lat - h.lat) / 2), 2) + cos(radians(h.lat)) * cos(radians(a.lat)) * power(sin(radians(a.lon - h.lon) / 2), 2))) < h.radius_m + a.radius_m`);
check('ほかの空港・番外編と印の円が重ならない', ov.length === 0, ov);

// 3. 種類の決まり
check('種類の決まりは heli を受け付ける（今の5つ）', /'heli'/.test(await q1(`select pg_get_constraintdef(oid) from pg_constraint where conname = 'airports_extra_kind_check'`)), null);
check('知らない種類は断る', isErr(await as('service_role', `insert into public.airports (id, name, category, prefecture, lat, lon, radius_m, rare, game_target, extra_kind) values (5999, 'x', 'heliport', '東京都', 35, 139, 600, false, false, 'helipad')`)), null);
check('今までの番外編の数は変わらない（基地27・秘密5）', JSON.stringify(await q(`select extra_kind, count(*)::int n from public.airports where extra_kind in ('mil', 'secret') group by 1 order by 1`)) === JSON.stringify([{ extra_kind: 'mil', n: 27 }, { extra_kind: 'secret', n: 5 }]), null);

// 4. 読み
const y = await q(`select y.airport_id, y.yomi, y.index_yomi from public.airport_yomi y join public.airports a on a.id = y.airport_id where a.extra_kind = 'heli' order by 1`);
check('12か所すべてに読み（ひらがな・索引の読みは正式な読みの中にある）', y.length === 12 && y.every(r => /^[ぁ-ゖー]+$/.test(r.yomi) && r.yomi.endsWith('へりぽーと') && r.yomi.includes(r.index_yomi)), y);
check('airports の全行に読みがある（図鑑の決まり）', await q1(`select count(*)::int from public.airports a where not exists (select 1 from public.airport_yomi y where y.airport_id = a.id)`) === 0, null);

// 5. RLS
check('airports の RLS は有効のまま', await q1(`select relrowsecurity from pg_class where oid = 'public.airports'::regclass`) === true, null);
check('ログインしていない人もヘリポートを読める', await as('anon', `select count(*)::int from public.airports where extra_kind = 'heli'`) === 12, null);
check('ログインした人もヘリポートを読める', await as('authenticated', `select count(*)::int from public.airports where extra_kind = 'heli'`) === 12, null);
for (const role of ['anon', 'authenticated']) {
  check(`${role} は足せない`, isErr(await as(role, `insert into public.airports (id, name, category, prefecture, lat, lon, radius_m, rare, game_target, extra_kind) values (5998, 'x', 'heliport', '東京都', 35, 139, 600, false, false, 'heli')`)), null);
  const u = await as(role, `with u as (update public.airports set radius_m = 5000 where id = 5006 returning 1) select count(*)::int from u`);
  check(`${role} は直せない`, isErr(u) || u === 0, u);
  const d = await as(role, `with d as (delete from public.airports where id = 5006 returning 1) select count(*)::int from d`);
  check(`${role} は消せない`, isErr(d) || d === 0, d);
}
check('読みも anon は書けない', isErr(await as('anon', `update public.airport_yomi set yomi = 'あ' where airport_id = 5006`)) || await q1(`select yomi from public.airport_yomi where airport_id = 5006`) === 'とうきょうへりぽーと', null);

// 6. もう一度流しても同じ
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流しても12か所・読み12行のまま', await q1(`select count(*)::int from public.airports where extra_kind = 'heli'`) === 12 && await q1(`select count(*)::int from public.airport_yomi where airport_id between 5001 and 5012`) === 12, null);

console.log(bad ? `NG ${bad}` : 'すべて OK');
process.exit(bad ? 1 : 0);
