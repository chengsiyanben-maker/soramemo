-- 滑走路の学習の記録に、離陸も入れる：離陸した滑走路と、どの方面へ向かったか（空港から30km・60kmの円を出た方角）
alter table public.arr_watch add column if not exists dir text not null default 'arr' check (dir in ('arr', 'dep'));
alter table public.arr_watch add column if not exists rwy text check (rwy ~ '^[0-9]{2}[LRC]?$');
alter table public.arr_watch add column if not exists ex30 smallint;
alter table public.arr_watch add column if not exists ex60 smallint;
alter table public.rwy_samples add column if not exists dir text not null default 'arr' check (dir in ('arr', 'dep'));
alter table public.rwy_samples add column if not exists ex30 smallint;
alter table public.rwy_samples add column if not exists ex60 smallint;

create or replace function public.rwy_sample_counts() returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select iata || ':' || dir || ':' || rwy as k, count(*) as n from public.rwy_samples group by 1) q
$$;
-- [時刻, 滑走路, 120km, 60km, 30km の方角（着陸は入った方角）, 最初に見えた方角, 着陸か離陸か, 30km・60km を出た方角（離陸）]
create or replace function public.rwy_samples_recent(p_iata text, p_days int default 14) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_array(extract(epoch from at)::bigint, rwy, ent120, ent60, ent30, first_brg, dir, ex30, ex60) order by at), '[]'::jsonb)
  from public.rwy_samples where iata = p_iata and at > now() - make_interval(days => least(greatest(coalesce(p_days, 14), 1), 90))
$$;
