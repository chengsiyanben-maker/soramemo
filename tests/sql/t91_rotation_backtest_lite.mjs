// 運用の予想の比べる SQL の軽い版（docs/pm/rotation-backtest-lite.sql）：読むだけ・今の版（rotation-backtest.sql）と同じ定数なら同じ数・
// 会社で絞れる・一時ファイルを使わない形か（EXPLAIN）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v).slice(0, 2000)); if (!ok) bad++; };
const T = `(now() at time zone 'Asia/Tokyo')::date`;
const at = (off, hm) => `((${T} - ${off}) + time '${hm}') at time zone 'Asia/Tokyo'`;

// ---- 作り物のデータ：決まった運用（t90 と同じ形）＋ 乱数で作ったゆらぎ（決まった種で、毎回同じ） ----
const rows = [];
const leg = (reg, cs, off, hm, endHm, dep, arr, type) => rows.push(`('${reg}', '${cs}', ${T} - ${off}, ${type ? `'${type}'` : 'null'}, ${at(off, hm)}, ${at(off, endHm)}, ${dep ? `'${dep}'` : 'null'}, ${arr ? `'${arr}'` : 'null'})`);
for (let off = 1; off <= 70; off++) {
  const s = 'JA73S' + (off % 5);
  leg(s, 'SKY1', off, '07:00', '09:00', 'HND', 'FUK', 'B738'); leg(s, 'SKY2', off, '10:00', '12:00', 'FUK', 'HND', 'B738');
  leg(s, 'SKY3', off, '13:00', '14:30', 'HND', 'CTS', 'B738'); leg(s, 'SKY4', off, '15:30', '17:00', 'CTS', 'HND', 'B738');
  const r = 'JA60R' + (off % 4);
  leg(r, 'APJ1', off, '08:00', '10:00', 'KIX', 'CTS', 'A320');
  leg(r, off <= 12 ? 'APJ8' : 'APJ2', off, off <= 12 ? '11:30' : '11:00', '13:00', 'CTS', 'KIX', 'A320');
  const small = off % 3 === 0, j = small ? 'JA30' + (off % 7) + 'J' : 'JA86' + (off % 7) + 'J';
  leg(j, 'JAL100', off, '08:00', '09:10', 'HND', 'ITM', small ? 'B738' : 'B789');
  leg(j, small ? 'JAL202' : 'JAL200', off, '10:00', '11:10', 'ITM', 'HND', small ? 'B738' : 'B789');
  if (off <= 4) { leg('JA01AD', 'ADO5', off, '09:00', '10:30', 'HND', 'CTS', 'B763'); leg('JA01AD', 'ADO6', off, '12:00', '13:30', 'HND', 'KMJ', 'B763'); }
}
let seed = 12345; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
const pick = (a) => a[Math.floor(rnd() * a.length)];
const aps = ['HND', 'ITM', 'CTS', 'FUK', 'OKA', 'KIX', null], cos = ['JAL', 'ANA', 'SFJ', 'ADO'], tys = ['B738', 'B789', 'A321', 'B763', null];
const pad = (n) => String(n).padStart(2, '0');
for (let off = 1; off <= 70; off++) for (let a = 0; a < 24; a++) {
  const co = cos[a % 4], reg = 'JA' + (500 + a) + 'X', ty = rnd() < 0.9 ? tys[a % 4] : pick(tys);
  let h = 6 + Math.floor(rnd() * 3), loc = pick(aps);
  for (let n = 0; n < 4 && h < 21; n++) {
    const fl = co + (1 + ((a * 7 + n * 3 + (rnd() < 0.25 ? Math.floor(rnd() * 5) : 0)) % 30));
    const dest = rnd() < 0.85 ? pick(aps) : null, m = pick(['00', '15', '30', '45']);
    leg(reg, fl, off, `${pad(h)}:${m}`, `${pad(h + 1)}:${m}`, rnd() < 0.9 ? loc : pick(aps), dest, ty);
    loc = dest; h += 2 + Math.floor(rnd() * 3);
  }
}
const uniq = [...new Map(rows.map((r) => [r.split(',').slice(0, 3).join(','), r])).values()];
for (let i = 0; i < uniq.length; i += 2000) await db.exec(`insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr) values ${uniq.slice(i, i + 2000).join(',\n')} on conflict do nothing`);
await db.exec(`insert into public.timetable (operator, dep, arr, flight, days, valid_from, valid_to, dep_time, arr_time, aircraft) values
  ('JAL', 'ITM', 'HND', 'JL200', 127, ${T} - 90, ${T} + 60, '10:00', '11:10', '789'),
  ('JAL', 'ITM', 'HND', 'JL202', 127, ${T} - 90, ${T} + 60, '10:00', '11:10', '738'),
  ('JAL', 'HND', 'ITM', 'JL5', 85, ${T} - 90, ${T} + 60, '10:00', '11:10', '738'),
  ('JAL', 'CTS', 'HND', 'JL9', 127, ${T} - 90, ${T} + 60, '12:00', '13:10', '738')`);
await db.exec(`insert into public.livery_sightings (reg, name, airline, lat, lon, src) values ('JA8088', '特別塗装A', 'JAL', 35, 139, 'test'), ('JA502X', '特別塗装B', 'SFJ', 35, 139, 'test');
  insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) select ${T} - g, 'JL500', 'HND', 'OKA', ${at(0, '12:00')} - g * interval '1 day', ${at(0, '14:30')} - g * interval '1 day', 'test' from generate_series(1, 3) g;
  insert into public.livery_plans (schedule_id, flight, dep, arr, std, livery) select id, flight, dep, arr, std, '特別塗装A ジェット' from public.flight_schedule where flight = 'JL500';
  insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr) select 'JA8088', 'JAL400', ${T} - g, 'B738', ${at(0, '08:00')} - g * interval '1 day', ${at(0, '09:10')} - g * interval '1 day', 'ITM', 'HND' from generate_series(1, 3) g;
  insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr) select 'JA8088', 'JAL500', ${T} - g, 'B738', ${at(0, '12:00')} - g * interval '1 day', ${at(0, '14:30')} - g * interval '1 day', 'HND', 'OKA' from generate_series(1, 3) g`);
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, reg, type, callsign, cancelled) select ${T} - g, f.flight, f.dep, f.arr,
  ((${T} - g) + f.t1) at time zone 'Asia/Tokyo', ((${T} - g) + f.t2) at time zone 'Asia/Tokyo', f.reg, 'B789', f.cs, (g % 9 = 4 and f.flight = 'NH12')
  from generate_series(1, 30) g, (values ('JL100', 'HND', 'ITM', time '08:00', time '09:10', 'JAL100', 'JA861J'), ('JL200', 'ITM', 'HND', time '10:00', time '11:10', 'JAL200', 'JA861J'),
    ('JL201', 'HND', 'FUK', time '12:30', time '14:10', 'JAL201', 'JA861J'), ('NH11', 'HND', 'CTS', time '07:00', time '08:30', 'ANA11', 'JA801A'),
    ('NH12', 'CTS', 'HND', time '09:30', time '11:00', 'ANA12', 'JA801A'), ('NH13', 'HND', 'OKA', time '12:00', time '14:30', 'ANA13', 'JA801A')) f(flight, dep, arr, t1, t2, cs, reg)`);
for (let off = 1; off <= 30; off++) await db.query(`select public.archive_rotations(${T} - ${off})`);
const nlegs = (await db.query(`select count(*)::int as n from public.reg_legs`)).rows[0].n;
console.log(`作り物の便 ${nlegs}件`);

// ---- 読むだけ ----
const full = fs.readFileSync(new URL('../../docs/pm/rotation-backtest.sql', import.meta.url), 'utf8');
const lite = fs.readFileSync(new URL('../../docs/pm/rotation-backtest-lite.sql', import.meta.url), 'utf8');
const code = lite.replace(/--.*$/gm, '');
check('軽い版：書き込み・表や関数の作成をしない（1つの文だけ）', !/\b(insert|update|delete|create|alter|drop|truncate|grant|revoke|merge|copy|set)\b/i.test(code) && code.trim().split(';').filter((s) => s.trim()).length === 1);
check('軽い版：先頭に「自動翻訳を切る」の一行', /自動翻訳を切って/.test(lite.split('\n').slice(0, 5).join('\n')));
check('軽い版：重いときの下げ方を先頭に書いている', /重いとき/.test(lite.slice(0, 2000)) && /max_per_day/.test(lite.slice(0, 2000)) && /carrier/.test(lite.slice(0, 2000)));

// ---- 定数を差し替える ----
const fullP = (off, max) => full.replace(/\np as \([\s\S]*?\n\),\n/, `\np as (select ${T} - ${off} as d_from, ${T} - ${off} as d_to, ${max} as max_per_day, 20 as min_n),\n`);
const liteP = (off, max, bd, ld, carrier) => lite.replace(/\np as \([\s\S]*?\n\),\n/, `\np as (select ${T} - ${off} as d, ${max} as max_per_day, ${bd} as base_days, ${ld} as learn_days, ${carrier ? `'${carrier}'` : 'null'}::text as carrier, 20 as min_n),\n`);
check('定数の差し替えができる', fullP(1, 5) !== full && liteP(1, 5, 60, 42) !== lite);
const run = async (sql) => { await db.exec('begin transaction read only'); try { return (await db.query(sql)).rows; } finally { await db.exec('commit'); } };
const norm = (rows) => rows.map((r) => JSON.stringify(Object.values(r).map((v) => (v == null ? null : String(v))))).join('\n');

// ---- 今の版と同じ数（同じ定数のとき：60日・42日） ----
const outLite = [];
for (const [off, max] of [[1, 1500], [2, 1500], [3, 1500], [5, 40], [8, 1500], [13, 1500], [20, 25]]) {
  const a = await run(fullP(off, max)), b = await run(liteP(off, max, 60, 42));
  const methods = new Set(b.map((r) => r['方式']));
  check(`${off}日前・上限${max}：今の版と同じ数（${b.length}行）`, a.length > 0 && norm(a) === norm(b) && methods.has('base') && methods.has('learn') && methods.has('obs'),
    { a: a.filter((r) => r['区分'] === '全体'), b: b.filter((r) => r['区分'] === '全体') });
  if (off === 1) outLite.push(...b);
}
const lvr = outLite.find((r) => r['方式'] === 'learn' && r['区分'] === '出どころ' && r['値'] === 'livery');
check('特別塗装機の予定の便も測れる', lvr && Number(lvr['当たり']) >= 1, lvr);
const learnSrc = outLite.find((r) => r['方式'] === 'learn' && r['区分'] === '出どころ' && r['値'] === 'learn');
check('学ぶ予想の便が出ている（比べる意味がある）', learnSrc && Number(learnSrc['予想を出した数']) > 0, learnSrc);

// ---- 21日にしても動く・会社で絞る ----
const d21 = await run(liteP(1, 300, 21, 21));
check('初めの定数（21日・300便）で動く', d21.some((r) => r['方式'] === 'learn' && r['区分'] === '全体'), d21.slice(0, 3));
const jal = await run(liteP(1, 300, 21, 21, 'JAL'));
const jalCo = new Set(jal.filter((r) => r['区分'] === '会社').map((r) => r['値']));
const nAll = (rows, m) => rows.filter((r) => r['方式'] === m && r['区分'] === '全体').reduce((s, r) => s + Number(r['基準の数']), 0);
check('会社を1つに絞れる（測る便が JAL だけ・obs も JAL だけ）', [...jalCo].every((v) => v === 'JAL') && nAll(jal, 'base') > 0 && nAll(jal, 'base') < nAll(d21, 'base')
  && jal.filter((r) => r['方式'] === 'obs' && r['区分'] === '会社').every((r) => r['値'] === 'JAL'), { jalCo: [...jalCo] });
const mx = await run(liteP(1, 10, 21, 21));
check('1日に測る便の上限が効く', nAll(mx, 'base') <= 40 && nAll(mx, 'base') > 0, nAll(mx, 'base'));

// ---- 一時ファイル（EXPLAIN ANALYZE の Temp Written Blocks）を、小さい作業メモリで比べる ----
const temp = (plan) => { let t = 0; const walk = (n) => { t += Number(n['Temp Written Blocks'] || 0); (n.Plans || []).forEach(walk); }; walk(plan); return t; };
const explain = async (sql) => {
  await db.exec(`set work_mem = '64kB'`);
  try { const r = (await db.query(`explain (analyze, buffers, format json) ${sql.replace(/;\s*$/, '')}`)).rows[0]['QUERY PLAN'];
    const j = typeof r === 'string' ? JSON.parse(r) : r; return { temp: temp(j[0].Plan), ms: j[0]['Execution Time'] }; }
  finally { await db.exec('reset work_mem'); }
};
const eFull = await explain(fullP(1, 1500)), eFull3 = await explain(full.replace(/\np as \([\s\S]*?\n\),\n/, `\np as (select ${T} - 3 as d_from, ${T} - 1 as d_to, 1500 as max_per_day, 20 as min_n),\n`));
const eLite = await explain(liteP(1, 300, 21, 21)), eLite60 = await explain(liteP(1, 1500, 60, 42));
console.log(`一時ファイル（ブロック）：今の版 1日 ${eFull.temp}・3日 ${eFull3.temp}／軽い版 21日 ${eLite.temp}・60日 ${eLite60.temp}（時間 ${Math.round(eFull3.ms)}ms → ${Math.round(eLite.ms)}ms）`);
check('軽い版は一時ファイルを使わない（作業メモリ 64kB でも）', eLite.temp === 0 && eLite60.temp === 0, { eLite, eLite60 });
check('今の版（3日）より一時ファイルが少ない', eFull3.temp > eLite.temp, { eFull3, eLite });
if (bad) process.exit(1);
