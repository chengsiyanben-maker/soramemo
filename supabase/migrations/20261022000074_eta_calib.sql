-- 到着予想を空港ごとに学習する：毎晩、記録（flight_history）から空港ごとの地上走行（taxi）と着陸までの寄り道（extra）を決め直す
--   ・地上走行：運航情報（搭乗口に着いた時刻）と機体の位置（着陸の時刻）の両方が10便以上あれば、2つの差の中央値。
--     機体の位置がない空港は、運航情報とのずれの中央値（着陸の予想のずれもまとめて、画面の「到着予想」が合うように）
--   ・寄り道：機体の位置（着陸の時刻）とくらべた予想の早すぎ。前に決め直した後の記録だけを使い、ずれの7割だけ動かす（行き過ぎない）
--   ・どちらも10便より少なければ前の値のまま。_shared/flight_watch.ts が10分に1回読む
create table if not exists public.eta_calib (
  iata       text primary key check (iata ~ '^[A-Z]{3}$'),
  taxi       real check (taxi between 0 and 30),
  extra      real check (extra between 0 and 20),
  n_odpt     int not null default 0,
  n_adsb     int not null default 0,
  extra_at   timestamptz,           -- 寄り道を最後に変えた時刻（これより後の記録で次を決める）
  updated_at timestamptz not null default now()
);
alter table public.eta_calib enable row level security;
revoke all on public.eta_calib from public, anon, authenticated;
-- はじめの値（_shared/flight_watch.ts の目安と同じ）。寄り道はもう反映ずみとして、いまから後の記録で決め直す
insert into public.eta_calib (iata, taxi, extra, extra_at) values
  ('HND', 10, 10, now()), ('NRT', 10, 8, now()), ('KIX', 7, 6, now()), ('ITM', 5, 0, now()), ('CTS', 8, 0, now()), ('FUK', 6, 3, now()), ('OKA', 6, 3, now()),
  ('NGO', 3, 3, now()), ('NGS', null, 3, now()), ('SDJ', 4, 0, now()), ('KMJ', 4, 0, now()), ('KOJ', 4, 0, now()), ('HIJ', 3, 0, now()), ('KMI', 2, 0, now()),
  ('HKD', 3, 0, now()), ('AKJ', 3, 0, now()), ('UKB', 4, 0, now())
on conflict (iata) do nothing;

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
    declare m real; c int;
    begin
      select percentile_cont(0.5) within group (order by extract(epoch from (eta30 - ata)) / 60), count(*) into m, c
      from public.flight_history
      where arr = r.arr and ata_src = 'adsb' and eta30 is not null and ata is not null and not cancelled and diverted_to is null
        and svc_date >= (now() at time zone 'Asia/Tokyo')::date - 14 and (ea is null or ata > ea);
      if c >= 10 and abs(m) >= 0.5 then ne := greatest(0, least(15, round((coalesce(ne, 0) - 0.7 * m)::numeric, 1))); ea := now(); end if;
    end;
    insert into public.eta_calib (iata, taxi, extra, n_odpt, n_adsb, extra_at, updated_at) values (r.arr, nt, ne, r.no, r.na, ea, now())
    on conflict (iata) do update set taxi = excluded.taxi, extra = excluded.extra, n_odpt = excluded.n_odpt, n_adsb = excluded.n_adsb, extra_at = excluded.extra_at, updated_at = now();
    n := n + 1;
  end loop;
  return n;
end $$;
revoke all on function public.refresh_eta_calib() from public, anon, authenticated;

-- 地上走行の目安：学習した値があればそれを使う
create or replace function public.taxi_in_min(p_iata text) returns int language sql stable security definer set search_path = public as $$
  select coalesce((select round(taxi)::int from public.eta_calib where iata = p_iata and taxi is not null),
    case p_iata when 'HND' then 10 when 'NRT' then 10 when 'KIX' then 7 when 'ITM' then 5 when 'CTS' then 8 when 'FUK' then 6 when 'OKA' then 6
      when 'NGO' then 3 when 'SDJ' then 4 when 'KMJ' then 4 when 'KOJ' then 4 when 'HIJ' then 3 when 'KMI' then 2 when 'HKD' then 3 when 'AKJ' then 3 when 'UKB' then 4 else 4 end)
$$;

-- だれでも読める：空港ごとに学習した値（便名などは含まない）
create or replace function public.eta_calib_list() returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('iata', iata, 'taxi', taxi, 'extra', extra, 'n_odpt', n_odpt, 'n_adsb', n_adsb, 'updated_at', updated_at) order by n_odpt + n_adsb desc), '[]'::jsonb) from public.eta_calib
$$;
revoke all on function public.eta_calib_list() from public;
grant execute on function public.eta_calib_list() to anon, authenticated;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 毎日の記録（19:50 UTC）の後に
  execute $q$ select cron.schedule('eta-calib', '35 20 * * *', $job$ select public.refresh_eta_calib() $job$) $q$;
end
$outer$;
