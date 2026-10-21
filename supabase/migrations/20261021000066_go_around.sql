-- ゴーアラウンドの知らせ：着陸に向かう機体が、滑走路の近くで 1,000ft より低く降りてから、着陸せずに 500ft 以上上がったことを
-- 機体の位置（adsb.lol）から見つけて残し（推定）、選んだ空港の人に知らせる。ゴーアラウンドが起きやすい天気（気象通報からの目安）も知らせる。
-- ・ga_watch：着陸に向かっている機体の、空港の近くでの高さの動き（airport-traffic が30秒ごとに書く。10分で消す）
-- ・ga_events：見つけたゴーアラウンド（推定）。だれでも ga_recent・ga_event で読める（公開の位置の情報からの推定だけ）
-- ・push_subs の ga_*：知らせる空港・種類・夜は知らせない・天気の知らせの間隔
create table if not exists public.ga_watch (
  iata       text not null check (iata ~ '^[A-Z]{3}$'),
  hex        text not null check (length(hex) <= 12),
  callsign   text check (length(callsign) <= 10),
  low_ft     integer,
  low_km     real,
  low_at     timestamptz,
  low_lat    real,
  low_lon    real,
  low_hdg    smallint,
  pts        jsonb not null default '[]'::jsonb,   -- [[秒（UNIX）, 高度ft, 空港までkm], …] 新しい20点まで
  updated_at timestamptz not null default now(),
  primary key (iata, hex)
);
create index if not exists ga_watch_updated on public.ga_watch (updated_at);
alter table public.ga_watch enable row level security;
revoke all on public.ga_watch from public, anon, authenticated;

create table if not exists public.ga_events (
  id        bigint generated always as identity primary key,
  iata      text not null check (iata ~ '^[A-Z]{3}$'),
  at        timestamptz not null,                 -- 上昇に移ったのを見つけた時刻
  hex       text not null check (length(hex) <= 12),
  callsign  text check (length(callsign) <= 10),
  flight    text check (flight is null or flight ~ '^[A-Z0-9]{2}[0-9]{1,4}$'),
  type      text check (length(type) <= 8),
  reg       text check (length(reg) <= 10),
  low_ft    integer not null,
  low_km    real,
  low_at    timestamptz,
  rwy       text check (rwy is null or rwy ~ '^[0-9]{2}[LRC]?$'),
  wx        jsonb,                                -- そのときの気象通報（風・突風・雲底・視程・時刻）
  pts       jsonb not null default '[]'::jsonb,
  again_at  timestamptz                           -- もう一度進入して低く降りた時刻（着陸したとみられる）
);
create index if not exists ga_events_iata_at on public.ga_events (iata, at desc);
create index if not exists ga_events_hex_at on public.ga_events (hex, at desc);
alter table public.ga_events enable row level security;
revoke all on public.ga_events from public, anon, authenticated;

alter table public.push_subs add column if not exists ga_airports text[] not null default '{}';
alter table public.push_subs add column if not exists ga_kinds text[] not null default '{}';
alter table public.push_subs add column if not exists ga_quiet boolean not null default false;
alter table public.push_subs add column if not exists ga_gap int not null default 3;
alter table public.push_subs drop constraint if exists push_subs_ga_check;
alter table public.push_subs add constraint push_subs_ga_check check (
  cardinality(ga_airports) <= 14 and ga_kinds <@ array['plane', 'cluster', 'wind', 'cloud', 'ts']::text[] and ga_gap in (0, 3));

-- 最近のゴーアラウンド（その空港・何時間ぶん）
create or replace function public.ga_recent(p_iata text, p_hours int default 24) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', id, 'iata', iata, 'at', at, 'callsign', callsign, 'flight', flight, 'type', type, 'reg', reg,
      'low_ft', low_ft, 'low_km', low_km, 'rwy', rwy, 'again_at', again_at) order by at desc), '[]'::jsonb)
  from (select * from public.ga_events where iata = p_iata and at > now() - make_interval(hours => least(greatest(coalesce(p_hours, 24), 1), 72)) order by at desc limit 50) e
$$;
revoke all on function public.ga_recent(text, int) from public;
grant execute on function public.ga_recent(text, int) to anon, authenticated;

-- 1件（高さの動きとそのときの天気つき）
create or replace function public.ga_event(p_id bigint) returns jsonb
language sql stable security definer set search_path = public as $$
  select to_jsonb(e) - 'hex' from public.ga_events e where id = p_id
$$;
revoke all on function public.ga_event(bigint) from public;
grant execute on function public.ga_event(bigint) to anon, authenticated;

-- 古いゴーアラウンドは30日で消す（毎日）
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  execute $q$ select cron.schedule('ga-cleanup', '17 19 * * *', $job$ delete from public.ga_events where at < now() - interval '30 days'; delete from public.ga_watch where updated_at < now() - interval '1 hour' $job$) $q$;
end
$outer$;
