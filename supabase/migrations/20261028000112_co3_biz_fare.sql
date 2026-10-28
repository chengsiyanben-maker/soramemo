-- エアライン経営 co-v3：仕事の客が多い路線の運賃の上がり方（10/27 企画者が決定）
--   上がり方 ＝ (仕事の客の割合 − 30%) ÷ 30% × 20%（0〜20%）。FSC とミドルコストだけ（LCC などは 0）
--   仕事の客の割合は路線の種類で決まる（大きい空港どうし 60% → +20%、地方 45% → +10%、リゾート 12% → 0%）
--   仕事の客の運賃だけに掛ける（上級席の客は全員仕事の客、普通席は乗った人のうち仕事の客の分だけ）
--   他社との取り合い（運賃の重み）には入れない。表は変えない（関数だけ）
create or replace function co3.biz_fare_rise(p_policy text, p_biz numeric) returns numeric
language sql immutable as $$
  select case when p_policy in ('fsc', 'mcc') then least(0.2, greatest(0, (p_biz - 0.3) / 0.3 * 0.2)) else 0 end::numeric
$$;
revoke all on function co3.biz_fare_rise(text, numeric) from public, anon, authenticated;

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('biz_fare_rise' in src) = 0 then
    if position('* co3_sat_mult(g.user_id) as share_prem' in src) = 0
       or position('(k2.car_e + k2.car_p * co3.premium_fare(k2.wide)) * co3.fare(k2.km)' in src) = 0 then
      raise exception 'co3_route_econ の形が変わっていて、仕事の客の運賃を入れられない';
    end if;
    -- 自社の客のうち仕事の客の割合
    src := replace(src, '* co3_sat_mult(g.user_id) as share_prem',
      '* co3_sat_mult(g.user_id) as share_prem,
           g.biz * (co3.policy(g.policy)).biz_mult * g.sb
             / nullif(g.biz * (co3.policy(g.policy)).biz_mult * g.sb + (1 - g.biz) * (co3.policy(g.policy)).leisure_mult * g.sl, 0) as biz_frac');
    -- 普通席の仕事の客 ＝ 自社の仕事の客 − 上級席の客（普通席に乗った人の割合で）
    src := replace(src, '(k2.car_e + k2.car_p * co3.premium_fare(k2.wide)) * co3.fare(k2.km)',
      '(k2.car_e * (1 + co3.biz_fare_rise(k2.policy, k2.biz)
                          * least(1, greatest(0, k2.own * coalesce(k2.biz_frac, 0) - k2.car_p) / nullif(k2.own - k2.car_p, 0)))
             + k2.car_p * co3.premium_fare(k2.wide) * (1 + co3.biz_fare_rise(k2.policy, k2.biz))) * co3.fare(k2.km)');
    execute src;
  end if;
end
$do$;
