// エアライン経営 co-v3：貨物の会社（見た貨物機の区間・本物の貨物の量・稼ぎ）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`set co3.season_day = '2026-05-20'`);   // 季節の需要のない日で手計算する（季節は t72）
await db.exec(`update ops.flags set value = 'true' where key in ('game_released', 'co_v3')`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const A = '00000000-0000-0000-0000-00000000000a';
await db.exec(`insert into auth.users (id) values ('${A}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const n = async (sql) => Number(await q1(sql));
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('NRT','HND','OKA','CTS')`)).rows.map((r) => [r.iata, r.id]));

// 本物の便（前の28日）：成田⇄アンカレッジ 貨物 1日2便（片道1便ずつ、飛ぶ時間7時間）、成田⇄ソウル 旅客 1日18便
await db.exec(`insert into flight_history (svc_date, flight, dep, arr, std, sta, type, reg)
  select (now() at time zone 'Asia/Tokyo')::date - d, case s when 0 then 'KZ110' else 'KZ111' end, case s when 0 then 'NRT' else 'ANC' end, case s when 0 then 'ANC' else 'NRT' end,
         now() - d * interval '1 day', now() - d * interval '1 day' + interval '7 hours', 'B748', 'JA1' || s || 'KZ'
    from generate_series(1, 28) d, generate_series(0, 1) s;
  insert into flight_history (svc_date, flight, dep, arr, std, sta, type)
  select (now() at time zone 'Asia/Tokyo')::date - d, 'JL' || (950 + i * 2 + s), case s when 0 then 'NRT' else 'ICN' end, case s when 0 then 'ICN' else 'NRT' end,
         now() - d * interval '1 day', now() - d * interval '1 day' + interval '150 minutes', 'B738'
    from generate_series(1, 28) d, generate_series(0, 8) i, generate_series(0, 1) s`);
await q1(`select public.co3_route_real_refresh()`);

// 国際線の貨物：成田 2,039,731t/年 ÷ 365 × 2便 ÷ 20便 ＝ 558.8t、貨物機の分 7割 ＝ 391.2t
const tons = 2039731 / 365 * 2 / 20;
check('成田⇄アンカレッジの貨物（全部）：558.8t/日', near(await n(`select public.co3_cargo_tons('NRT', 'ANC')`), tons, 0.1), await n(`select public.co3_cargo_tons('NRT', 'ANC')`));
check('距離：海外の空港は飛ぶ時間から（(420 − 30) 分 × 時速820km ＝ 5,330km）', await n(`select public.co3_km('NRT', 'ANC')`) === 5330, null);
check('国内の空港どうしは位置から（羽田⇄新千歳 約820km）', near(await n(`select public.co3_km('HND', 'CTS')`), 822, 15), await n(`select public.co3_km('HND', 'CTS')`));
// 国内線：羽田⇄那覇（本物の便がない表だけのとき、相手は羽田だけ → 那覇の国内の貨物 177,597t ÷ 365）
check('国内の貨物：那覇の相手が羽田だけなら 177,597 ÷ 365 ＝ 486.6t', near(await n(`select public.co3_cargo_tons('HND', 'OKA')`), 177597 / 365, 0.1), await n(`select public.co3_cargo_tons('HND', 'OKA')`));

// A は成田で KZ110 の出発の20分前にチェックイン → JA10KZ を見る。貨物の会社にして買って、成田⇄アンカレッジに入れる
await db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values
    ('${A}', ${ids.NRT}, 35.77, 140.39, 10, now() - interval '1 day' - interval '20 minutes', now() - interval '1 day' - interval '20 minutes')`);
await as(A, `select public.co_state()`);
await db.exec(`update companies set cash = 1000000, satisfaction = 60 where user_id = '${A}'`);
let s = await as(A, `select public.co3_set_policy('cargo')`);
check('方針を貨物にできる', s.policy === 'cargo', s.policy);
check('貨物の路線：見た貨物機の区間 成田⇄アンカレッジ', s.cargo_routes.some((r) => r.k === 'ANC-NRT' && r.intl && r.seen && Number(r.km) === 5330), s.cargo_routes);
s = await as(A, `select public.co3_buy_seen('JA10KZ')`);
const ac = (await db.query(`select id from aircraft where reg = 'JA10KZ'`)).rows[0].id;
check('貨物機でない機体は貨物の路線に入れられない', String(await as(A, `select public.co3_cargo_assign(999999, 'ANC-NRT')`)).includes('not a freighter'), null);
check('貨物の路線にない区間は入れられない', String(await as(A, `select public.co3_cargo_assign(${ac}, 'ICN-NRT')`)).includes('route not found'), null);
s = await as(A, `select public.co3_cargo_assign(${ac}, 'ANC-NRT')`);
const e = s.cargo.find((x) => x.k === 'ANC-NRT');
// 手計算：B747-8F 134t、5,330km は1日2便 → 運べる 2×134×0.85 ＝ 227.8t（391.2t より少ない）
//   運賃 0.25＋5,330×0.0003 ＝ 1.849。収益 ＝ 227.8 × 4（国際線）× 1.849 × はじめの上乗せ 1.5
//   費用 ＝ 2便 × 134t × 4 × 0.35 × 1.849。着陸料 ＝ 重さ 447.7t の段階の額 18.47 ＋ 騒音 1.0、×2便
const fare = 0.25 + 5330 * 0.0003, car = 2 * 134 * 0.85;
const rev = car * 4 * fare * 1.5, cost = 2 * 134 * 4 * 0.35 * fare;
const wf = 25 * 0.024 + 75 * 0.035 + 100 * 0.041 + (447.7 - 200) * 0.045, land = 2 * (wf + 1.0);
check('貨物機の分 391.2t・1日2便・運べる 227.8t', near(Number(e.tons), tons * 0.7, 0.1) && e.flights === 2 && near(Number(e.carried), car, 0.1), e);
check('収益（国際線 1t ＝ 4席分）', near(Number(e.revenue), rev, 0.05), { got: e.revenue, want: rev });
check('費用（積み込み35%で赤字）', near(Number(e.cost), cost, 0.05), { got: e.cost, want: cost });
check('着陸料（重さの額）', near(Number(e.landing), land, 0.05), { got: e.landing, want: land });
check('1日の収益 ＝ 手計算のもうけ', Number(s.gross) === Math.round(rev - cost - land), { got: s.gross, want: Math.round(rev - cost - land) });
check('貨物の会社は旅客の路線を持っても旅客を運ばない', (s.econ ?? []).every((x) => x.flights === 0), s.econ);

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('すべて OK');
