-- 羽田の到着予想を、滑走路の使い方ごとに分けて当てる（10/27）。
-- 南風の日ほど予想が早すぎになり（10/21 は南風65%で −12.9分、北風だけの日は −0.1〜+2.7分）、空港ひとつの寄り道では
-- 北風と南風が入れ替わるたびに補正が逆に振れていた。使い方は運用の記録（ops_log：実際の機体からの判定を優先、なければ風からの推定）。
-- 新しい表 eta_calib_mode は RLS を有効にし、利用者からは読めない（読むのは到着予想の関数＝service_role と、下の関数だけ）

create table if not exists public.eta_calib_mode (
  iata       text not null check (iata ~ '^[A-Z]{3}$'),
  mode       text not null check (mode ~ '^[A-Za-z]{2,12}$'),
  extra      real not null check (extra between 0 and 30),
  n          int not null default 0,
  extra_at   timestamptz not null default now(),   -- 寄り道を最後に変えた時刻（これより後の記録で次を決める）
  updated_at timestamptz not null default now(),
  primary key (iata, mode)
);
alter table public.eta_calib_mode enable row level security;
revoke all on public.eta_calib_mode from public, anon, authenticated;

-- その時刻の滑走路の使い方（20分より前の記録しかなければ分からない＝null）
create or replace function public.ops_mode_at(p_iata text, p_at timestamptz) returns text
language sql stable security definer set search_path = public as $$
  select coalesce(o.obs_mode, o.est_mode) from public.ops_log o
  where o.iata = p_iata and o.at <= p_at and o.at > p_at - interval '20 minutes'
  order by o.at desc limit 1
$$;
revoke all on function public.ops_mode_at(text, timestamptz) from public, anon, authenticated;

-- 始めの値：前の2週間で、その使い方の便が羽田全体と比べて何分ずれやすいか（中央値の差）を、いまの寄り道に足す。20便より少ない使い方は作らない
insert into public.eta_calib_mode (iata, mode, extra, n)
select 'HND', x.mode, greatest(0, least(30, round((coalesce((select extra from public.eta_calib where iata = 'HND'), 10) - (x.med - a.med))::numeric, 1))), x.n
from (
  select public.ops_mode_at('HND', h.ata) as mode, count(*) as n,
         percentile_cont(0.5) within group (order by extract(epoch from (h.eta30 - h.ata)) / 60) as med
  from public.flight_history h
  where h.arr = 'HND' and h.ata_src = 'adsb' and h.eta30 is not null and h.ata is not null and not h.cancelled and h.diverted_to is null
    and h.svc_date >= (now() at time zone 'Asia/Tokyo')::date - 14
  group by 1 having count(*) >= 20
) x cross join (
  select percentile_cont(0.5) within group (order by extract(epoch from (h.eta30 - h.ata)) / 60) as med
  from public.flight_history h
  where h.arr = 'HND' and h.ata_src = 'adsb' and h.eta30 is not null and h.ata is not null and not h.cancelled and h.diverted_to is null
    and h.svc_date >= (now() at time zone 'Asia/Tokyo')::date - 14
) a
where x.mode is not null and a.med is not null
on conflict (iata, mode) do nothing;

create or replace function public.refresh_eta_calib() returns int
language plpgsql security definer set search_path = public as $$
declare r record; n int := 0; old record; nt real; ne real; ea timestamptz;
begin
  for r in
    with x as (
      select arr, ata_src as src, extract(epoch from (eta30 - ata)) / 60 as diff, ata
      from public.flight_history
      where svc_date >= (now() at time zone 'Asia/Tokyo')::date - 14 and eta30 is not null and ata is not null and not cancelled and diverted_to is null
    )
    select arr,
      count(*) filter (where src = 'odpt') as no, percentile_cont(0.5) within group (order by diff) filter (where src = 'odpt') as mo,
      count(*) filter (where src = 'adsb') as na, percentile_cont(0.5) within group (order by diff) filter (where src = 'adsb') as ma
    from x group by arr
  loop
    select * into old from public.eta_calib where iata = r.arr;
    nt := old.taxi; ne := old.extra; ea := old.extra_at;
    if r.no >= 10 and r.na >= 10 then nt := greatest(0, least(20, round((r.ma - r.mo)::numeric, 1)));
    elsif r.no >= 10 and r.na < 10 then nt := greatest(0, least(20, round((-r.mo)::numeric, 1)));
    end if;
    -- 寄り道：前に変えた後の、機体の位置の記録だけで
    declare m real; c int; dd int;
    begin
      select percentile_cont(0.5) within group (order by extract(epoch from (eta30 - ata)) / 60), count(*), count(distinct svc_date) into m, c, dd
      from public.flight_history
      where arr = r.arr and ata_src = 'adsb' and eta30 is not null and ata is not null and not cancelled and diverted_to is null
        and svc_date >= (now() at time zone 'Asia/Tokyo')::date - 14 and (ea is null or ata > ea);
      -- 2日分・40便がそろってから、ずれの3割だけ（1回に2分まで）直す。日ごとの振れ（風向き・混み具合）を追いかけて行き過ぎないため
      if c >= 40 and dd >= 2 and abs(m) >= 0.5 then
        ne := greatest(0, least(15, round((coalesce(ne, 0) - greatest(-2, least(2, 0.3 * m)))::numeric, 1))); ea := now();
      end if;
    end;
    insert into public.eta_calib (iata, taxi, extra, n_odpt, n_adsb, extra_at, updated_at) values (r.arr, nt, ne, r.no, r.na, ea, now())
    on conflict (iata) do update set taxi = excluded.taxi, extra = excluded.extra, n_odpt = excluded.n_odpt, n_adsb = excluded.n_adsb, extra_at = excluded.extra_at, updated_at = now();
    n := n + 1;
  end loop;
  -- 滑走路の使い方ごとの寄り道（eta_calib_mode に行がある空港・使い方だけ）。決め方は空港全体と同じ（2日分・40便、3割、1回に2分まで）
  declare q record; m2 real; c2 int; d2 int;
  begin
    for q in select * from public.eta_calib_mode loop
      select percentile_cont(0.5) within group (order by extract(epoch from (h.eta30 - h.ata)) / 60), count(*), count(distinct h.svc_date) into m2, c2, d2
      from public.flight_history h
      where h.arr = q.iata and h.ata_src = 'adsb' and h.eta30 is not null and h.ata is not null and not h.cancelled and h.diverted_to is null
        and h.svc_date >= (now() at time zone 'Asia/Tokyo')::date - 14 and h.ata > q.extra_at and public.ops_mode_at(q.iata, h.ata) = q.mode;
      if c2 >= 40 and d2 >= 2 and abs(m2) >= 0.5 then
        update public.eta_calib_mode set extra = greatest(0, least(30, round((extra - greatest(-2, least(2, 0.3 * m2)))::numeric, 1))),
          n = c2, extra_at = now(), updated_at = now() where iata = q.iata and mode = q.mode;
      else
        update public.eta_calib_mode set n = coalesce(c2, 0), updated_at = now() where iata = q.iata and mode = q.mode;
      end if;
    end loop;
  end;
  return n;
end $$;
revoke all on function public.refresh_eta_calib() from public, anon, authenticated;

-- 使い方ごとの日ごとのずれ（中央値と便数だけ。個々の便は返さない）。南風の日に小さくなったかを見るため
create or replace function public.eta_daily_mode(p_iata text, p_days int default 14) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('day', d, 'mode', m, 'n', n, 'median', med) order by d, m), '[]'::jsonb) from (
    select h.svc_date as d, public.ops_mode_at(h.arr, h.ata) as m, count(*) as n,
           round((percentile_cont(0.5) within group (order by extract(epoch from (h.eta30 - h.ata)) / 60))::numeric, 1) as med
    from public.flight_history h
    where h.arr = upper(p_iata) and h.ata_src = 'adsb' and h.eta30 is not null and h.ata is not null and not h.cancelled and h.diverted_to is null
      and h.svc_date >= (now() at time zone 'Asia/Tokyo')::date - least(greatest(p_days, 1), 30)
    group by 1, 2 having count(*) >= 3
  ) t
$$;
revoke all on function public.eta_daily_mode(text, int) from public;
grant execute on function public.eta_daily_mode(text, int) to anon, authenticated;
