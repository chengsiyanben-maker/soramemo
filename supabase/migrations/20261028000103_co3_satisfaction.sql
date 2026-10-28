-- エアライン経営 co-v3：満足度（仕様書 第7章）
--   満足度は会社ごとに0〜100。始まりは40（固定。企画者の指示があるまで変えない）。
--   毎日、日本時間の深夜3時に「目標値」に向かって（目標値 − 満足度）× 0.1 だけ動く（±3まで）。
--   目標値 ＝ 50 ＋ サービス ＋ 運航 ＋ 対応 ＋ 方針の補正。
--     いま co-v3 で決まるもの：席を詰める −4（LCC）、新しい機体（会社に入れて90日まで）の割合 ×6、古さ 0〜−8、方針の補正 FSC −5・ミドルコスト 0・LCC +5。
--     機内食・Wi-Fi・ラウンジ・荷物・マイル・SAF・定時率・欠航・乗員の経験・神対応は、その機能を作るときに足す（今は0）
--   お客さん：満足度が60から5離れるごとに、仕事の客も旅行の客も ±1%（最大 ±8%）

alter table public.companies add column if not exists satisfaction numeric not null default 40 check (satisfaction between 0 and 100);
alter table public.companies add column if not exists satisfaction_day date;

-- 目標値の中身（画面に出す。上げるためにできることもここから選ぶ）
create or replace function public.co3_satisfaction_parts(p_uid uuid,
  out base numeric, out packed numeric, out new_share numeric, out aging numeric, out policy_adj numeric, out target numeric)
language sql stable security definer set search_path = public as $$
  with c as (select policy from companies where user_id = p_uid),
  f as (select count(*) as n,
               count(*) filter (where bought_at > now() - interval '90 days') as fresh,
               avg(ac_age(bought_at)) as age
          from aircraft where user_id = p_uid)
  select 50::numeric,
         case when c.policy = 'lcc' then -4 else 0 end::numeric,
         round(case when f.n > 0 then 6.0 * f.fresh / f.n else 0 end, 2),
         round(case when f.n > 0 then -8 * (1 - f.age) / 0.2 else 0 end, 2),
         case c.policy when 'fsc' then -5 when 'lcc' then 5 else 0 end::numeric,
         greatest(0, least(100, 50 + case when c.policy = 'lcc' then -4 else 0 end
                                  + case when f.n > 0 then 6.0 * f.fresh / f.n else 0 end
                                  + case when f.n > 0 then -8 * (1 - f.age) / 0.2 else 0 end
                                  + case c.policy when 'fsc' then -5 when 'lcc' then 5 else 0 end))
    from c cross join f
$$;
revoke all on function public.co3_satisfaction_parts(uuid) from public, anon, authenticated;

-- 1日の動き：（目標値 − 満足度）× 0.1、±3まで
create or replace function co3.satisfaction_step(p_now numeric, p_target numeric) returns numeric
language sql immutable as $$ select greatest(0, least(100, p_now + greatest(-3, least(3, (p_target - p_now) * 0.1)))) $$;

-- お客さんの倍率：60から5離れるごとに ±1%（最大 ±8%）
create or replace function co3.satisfaction_mult(p_sat numeric) returns numeric
language sql immutable as $$ select 1 + greatest(-0.08, least(0.08, trunc((p_sat - 60) / 5) * 0.01)) $$;

-- 毎日の処理（日本時間の深夜3時）。同じ日に2回動かしても1回分だけ
create or replace function public.co3_satisfaction_refresh() returns integer
language plpgsql security definer set search_path = public as $$
declare d date := ((now() at time zone 'Asia/Tokyo') - interval '3 hours')::date; cnt integer;
begin
  update companies c set satisfaction = round(co3.satisfaction_step(c.satisfaction, (co3_satisfaction_parts(c.user_id)).target), 2),
                         satisfaction_day = d
   where c.satisfaction_day is distinct from d;
  get diagnostics cnt = row_count;
  return cnt;
end;
$$;
revoke all on function public.co3_satisfaction_refresh() from public, anon, authenticated;

-- 路線ごとの内わけ：お客さんに満足度の倍率を掛ける（ほかは 20261026000092 と同じ）
create or replace function public.co3_sat_mult(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select co3.satisfaction_mult(coalesce((select satisfaction from companies where user_id = p_uid), 40))
$$;
revoke all on function public.co3_sat_mult(uuid) from public, anon, authenticated;

do $do$
declare src text;
begin
  -- co3_route_econ の「方針の客の取り方」の行に、満足度の倍率を掛ける
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_sat_mult' in src) = 0 then
    src := replace(src,
      'g.pool * (g.biz * (co3.policy(g.policy)).biz_mult * g.sb + (1 - g.biz) * (co3.policy(g.policy)).leisure_mult * g.sl) as share_pax,',
      'g.pool * (g.biz * (co3.policy(g.policy)).biz_mult * g.sb + (1 - g.biz) * (co3.policy(g.policy)).leisure_mult * g.sl) * co3_sat_mult(g.user_id) as share_pax,');
    src := replace(src,
      'g.pool * g.biz * (co3.policy(g.policy)).biz_mult * g.sb * co3.premium_share(g.kind, g.intl, g.small_end) as share_prem',
      'g.pool * g.biz * (co3.policy(g.policy)).biz_mult * g.sb * co3.premium_share(g.kind, g.intl, g.small_end) * co3_sat_mult(g.user_id) as share_prem');
    if position('co3_sat_mult' in src) = 0 then raise exception 'co3_route_econ の形が変わっていて、満足度を入れられない'; end if;
    execute src;
  end if;
end
$do$;

-- 会社の状態に満足度と目標値の中身を足す（co_state の最後の要素に足す）
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('satisfaction' in src) = 0 then
    src := replace(src,
      $r$'premium', coalesce(c.premium, co3.premium_default(c.policy)),$r$,
      $r$'premium', coalesce(c.premium, co3.premium_default(c.policy)),
    'satisfaction', c.satisfaction, 'sat_mult', co3.satisfaction_mult(c.satisfaction),
    'sat_parts', (select to_jsonb(p) from co3_satisfaction_parts(uid) p),$r$);
    if position('satisfaction' in src) = 0 then raise exception 'co_state の形が変わっていて、満足度を入れられない'; end if;
    execute src;
  end if;
end
$do$;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 日本時間の深夜3時（18:00 UTC）
  execute $q$ select cron.schedule('co3-satisfaction', '0 18 * * *', $job$ select public.co3_satisfaction_refresh() $job$) $q$;
end
$outer$;
