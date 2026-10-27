-- エアライン経営 co-v3：会社の格付け（仕様書「会社の格付けと機能の解放」）
--   1 地域航空会社：はじめから
--   2 国内線の航空会社：路線5本・機体3機
--   3 国内大手：路線12本・機体8機・評判★3・始めてから30日
--   4 国際航空会社：国際線1本・路線25本・機体20機・評判★4（国際線がない会社は 路線30本・機体25機・評判★4 でもよい）
--   5 世界の航空会社：国際線5本・路線40本・機体35機・評判★5
--   上がるのは順番に1つずつではなく、満たしているいちばん上まで。いちど上がったら下がらない
--   会社の状態（co_state）を開くたびに確かめる。上がった日を残す（ニュース・解放の紹介に使う）
--   解放の鍵（いま作ってあるもの）：運賃の5段階・機内食と荷物 ＝ 格付け2から、上級席の割合 ＝ 格付け4から
--     格付け1のうちは運賃は普通・機内食なし・荷物無料（10/27 の決定）、上級席は方針のはじめの割合
--   機体はまだリースがないので、持っている機体の数で数える

alter table public.companies add column if not exists rating smallint not null default 1 check (rating between 1 and 5);
alter table public.companies add column if not exists rating_at timestamptz;
alter table public.companies enable row level security;

-- いまの数（路線・国際線・機体・評判の星・始めてからの日数）
create or replace function public.co3_rating_have(p_uid uuid,
  out routes integer, out intl integer, out fleet integer, out stars integer, out days integer)
language sql stable security definer set search_path = public as $$
  select (select count(*) from co_routes(p_uid))::int,
         (select count(*) from co_routes(p_uid) r where r.intl)::int,
         (select count(*) from aircraft a where a.user_id = p_uid)::int,
         rep_stars(co_rep_points(p_uid)),
         coalesce((select (now() at time zone 'Asia/Tokyo')::date - (c.created_at at time zone 'Asia/Tokyo')::date from companies c where c.user_id = p_uid), 0)::int
$$;
revoke all on function public.co3_rating_have(uuid) from public, anon, authenticated;

-- 満たしているいちばん上の格付け
create or replace function co3.rating_of(p_routes integer, p_intl integer, p_fleet integer, p_stars integer, p_days integer) returns integer
language sql immutable as $$
  select case
    when p_intl >= 5 and p_routes >= 40 and p_fleet >= 35 and p_stars >= 5 then 5
    when p_stars >= 4 and ((p_intl >= 1 and p_routes >= 25 and p_fleet >= 20) or (p_routes >= 30 and p_fleet >= 25)) then 4
    when p_routes >= 12 and p_fleet >= 8 and p_stars >= 3 and p_days >= 30 then 3
    when p_routes >= 5 and p_fleet >= 3 then 2
    else 1 end
$$;
revoke all on function co3.rating_of(integer, integer, integer, integer, integer) from public, anon, authenticated;

-- 確かめて上げる（下げない）
create or replace function public.co3_rating_refresh(p_uid uuid) returns integer
language plpgsql security definer set search_path = public as $$
declare h record; r integer; cur integer;
begin
  select rating into cur from companies where user_id = p_uid;
  if cur is null then return null; end if;
  select * into h from co3_rating_have(p_uid);
  r := co3.rating_of(h.routes, h.intl, h.fleet, h.stars, h.days);
  if r > cur then update companies set rating = r, rating_at = now() where user_id = p_uid; return r; end if;
  return cur;
end;
$$;
revoke all on function public.co3_rating_refresh(uuid) from public, anon, authenticated;

create or replace function public.co3_rating_need(p_uid uuid) returns integer
language sql stable security definer set search_path = public as $$ select rating from companies where user_id = p_uid $$;
revoke all on function public.co3_rating_need(uuid) from public, anon, authenticated;

-- 解放の鍵：運賃・サービスは2から、上級席は4から（関数の頭に足す）
do $do$
declare f text; need int; src text;
begin
  for f, need in select * from (values ('public.co3_set_fare(text,integer)', 2), ('public.co3_set_service(text,text)', 2), ('public.co3_set_premium(integer)', 4)) v(f, n) loop
    select pg_get_functiondef(f::regprocedure) into src;
    if position('rating required' in src) = 0 then
      if position('perform co_settle(uid);' in src) = 0 then raise exception '% の形が変わっていて、格付けの鍵を入れられない', f; end if;
      src := replace(src, 'perform co_settle(uid);',
        format('perform co_settle(uid);' || chr(10) || '  if coalesce(co3_rating_need(uid), 1) < %s then raise exception ''rating required %s''; end if;', need, need));
      execute src;
    end if;
  end loop;
end
$do$;

-- 会社の状態：開くたびに格付けを確かめ、いまの格付け・上がった時刻・いまの数を出す
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_rating_refresh' in src) = 0 then
    if position('perform co_check(uid);' in src) = 0 or position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then
      raise exception 'co_state の形が変わっていて、格付けを入れられない';
    end if;
    src := replace(src, 'perform co_check(uid);', 'perform co_check(uid);' || chr(10) || '  if v3 then perform co3_rating_refresh(uid); end if;');
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'rating', case when v3 then (select rating from companies where user_id = uid) end,
    'rating_at', case when v3 then (select rating_at from companies where user_id = uid) end,
    'rating_have', case when v3 then (select to_jsonb(h) from co3_rating_have(uid) h) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;
