-- エアライン経営 co-v3：季節の需要（繁忙期。仕様書「季節の需要（繁忙期）」。格付けに関係なく全社に効く）
--   全国の時期（日本時間の日付）           旅行の客  仕事の客  運賃
--     年末年始 12/27〜1/4                  ×1.5     ×0.5     ×1.2
--     ゴールデンウィーク 4/28〜5/6          ×1.5     ×0.6     ×1.2
--     お盆 8/8〜8/18                       ×1.5     ×0.5     ×1.2
--     夏休み 7/20〜8/31（お盆を除く）        ×1.2     ×0.9     ×1.1
--     春休み 3/20〜4/5                     ×1.15    ×1.0     ×1.05
--     閑散期 1/15〜2月末・11月              ×0.85    ×1.0     ×0.9
--     3連休・シルバーウィークは祝日の表が要るので、あとで足す
--   地域のシーズン（旅行の客にかけ合わせる。路線の両端のうち地域に入る空港の平均）
--     北海道：冬 12/20〜3/10 ×1.4（2/1〜2/11 は ×1.6）・夏 7〜8月 ×1.3・春 4/1〜5/10 と11月 ×0.85
--     沖縄・南西諸島：夏 7〜9月 ×1.5・6月 ×1.2・冬 1〜2月 ×1.1
--     ほかのリゾート（奄美・屋久島・八丈島など）：夏 7〜9月 ×1.5・6月 ×1.2・冬 1〜2月 ×0.8
--     東北：8/1〜8/10 ×1.2・10月 ×1.1
--     京都・奈良に近い空港（伊丹・関西・神戸）：3/25〜4/10 と11月 ×1.15
--   試験では設定 co3.season_day で日付を決められる（ふだんは今日）
--   ゲームでは、路線の客の総数を「仕事の割合 × 仕事の倍率 ＋ 旅行の割合 × 旅行の倍率」倍にし、仕事の客の割合もそれに合わせて変える。運賃は収益にかける

-- 全国の時期
create or replace function co3.season_nat(p_day date, out name text, out lei numeric, out biz numeric, out fare numeric)
language sql immutable as $$
  with m as (select extract(month from p_day)::int as mo, extract(day from p_day)::int as dd)
  select case when (mo = 12 and dd >= 27) or (mo = 1 and dd <= 4) then '年末年始'
              when (mo = 4 and dd >= 28) or (mo = 5 and dd <= 6) then 'ゴールデンウィーク'
              when mo = 8 and dd between 8 and 18 then 'お盆'
              when (mo = 7 and dd >= 20) or mo = 8 then '夏休み'
              when (mo = 3 and dd >= 20) or (mo = 4 and dd <= 5) then '春休み'
              when (mo = 1 and dd >= 15) or mo = 2 or mo = 11 then '閑散期' end,
         case when (mo = 12 and dd >= 27) or (mo = 1 and dd <= 4) or (mo = 4 and dd >= 28) or (mo = 5 and dd <= 6) or (mo = 8 and dd between 8 and 18) then 1.5
              when (mo = 7 and dd >= 20) or mo = 8 then 1.2
              when (mo = 3 and dd >= 20) or (mo = 4 and dd <= 5) then 1.15
              when (mo = 1 and dd >= 15) or mo = 2 or mo = 11 then 0.85 else 1 end,
         case when (mo = 12 and dd >= 27) or (mo = 1 and dd <= 4) or (mo = 8 and dd between 8 and 18) then 0.5
              when (mo = 4 and dd >= 28) or (mo = 5 and dd <= 6) then 0.6
              when (mo = 7 and dd >= 20) or mo = 8 then 0.9 else 1 end,
         case when (mo = 12 and dd >= 27) or (mo = 1 and dd <= 4) or (mo = 4 and dd >= 28) or (mo = 5 and dd <= 6) or (mo = 8 and dd between 8 and 18) then 1.2
              when (mo = 7 and dd >= 20) or mo = 8 then 1.1
              when (mo = 3 and dd >= 20) or (mo = 4 and dd <= 5) then 1.05
              when (mo = 1 and dd >= 15) or mo = 2 or mo = 11 then 0.9 else 1 end
    from m
$$;
revoke all on function co3.season_nat(date) from public, anon, authenticated;

-- 地域（空港ごと）。地域に入らなければ null
create or replace function co3.season_region(p_iata text, p_day date) returns numeric
language sql immutable as $$
  with m as (select extract(month from p_day)::int as mo, extract(day from p_day)::int as dd)
  select case
    when p_iata = any (array['CTS','OKD','HKD','AKJ','KUH','OBO','MMB','WKJ','MBE','SHB','RIS','RBJ','OIR']) then
      case when mo = 2 and dd <= 11 then 1.6
           when (mo = 12 and dd >= 20) or mo in (1, 2) or (mo = 3 and dd <= 10) then 1.4
           when mo in (7, 8) then 1.3
           when mo = 4 or (mo = 5 and dd <= 10) or mo = 11 then 0.85 else 1 end
    when p_iata = any (array['OKA','ISG','MMY','SHI','UEO','KJP','AGJ','IEJ','MMD','KTD','TRA','HTR','OGN']) then
      case when mo in (7, 8, 9) then 1.5 when mo = 6 then 1.2 when mo in (1, 2) then 1.1 else 1 end
    when p_iata = any (array['ASJ','KKX','TKN','OKE','RNJ','KUM','TNE','HAC','OIM','MYE']) then
      case when mo in (7, 8, 9) then 1.5 when mo = 6 then 1.2 when mo in (1, 2) then 0.8 else 1 end
    when p_iata = any (array['AOJ','MSJ','HNA','AXT','ONJ','GAJ','SYO','SDJ','FKS']) then
      case when mo = 8 and dd <= 10 then 1.2 when mo = 10 then 1.1 else 1 end
    when p_iata = any (array['ITM','KIX','UKB']) then
      case when (mo = 3 and dd >= 25) or (mo = 4 and dd <= 10) or mo = 11 then 1.15 else 1 end
  end from m
$$;
revoke all on function co3.season_region(text, date) from public, anon, authenticated;

-- 路線の倍率（旅行・仕事・運賃）
create or replace function co3.season(p_a text, p_b text, p_day date default null, out lei numeric, out biz numeric, out fare numeric)
language sql stable as $$
  with d as (select coalesce(p_day, nullif(current_setting('co3.season_day', true), '')::date, (now() at time zone 'Asia/Tokyo')::date) as d),
  r as (select avg(x) as reg from (select co3.season_region(p_a, (select d from d)) x union all select co3.season_region(p_b, (select d from d))) z where x is not null)
  select (n.lei * coalesce((select reg from r), 1))::numeric, n.biz, n.fare from co3.season_nat((select d from d)) n
$$;
revoke all on function co3.season(text, text, date) from public, anon, authenticated;

-- 仕事の客の割合（季節で変える）と、客の総数の倍率
create or replace function co3.season_biz(p_biz numeric, p_a text, p_b text) returns numeric
language sql stable as $$
  select p_biz * s.biz / nullif(p_biz * s.biz + (1 - p_biz) * s.lei, 0) from co3.season(p_a, p_b) s
$$;
create or replace function co3.season_pool(p_biz numeric, p_a text, p_b text) returns numeric
language sql stable as $$ select p_biz * s.biz + (1 - p_biz) * s.lei from co3.season(p_a, p_b) s $$;
create or replace function co3.season_fare(p_a text, p_b text) returns numeric
language sql stable as $$ select s.fare from co3.season(p_a, p_b) s $$;
revoke all on function co3.season_biz(numeric, text, text) from public, anon, authenticated;
revoke all on function co3.season_pool(numeric, text, text) from public, anon, authenticated;
revoke all on function co3.season_fare(text, text) from public, anon, authenticated;

-- 画面用：いまの時期と、次の繁忙期（旅行の客が増える全国の時期）までの日数
create or replace function public.co3_season_view() returns jsonb
language sql stable security definer set search_path = public as $$
  with d as (select coalesce(nullif(current_setting('co3.season_day', true), '')::date, (now() at time zone 'Asia/Tokyo')::date) as d),
  n as (select * from co3.season_nat((select d from d))),
  nx as (select g::date as day, (co3.season_nat(g::date)).name as name, (co3.season_nat(g::date)).lei as lei
           from generate_series((select d from d) + 1, (select d from d) + 370, interval '1 day') g)
  select jsonb_build_object('name', n.name, 'lei', n.lei, 'biz', n.biz, 'fare', n.fare,
           'next', (select jsonb_build_object('name', x.name, 'days', x.day - (select d from d), 'lei', x.lei) from nx x
                     where x.lei > 1 and x.name is distinct from n.name order by x.day limit 1))
    from n
$$;
revoke all on function public.co3_season_view() from public, anon, authenticated;

do $do$
declare src text; n0 text;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3.season_biz' in src) = 0 then
    n0 := src;
    src := replace(src, $r$case e.kind when 'big' then 0.60 when 'resort' then 0.12 else 0.45 end as biz,$r$,
                        $r$co3.season_biz(case e.kind when 'big' then 0.60 when 'resort' then 0.12 else 0.45 end, e.a, e.b) as biz,
           co3.season_pool(case e.kind when 'big' then 0.60 when 'resort' then 0.12 else 0.45 end, e.a, e.b) as season_pool,$r$);
    src := replace(src, 'f.dem0 * co3.route_total_mult(f.n_other + 1) as pool,', 'f.dem0 * co3.route_total_mult(f.n_other + 1) * f.season_pool as pool,');
    src := replace(src, '* co3_extra_rev_mult(p_uid, k2.a, k2.b, k2.biz, k2.policy, k2.n_other) as rev,', '* co3_extra_rev_mult(p_uid, k2.a, k2.b, k2.biz, k2.policy, k2.n_other) * co3.season_fare(k2.a, k2.b) as rev,');
    if position('f.season_pool' in src) = 0 or position('co3.season_fare' in src) = 0 or position('co3.season_biz' in src) = 0 then raise exception 'co3_route_econ の形が変わっていて、季節の需要を入れられない'; end if;
    execute src;
  end if;
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_season_view' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、季節を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'season', case when v3 then co3_season_view() end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;
