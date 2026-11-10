// 図鑑の索引の名前の読み（airport_yomi）：airports とアプリの空港の全部に1行・ひらがなだけ・誰でも読める・書けるのは運営だけ
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const as = async (role, sql) => {
  try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; }
  finally { await db.exec(`reset role`); }
};
const isErr = (v) => String(v).startsWith('ERROR');

check('RLS は有効', await q1(`select relrowsecurity from pg_class where relname = 'airport_yomi'`) === true, null);
const nAp = await q1(`select count(*)::int from public.airports`), nY = await q1(`select count(*)::int from public.airport_yomi`);
check('airports の全行に読みがある', nAp === nY && await q1(`select count(*)::int from public.airports a left join public.airport_yomi y on y.airport_id = a.id where y.airport_id is null`) === 0, { nAp, nY });

// アプリの空港（86空港の RAW と番外編の EXTRA_RAW）の id が全部ある
const html = fs.readFileSync(new URL('../../src/index.html', import.meta.url), 'utf8');
const ids = (name) => { const m = html.match(new RegExp(`const ${name} = (\\[\\[[\\s\\S]*?\\]\\]);`)); return m ? [...m[1].matchAll(/\[(\d+),"/g)].map(x => Number(x[1])) : []; };
const appIds = [...ids('RAW'), ...ids('EXTRA_RAW')];
check('アプリの空港の一覧が読めた（86空港＋番外編）', ids('RAW').length === 86 && ids('EXTRA_RAW').length > 50, appIds.length);
const have = new Set((await db.query(`select airport_id from public.airport_yomi`)).rows.map(r => r.airport_id));
const miss = appIds.filter(i => !have.has(i));
check('アプリの空港の全部に読みがある', miss.length === 0, miss);

// 中身
check('読みはひらがなと長音だけ', await q1(`select count(*)::int from public.airport_yomi where yomi !~ '^[ぁ-ゖー]+$' or index_yomi !~ '^[ぁ-ゖー]+$'`) === 0, null);
check('正式な読みは索引の読みを含む（はねだ・こまき・おかだま・いたみ・いばらき・よなご・すかいぽーとの3つは別）',
  await q1(`select count(*)::int from public.airport_yomi where strpos(yomi, index_yomi) = 0 and airport_id not in (4, 5, 84)`) === 0,
  (await db.query(`select airport_id, yomi, index_yomi from public.airport_yomi where strpos(yomi, index_yomi) = 0`)).rows);
check('羽田は「はねだ」で並び、「とうきょう」でも当たる', await q1(`select index_yomi || '/' || yomi || '/' || array_to_string(alt_yomi, ',') from public.airport_yomi where airport_id = 5`) === 'はねだ/とうきょうこくさいくうこう/とうきょう', null);
check('小値賀は「おぢか」（おじかでも当たる）', await q1(`select index_yomi || '/' || array_to_string(alt_yomi, ',') from public.airport_yomi where airport_id = 60`) === 'おぢか/おじか', null);
check('今は全部「手で付けた読み」', await q1(`select count(*)::int from public.airport_yomi where source <> 'manual'`) === 0, null);
// 読みで探す（アプリが手元でする形を SQL で）
const hit = async (s) => (await db.query(`select airport_id from public.airport_yomi where yomi like '%${s}%' or index_yomi like '${s}%' or exists (select 1 from unnest(alt_yomi) a where a like '${s}%') order by airport_id`)).rows.map(r => r.airport_id);
check('「せんとれあ」で中部', JSON.stringify(await hit('せんとれあ')) === '[2]', await hit('せんとれあ'));
check('「ちとせ」で新千歳・千歳空港・千歳基地', JSON.stringify(await hit('ちとせ')) === '[6,91,1001]', await hit('ちとせ'));

// 書く
check('ログインしていない人は読める', await as('anon', `select count(*)::int from public.airport_yomi`) === nY, null);
check('ログインした人も読める', await as('authenticated', `select count(*)::int from public.airport_yomi`) === nY, null);
check('ログインした人は書けない（足す）', isErr(await as('authenticated', `insert into public.airport_yomi (airport_id, yomi, index_yomi) values (1, 'あ', 'あ')`)), null);
check('ログインした人は書けない（直す）', isErr(await as('authenticated', `update public.airport_yomi set yomi = 'あ' where airport_id = 1`)), null);
check('ログインしていない人は消せない', isErr(await as('anon', `delete from public.airport_yomi where airport_id = 1`)), null);
check('運営は直せる', await as('service_role', `with u as (update public.airport_yomi set alt_yomi = '{なりたくうこう}' where airport_id = 1 returning 1) select count(*)::int from u`) === 1, null);
check('直すと updated_at が新しくなる', await q1(`select updated_at > (select min(updated_at) from public.airport_yomi) from public.airport_yomi where airport_id = 1`) === true, null);
check('カタカナは入れられない', isErr(await as('service_role', `update public.airport_yomi set yomi = 'ナリタ' where airport_id = 1`)), null);
check('空の読みは入れられない', isErr(await as('service_role', `update public.airport_yomi set index_yomi = '' where airport_id = 1`)), null);
check('別の読みに漢字は入れられない', isErr(await as('service_role', `update public.airport_yomi set alt_yomi = '{成田}' where airport_id = 1`)), null);
check('official は出典なしでは入れられない', isErr(await as('service_role', `update public.airport_yomi set source = 'official' where airport_id = 1`)), null);
check('official は出典があれば入れられる', !isErr(await as('service_role', `update public.airport_yomi set source = 'official', source_ref = '例' where airport_id = 1`)), null);

// もう一度流しても同じ（読みは上書き、数は変わらない）
const me = files.find(f => f.endsWith('_airport_yomi.sql'));
await db.exec(fs.readFileSync(dir + me, 'utf8'));
check('もう一度流しても行の数は同じで、読みは元に戻る', await q1(`select count(*)::int from public.airport_yomi`) === nY && await q1(`select array_length(alt_yomi, 1) is null from public.airport_yomi where airport_id = 1`) === true, null);

console.log(bad ? `NG ${bad}件` : 'すべて通過'); process.exit(bad ? 1 : 0);
