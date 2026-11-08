// 運用予想担当：特別塗装機ごとに予想が出せるかを見る読むだけの SQL（docs/pm/yosoku-livery-coverage.sql）。
// 一覧（liveries.ts）と合っているか・表を変えないか・[1]〜[5] がそれぞれ流れて、作った記録どおりの数になるか
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
import { buildSql, specialLiveries } from '../../tools/yosoku_livery_sql.mjs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };

// 一覧と合っているか・読むだけか
const file = fs.readFileSync(new URL('../../docs/pm/yosoku-livery-coverage.sql', import.meta.url), 'utf8');
check('SQL が liveries.ts の一覧から作り直したものと同じ（一覧が変わったら node tools/yosoku_livery_sql.mjs）', file === await buildSql());
const list = await specialLiveries();
check('特別塗装機だけ（アライアンス塗装は入れない）', list.length > 80 && list.every(l => !l.kind || l.kind === 'special') && !file.includes("'JA899A'"), list.length);
const body = file.replace(/--.*$/gm, '').replace(/'(?:[^']|'')*'/g, "''");
check('表を変える文がない', !/\b(insert|update|delete|truncate|alter|drop|create|grant|revoke)\b/i.test(body));

// 記録：ポケモンジェット 赤（JA819A）は毎日 ANA1→ANA2→ANA3、今日も飛んでいる。FDA 1号機（JA01FJ）は12〜8日前だけ。海外の機体は記録なし
const T = `(now() at time zone 'Asia/Tokyo')::date`;
const at = (off, hm) => `((${T} - ${off}) + time '${hm}') at time zone 'Asia/Tokyo'`;
const rows = [];
const leg = (reg, cs, off, hm, endHm, dep, arr, type) => rows.push(`('${reg}', '${cs}', ${T} - ${off}, '${type}', ${at(off, hm)}, ${at(off, endHm)}, '${dep}', '${arr}')`);
for (let off = 1; off <= 20; off++) {
  leg('JA819A', 'ANA1', off, '07:00', '08:30', 'HND', 'ITM', 'B763'); leg('JA819A', 'ANA2', off, '09:30', '10:40', 'ITM', 'HND', 'B763');
  leg('JA819A', 'ANA3', off, '12:00', '13:30', 'HND', 'CTS', 'B763');
  if (off >= 8 && off <= 12) { leg('JA01FJ', 'FDA1', off, '08:00', '09:00', 'FSZ', 'CTS', 'E170'); leg('JA01FJ', 'FDA2', off, '10:00', '11:00', 'CTS', 'FSZ', 'E170'); }
}
leg('JA819A', 'ANA1', 0, '07:00', '07:30', 'HND', 'ITM', 'B763');
await db.exec(`insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr) values ${rows.join(',\n')}`);
for (let off = 0; off <= 20; off++) await db.query(`select public.rot_pairs_build(${T} - ${off})`);

const blocks = file.split(/^-- ===== /m).slice(1).map(b => b.replace(/^.*\n/, ''));
check('[1]〜[5] の5つに分かれている', blocks.length === 5, blocks.length);
const run = async i => { const r = await db.exec(blocks[i]); return r[r.length - 1].rows; };
const active = list.filter(l => (!l.from || l.from <= new Date().toISOString().slice(0, 10)) && (!l.until || l.until >= new Date().toISOString().slice(0, 10)));

const b1 = (await run(0))[0];
check('[1] 数える塗装機の数（期間に入っているものだけ）・学ぶ予想の関数がある', b1['数える塗装機'] === active.length && b1['学ぶ予想の関数がある'] === true
  && b1['うち国内'] === active.filter(l => l.reg.startsWith('JA')).length && b1['つながりを作った日数（前の60日）'] === 21, b1);

const b2 = await run(1);
const p819 = b2.find(r => r['登録記号'] === 'JA819A'), f01 = b2.find(r => r['登録記号'] === 'JA01FJ'), ov = b2.find(r => r['登録記号'] === '9V-OJJ');
check('[2] 機体ごとの飛んだ日・便の数・今日かきのう', b2.length === active.length && p819['飛んだ日（30日）'] === 21 && p819['便の数'] === 61 && p819['今日かきのう飛んだ'] === true
  && f01['飛んだ日（30日）'] === 5 && f01['今日かきのう飛んだ'] === false && ov['飛んだ日（30日）'] === 0, { p819, f01, ov });
check('[2] 国内が先、飛んだ日の多い順', b2[0]['登録記号'] === 'JA819A' && b2[b2.length - 1]['区分'] === '海外', b2[0]);

const b3 = await run(2);
const sum = b3.find(r => r['区分'] === '合計'), dom = b3.find(r => r['区分'] === '国内');
check('[3] まとめ（合計は最後）', b3[b3.length - 1]['区分'] === '合計' && sum['塗装機'] === active.length && sum['30日に1回でも飛んだ'] === 2
  && sum['10日以上飛んだ'] === 1 && sum['今日かきのう飛んだ'] === 1 && dom['30日に1回でも飛んだ'] === 2, b3);

const b4 = await run(3);
const r4 = b4.find(r => r['登録記号'] === 'JA819A'), s4 = b4.find(r => r['登録記号'] === '合計');
check('[4] 今日飛んだ機体だけ、画面・今の予想・学ぶ予想を呼ぶ', b4.length === 2 && r4['今の予想（便の数）'] === 2 && r4['画面の予想（便の数）'] === 2
  && r4['学ぶ予想（便の数）'] === 2 && r4['学ぶ予想の次の便'] === 'ANA2' && r4['時刻表で今の便が分かる'] === 'false', b4);
check('[4] 合計の行', s4['画面の予想（便の数）'] === 1 && s4['学ぶ予想（便の数）'] === 1, s4);

const b5 = await run(4);
const t5 = b5.find(r => r['区分'] === '合計'), m5 = b5.find(r => r['登録記号'] === 'JA819A'), q5 = b5.find(r => r['登録記号'] === 'JA01FJ');
// JA819A：前の14日 × 2便（ANA1・ANA2 に次の便がある）。前の日までの記録があるので予想が出て当たる。JA01FJ：5日×1便。今の予想（3回以上）は 3回たまった後の2日だけ、学ぶ予想（2回以上）は3日
check('[5] 前の14日の便と、予想が出た・当たった数', t5['便'] === 28 + 5 && m5['便'] === 28 && m5['今の予想が当たった'] === 28 && m5['学ぶ予想が当たった'] === 28
  && q5['便'] === 5 && q5['今の予想が出た'] === 2 && q5['学ぶ予想が出た'] === 3 && t5['学ぶ予想が1回でも出た機体'] === 2, b5);
check('[5] 予想は表に残さない（rot_eval は空のまま）', (await db.query('select count(*)::int as n from public.rot_eval')).rows[0].n === 0);

if (bad) { console.log(`NG ${bad} 件`); process.exit(1); }
console.log('すべて OK');
