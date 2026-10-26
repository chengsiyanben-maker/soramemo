-- エアライン経営 co-v3：今の仕様書（2026年10月26日）の計算をまとめた関数
--   ここにあるのは「数字を入れると答えを返す」だけの関数で、表は作らない・書き換えない。
--   画面や毎日の処理はまだ co-v2 のまま。次の段階で、co-v2 の関数をこれらに置き換える。
--   数字を変えるときは、仕様書とここの両方を直す。
--   使う単位：お金はゲームの額（B737-800 の値段が 15,300）、客は人、貨物はトン、距離は km。

create schema if not exists co3;
revoke all on schema co3 from public, anon, authenticated;
grant usage on schema co3 to service_role;

-- ── 運賃と方針 ───────────────────────────────────────────────
-- 普通席1人の運賃（FSC のとき）
create or replace function co3.fare(p_km numeric) returns numeric
language sql immutable as $$ select 0.25 + p_km * 0.0003 $$;

-- 方針ごとの数字：運賃の倍率・赤字になる搭乗率・仕事の客の倍率・旅行の客の倍率・上級席の割合
create or replace function co3.policy(p text,
  out fare_mult numeric, out breakeven numeric, out biz_mult numeric, out leisure_mult numeric, out premium_share numeric)
language sql immutable as $$
  select f, b, bz, ls, pr from (values
    ('fsc', 1.00, 0.50, 1.0, 0.85, 0.2),
    ('mcc', 0.85, 0.45, 1.1, 1.15, 0.1),
    ('lcc', 0.72, 0.40, 0.4, 1.70, 0.0)
  ) t(k, f, b, bz, ls, pr) where k = p
$$;

-- 1便の運航の費用：席の数 × 赤字になる搭乗率 × 運賃（空席でも同じだけかかる）
create or replace function co3.flight_cost(p_policy text, p_seats numeric, p_km numeric) returns numeric
language sql immutable as $$
  select p_seats * (co3.policy(p_policy)).breakeven * co3.fare(p_km) * (co3.policy(p_policy)).fare_mult
$$;

-- 運賃の分け方：同じ路線の会社の運賃（普通の運賃を1とした割合）の重み。旅行の客は 1/運賃³、仕事の客は 1/運賃
create or replace function co3.fare_weight(p_fare_rel numeric, p_business boolean) returns numeric
language sql immutable as $$ select case when p_business then 1 / p_fare_rel else 1 / power(p_fare_rel, 3) end $$;

-- ── 空港の大きさ ─────────────────────────────────────────────
-- 1日の乗降客数（空港管理状況調書の前の年 ÷ 365）で5段階。統計にない空港は小規模、海外は拠点
create or replace function co3.airport_size(p_pax_per_day numeric, p_overseas boolean default false) returns text
language sql immutable as $$
  select case when p_overseas then 'hub'
              when p_pax_per_day >= 150000 then 'xl'
              when p_pax_per_day >= 30000 then 'hub'
              when p_pax_per_day >= 7000 then 'large'
              when p_pax_per_day >= 1500 then 'mid'
              else 'small' end
$$;

-- ── 路線のお客さん ───────────────────────────────────────────
-- 本物の便がある路線の1日のお客さん（1社のとき）＝ 本物の便の数（前の28日の平均）× 平均の座席 × 0.7 × 0.5
create or replace function co3.route_pax_real(p_flights numeric, p_avg_seats numeric) returns numeric
language sql immutable as $$ select p_flights * p_avg_seats * 0.7 * 0.5 $$;

-- 本物の便がない路線：A の旅客数 × B の旅客数 ÷ 全国の合計 ÷ 365 × 0.5 × 距離の係数、最低10人
create or replace function co3.route_pax_nodirect(p_pax_a numeric, p_pax_b numeric, p_total numeric, p_km numeric) returns numeric
language sql immutable as $$
  select greatest(10, p_pax_a * p_pax_b / p_total / 365 * 0.5
    * case when p_km < 300 then 0.3 when p_km < 600 then 0.7 else 1.0 end)
$$;

-- 同じ路線を飛ばす会社が n 社のとき、客の総数の倍率（最大3倍）と1社あたりの割合
create or replace function co3.route_total_mult(p_n integer) returns numeric
language sql immutable as $$ select least(3, 1 + 0.5 * (greatest(p_n, 1) - 1))::numeric $$;
create or replace function co3.route_share(p_n integer) returns numeric
language sql immutable as $$ select co3.route_total_mult(p_n) / greatest(p_n, 1) $$;

-- 地元の応援：本拠地を発着する自社の路線の客。大規模 ×3・中規模 ×4・小規模 ×5（拠点以上 ×1）。
--   本拠地にして30日たってから効く。最低500人は本物の便がある路線だけ（10/26）
create or replace function co3.local_support(p_size text, p_own_pax numeric, p_has_real boolean, p_days_as_home integer) returns numeric
language sql immutable as $$
  select case when p_days_as_home < 30 then p_own_pax
    else case when p_has_real then greatest(500, x) else x end end
  from (select p_own_pax * case p_size when 'large' then 3 when 'mid' then 4 when 'small' then 5 else 1 end as x) t
$$;

-- ── 収益の上乗せ ─────────────────────────────────────────────
-- 「会社」「空港」「機体」の3つの組。組の中は足し算、組どうしは掛け算。上限は +40%・+60%・+25%
create or replace function co3.bonus_mult(p_company numeric, p_airport numeric, p_aircraft numeric) returns numeric
language sql immutable as $$
  select (1 + least(0.40, greatest(0, p_company))) * (1 + least(0.60, greatest(0, p_airport))) * (1 + least(0.25, greatest(0, p_aircraft)))
$$;

-- はじめの上乗せ：1〜60日目 1.5倍、61〜90日目 1.3倍、91〜120日目 1.15倍
create or replace function co3.newbie_mult(p_day integer) returns numeric
language sql immutable as $$ select case when p_day <= 60 then 1.5 when p_day <= 90 then 1.3 when p_day <= 120 then 1.15 else 1 end::numeric $$;

-- ── 着陸料（10/26）─────────────────────────────────────────
-- 騒音の額：小型機・ヘリ 0、プロペラ機 0.2、小さいジェット 0.6、大きいジェット 1.0
create or replace function co3.noise_fee(p_kind text) returns numeric
language sql immutable as $$ select case p_kind when 'prop' then 0.2 when 'jet' then 0.6 when 'wide' then 1.0 else 0 end::numeric $$;

-- 国際線（と貨物機）の重さの額：最大の重さ（トン）に段階の単価。羽田の国際線は1トン 0.065
create or replace function co3.weight_fee(p_mtow numeric, p_haneda boolean) returns numeric
language sql immutable as $$
  select case when p_haneda then p_mtow * 0.065 else
    least(p_mtow, 25) * 0.024
    + greatest(0, least(p_mtow, 100) - 25) * 0.035
    + greatest(0, least(p_mtow, 200) - 100) * 0.041
    + greatest(0, p_mtow - 200) * 0.045 end
$$;

-- 1回の着陸の着陸料。国内線の旅客便は乗っていた客1人 0.027＋騒音、国際線と貨物機は重さ＋騒音（羽田の国際線は騒音1.5倍）。離島は半分
create or replace function co3.landing_fee(p_intl boolean, p_freighter boolean, p_pax numeric, p_noise text,
                                           p_mtow numeric, p_haneda boolean, p_island boolean) returns numeric
language sql immutable as $$
  select (case when p_intl or p_freighter
            then co3.weight_fee(p_mtow, p_intl and p_haneda) + co3.noise_fee(p_noise) * case when p_intl and p_haneda then 1.5 else 1 end
            else p_pax * 0.027 + co3.noise_fee(p_noise) end)
         * case when p_island then 0.5 else 1 end
$$;

-- ── 発着枠と混雑料金（混雑空港5つ）──────────────────────────
-- ゲームの枠（1日の便数）＝ 時間値 × 運用時間 × ゲームの倍率（遊んでいる会社 ÷ 50、1より小さいときは1）
create or replace function co3.slot_capacity(p_hourly numeric, p_hours numeric, p_active_companies integer) returns numeric
language sql immutable as $$ select p_hourly * p_hours * greatest(1, p_active_companies / 50.0) $$;

-- 申し込みを分ける：合計が枠に収まればそのまま。超えたら申し込みの割合で分け、どの会社も最低1日4便（申し込みより多くはしない）
create or replace function co3.slot_allot(p_request integer, p_total_requests integer, p_capacity numeric) returns integer
language sql immutable as $$
  select case when p_total_requests <= p_capacity then p_request
    else greatest(least(4, p_request), floor(p_request * p_capacity / p_total_requests)::int) end
$$;

-- 混雑料金の割合：（混み具合 − 1）× 20%、上限20%。混み具合＝その月の全社の申し込み ÷ ゲームの枠。羽田の地方の枠の路線は半分
create or replace function co3.congestion_rate(p_total_requests numeric, p_capacity numeric, p_regional_slot boolean default false) returns numeric
language sql immutable as $$
  select least(0.20, greatest(0, (p_total_requests / p_capacity - 1) * 0.20)) * case when p_regional_slot then 0.5 else 1 end
$$;

-- ── 機体 ───────────────────────────────────────────────────
-- 翼の幅の区分（ICAO）：A・B 24m未満、C 36m未満、D 52m未満、E 65m未満、F 80m未満
create or replace function co3.wing_class(p_span_m numeric) returns text
language sql immutable as $$
  select case when p_span_m < 24 then 'B' when p_span_m < 36 then 'C' when p_span_m < 52 then 'D' when p_span_m < 65 then 'E' else 'F' end
$$;

-- 空港の上限の区分：前の365日の本物の発着が50回以上なら、本物で発着したいちばん大きい区分。
--   少ない空港は滑走路の長さと幅で（ジェット機は別に 2,000m×45m が要る）。E・F は本物の記録がある空港だけ
create or replace function co3.airport_wing_cap(p_max_seen text, p_movements_365 integer, p_rwy_len numeric, p_rwy_width numeric) returns text
language sql immutable as $$
  select case when p_movements_365 >= 50 and p_max_seen is not null then p_max_seen
    when p_rwy_len < 1200 or p_rwy_width < 30 then 'B'
    when p_rwy_len >= 2500 and p_rwy_width >= 45 then greatest('D', coalesce(p_max_seen, 'B'))
    else 'C' end
$$;

-- その機体がその空港に降りられるか：区分が上限以下で、記録が少ない空港のジェット機は 2,000m×45m の滑走路が要る。
--   空港の決まり（伊丹の3発機・4発機なし、調布は小型機だけ）は運営の一覧で別に見る
create or replace function co3.can_land(p_ac_class text, p_jet boolean, p_cap text, p_movements_365 integer,
                                        p_rwy_len numeric, p_rwy_width numeric) returns boolean
language sql immutable as $$
  select p_ac_class <= p_cap and (not p_jet or p_movements_365 >= 50 or (p_rwy_len >= 2000 and p_rwy_width >= 45))
$$;

-- 機体の値段：持っている機体1機ごとに +25%（小型機・プロペラ機・ヘリは0.5機と数える）、会社で最初の1機だけ半額
create or replace function co3.count_weight(p_small_or_prop boolean) returns numeric
language sql immutable as $$ select case when p_small_or_prop then 0.5 else 1 end::numeric $$;
create or replace function co3.aircraft_price(p_base numeric, p_owned_weighted numeric, p_first boolean) returns numeric
language sql immutable as $$ select p_base * (1 + 0.25 * p_owned_weighted) * case when p_first then 0.5 else 1 end $$;

-- ── 貨物（10/25〜26）───────────────────────────────────────
-- 国内線の路線の貨物（1日・トン、両方向）＝ 小さいほうの空港の国内の貨物 × 相手の大きさ ÷ その空港の相手の大きさの合計 ÷ 365
create or replace function co3.cargo_dom_route(p_small_t numeric, p_partner_t numeric, p_partners_sum numeric) returns numeric
language sql immutable as $$ select p_small_t * p_partner_t / p_partners_sum / 365 $$;
-- 国際線の区間の貨物 ＝ 日本の空港の国際の貨物 ÷ 365 × その区間の便数 ÷ その空港の国際線の便数（前の28日）
create or replace function co3.cargo_intl_route(p_airport_intl_t numeric, p_route_flights numeric, p_airport_intl_flights numeric) returns numeric
language sql immutable as $$ select p_airport_intl_t / 365 * p_route_flights / nullif(p_airport_intl_flights, 0) $$;
-- 旅客の会社の床下が取れるのは3割まで、残りを貨物機で取り合う。貨物1トン＝普通席2.5席分、国際線は4席分
create or replace function co3.cargo_for_freighters(p_route_t numeric) returns numeric
language sql immutable as $$ select p_route_t * 0.7 $$;
create or replace function co3.cargo_seat_eq(p_intl boolean) returns numeric
language sql immutable as $$ select case when p_intl then 4.0 else 2.5 end $$;

-- ── プライベートジェット（10/25）───────────────────────────
-- 路線の1日の VIP の客 ＝ その路線の客（1社のとき）× リゾート20%・国際線16%・大きい空港どうし8%・地方4%
create or replace function co3.vip_pax(p_route_pax numeric, p_kind text) returns numeric
language sql immutable as $$
  select p_route_pax * case p_kind when 'resort' then 0.20 when 'intl' then 0.16 when 'big' then 0.08 else 0.04 end
$$;
-- VIP 席の埋まり方の上限：リゾート90%・国際線80%・大きい空港どうし50%・地方25%。VIP 席1席＝普通席25席分
create or replace function co3.vip_fill_cap(p_kind text) returns numeric
language sql immutable as $$ select case p_kind when 'resort' then 0.90 when 'intl' then 0.80 when 'big' then 0.50 else 0.25 end::numeric $$;
create or replace function co3.vip_seat_eq() returns numeric language sql immutable as $$ select 25::numeric $$;

-- ── 地域航空（10/25）──────────────────────────────────────
-- 仕事の1日の稼ぎ：遊覧 席数 × 3.8 × 観光地の度合い（0.5〜1.5）、チャーター・撮影・測量 席数 × 4.3
create or replace function co3.regional_job(p_seats numeric, p_kind text, p_degree numeric default 1) returns numeric
language sql immutable as $$
  select case when p_kind = 'sightseeing' then p_seats * 3.8 * least(1.5, greatest(0.5, p_degree)) else p_seats * 4.3 end
$$;
-- 遊覧の上限：1空港1社あたり 観光地の度合い × 6機。チャーター：前の7日にチェックインした空港ごとに週3件
create or replace function co3.sightseeing_cap(p_degree numeric) returns integer
language sql immutable as $$ select floor(least(1.5, greatest(0.5, p_degree)) * 6)::int $$;
create or replace function co3.charter_jobs_per_week(p_airports_checked_7d integer) returns integer
language sql immutable as $$ select 3 * p_airports_checked_7d $$;

-- 中の計算なので、アプリ（anon・authenticated）からは呼ばない
revoke all on all functions in schema co3 from public, anon, authenticated;
grant execute on all functions in schema co3 to service_role;
