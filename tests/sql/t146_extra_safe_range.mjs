// 番外編の判定範囲の見直し案（移行 extra_safe_range）
//   1. 変わるのは番外編（extra_kind あり・game_target でない）の radius_m だけ。今より小さくなる行はない
//   2. 86空港（game_target）の radius_m と、すべての行の airport_size（経営の空港の大きさ）は変わらない
//   3. 案を作ったときの値（old_m）と違う行は変えない（手で直した値を上書きしない）。2回流しても同じ
//   4. 道具 tools/extra_safe_range.py の結果（docs の表）と移行の値が一致する（表 docs/pm/extra-safe-range.json）
//   5. RLS：airports は anon が読める・書けない（今のまま）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
const files = fs.readdirSync(dir).filter(f => f.endsWith('.sql')).sort();
const mine = files.find(f => f.endsWith('_extra_safe_range.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 300)); if (!ok) bad++; };
check('移行がある', !!mine);
const sql = fs.readFileSync(dir + mine, 'utf8');
const boot = async () => { const db = new PGlite(); await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select null::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select '{}'::jsonb $$;
grant usage on schema public, auth to anon, authenticated, service_role;`); return db; };
const Q = `select id, radius_m, public.airport_size(radius_m) sz, extra_kind, game_target from public.airports order by id`;
const db = await boot();
let before;
for (const f of files) { if (f === mine) before = (await db.query(Q)).rows; await db.exec(fs.readFileSync(dir + f, 'utf8')); }
const after = (await db.query(Q)).rows, B = Object.fromEntries(before.map(r => [r.id, r]));
const changed = after.filter(r => r.radius_m !== B[r.id].radius_m);
check('変わった行がある（10か所）', changed.length === 10, changed.length);
check('変わったのは番外編だけ', changed.every(r => r.extra_kind && !r.game_target), changed.filter(r => !(r.extra_kind && !r.game_target)));
check('小さくなった行はない', after.every(r => r.radius_m >= B[r.id].radius_m));
check('86空港の radius_m は変わらない', after.filter(r => r.game_target).every(r => r.radius_m === B[r.id].radius_m));
check('airport_size（経営の空港の大きさ）はどの行も変わらない', after.every(r => Number(r.sz) === Number(B[r.id].sz)), after.filter(r => Number(r.sz) !== Number(B[r.id].sz)));
check('上限 3000m を超えない', changed.every(r => r.radius_m <= 3000));
await db.exec(sql); check('2回流しても同じ', JSON.stringify((await db.query(Q)).rows) === JSON.stringify(after));
// 手で直した値は上書きしない
const db2 = await boot();
for (const f of files) { if (f === mine) await db2.exec(`update public.airports set radius_m = 1234 where id = 1029`); await db2.exec(fs.readFileSync(dir + f, 'utf8')); }
check('案を作ったときと違う値（手で直した嘉手納 1234m）は変えない', (await db2.query(`select radius_m from public.airports where id = 1029`)).rows[0].radius_m === 1234);
// 表との一致
const tbl = JSON.parse(fs.readFileSync(new URL('../../docs/pm/extra-safe-range.json', import.meta.url), 'utf8'));
const want = Object.fromEntries(tbl.filter(x => x.new_m > x.radius_m).map(x => [x.id, x.new_m]));
check('移行の値が表（extra-safe-range.json）の新しい範囲と同じ', changed.length === Object.keys(want).length && changed.every(r => want[r.id] === r.radius_m), { want, got: changed.map(r => [r.id, r.radius_m]) });
check('表の今の範囲は移行の前の値と同じ', tbl.every(x => B[x.id] && B[x.id].radius_m === x.radius_m));
// RLS
await db.exec(`grant select, update on public.airports to anon; set role anon`);
const n = (await db.query(`select count(*)::int n from public.airports where id = 1029`)).rows[0].n;
const up = await db.query(`update public.airports set radius_m = 1 where id = 1029`).then(r => r.affectedRows).catch(e => 'ERR ' + e.message);
await db.exec('reset role');
check('anon は読める', n === 1, n);
check('anon は書けない（RLS で0行か拒否）', up === 0 || String(up).startsWith('ERR'), up);
console.log(bad ? `NG ${bad}` : 'すべて OK'); process.exit(bad ? 1 : 0);
