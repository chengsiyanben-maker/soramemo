// 空港のデータを作る元を書き出す（data/ap-shape。tools/ap_shape.py の 1）
//   node tools/ap_master_dump.mjs [出力フォルダ（既定 data/ap_shape/raw）]
//   1. master.json：移行を全部流した模擬のデータベース（PGlite）の airports・terminals（本番の表と同じ中身。本番にはつながない）
//   2. aip_rwy.json：運用タブの AIP から作った滑走路の線（supabase/functions/_shared/ops_core.js の OPS_AIRPORTS[].rwy）
//   PGlite は tests/sql の node_modules のものを使う（cd tests/sql && npm install のあと）
import fs from 'fs';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = process.argv[2] || path.join(root, 'data', 'ap_shape', 'raw');
fs.mkdirSync(out, { recursive: true });
const { PGlite } = await import(pathToFileURL(path.join(root, 'tests', 'sql', 'node_modules', '@electric-sql', 'pglite', 'dist', 'index.js')).href);
const db = new PGlite(); const dir = path.join(root, 'supabase', 'migrations');
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select null::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select '{}'::jsonb $$;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(path.join(dir, f), 'utf8'));
const airports = (await db.query(`select id, name, icao, iata, category, prefecture, lat, lon, radius_m, rare, game_target, extra_kind from public.airports order by id`)).rows;
const terminals = (await db.query(`select id, airport_id, name, tag, lat, lon, stamp_m from public.terminals order by id`)).rows;
fs.writeFileSync(path.join(out, 'master.json'), JSON.stringify({ airports, terminals }, null, 1) + '\n');

// ops_core.js は export のある素の JS なので、.mjs に写して読む
const tmp = path.join(out, '.ops_core.mjs');
fs.copyFileSync(path.join(root, 'supabase', 'functions', '_shared', 'ops_core.js'), tmp);
const { OPS_AIRPORTS } = await import(pathToFileURL(tmp).href);
fs.unlinkSync(tmp);
const aip = {};
for (const [k, v] of Object.entries(OPS_AIRPORTS)) if (v.rwy) aip[k] = { icao: v.icao, rwy: v.rwy.map((r) => [r[0], r[1], r[2], r[4], r[5], r[6], r[8] ?? null]) };
fs.writeFileSync(path.join(out, 'aip_rwy.json'), JSON.stringify(aip, null, 1) + '\n');
console.log(`空港 ${airports.length}・ターミナル ${terminals.length}・AIP の線がある空港 ${Object.keys(aip).length} を ${out} に書いた`);
