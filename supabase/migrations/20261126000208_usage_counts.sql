-- 使われ方を、個人を特定しない回数だけで見る（11/26 本人の OK ④）
--   元：ops.usage_events（session はその起動ごとの使い捨ての値）・ops.checkin_rejections（利用者ID・座標なし）・
--       ops.client_errors（種類だけ数える）・public.checkins（その日の数だけ数える）
--   作るもの：日ごとの回数の表 ops.usage_daily と、毎晩それを作る処理、運営コンソールで見る読むだけの関数 admin_usage_counts
--   使わないもの：利用者ID・IP・位置（表に列がない。checkins は count(*) だけ読む）
--   翌日・翌月に戻った割合は、ずっと同じ端末の ID が要るので作らない（案だけ：docs/pm/report-usage-counts.md の 4）
--   usage_events などは180日で消えるが、この表は回数だけなので残す（記録を消さずに長く見られる）
--   RLS：ops.usage_daily は RLS を有効にし、anon / authenticated には何も許さない（見るのは admin_usage_counts だけ・中で is_admin）
--   影響：チェックイン・経営とも画面は変わらない。checkins に created_at だけの索引を1本足す（印を書く速さへの影響は小さい）

create table if not exists ops.usage_daily (
  day      date not null,
  metric   text not null,          -- checkin・geo・client_fail・error・tab・open・onboard
  key      text not null default '',
  n        integer not null,        -- 回数
  sessions integer,                 -- その回数を出した起動の数（起動ごとの使い捨ての値を数えただけ。checkin・error は null）
  primary key (day, metric, key)
);
create table if not exists ops.usage_daily_runs (
  day     date primary key,
  made_at timestamptz not null default now(),
  rows    integer not null default 0
);
alter table ops.usage_daily      enable row level security;
alter table ops.usage_daily_runs enable row level security;
revoke all on ops.usage_daily, ops.usage_daily_runs from public, anon, authenticated;

-- その日の印の数を数えるための索引（今は user_id が先頭の索引しかなく、日で数えると表をまるごと読む）
create index if not exists checkins_time on public.checkins (created_at);

-- 1日分（日本時間）を作り直す。表はその日の行だけ消して入れ直す（回数の表なので消しても記録は失われない。元の表には触らない）
create or replace function ops.usage_daily_build(p_day date) returns integer
language plpgsql security definer set search_path = ops, public set statement_timeout = '60s' as $$
declare
  t0 timestamptz := (p_day::timestamp at time zone 'Asia/Tokyo');
  t1 timestamptz := ((p_day + 1)::timestamp at time zone 'Asia/Tokyo');
  v_rows integer;
begin
  if p_day is null then return 0; end if;
  delete from ops.usage_daily where day = p_day;
  insert into ops.usage_daily (day, metric, key, n, sessions)
  -- 印が押せた数（サーバーが記録した数）
  select p_day, 'checkin', 'ok', count(*)::int, null::int from public.checkins where created_at >= t0 and created_at < t1 having count(*) > 0
  union all
  -- サーバーが断った数（範囲外・精度が低い＝屋内など・古い位置・押しすぎ・もう押した）
  select p_day, 'checkin', reason, count(*)::int, null from ops.checkin_rejections where created_at >= t0 and created_at < t1 group by reason
  union all
  -- 画面の記録：電波がなく端末に保存した・画面に返った失敗の理由・位置が取れなかった（1 許可なし・2 取れない・3 時間切れ）
  select p_day,
         case event when 'checkin_queued' then 'checkin' when 'checkin_fail' then 'client_fail' when 'geo_fail' then 'geo'
                    when 'tab' then 'tab' when 'open' then 'open' else 'onboard' end,
         case event when 'checkin_queued' then 'queued' when 'checkin_fail' then coalesce(prop, '')
                    when 'geo_fail' then coalesce(prop, '') when 'tab' then coalesce(prop, '') when 'open' then coalesce(prop, '')
                    else event || ':' || coalesce(prop, '') end,
         count(*)::int, count(distinct session)::int
    from ops.usage_events
   where created_at >= t0 and created_at < t1
     and (event in ('checkin_queued', 'checkin_fail', 'geo_fail', 'tab', 'open')
          -- はじめての流れ：案内（guide done/skip）・登録（signup の各段）・同意（terms）・入口（gate）
          or event in ('guide', 'signup', 'terms', 'gate'))
   group by 2, 3
  union all
  -- エラーの種類（中身・端末は見ない。種類ごとの数だけ）
  select p_day, 'error', kind, count(*)::int, null from ops.client_errors where created_at >= t0 and created_at < t1 group by kind;
  get diagnostics v_rows = row_count;
  insert into ops.usage_daily_runs (day, made_at, rows) values (p_day, now(), v_rows)
  on conflict (day) do update set made_at = excluded.made_at, rows = excluded.rows;
  return v_rows;
end $$;
revoke all on function ops.usage_daily_build(date) from public, anon, authenticated;

-- 毎晩：前の日と前の前の日（遅れて届いた記録の分）を作り直し、まだ作っていない古い日を1回に p_max 日ずつ（180日前まで）
create or replace function ops.usage_daily_fill(p_max integer default 14) returns integer
language plpgsql security definer set search_path = ops, public set statement_timeout = '110s' as $$
declare
  today date := (now() at time zone 'Asia/Tokyo')::date;
  d date; done integer := 0;
begin
  perform ops.usage_daily_build(today - 1);
  perform ops.usage_daily_build(today - 2);
  done := 2;
  for d in
    select g::date from generate_series(today - 3, today - 180, interval '-1 day') g
     where not exists (select 1 from ops.usage_daily_runs r where r.day = g::date)
     order by g desc limit greatest(coalesce(p_max, 0), 0)
  loop
    perform ops.usage_daily_build(d);
    done := done + 1;
  end loop;
  return done;
end $$;
revoke all on function ops.usage_daily_fill(integer) from public, anon, authenticated;

-- 運営コンソールで見る（管理者だけ）。日ごとに、印・位置・画面の失敗・エラー・タブ・起動・はじめての流れの回数
--   indoor は「屋内などで位置が取れなかった」の目安：サーバーの low_accuracy ＋ 画面の geo_fail の 2（取れない）と 3（時間切れ）
create or replace function public.admin_usage_counts(p_days integer default 30) returns jsonb
language plpgsql stable security definer set search_path = ops, public as $$
declare d integer := least(greatest(coalesce(p_days, 30), 1), 400);
        d1 date := (now() at time zone 'Asia/Tokyo')::date - 1;
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'note', '回数だけ（利用者ID・IP・位置は使わない）。sessions は起動ごとの使い捨ての値を数えたもの。前の日まで（毎晩3時37分に作る）',
    'days', (select coalesce(jsonb_agg(x order by x.day desc), '[]'::jsonb) from (
      select g::date as day,
             (select coalesce(jsonb_object_agg(key, n), '{}'::jsonb) from ops.usage_daily u where u.day = g::date and metric = 'checkin') as checkin,
             (select coalesce(sum(n) filter (where (metric = 'checkin' and key = 'low_accuracy') or (metric = 'geo' and key in ('2', '3'))), 0)
                from ops.usage_daily u where u.day = g::date) as indoor,
             (select coalesce(jsonb_object_agg(key, n), '{}'::jsonb) from ops.usage_daily u where u.day = g::date and metric = 'geo') as geo,
             (select coalesce(jsonb_object_agg(key, n), '{}'::jsonb) from ops.usage_daily u where u.day = g::date and metric = 'client_fail') as client_fail,
             (select coalesce(jsonb_object_agg(key, n), '{}'::jsonb) from ops.usage_daily u where u.day = g::date and metric = 'error') as error,
             (select coalesce(jsonb_object_agg(key, jsonb_build_object('n', n, 'sessions', sessions)), '{}'::jsonb) from ops.usage_daily u where u.day = g::date and metric = 'tab') as tab,
             (select coalesce(jsonb_object_agg(key, jsonb_build_object('n', n, 'sessions', sessions)), '{}'::jsonb) from ops.usage_daily u where u.day = g::date and metric = 'open') as open,
             (select coalesce(jsonb_object_agg(key, jsonb_build_object('n', n, 'sessions', sessions)), '{}'::jsonb) from ops.usage_daily u where u.day = g::date and metric = 'onboard') as onboard,
             exists (select 1 from ops.usage_daily_runs r where r.day = g::date) as made
        from generate_series(d1 - (d - 1), d1, interval '1 day') g) x));
end $$;
revoke all on function public.admin_usage_counts(integer) from public, anon;
grant execute on function public.admin_usage_counts(integer) to authenticated;

-- 毎晩 3時37分（日本時間）。上限2分・ロック待ち5秒
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  if exists (select 1 from cron.job where jobname = 'usage-daily') then perform cron.unschedule('usage-daily'); end if;
  execute $q$ select cron.schedule('usage-daily', '37 18 * * *', $job$ set statement_timeout = '2min'; set lock_timeout = '5s';
    select ops.usage_daily_fill(14) $job$) $q$;
end
$outer$;
