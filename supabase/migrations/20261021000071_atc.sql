-- 管制の交信（受信の協力）：協力者が受信機で聞いた交信を、その端末で英語の文字にして送る。
--   サーバーは文字を読み解いて（_shared/atc_parse.ts）日本語にし、その時間に空港の近くを飛んでいる機体と呼び出し符号が合うものだけを出す。
--   音は受け取らない。協力者の名前・細かい場所は出さない（地域は決まった選択肢から選んだものだけ）
create table if not exists public.atc_feeders (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users (id) on delete cascade,
  kind        text not null check (kind in ('phone', 'pc')),
  token_hash  text not null unique,
  area        text check (area ~ '^[a-z0-9-]{2,32}$'),
  iata        text check (iata ~ '^[A-Z]{3}$'),
  ch          text check (ch in ('atis', 'del', 'ramp', 'gnd', 'twr', 'app', 'dep')),
  freq        text check (freq ~ '^1[1-3][0-9]\.[0-9]{1,3}$'),
  consent_at  timestamptz not null,
  last_seen   timestamptz,
  sent        int not null default 0,
  created_at  timestamptz not null default now()
);
create index if not exists atc_feeders_user on public.atc_feeders (user_id);
alter table public.atc_feeders enable row level security;
revoke all on public.atc_feeders from public, anon, authenticated;

create table if not exists public.atc_msgs (
  id        bigint generated always as identity primary key,
  iata      text not null check (iata ~ '^[A-Z]{3}$'),
  ch        text not null check (ch in ('atis', 'del', 'ramp', 'gnd', 'twr', 'app', 'dep')),
  freq      text,
  at        timestamptz not null,
  feeder    uuid references public.atc_feeders (id) on delete set null,
  text_en   text check (length(text_en) <= 400),
  conf      real,
  callsign  text check (length(callsign) <= 10),
  flight    text,
  items     jsonb not null default '[]'::jsonb,
  ja        text check (length(ja) <= 400),
  tags      text[] not null default '{}',
  verified  boolean not null default false,
  heard     smallint not null default 1,   -- 同じ交信を受けた協力者の数
  created_at timestamptz not null default now()
);
create index if not exists atc_msgs_iata_at on public.atc_msgs (iata, at desc);
alter table public.atc_msgs enable row level security;
revoke all on public.atc_msgs from public, anon, authenticated;

-- だれでも読める：その空港の最近の交信（呼び出し符号が、その時間に近くを飛んでいた機体と合ったものだけ。英語の文字と協力者は出さない）
create or replace function public.atc_recent(p_iata text, p_ch text default null, p_minutes int default 30) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', id, 'at', at, 'ch', ch, 'freq', freq, 'flight', flight, 'callsign', callsign, 'ja', ja, 'tags', tags, 'items', items, 'heard', heard) order by at desc), '[]'::jsonb)
  from (select * from public.atc_msgs
        where iata = p_iata and verified and (p_ch is null or ch = p_ch)
          and at > now() - make_interval(mins => least(greatest(coalesce(p_minutes, 30), 1), 180))
        order by at desc limit 80) q
$$;
revoke all on function public.atc_recent(text, text, int) from public;
grant execute on function public.atc_recent(text, text, int) to anon, authenticated;

-- だれでも読める：受信のネットワーク（空港・管制ごとのいま受信している人数と今日の交信の数、地域ごとの協力者の数）
create or replace function public.atc_coverage() returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'ch', coalesce((select jsonb_agg(jsonb_build_object('iata', iata, 'ch', ch, 'live', live, 'today', today)) from (
      select k.iata, k.ch,
        (select count(*) from public.atc_feeders f where f.iata = k.iata and f.ch = k.ch and f.last_seen > now() - interval '5 minutes') as live,
        (select count(*) from public.atc_msgs m where m.iata = k.iata and m.ch = k.ch and m.verified and m.at > date_trunc('day', now() at time zone 'Asia/Tokyo') at time zone 'Asia/Tokyo') as today
      from (select i as iata, c as ch from unnest(array['HND', 'NRT']) i, unnest(array['twr', 'gnd', 'app', 'dep']) c) k) z), '[]'::jsonb),
    'areas', coalesce((select jsonb_object_agg(area, n) from (select area, count(*) as n from public.atc_feeders where area is not null and last_seen > now() - interval '7 days' group by area) a), '{}'::jsonb))
$$;
revoke all on function public.atc_coverage() from public;
grant execute on function public.atc_coverage() to anon, authenticated;

-- 協力をはじめる（ログインした人）：協力用の合言葉を作って1回だけ返す（保存するのはハッシュだけ）。1人5台まで
create or replace function public.atc_new_feeder(p_kind text, p_area text, p_consent boolean) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); tok text; fid uuid;
begin
  if uid is null then raise exception 'login required'; end if;
  if not coalesce(p_consent, false) then raise exception 'consent required'; end if;
  if p_kind not in ('phone', 'pc') then raise exception 'bad kind'; end if;
  if p_area is not null and p_area !~ '^[a-z0-9-]{2,32}$' then raise exception 'bad area'; end if;
  if (select count(*) from public.atc_feeders where user_id = uid) >= 5 then raise exception 'too many feeders'; end if;
  tok := replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '');
  insert into public.atc_feeders (user_id, kind, token_hash, area, consent_at) values (uid, p_kind, encode(sha256(convert_to(tok, 'UTF8')), 'hex'), p_area, now()) returning id into fid;
  return jsonb_build_object('id', fid, 'token', tok);
end $$;
revoke all on function public.atc_new_feeder(text, text, boolean) from public, anon;
grant execute on function public.atc_new_feeder(text, text, boolean) to authenticated;

-- 自分の協力の記録（ログインした人）と、やめる
create or replace function public.atc_my_feeders() returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', id, 'kind', kind, 'area', area, 'iata', iata, 'ch', ch, 'freq', freq, 'last_seen', last_seen, 'sent', sent,
    'shown', (select count(*) from public.atc_msgs m where m.feeder = f.id and m.verified)) order by created_at), '[]'::jsonb)
  from public.atc_feeders f where user_id = auth.uid()
$$;
revoke all on function public.atc_my_feeders() from public, anon;
grant execute on function public.atc_my_feeders() to authenticated;
create or replace function public.atc_delete_feeder(p_id uuid) returns void
language sql security definer set search_path = public as $$ delete from public.atc_feeders where id = p_id and user_id = auth.uid() $$;
revoke all on function public.atc_delete_feeder(uuid) from public, anon;
grant execute on function public.atc_delete_feeder(uuid) to authenticated;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  execute $q$ select cron.schedule('atc-cleanup', '17 19 * * *', $job$ delete from public.atc_msgs where at < now() - interval '7 days' $job$) $q$;
end
$outer$;
