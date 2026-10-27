-- エアライン経営 co-v3：シーズン順位（仕様書「会社の価値とランキング」。3か月ごと）
--   シーズン：1〜3月（冬）・4〜6月（春）・7〜9月（夏）・10〜12月（秋）。日本時間で区切る
--   順位は「そのシーズンに伸ばした会社の価値の割合（伸び率）」。はじめの価値は、シーズンに入ってからいちばん早い毎朝の記録（co_rank_days）
--     （はじめの価値が 5,000 より小さいときは 5,000 で割る。始めたばかりの会社が極端な率にならないように）
--   部門：格付け1〜2・3・4〜5 の3つ。ほかの会社は毎朝の記録、自分はいまの価値
--   シーズンが終わったら（次のシーズンの1日の朝）、部門ごとに上位10%に印、1位に称号（co3_awards）。会社・機体・資金は消えない
--   出さない設定の会社は順位に出ない（印・称号もつかない）。月ごとの表彰は、あとで足す

create table if not exists public.co3_awards (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  kind text not null check (kind in ('season_top10', 'season_champ')),
  ref text not null,
  label text not null,
  created_at timestamptz not null default now(),
  unique (user_id, kind, ref)
);
alter table public.co3_awards enable row level security;
revoke all on public.co3_awards from public, anon, authenticated;
grant select on public.co3_awards to authenticated;
drop policy if exists co3_awards_own on public.co3_awards;
create policy co3_awards_own on public.co3_awards for select to authenticated using (user_id = (select auth.uid()));

create or replace function co3.season_name(p_start date) returns text
language sql immutable as $$
  select extract(year from p_start)::int || '年' || case extract(month from p_start)::int when 1 then '冬' when 4 then '春' when 7 then '夏' else '秋' end || 'シーズン'
$$;
revoke all on function co3.season_name(date) from public, anon, authenticated;

create or replace function co3.division(p_rating integer) returns text
language sql immutable as $$ select case when coalesce(p_rating, 1) <= 2 then '1-2' when p_rating = 3 then '3' else '4-5' end $$;
revoke all on function co3.division(integer) from public, anon, authenticated;

-- そのシーズンの伸び率（会社ごと）。p_end は比べる日（null ならいちばん新しい記録）
create or replace function public.co3_season_growth(p_start date, p_end date default null)
returns table (user_id uuid, base bigint, value bigint, growth numeric)
language sql stable security definer set search_path = public as $$
  with r as (select * from co_rank_days where day >= p_start and day < (p_start + interval '3 months')::date and (p_end is null or day <= p_end)),
  b as (select distinct on (r.user_id) r.user_id, r.value from r order by r.user_id, r.day),
  l as (select distinct on (r.user_id) r.user_id, r.value from r order by r.user_id, r.day desc)
  select b.user_id, b.value, l.value, round((l.value - b.value)::numeric / greatest(b.value, 5000), 4) from b join l using (user_id)
$$;
revoke all on function public.co3_season_growth(date, date) from public, anon, authenticated;

-- 画面用：自分の部門の順位
create or replace function public.co3_season_rank() returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); s date := date_trunc('quarter', (now() at time zone 'Asia/Tokyo'))::date; dv text; me_b bigint; me_v bigint; me_g numeric;
        out jsonb; me_rank int; total int; cut numeric;
begin
  perform co_check(uid);
  dv := co3.division((select rating from companies where user_id = uid));
  select g.base into me_b from co3_season_growth(s) g where g.user_id = uid;
  me_v := co_value(uid);
  me_b := coalesce(me_b, me_v);
  me_g := round((me_v - me_b)::numeric / greatest(me_b, 5000), 4);
  with o as (
    select g.user_id, c.name, g.growth, false as me from co3_season_growth(s) g join companies c on c.user_id = g.user_id
     where g.user_id <> uid and not c.hide_rank and co3.division(c.rating) = dv
    union all select uid, (select name from companies where user_id = uid), me_g, true
  ), x as (select *, rank() over (order by growth desc, me desc) as no, count(*) over () as n from o)
  select (select no from x where me), (select count(*) from x),
         (select min(growth) from x where no <= greatest(1, ceil(n * 0.1))),
         coalesce(jsonb_agg(jsonb_build_object('no', no, 'name', name, 'growth', growth, 'me', me) order by no, me desc)
                  filter (where no <= 20 or abs(no - (select no from x where me)) <= 2), '[]'::jsonb)
    into me_rank, total, cut, out from x;
  return jsonb_build_object('season', co3.season_name(s), 'start', s, 'end', (s + interval '3 months' - interval '1 day')::date,
    'days_left', (s + interval '3 months')::date - (now() at time zone 'Asia/Tokyo')::date, 'division', dv,
    'rank', me_rank, 'total', total, 'growth', me_g, 'top10_cut', cut, 'rows', out,
    'awards', coalesce((select jsonb_agg(jsonb_build_object('kind', a.kind, 'label', a.label, 'at', a.created_at) order by a.created_at desc) from co3_awards a where a.user_id = uid), '[]'::jsonb));
end;
$$;
revoke all on function public.co3_season_rank() from public, anon;
grant execute on function public.co3_season_rank() to authenticated;

-- シーズンを締める（印と称号）。p_start は締めるシーズンの1日（null なら前のシーズン）
create or replace function public.co3_season_close(p_start date default null) returns integer
language plpgsql security definer set search_path = public as $$
declare s date := coalesce(p_start, (date_trunc('quarter', (now() at time zone 'Asia/Tokyo')) - interval '3 months')::date); n int := 0; k int;
begin
  with x as (
    select g.user_id, co3.division(c.rating) as dv, rank() over (partition by co3.division(c.rating) order by g.growth desc) as no,
           count(*) over (partition by co3.division(c.rating)) as cnt
      from co3_season_growth(s, (s + interval '3 months' - interval '1 day')::date) g join companies c on c.user_id = g.user_id
     where not c.hide_rank
  ), t as (
    insert into co3_awards (user_id, kind, ref, label)
    select x.user_id, 'season_top10', to_char(s, 'YYYY-MM'), co3.season_name(s) || ' 上位10%（格付け' || x.dv || 'の部門）'
      from x where x.no <= greatest(1, ceil(x.cnt * 0.1))
    union all
    select x.user_id, 'season_champ', to_char(s, 'YYYY-MM'), co3.season_name(s) || ' 1位（格付け' || x.dv || 'の部門）'
      from x where x.no = 1
    on conflict do nothing returning 1
  ) select count(*) into k from t;
  n := n + coalesce(k, 0);
  return n;
end;
$$;
revoke all on function public.co3_season_close(date) from public, anon, authenticated;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    -- 毎朝6時（日本時間。毎朝の記録のあと）に動かし、1・4・7・10月の1日だけ、前のシーズンを締める（2回動いても同じ印は増えない）
    execute $q$ select cron.schedule('co3-season-close', '0 21 * * *', $job$
      select public.co3_season_close() where extract(day from (now() at time zone 'Asia/Tokyo')) = 1 and extract(month from (now() at time zone 'Asia/Tokyo'))::int in (1, 4, 7, 10) $job$) $q$;
  end if;
end
$$;
