// 撮影地の情報：羽田の6地点が入っている・誰でも読める・表には直接書けない・運営者だけが関数で直せる・開いている時間の形
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

await db.exec('set role anon');
const rows = (await db.query(`select name, open_kind, open_from::text as f, open_to::text as t, cardinality(rules) as nr, jsonb_array_length(sources) as ns, checked_on::text as d from public.spot_info where iata = 'HND' order by name`)).rows;
let denied = false; try { await db.query(`insert into public.spot_info (iata, name, checked_on) values ('HND', 'x', now())`); } catch { denied = true; }
let denied2 = false; try { await db.query(`select public.spot_info_put('{"iata":"HND","name":"x"}'::jsonb)`); } catch { denied2 = true; }
await db.exec('reset role');
const by = Object.fromEntries(rows.map((r) => [r.name, r]));
const names = ['第1ターミナル 展望デッキ', '第2ターミナル 展望デッキ', '第3ターミナル 展望デッキ', '城南島海浜公園', '京浜島つばさ公園', '浮島町公園'];
check('羽田の6地点（アプリの撮影地と同じ名前）', names.every((n) => by[n]), rows.map((r) => r.name));
check('開いている時間：第1は 6:30〜22:00・第3は24時間・城南島は記載なし', by[names[0]]?.open_kind === 'hours' && by[names[0]].f === '06:30:00' && by[names[0]].t === '22:00:00' && by[names[2]]?.open_kind === 'always' && by[names[3]]?.open_kind === 'unknown', rows);
check('どの地点にも出典と確認日', rows.every((r) => r.ns >= 1 && r.d === '2026-11-02'), rows);
check('誰でも読めるが、表には直接書けない', rows.length === 6 && denied);
check('運営者でないと直せない', denied2);
// アプリの撮影地の名前と合っているか（src/index.html の OPS_SPOTS の HND）
const html = fs.readFileSync(new URL('../../src/index.html', import.meta.url), 'utf8');
const hnd = /HND:\[(.+?)\]\],/.exec(html.slice(html.indexOf('const OPS_SPOTS = {')))?.[1] ?? '';
check('アプリの撮影地の名前と同じ', names.every((n) => hnd.includes(`"${n}"`)), hnd.slice(0, 120));
if (bad) process.exit(1);
