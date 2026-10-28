// エアライン経営 co-v3：気象庁の台風解析・予報情報（防災情報XML）の読み方と、予報を自動で入れる関数・CAT III の空港の表
//   data/ の電文は気象庁ホームページの防災情報XML（2026年10月29日 0時45分発表の台風第31号）をそのまま試験に使うもの
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
import { typhoonFeedUrls, parseTyphoon, approachDays, latestPerEvent, distKm, jstDay } from '../../supabase/functions/_shared/co3_typhoon.js';
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const here = new URL('./data/', import.meta.url).pathname;

// ---- 電文の読み方 ----
const feed = fs.readFileSync(here + 'jma_feed_sample.xml', 'utf8');
const urls = typhoonFeedUrls(feed);
check('一覧から台風の電文だけを取る（新しい順）', urls.length === 2 && urls.every((u) => /VPTW61_010000\.xml$/.test(u)) && urls[0] > urls[1], urls);
const xml = fs.readFileSync(here + 'jma_vptw61_tc2637.xml', 'utf8');
const st = parseTyphoon(xml);
check('電文：台風の番号・名前・発表の時刻', st && st.event === 'TC2637' && st.number === '2631' && st.name === 'IN-FA' && st.reported === '2026-10-29T00:45:00+09:00', st && { e: st.event, n: st.number, nm: st.name });
check('電文：実況1つと予報6つの中心', st.points.length === 7 && st.points[0].kind === 'now' && st.points[0].lat === 15.4 && st.points[0].lon === 157.0
  && st.points[6].lat === 21.4 && st.points[6].lon === 137.0 && st.points[1].t === Date.parse('2026-10-29T12:00:00+09:00'), st.points);
check('電文：台風の階級', st.points.every((p) => typeof p.typhoon === 'boolean') && st.points[0].typhoon === true, st.points.map((p) => p.typhoon));
check('訓練の電文は使わない', parseTyphoon(xml.replace('<Status>通常</Status>', '<Status>訓練</Status>')) === null, null);
const cx = parseTyphoon(xml.replace('<InfoType>発表</InfoType>', '<InfoType>取消</InfoType>'));
check('取り消しの電文は進路なし', cx && cx.cancelled === true && Object.keys(approachDays(cx, [{ iata: 'OKA', lat: 26.2, lon: 127.6 }])).length === 0, cx);
check('形の違う電文は使わない', parseTyphoon('<Report></Report>') === null && parseTyphoon('') === null, null);
check('距離：羽田と那覇は約1,560km', Math.abs(distKm(35.55, 139.78, 26.21, 127.65) - 1560) < 30, distKm(35.55, 139.78, 26.21, 127.65));

// 本物の電文：日本の空港の近くは通らない（南鳥島近海から西へ。父島・南鳥島には空港の記録がない）
const aps = [{ iata: 'HND', lat: 35.55, lon: 139.78 }, { iata: 'OKA', lat: 26.21, lon: 127.65 }, { iata: 'ISG', lat: 24.40, lon: 124.25 }];
check('本物の電文：本土と沖縄の空港には近づかない', Object.keys(approachDays(st, aps)).length === 0, approachDays(st, aps));

// 作った進路：宮古島の南から那覇の西を北へ。那覇は 10/30 に300km以内、羽田は遠い
const mk = (h, lat, lon, typhoon = true) => ({ t: Date.parse('2026-10-29T00:00:00+09:00') + h * 3600_000, lat, lon, typhoon });
const fake = { event: 'TC2699', reported: '2026-10-29T00:45:00+09:00', number: '2640', points: [mk(0, 21.0, 126.0), mk(24, 23.5, 126.5), mk(45, 26.5, 126.8), mk(69, 30.0, 128.0, false)] };
const hit = approachDays(fake, aps, 300);
check('作った進路：那覇は 10/30 と 10/31、石垣は 10/30', JSON.stringify(hit.OKA) === '["2026-10-30","2026-10-31"]' && (hit.ISG || []).includes('2026-10-30') && !hit.HND, hit);
const weak = { ...fake, points: fake.points.map((p) => ({ ...p, typhoon: false })) };
check('熱帯低気圧になった点からは見ない', Object.keys(approachDays(weak, aps)).length === 0, approachDays(weak, aps));
check('台風ごとにいちばん新しい電文', latestPerEvent([fake, { ...fake, reported: '2026-10-29T03:45:00+09:00', points: [] }, st, null]).length === 2
  && latestPerEvent([fake, { ...fake, reported: '2026-10-29T03:45:00+09:00', points: [] }]).find((s) => s.event === 'TC2699').points.length === 0, null);
check('日本時間の日付', jstDay(Date.parse('2026-10-29T15:30:00Z')) === '2026-10-30' && jstDay(Date.parse('2026-10-29T14:59:00Z')) === '2026-10-29', null);

// ---- SQL ----
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`set co3.season_day = '2026-05-20'`);
const A = '00000000-0000-0000-0000-00000000000a';
await db.exec(`insert into auth.users (id) values ('${A}')`);
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const role = async (r, sql) => { try { await db.exec(`set role ${r}; select set_config('request.jwt.claim.sub','${A}',false);`); const x = await db.query(sql); return x.rows.length ? Object.values(x.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const auto = (day, rows) => role('service_role', `select public.co3_typhoon_auto('${day}', '${JSON.stringify(rows)}'::jsonb)`);
const fc = async () => (await db.query(`select iata, day::text as day, source, event, note from co3_typhoon_fcst order by iata, day`)).rows;

check('アプリからは自動の関数を呼べない', String(await role('authenticated', `select public.co3_typhoon_auto('2026-05-21', '[]'::jsonb)`)).startsWith('ERROR'), null);
let r = await auto('2026-05-21', [{ iata: 'OKA', event: 'TC2699', note: '台風第40号' }, { iata: 'ISG', event: 'TC2699', note: '台風第40号' }, { iata: 'ZZZ', event: 'TC2699' }]);
let f = await fc();
check('明日の予報を入れる（知らない空港は入れない）', r.saved === 2 && f.length === 2 && f.every((x) => x.source === 'jma' && x.day === '2026-05-21' && x.event === 'TC2699' && x.note === '台風第40号'), { r, f });
check('昨日や遠い日は入れられない', String(await auto('2026-05-19', [])).includes('invalid day') && String(await auto('2026-05-24', [])).includes('invalid day'), null);
await db.exec(`insert into co3_typhoon_fcst (iata, day, note) values ('KOJ', '2026-05-21', '運営')`);
await db.exec(`insert into co3_typhoon_plan (user_id, route_key, day, iata, cancel) values ('${A}', '1-2', '2026-05-21', 'ISG', true)`);
r = await auto('2026-05-21', [{ iata: 'KOJ', event: 'TC2699', note: '台風第40号' }]);
f = await fc();
check('それた空港は消す・計画欠航を決めた空港は残す・運営の予報は変えない', r.removed === 1 && f.map((x) => x.iata).join() === 'ISG,KOJ'
  && f.find((x) => x.iata === 'KOJ').source === 'admin' && f.find((x) => x.iata === 'KOJ').note === '運営', { r, f });
check('予報はアプリから読めるが書けない', Number(await role('authenticated', `select count(*) from co3_typhoon_fcst`)) === 2
  && String(await role('authenticated', `insert into co3_typhoon_fcst (iata, day) values ('HND', '2026-05-21')`)).startsWith('ERROR'), null);
const src = String(await q1(`select pg_get_functiondef('public.co_state()'::regprocedure)`));
check('会社の状態の台風に出どころ', src.includes(`'src', f.source`), null);

// ---- CAT III の空港 ----
const c3 = (await db.query(`select iata, note from co3_cat3_airports order by iata`)).rows;
check('CAT III は8空港（高松はまだ）', c3.map((x) => x.iata).join() === 'AOJ,CTS,HIJ,HND,KMJ,KUH,NGO,NRT' && c3.every((x) => /CAT IIIb/.test(x.note)), c3);
check('羽田は 34R', /^34R/.test(c3.find((x) => x.iata === 'HND').note), null);

console.log(bad ? `NG ${bad}` : 'ALL OK'); process.exit(bad ? 1 : 0);
