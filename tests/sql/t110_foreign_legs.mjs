// 海外の航空会社の便の実績（移行 171）：
//   1. airline_codes は Edge Functions の PREFIX と同じ中身か
//   2. foreign_legs_build：海外の会社の便だけ・登録記号と機種・便名・何度流しても同じ・元が変わった分だけ入れ替え・ほかの日に触らない
//   3. 相手の空港・引き返し・ダイバート
//   4. foreign_usual_build：曜日ごと（3回以上）・曜日を問わない（5回以上）・0時をまたぐ便・ばらつきの大きい便は作らない
//   5. foreign_late：いつもとのずれ（推定）・いつもの時刻がない便・日本の会社・読めない便名
//   6. RLS と権限・lock_timeout
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
const rows = async (sql, p) => (await db.query(sql, p)).rows;
const one = async (sql, p) => (await rows(sql, p))[0];

// 1
const ts = fs.readFileSync(new URL('../../supabase/functions/_shared/flight_watch.ts', import.meta.url), 'utf8');
const body = ts.slice(ts.indexOf('const PREFIX'), ts.indexOf('};', ts.indexOf('const PREFIX')));
const jpLine = /JAPAN_CARRIERS = new Set\(\[([^\]]*)\]/.exec(ts)[1]; const JP = new Set(jpLine.match(/[A-Z0-9]{2}/g));
// 11/16 本人：ODPT で見られる会社（JL・NH の便名で飛ぶ呼び出し符号）だけを外し、ODPT にない日本の会社は集める
const ODPT = new Set(); for (const x of body.matchAll(/"?(JL|NH)"?:\s*\[([^\]]*)\]/g)) for (const c of x[2].match(/[A-Z]{3}/g)) ODPT.add(c);
const want = new Map();
for (const x of body.matchAll(/"?([A-Z0-9]{2})"?:\s*\[([^\]]*)\]/g)) for (const c of x[2].match(/[A-Z]{3}/g)) if (!want.has(c) || JP.has(x[1])) want.set(c, [x[1], ODPT.has(c)]);
const have = new Map((await rows(`select icao, iata, odpt from public.airline_codes`)).map((r) => [r.icao, [r.iata, r.odpt]]));
const diff = [...want].filter(([c, v]) => JSON.stringify(have.get(c)) !== JSON.stringify(v));
check('airline_codes は flight_watch.ts の PREFIX と同じ・odpt は JL・NH の呼び出し符号だけ（JAL・JLJ・JTA・JAC・HAC・ANA・AKX・AJX）', diff.length === 0 && want.size > 50 && [...have].filter(([, v]) => v[1]).map(([c]) => c).sort().join() === 'AJX,AKX,ANA,HAC,JAC,JAL,JLJ,JTA', diff.slice(0, 5));
check('日本貨物航空（NCA）・スカイマーク・ピーチ・ZIPAIR は ODPT にないので集める', JSON.stringify(have.get('NCA')) === '["KZ",false]' && have.get('SKY')?.[1] === false && have.get('APJ')?.[1] === false && have.get('TZP')?.[1] === false, [have.get('NCA'), have.get('SKY')]);

// 空港があるか
const aps = (await rows(`select iata from public.airports where iata in ('HND','NRT','KIX','CTS')`)).map((r) => r.iata).sort();
check('空港の表に HND・NRT・KIX・CTS がある（試しの前提）', aps.join() === 'CTS,HND,KIX,NRT', aps);

const today = (await one(`select (now() at time zone 'Asia/Tokyo')::date::text d`)).d;
const D = async (k) => (await one(`select ($1::date + $2::int)::text d`, [today, k])).d;
const T = (day, hm) => `(('${day} ${hm}')::timestamp at time zone 'Asia/Tokyo')`;
const track = (iata, day, cs, hm, dep) => `insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values ('${iata}', '${day}', '${cs}', ${T(day, hm)}, ${dep}, 'abc');`;
const leg = (reg, cs, day, hm1, hm2, type) => `insert into public.reg_legs (reg, callsign, day, type, first_at, last_at) values ('${reg}', '${cs}', '${day}', ${type ? `'${type}'` : 'null'}, ${T(day, hm1)}, ${T(day, hm2)});`;

// 2
const d0 = await D(-1);
await db.exec([
  track('HND', d0, 'BAW5', '06:42', 0), leg('G-YMMU', 'BAW5', d0, '05:50', '06:43', 'B772'),
  track('HND', d0, 'JAL123', '07:00', 1), leg('JA731J', 'JAL123', d0, '06:55', '07:30', 'B738'),
  track('NRT', d0, 'TZP12', '09:00', 1), leg('JA822J', 'TZP12', d0, '08:55', '09:40', 'B788'),   // ZIPAIR は ODPT にないので入れる（日本の機体でも）
  track('HND', d0, 'SKY701', '08:00', 1), leg('JA737L', 'SKY701', d0, '07:55', '08:30', 'B738'),  // スカイマークも入れる
  track('HND', d0, 'XQZ1', '10:00', 1), leg('JA01AB', 'XQZ1', d0, '09:55', '10:30', 'C56X'),      // 表にない会社の日本の機体（自家用など）は入れない
  track('NRT', d0, 'QQQ5100', '03:10', 0), leg('N123FE', 'QQQ5100', d0, '02:20', '03:12', 'MD11'), // 表にない会社：便名なしで残す
  track('NRT', d0, 'KAL703', '13:00', 1), track('NRT', d0, 'KAL703', '14:20', 0),               // 引き返し
  track('KIX', d0, 'UAL32', '17:00', 1), track('NRT', d0, 'UAL32', '18:15', 0),                 // 日本の中の区間
  track('NRT', await D(-2), 'BAW5', '06:40', 0),                                                 // ほかの日
].join('\n'));
let n = (await one(`select public.foreign_legs_build($1::date) n`, [d0])).n;
let got = await rows(`select callsign, iata, dep_here, flight, airline, reg, type, other, event from public.foreign_legs where day = $1 order by callsign, at`, [d0]);
const by = Object.fromEntries(got.map((r) => [`${r.callsign}|${r.iata}|${r.dep_here}`, r]));
check('海外の会社と ODPT にない日本の会社の便（JAL と表にない会社の日本の機体は入らない）', n === 8 && got.length === 8 && !by['JAL123|HND|1'] && !by['XQZ1|HND|1'] && by['TZP12|NRT|1']?.flight === 'ZG12' && by['SKY701|HND|1']?.flight === 'BC701' && by['SKY701|HND|1'].reg === 'JA737L', got.map((r) => r.callsign));
check('便名・会社・登録記号・機種', by['BAW5|HND|0']?.flight === 'BA5' && by['BAW5|HND|0'].airline === 'BA' && by['BAW5|HND|0'].reg === 'G-YMMU' && by['BAW5|HND|0'].type === 'B772', by['BAW5|HND|0']);
check('表にない会社は便名なしで残す', by['QQQ5100|NRT|0'] && by['QQQ5100|NRT|0'].flight === null && by['QQQ5100|NRT|0'].reg === 'N123FE', by['QQQ5100|NRT|0']);
check('引き返し：同じ空港を出て5時間以内に着いた', by['KAL703|NRT|0']?.event === 'return' && by['KAL703|NRT|0'].other === 'NRT' && by['KAL703|NRT|1'].event === null, [by['KAL703|NRT|0'], by['KAL703|NRT|1']]);
check('相手の空港：日本の中の区間は両方に付く', by['UAL32|KIX|1']?.other === 'NRT' && by['UAL32|NRT|0']?.other === 'KIX' && by['UAL32|NRT|0'].event === null, [by['UAL32|KIX|1'], by['UAL32|NRT|0']]);
const sk = (await one(`select public.foreign_late('BC701', $1::date) j`, [d0])).j;
check('foreign_late：ODPT にない日本の会社（スカイマーク）の便も返す', sk.legs.length === 1 && sk.legs[0].callsign === 'SKY701' && sk.legs[0].reg === 'JA737L', sk.legs);
const before = await rows(`select * from public.foreign_legs order by callsign, at`);
await db.query(`select public.foreign_legs_build($1::date)`, [d0]);
const again = await rows(`select * from public.foreign_legs order by callsign, at`);
check('もう一度流しても同じ（built_at のほか）', JSON.stringify(before.map(({ built_at, ...r }) => r)) === JSON.stringify(again.map(({ built_at, ...r }) => r)), null);
check('ほかの日（前の前の日）には触らない', (await one(`select count(*)::int c from public.foreign_legs where day = $1`, [await D(-2)])).c === 0, null);
// 元の判定が変わった（同じ便の時刻が直った）
await db.exec(`update public.airport_tracks_all set at = ${T(d0, '06:44')} where callsign = 'BAW5' and day = '${d0}'`);
await db.query(`select public.foreign_legs_build($1::date)`, [d0]);
const bw = await rows(`select to_char(at at time zone 'Asia/Tokyo', 'HH24:MI') t from public.foreign_legs where callsign = 'BAW5' and day = $1`, [d0]);
check('元が変わった行だけ入れ替わる（古い時刻の行は残らない）', bw.length === 1 && bw[0].t === '06:44', bw);

// 3 ダイバート：前の8週で香港からの便がいつも羽田に着いているのに、成田に着いた
const hist = []; for (let k = 2; k <= 6; k++) hist.push(track('HND', await D(-k), 'CPA500', '20:30', 0));
hist.push(track('NRT', d0, 'CPA500', '21:10', 0), track('HND', d0, 'CPA542', '15:00', 0));   // CPA542 は記録がないのでダイバートにしない
await db.exec(hist.join('\n'));
for (let k = 6; k >= 2; k--) await db.query(`select public.foreign_legs_build($1::date)`, [await D(-k)]);
await db.query(`select public.foreign_legs_build($1::date)`, [d0]);
const dv = await rows(`select callsign, iata, event from public.foreign_legs where day = $1 and callsign like 'CPA%' order by 1`, [d0]);
check('ダイバート：いつもの空港（4回以上・8割以上）と違う、着いたことのない空港', JSON.stringify(dv) === JSON.stringify([{ callsign: 'CPA500', iata: 'NRT', event: 'divert' }, { callsign: 'CPA542', iata: 'HND', event: null }]), dv);
check('ダイバートを作っても前の日の羽田の行はそのまま', (await one(`select count(*)::int c from public.foreign_legs where callsign = 'CPA500' and iata = 'HND' and event is null`)).c === 5, null);

// 4 いつもの時刻
await db.exec(`delete from public.foreign_legs; delete from public.airport_tracks_all; delete from public.reg_legs;`);
const ins = [];
const put = async (cs, iata, dep, k, hm) => ins.push(`insert into public.foreign_legs (day, callsign, iata, dep_here, at, flight, airline) values ('${await D(k)}', '${cs}', '${iata}', ${dep}, ${T(await D(k), hm)}, ${/^BAW/.test(cs) ? `'BA${cs.slice(3)}'` : 'null'}, ${/^BAW/.test(cs) ? "'BA'" : 'null'});`);
for (const [k, hm] of [[-7, '06:38'], [-14, '06:40'], [-21, '06:41'], [-28, '06:45'], [-35, '06:39'], [-3, '06:50']]) await put('BAW5', 'HND', 0, k, hm);
for (const [k, hm] of [[-1, '23:50'], [-2, '23:55'], [-3, '00:05'], [-4, '00:10'], [-5, '23:58']]) await put('AAL61', 'NRT', 0, k, hm);
for (const [k, hm] of [[-1, '08:00'], [-2, '12:00'], [-3, '16:00'], [-4, '20:00'], [-5, '10:00']]) await put('FDX9', 'KIX', 0, k, hm);
for (const [k, hm] of [[-7, '10:00'], [-14, '10:05']]) await put('THA640', 'NRT', 0, k, hm);
await put('BAW5', 'HND', 0, -70, '01:00');   // 8週より前は入れない
await db.exec(ins.join('\n'));
n = (await one(`select public.foreign_usual_build() n`)).n;
const us = Object.fromEntries((await rows(`select callsign, dow, mins, n, spread from public.foreign_usual order by 1, 2`)).map((r) => [`${r.callsign}|${r.dow}`, r]));
const dowToday = (await one(`select extract(dow from $1::date)::int w`, [today])).w;
check('曜日ごと：同じ曜日5回の中央値 06:40', us[`BAW5|${dowToday}`]?.mins === 400 && us[`BAW5|${dowToday}`].n === 5, us[`BAW5|${dowToday}`]);
check('曜日を問わない：6回（8週より前は入れない）', us['BAW5|-1']?.n === 6, us['BAW5|-1']);
check('0時をまたぐ便は 23:58 前後・ばらつき小', us['AAL61|-1'] && (us['AAL61|-1'].mins === 1438) && us['AAL61|-1'].spread <= 15, us['AAL61|-1']);
check('時刻がばらばらの便（ばらつき60分超）は作らない', !Object.keys(us).some((k) => k.startsWith('FDX9|')), Object.keys(us));
check('記録が少ない便（2回）は作らない', !Object.keys(us).some((k) => k.startsWith('THA640|')), Object.keys(us));
check('作り直すと前の行は残らない', (await one(`select public.foreign_usual_build() n`)).n === n, null);

// 5 いつもとのずれ
await db.exec(`insert into public.foreign_legs (day, callsign, iata, dep_here, at, flight, airline, reg) values ('${today}', 'BAW5', 'HND', 0, ${T(today, '07:12')}, 'BA5', 'BA', 'G-YMMU'),
  ('${today}', 'AAL61', 'NRT', 0, ${T(today, '00:20')}, null, null, null), ('${today}', 'THA640', 'NRT', 0, ${T(today, '11:00')}, null, null, null);`);
let r = (await one(`select public.foreign_late('ba5') j`)).j;
check('BA5：いつもの 06:40 より32分遅い（推定）', r.legs.length === 1 && r.legs[0].usual === '06:40' && r.legs[0].late_min === 32 && r.legs[0].dir === 'arr' && r.legs[0].reg === 'G-YMMU' && /推定/.test(r.note), r);
r = (await one(`select public.foreign_late('AA61') j`)).j;
check('0時をまたぐ：23:58 がいつもで 0:20 着は22分遅い', r.legs[0]?.late_min === 22, r.legs);
r = (await one(`select public.foreign_late('TG640') j`)).j;
check('いつもの時刻がない便は実績だけ（ずれは出さない）', r.legs.length === 1 && r.legs[0].usual === null && r.legs[0].late_min === null, r.legs);
r = (await one(`select public.foreign_late('JL5') j`)).j;
check('ODPT で見られる会社（JAL）の便は返さない', r.legs.length === 0, r);
r = (await one(`select public.foreign_late($1) j`, ["x'; drop table x;--"])).j;
check('読めない便名でもエラーにならず空', Array.isArray(r.legs) && r.legs.length === 0, r);
r = (await one(`select public.foreign_late('BA5', $1::date) j`, [await D(-7)])).j;
check('日を選べる', r.legs.length === 1 && r.legs[0].late_min === -2, r.legs);

// 6 RLS と権限
const cfg = Object.fromEntries((await rows(`select proname, proconfig from pg_proc where proname in ('foreign_legs_build','foreign_usual_build')`)).map((x) => [x.proname, x.proconfig]));
check('作る関数に lock_timeout 5s', Object.values(cfg).every((c) => (c ?? []).includes('lock_timeout=5s')) && Object.keys(cfg).length === 2, cfg);
await db.exec('set role anon');
const tryq = async (q) => { try { await db.query(q); return 'ok'; } catch (e) { return 'denied'; } };
check('誰でも：airline_codes は読める', (await rows(`select count(*)::int c from public.airline_codes`))[0].c > 50, null);
check('誰でも：foreign_late は呼べる', (await tryq(`select public.foreign_late('BA5')`)) === 'ok', null);
check('誰でも：foreign_legs・foreign_usual は読めない', (await tryq(`select * from public.foreign_legs`)) === 'denied' && (await tryq(`select * from public.foreign_usual`)) === 'denied', null);
check('誰でも：作る関数は呼べない', (await tryq(`select public.foreign_legs_build(current_date)`)) === 'denied' && (await tryq(`select public.foreign_usual_build()`)) === 'denied', null);
check('誰でも：airline_codes に書けない', (await tryq(`insert into public.airline_codes values ('ZZZ','ZZ',false)`)) === 'denied', null);
await db.exec('reset role; set role authenticated');
check('ログインした人も foreign_legs は読めない', (await tryq(`select * from public.foreign_legs`)) === 'denied', null);
await db.exec('reset role');

// 移行の文
const sql = fs.readFileSync(dir + '20261116000171_foreign_legs.sql', 'utf8');
check('毎日の仕事に statement_timeout と lock_timeout', (sql.match(/set statement_timeout = '2min'; set lock_timeout = '5s';/g) ?? []).length === 2, null);
check('pg_cron がない所では仕事を作らない', sql.includes("where extname = 'pg_cron') then return"), null);

console.log(bad ? `NG ${bad}件` : 'すべて OK');
process.exit(bad ? 1 : 0);
