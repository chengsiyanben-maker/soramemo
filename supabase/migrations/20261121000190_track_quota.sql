-- 空の道すじ（全機の航跡）をまとめて持っていかれないための上限（11/21・PM の指示「案1」）。
-- adsb.lol の条件「大量のデータを配り直さない」に合わせる。自分のアプリで線を見せる使い方は今までどおり。
--   ・今日と前の7日：だれでも（ログインなし・デモも）今までどおり読める。数えない
--   ・それより前の日：ログインした人だけ。1人1時間に「空港×日」60組まで（同じ組を読み直しても数えない）
--     ログインなし → {"error":"login_required"}、上限を超えた → {"error":"rate_limited","retry_after_min":n}
--   ・運営（service_role・postgres など。anon・authenticated の役でない呼び出し）は数えない
-- 表は数える表 track_quota を1つ足す（RLS 有効・方針なし＝本人も直接は読めない。関数の中だけで使う）。
-- 退会で消える（auth.users を on delete cascade）。2時間より前の行は呼ばれたときに消す（航跡の記録ではない）。
-- 航跡の表（airport_tracks_all・flight_tracks）と RLS は変えない。返す形（配列）も今の日付なら同じ。
-- 影響：チェックイン（空の道すじ）。古い日を見るときにログインの鍵を付けて呼ぶ直しが要る（チェックイン担当へ依頼）。経営は使っていない。
-- 注意：airport_tracks は数える表に書くので volatile になる。アプリは POST で呼んでいるのでそのまま動く（GET では呼べない）。

create table if not exists public.track_quota (
  user_id uuid not null references auth.users (id) on delete cascade,
  hr      timestamptz not null,           -- その1時間の頭（date_trunc('hour', now())）
  iata    text not null check (iata ~ '^[A-Z]{3}$'),
  day     date not null,
  primary key (user_id, hr, iata, day)
);
alter table public.track_quota enable row level security;
revoke all on table public.track_quota from public, anon, authenticated;
comment on table public.track_quota is '空の道すじの古い日を読んだ回数（1人1時間に空港×日60組まで）。関数 track_quota_take だけが使う';

-- 1組を数えて、上限の中なら true。運営の関数（cold-tracks）からも使う
create or replace function public.track_quota_take(p_uid uuid, p_iata text, p_day date) returns boolean
language plpgsql volatile security definer set search_path = public set lock_timeout = '2s' as $$
declare h timestamptz := date_trunc('hour', now()); n int;
begin
  if p_uid is null then return false; end if;
  delete from public.track_quota where user_id = p_uid and hr < h - interval '2 hours';
  if exists (select 1 from public.track_quota where user_id = p_uid and hr = h and iata = p_iata and day = p_day) then return true; end if;
  select count(*) into n from public.track_quota where user_id = p_uid and hr = h;
  if n >= 60 then return false; end if;
  insert into public.track_quota (user_id, hr, iata, day) values (p_uid, h, p_iata, p_day) on conflict do nothing;
  return true;
end $$;
revoke all on function public.track_quota_take(uuid, text, date) from public, anon, authenticated;
grant execute on function public.track_quota_take(uuid, text, date) to service_role;

-- 今までの airport_tracks の中身（092 と同じ）。直接は呼ばせない
create or replace function public.airport_tracks_raw(p_iata text, p_day date) returns jsonb
language sql stable security definer set search_path = public as $$
  with d as (select (now() at time zone 'Asia/Tokyo')::date as today),
  a as (
    select callsign, dep_here, pts, extract(hour from at at time zone 'Asia/Tokyo')::int as h, at
    from public.airport_tracks_all, d where iata = p_iata and day = p_day and p_day <= d.today order by at limit 3000
  ),
  b as (
    select case when h.dep = p_iata then 1 else 0 end as dep_here, t.pts,
           extract(hour from (case when h.dep = p_iata then coalesce(h.atd, h.std) else coalesce(h.ata, h.sta) end) at time zone 'Asia/Tokyo')::int as hr,
           case when h.dep = p_iata then coalesce(h.atd, h.std) else coalesce(h.ata, h.sta) end as at
    from d, public.flight_history h join public.flight_tracks t on t.svc_date = h.svc_date and t.flight = h.flight and t.dep = h.dep
    where h.svc_date = p_day and p_day < d.today and (h.dep = p_iata or h.arr = p_iata) and not h.cancelled
      and (case when h.callsign is null then not exists (select 1 from a) else not exists (select 1 from a where a.callsign = upper(h.callsign)) end)
    order by h.std limit 2000
  )
  select coalesce((select jsonb_agg(x.j order by x.at) from (
    select jsonb_build_object('d', dep_here, 'p', pts, 'h', h) as j, at from a
    union all
    select jsonb_build_object('d', dep_here, 'p', pts, 'h', hr), at from b
  ) x), '[]'::jsonb)
$$;
revoke all on function public.airport_tracks_raw(text, date) from public, anon, authenticated;

create or replace function public.airport_tracks(p_iata text, p_day date) returns jsonb
language plpgsql volatile security definer set search_path = public set statement_timeout = '8s' as $$
declare today date := (now() at time zone 'Asia/Tokyo')::date; r text := coalesce(current_setting('role', true), 'none');
begin
  if p_iata is null or p_iata !~ '^[A-Z]{3}$' or p_day is null or p_day > today then return '[]'::jsonb; end if;
  if p_day < today - 7 and r in ('anon', 'authenticated') then
    if auth.uid() is null then return jsonb_build_object('error', 'login_required'); end if;
    if not public.track_quota_take(auth.uid(), p_iata, p_day) then
      return jsonb_build_object('error', 'rate_limited', 'retry_after_min', 60 - extract(minute from now())::int);
    end if;
  end if;
  return public.airport_tracks_raw(p_iata, p_day);
end $$;
revoke all on function public.airport_tracks(text, date) from public;
grant execute on function public.airport_tracks(text, date) to anon, authenticated;
