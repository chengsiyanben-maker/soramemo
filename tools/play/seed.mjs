// 試遊版のデータベースを作る：本番と同じマイグレーション → 試遊用の SQL（play.sql） → 見本の利用者 → スイッチをオン → 1つのファイルに書き出す
//   node tools/play/seed.mjs <書き出す先.tar.gz>
import { PGlite } from '../../tests/sql/node_modules/@electric-sql/pglite/dist/index.js';
import fs from 'fs';
const ROOT = new URL('../../', import.meta.url).pathname;
export const UID = '00000000-0000-4000-8000-00000000c0de';
export async function buildDb() {
  const db = new PGlite();
  await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
  const dir = ROOT + 'supabase/migrations/';
  for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
  await db.exec(fs.readFileSync(ROOT + 'tools/play/play.sql', 'utf8'));
  await db.exec(`update ops.flags set value = 'true'::jsonb where key in ('game_released', 'co_v3')`);
  await db.query(`select play.seed($1)`, [UID]);
  await db.exec(`select public.co3_route_real_refresh(); select public.co_size_refresh();`);
  return db;
}
if (process.argv[1] && process.argv[1].endsWith('seed.mjs')) {
  const t0 = Date.now();
  const db = await buildDb();
  const n = (await db.query(`select (select count(*) from flights) f, (select count(*) from flight_history) h, (select count(*) from checkins) c`)).rows[0];
  console.log('見本：フライト', n.f, '便の記録', n.h, 'チェックイン', n.c, (Date.now() - t0) + 'ms');
  if (process.argv[2]) { const blob = await db.dumpDataDir('gzip'); fs.writeFileSync(process.argv[2], Buffer.from(await blob.arrayBuffer())); console.log('書き出し', blob.size); }
}
