-- 撮影記録（撮る人用の計画の E。仕様は docs/pm/spec-photo-log.md の 5。データ担当 11/6）
--   写真の撮影時刻から「その時刻に空港の近くにいた機体」の候補を出し、本人が選んだ機体を photo_log に残す。
--   写真そのもの・写真の位置（EXIF の GPS）はサーバーに来ない。来るのは空港（IATA）・撮影時刻（分まで）・選んだ機体だけ。
--
--   1. 表 photo_log（新規）：本人だけ読む・足す・消す（update は許さない。選び直しは「消して足す」）。
--      auth.users を on delete cascade で参照するので、退会で消える（決定事項「退会したら本人の記録を消す」）。
--      同じ人・同じ機体・同じ分は1行（unique）。1人1日（日本時間・足した日）200行まで。撮影時刻は分に丸め、未来と2000年より前を断る
--   2. 関数 photo_candidates(p_iata, p_at)（新規・ログインした人だけ）：前後20分に空港にいちばん近かった機体を、時刻の差の小さい順に20件まで
--      元は全機の航跡 airport_tracks_all（3時間ごとに作られる）＋ reg_legs（便名と日 → 登録記号・機種）。
--      36時間以内は airport_tracks_all がまだない時間があるので、track_points（36時間で消える）から同じ形を作って足す（同じ便は airport_tracks_all を優先）。
--      記録している14空港だけ。31日より前は断る（30日を過ぎた日は cold-archive で表の外へ移るため）。航跡の点は返さない
--   3. admin_backup に photo_log を足す（20261104000146_user_profiles の admin_backup に1行足しただけ。バックアップは有料機能にしない）
--   RLS：photo_log は有効にして本人だけ（select・insert・delete）。anon は何もできない。photo_candidates は authenticated だけ実行できる。
--   影響：チェックイン・経営の表と関数は変えない（新しい表と関数を足すだけ）。画面はまだ使わない（撮る人用担当が作る）。

-- 1. 表 photo_log
create table if not exists public.photo_log (
  id         bigint generated always as identity primary key,
  user_id    uuid not null default auth.uid() references auth.users (id) on delete cascade,
  taken_at   timestamptz not null check (taken_at >= timestamptz '2000-01-01 00:00:00+09'),
  iata       text not null check (iata ~ '^[A-Z]{3}$'),
  reg        text not null check (reg ~ '^[A-Z0-9-]{2,10}$'),
  callsign   text check (callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$'),
  type       text check (length(type) <= 8),
  phase      text check (phase in ('arr', 'dep')),
  src        text not null check (src in ('cand', 'manual')),
  created_at timestamptz not null default now(),
  unique (user_id, reg, taken_at)
);
create index if not exists photo_log_user_taken on public.photo_log (user_id, taken_at desc);
create index if not exists photo_log_user_created on public.photo_log (user_id, created_at);

alter table public.photo_log enable row level security;
revoke all on public.photo_log from public, anon, authenticated;
grant select, insert, delete on public.photo_log to authenticated;
revoke update on public.photo_log from authenticated;
drop policy if exists photo_log_select on public.photo_log;
create policy photo_log_select on public.photo_log for select to authenticated using (user_id = (select auth.uid()));
drop policy if exists photo_log_insert on public.photo_log;
create policy photo_log_insert on public.photo_log for insert to authenticated with check (user_id = (select auth.uid()));
drop policy if exists photo_log_delete on public.photo_log;
create policy photo_log_delete on public.photo_log for delete to authenticated using (user_id = (select auth.uid()));

-- 足す前に：撮影時刻を分に丸める・未来を断る・1人1日200行まで（足した日・日本時間）
create or replace function public.photo_log_before_insert() returns trigger
language plpgsql security definer set search_path = '' as $$
declare d0 timestamptz := ((now() at time zone 'Asia/Tokyo')::date)::timestamp at time zone 'Asia/Tokyo';
begin
  new.taken_at := date_trunc('minute', new.taken_at);
  new.created_at := now();
  if new.taken_at > now() then raise exception 'photo_log: future time' using errcode = '22023'; end if;
  if (select count(*) from public.photo_log where user_id = new.user_id and created_at >= d0) >= 200 then
    raise exception 'photo_log: too many today' using errcode = '54000';
  end if;
  return new;
end $$;
revoke all on function public.photo_log_before_insert() from public, anon, authenticated;
drop trigger if exists photo_log_before_insert on public.photo_log;
create trigger photo_log_before_insert before insert on public.photo_log for each row execute function public.photo_log_before_insert();

-- 2. 候補：photo_candidates(空港, 補正後の撮影時刻) → [{reg, callsign, type, phase, at, dmin}]
--   at：空港にいちばん近かった時刻（着陸は最後の点・離陸は最初の点。36時間以内で航跡から作るときは22km以内でいちばん近い点）
--   dmin：p_at との差（分・小数1けた）。差の小さい順に20件まで。登録記号が分からない便は返さない（選べないため）
--   断るとき（例外の文）：'photo_candidates: login required'・'not recorded'（14空港の外）・'future'・'too old'（31日より前）
create or replace function public.photo_candidates(p_iata text, p_at timestamptz) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare
  ap record;
  lo timestamptz := p_at - interval '20 minutes';
  hi timestamptz := p_at + interval '20 minutes';
  out jsonb;
begin
  if auth.uid() is null then raise exception 'photo_candidates: login required' using errcode = '42501'; end if;
  if p_at is null then raise exception 'photo_candidates: bad time' using errcode = '22023'; end if;
  -- 記録している14空港（airport-traffic の RECORD と同じ。中心は _shared/jp_runways.json の center）
  select * into ap from (values
    ('HND', 35.549678, 139.786958), ('NRT', 35.76858, 140.388714), ('NGO', 34.858398, 136.804993), ('ITM', 34.780853, 135.440829),
    ('KIX', 34.427299, 135.244003), ('SDJ', 38.139702, 140.917007), ('FUK', 33.585899, 130.451004), ('KMJ', 32.837299, 130.854996),
    ('NGS', 32.916901, 129.914001), ('KOJ', 31.8034, 130.718994),   ('HIJ', 34.4361, 132.919006),   ('MYJ', 33.826893, 132.700114),
    ('CTS', 42.774753, 141.690414), ('OKA', 26.192437, 127.639804)) v(iata, lat, lon)
  where v.iata = upper(p_iata);
  if not found then raise exception 'photo_candidates: not recorded' using errcode = '22023'; end if;
  if p_at > now() + interval '5 minutes' then raise exception 'photo_candidates: future' using errcode = '22023'; end if;
  if p_at < now() - interval '31 days' then raise exception 'photo_candidates: too old' using errcode = '22023'; end if;

  with a as (   -- 全機の航跡（主キーの iata, day で引く）
    select t.callsign, t.at, case when t.dep_here = 1 then 'dep' else 'arr' end as phase
    from public.airport_tracks_all t
    where t.iata = ap.iata
      and t.day between (lo at time zone 'Asia/Tokyo')::date and (hi at time zone 'Asia/Tokyo')::date
      and t.at between lo and hi
  ),
  p as (        -- 36時間以内：航跡の点（t の索引で前後20分だけ読み、空港のまわりの箱で絞る）
    select q.callsign, q.t, q.alt,
           sqrt(power((q.lat - ap.lat) * 111.0, 2) + power((q.lon - ap.lon) * 111.0 * cos(radians(ap.lat)), 2)) as km
    from public.track_points q
    where hi > now() - interval '36 hours'
      and q.t between lo and hi
      and q.lat between ap.lat - 0.2 and ap.lat + 0.2
      and q.lon between ap.lon - 0.25 and ap.lon + 0.25
      and q.callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$'
  ),
  pn as (       -- 22km 以内の点だけ（全機の航跡の TRK_NEAR と同じ）
    select * from p where km <= 22
  ),
  b as (        -- 便ごとに、いちばん近い点の時刻。高さが下っていれば着陸・上っていれば離陸（どちらでもなければ空）
    select c.callsign, c.t as at,
      case when s.alt_last < s.alt_first - 5 then 'arr' when s.alt_last > s.alt_first + 5 then 'dep' end as phase
    from (select distinct on (callsign) callsign, t, alt from pn order by callsign, km, t) c
    join (select callsign,
                 (array_agg(alt order by t) filter (where alt is not null))[1] as alt_first,
                 (array_agg(alt order by t desc) filter (where alt is not null))[1] as alt_last,
                 min(alt) as alt_min
          from pn group by callsign) s using (callsign)
    where coalesce(s.alt_min, 0) <= 60                            -- 6,000ft より下に来た便だけ（上を通り過ぎた便は外す）
      and not exists (select 1 from a where a.callsign = c.callsign and abs(extract(epoch from a.at - c.t)) < 1800)
  ),
  c as (
    select * from a union all select * from b
  ),
  r as (        -- 便名と日から登録記号・機種（reg_legs の callsign, day の索引で引く。前の日にまたがる便も）
    select l.reg, c.callsign, l.type, c.phase, c.at, abs(extract(epoch from c.at - p_at)) as ds
    from c
    cross join lateral (
      select g.reg, g.type from public.reg_legs g
      where g.callsign = c.callsign
        and g.day between (c.at at time zone 'Asia/Tokyo')::date - 1 and (c.at at time zone 'Asia/Tokyo')::date
        and g.first_at <= c.at + interval '40 minutes' and g.last_at >= c.at - interval '40 minutes'
      order by (g.first_at <= c.at and g.last_at >= c.at) desc, g.last_at desc
      limit 1) l
  )
  select coalesce(jsonb_agg(jsonb_build_object('reg', reg, 'callsign', callsign, 'type', type, 'phase', phase, 'at', at,
                                               'dmin', round((ds / 60.0)::numeric, 1)) order by ds, reg), '[]'::jsonb)
  into out
  from (select * from r order by ds, reg limit 20) z;
  return out;
end $$;
revoke all on function public.photo_candidates(text, timestamptz) from public, anon;
grant execute on function public.photo_candidates(text, timestamptz) to authenticated;

-- 3. バックアップに photo_log を足す（20261104000146 の admin_backup に1行足しただけ）
create or replace function public.admin_backup() returns jsonb
language plpgsql security definer set search_path = ops, public, auth as $$
declare out jsonb;
begin
  if not is_admin() then raise exception 'admin only'; end if;
  out := jsonb_build_object(
    'app', 'soramemo', 'format', 1, 'created_at', now(),
    'users',           (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'email', email, 'created_at', created_at) order by created_at), '[]') from auth.users),
    'user_profiles',   (select coalesce(jsonb_agg(to_jsonb(t) order by t.user_id), '[]') from public.user_profiles t),
    'checkins',        (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.checkins t),
    'flights',         (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.flights t),
    'manual_flights',  (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.manual_flights t),
    'intl_flights',    (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.intl_flights t),
    'shugyo_prefs',    (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.shugyo_prefs t),
    'photo_log',       (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.photo_log t),
    'companies',       (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.companies t),
    'route_levels',    (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.route_levels t),
    'aircraft',        (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.aircraft t),
    'facilities',      (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.facilities t),
    'subscriptions',   (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.subscriptions t),
    'admins',          (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from ops.admins t),
    'flags',           (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from ops.flags t));
  insert into ops.admin_actions (admin_id, action, target, detail)
  values (auth.uid(), 'backup', 'all', jsonb_build_object('users', jsonb_array_length(out->'users'), 'checkins', jsonb_array_length(out->'checkins'), 'flights', jsonb_array_length(out->'flights')));
  return out;
end;
$$;
revoke all on function public.admin_backup() from public, anon;
grant execute on function public.admin_backup() to authenticated;
