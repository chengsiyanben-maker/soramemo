-- いま飛んでいる特別塗装機：機体の記録（airport-traffic）のたびに、特別塗装機の一覧（_shared/liveries.ts）にある登録記号の機体を見つけて残す。
-- 利用者は public.special_now()（直近15分に見えたもの）で読む。ログインしていなくても読める。
create table if not exists public.livery_sightings (
  reg       text primary key check (reg ~ '^JA[0-9A-Z]{3,5}$'),
  name      text not null check (length(name) <= 80),
  airline   text not null check (length(airline) <= 40),
  callsign  text check (length(callsign) <= 10),
  lat       double precision not null,
  lon       double precision not null,
  alt_ft    integer,
  iata      text check (iata ~ '^[A-Z]{3}$'),   -- 運用タブの空港の近く（着陸・離陸中）なら、その空港
  phase     text check (phase in ('arr', 'dep')),
  src       text not null check (length(src) <= 300),
  seen_at   timestamptz not null default now()
);
create index if not exists livery_sightings_seen on public.livery_sightings (seen_at desc);
alter table public.livery_sightings enable row level security;
revoke all on public.livery_sightings from public, anon, authenticated;

create or replace function public.special_now() returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('reg', reg, 'name', name, 'airline', airline, 'callsign', callsign,
           'lat', round(lat::numeric, 3), 'lon', round(lon::numeric, 3), 'alt_ft', alt_ft, 'iata', iata, 'phase', phase, 'src', src, 'at', seen_at)
           order by (iata is null), seen_at desc), '[]'::jsonb)
  from public.livery_sightings where seen_at > now() - interval '15 minutes'
$$;
revoke all on function public.special_now() from public;
grant execute on function public.special_now() to anon, authenticated;
