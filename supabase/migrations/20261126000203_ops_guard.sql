-- 裏側の守り（データ担当・data/ops-guard。PM の指示 11/26 3時25分：Gemini の裏側10案のうち 1・2）
--   1. 死活の記録：毎日・毎分の取り込みが止まっていないかを、今ある記録（各処理の runs の表・最新の行の時刻）から1か所で見る
--      ops.data_health()：取り込みごとに「最後に届いた時刻・上限・ok」を返す（読むだけ。新しい表は作らない）
--      ops.data_health_watch()：止まっている・0件・失敗があるときだけ ops.client_errors に kind = 'data_stale' を1行（同じ中身は6時間に1回まで）。
--        detail.notify に、本人へ送る通知の下書きの文を入れる（今は送らない。送る先と方法は本人が決めてから）
--      public.admin_data_health()：管理の画面から読む口（管理者だけ）。画面にはまだ出さない
--      毎時23分に watch を呼ぶ（上限30秒）
--   2. 前の正しい値を守る：
--      timetable_replace：ODPT が空や極端に少ない返事をしたときに、空港×航空会社の時刻表をまるごと消していた → 前のまま残して例外にする
--        （新しい行が0で前に行がある／前が20行以上で新しい行が前の4割未満）。timetable-sync は例外を「〇〇_error」として記録するだけなので変えなくてよい
--      foreign_usual_build：作り直しの結果が前の半分未満（前が20行以上）なら、消さずに前のまま残す
--   表・列・RLS・表の権限は変えない。記録は消さない。影響：チェックイン（時刻表と「いつもより遅い」が、取り込みの失敗で消えなくなるだけ）。経営は関係しない
set lock_timeout = '5s';

-- 2-1 時刻表の入れ替え
create or replace function public.timetable_replace(p_operator text, p_dep text, p_rows jsonb) returns integer
language plpgsql security definer set search_path = public set lock_timeout = '5s' as $$
declare n integer; v_old integer; v_new integer;
begin
  if p_operator not in ('JAL', 'ANA') or p_dep !~ '^[A-Z]{3}$' or jsonb_typeof(p_rows) <> 'array' then raise exception 'bad input'; end if;
  select count(*) into v_old from public.timetable where operator = p_operator and dep = p_dep;
  select count(*) into v_new from jsonb_array_elements(p_rows) r where r->>'dep' = p_dep and r->>'operator' = p_operator;
  -- 空の返事・極端に少ない返事では入れ替えない（前の正しい時刻表を残す）
  if v_old > 0 and (v_new = 0 or (v_old >= 20 and v_new < v_old * 0.4)) then
    raise exception 'kept previous timetable: % rows -> % rows', v_old, v_new;
  end if;
  delete from public.timetable where operator = p_operator and dep = p_dep;
  insert into public.timetable (operator, dep, arr, flight, days, valid_from, valid_to, dep_time, arr_time, arr_day, aircraft)
  select p_operator, p_dep, r->>'arr', r->>'flight', (r->>'days')::smallint, (r->>'valid_from')::date, (r->>'valid_to')::date,
         r->>'dep_time', r->>'arr_time', coalesce((r->>'arr_day')::smallint, 0), nullif(r->>'aircraft', '')
  from jsonb_array_elements(p_rows) r
  where r->>'dep' = p_dep and r->>'operator' = p_operator
  on conflict do nothing;
  get diagnostics n = row_count;
  return n;
end;
$$;

-- 2-2 海外の便の「いつもの時刻」の作り直し
create or replace function public.foreign_usual_build() returns int
language plpgsql security definer set search_path = public set lock_timeout = '5s' as $$
declare today date := (now() at time zone 'Asia/Tokyo')::date; v_n int; v_old int;
begin
  select count(*) into v_old from public.foreign_usual;
  create temp table if not exists foreign_usual_new (like public.foreign_usual including defaults) on commit drop;
  truncate foreign_usual_new;
  with b as (
    select callsign, iata, dep_here, day, extract(dow from day)::int as dow,
           (extract(hour from at at time zone 'Asia/Tokyo') * 60 + extract(minute from at at time zone 'Asia/Tokyo'))::int as m
      from public.foreign_legs
     where day >= today - 56 and day < today and event is null
  ), g as (
    -- 0時をまたぐ便（23:50 と 0:10）のために、12時間ずらした時刻でも中央値を出し、ばらつきの小さいほうを使う
    select callsign, iata, dep_here, case when grouping(dow) = 1 then -1 else dow end as dow, count(*) as n, max(day) as last_day,
           percentile_cont(0.5) within group (order by m) as med_a,
           percentile_cont(0.75) within group (order by m) - percentile_cont(0.25) within group (order by m) as iqr_a,
           percentile_cont(0.5) within group (order by (m + 720) % 1440) as med_b,
           percentile_cont(0.75) within group (order by (m + 720) % 1440) - percentile_cont(0.25) within group (order by (m + 720) % 1440) as iqr_b
      from b
     group by grouping sets ((callsign, iata, dep_here, dow), (callsign, iata, dep_here))
  )
  insert into foreign_usual_new (callsign, iata, dep_here, dow, mins, n, spread, last_day)
  select callsign, iata, dep_here, dow,
         (case when iqr_a <= iqr_b then round(med_a)::int else (round(med_b)::int + 720) % 1440 end) % 1440,
         n, round(least(iqr_a, iqr_b))::int, last_day
    from g
   where least(iqr_a, iqr_b) <= 60 and ((dow >= 0 and n >= 3) or (dow = -1 and n >= 5));
  select count(*) into v_n from foreign_usual_new;
  -- 全機の記録が止まっていた等で、作り直しが前の半分未満なら前のまま残す
  if v_old >= 20 and v_n < v_old * 0.5 then
    raise warning 'foreign_usual_build: kept previous (% rows -> % rows)', v_old, v_n;
    return 0;
  end if;
  delete from public.foreign_usual where true;
  insert into public.foreign_usual (callsign, iata, dep_here, dow, mins, n, spread, last_day, built_at)
  select callsign, iata, dep_here, dow, mins, n, spread, last_day, coalesce(built_at, now()) from foreign_usual_new;
  return v_n;
end $$;

-- 1 死活の記録（今ある記録を読むだけ。どれも索引の先頭か小さな表で引く）
create or replace function ops.data_health() returns jsonb
language plpgsql stable security definer set search_path = public, ops set statement_timeout = '20s' as $$
declare
  today date := (now() at time zone 'Asia/Tokyo')::date;
  jst_h int := extract(hour from now() at time zone 'Asia/Tokyo')::int;
  want_hist date;
  out jsonb := '[]'::jsonb;
  tt_bad jsonb;
  cron_bad jsonb := '[]'::jsonb;
begin
  -- 便の実績は毎朝4時50分ごろに前の日の分ができる（6時より前は、おとといの分まであればよい）
  want_hist := case when jst_h >= 6 then today - 1 else today - 2 end;
  with s(key, label, last, limit_min) as (values
    ('live_positions', '機体の位置（adsb.lol）',                (select max(seen_at) from public.live_positions), 60),
    ('track_points',   '全機の航跡（adsb.lol）',                (select max(t) from public.track_points), 60),
    ('reg_legs',       '機体の区間（全機の記録から）',          (select max(last_at) from public.reg_legs where day >= today - 1), 180),
    ('odpt_status',    '航空会社の運航情報の取り込み（ODPT）',  (select max(ran_at) from public.odpt_status_runs), 30),
    ('odpt_feed',      'ODPT のデータの時刻',                   (select max(fetched_at) from public.odpt_feed_dates), 180),
    ('flight_watch',   '乗る便の見張り',                        (select max(ran_at) from public.flight_watch_runs), 15),
    ('schedule_sync',  '今日と明日の便（ODPT）',                (select max(ran_at) from public.schedule_sync_runs), 26 * 60),
    ('timetable_sync', '先の時刻表（ODPT）',                    (select max(ran_at) from public.timetable_sync_runs), 26 * 60),
    ('daily_archive',  '毎朝の記録づくり',                      (select max(ran_at) from public.archive_runs), 26 * 60),
    ('foreign_legs',   '海外の便の実績（全機の記録から）',      (select max(built_at) from public.foreign_legs where day >= today - 1), 6 * 60),
    ('wx_obs',         '羽田の天気の実況（METAR）',             (select max(at) from public.wx_obs where icao = 'RJTT'), 180),
    ('wx_taf',         '羽田の予報（TAF）',                     (select max(issued) from public.wx_taf where icao = 'RJTT'), 12 * 60)
  )
  select coalesce(jsonb_agg(jsonb_build_object('key', key, 'label', label, 'last', last, 'limit_min', limit_min,
           'ok', last is not null and last > now() - make_interval(mins => limit_min)) order by key), '[]'::jsonb)
    into out from s;

  -- 便の実績の0件（前の日の分ができていない）
  out := out || jsonb_build_array(jsonb_build_object('key', 'flight_history', 'label', '便の実績（' || to_char(want_hist, 'MM/DD') || ' の分）',
           'last', (select max(svc_date) from public.flight_history where svc_date >= today - 3), 'limit_min', null,
           'ok', exists (select 1 from public.flight_history where svc_date = want_hist)));

  -- 先の時刻表：直近26時間の取り込みで、失敗か0件の空港×航空会社
  select coalesce(jsonb_agg(r.iata || ' ' || e.key || '：' || left(e.value #>> '{}', 60) order by r.iata, e.key), '[]'::jsonb) into tt_bad
    from public.timetable_sync_runs r, jsonb_each(coalesce(r.result, '{}'::jsonb)) e
   where r.ran_at > now() - interval '26 hours'
     and (e.key like '%\_error' or (e.key in ('JAL', 'ANA') and e.value = '0'::jsonb));
  out := out || jsonb_build_array(jsonb_build_object('key', 'timetable_rows', 'label', '先の時刻表の失敗・0件（直近26時間）',
           'last', null, 'limit_min', null, 'ok', jsonb_array_length(tt_bad) = 0, 'detail', tt_bad));

  -- pg_cron の失敗（直近26時間。pg_cron のないところでは数えない）
  if to_regclass('cron.job_run_details') is not null then
    execute $q$
      select coalesce(jsonb_agg(x order by x), '[]'::jsonb) from (
        select coalesce(j.jobname, d.jobid::text) || ' ×' || count(*) as x
          from cron.job_run_details d left join cron.job j on j.jobid = d.jobid
         where d.status = 'failed' and d.start_time > now() - interval '26 hours'
         group by 1, j.jobname, d.jobid) s $q$ into cron_bad;
  end if;
  out := out || jsonb_build_array(jsonb_build_object('key', 'cron_failed', 'label', '毎日・毎分の処理の失敗（直近26時間）',
           'last', null, 'limit_min', null, 'ok', jsonb_array_length(cron_bad) = 0, 'detail', cron_bad));
  return out;
end $$;
revoke all on function ops.data_health() from public, anon, authenticated;

create or replace function ops.data_health_watch() returns int
language plpgsql security definer set search_path = public, ops set statement_timeout = '30s' as $$
declare h jsonb := ops.data_health(); bad jsonb; msg text;
begin
  select coalesce(jsonb_agg(x order by x->>'key'), '[]'::jsonb) into bad from jsonb_array_elements(h) x where not (x->>'ok')::boolean;
  if jsonb_array_length(bad) = 0 then return 0; end if;
  msg := left('取り込みが止まっている・失敗しているものがあります：' ||
              (select string_agg(x->>'label', '、' order by x->>'key') from jsonb_array_elements(bad) x), 300);
  -- 同じ中身は6時間に1回まで
  if exists (select 1 from ops.client_errors where kind = 'data_stale' and message = msg and created_at > now() - interval '6 hours') then return 0; end if;
  insert into ops.client_errors (session, platform, version, kind, message, detail)
  values ('server', 'server', 'data_health_watch', 'data_stale', msg,
          jsonb_build_object('bad', bad,
            -- 通知の下書き（今は送らない）
            'notify', jsonb_build_object('title', 'そらメモ：データの取り込みを確認してください',
                                         'body', left(msg || '（' || to_char(now() at time zone 'Asia/Tokyo', 'MM/DD HH24:MI') || ' 時点）', 200))));
  return 1;
end $$;
revoke all on function ops.data_health_watch() from public, anon, authenticated;

create or replace function public.admin_data_health() returns jsonb
language plpgsql stable security definer set search_path = ops, public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object('now', now(), 'items', ops.data_health());
end $$;
revoke all on function public.admin_data_health() from public, anon;
grant execute on function public.admin_data_health() to authenticated;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  if exists (select 1 from cron.job where jobname = 'data-health') then perform cron.unschedule('data-health'); end if;
  execute $q$ select cron.schedule('data-health', '23 * * * *', $job$ set statement_timeout = '30s'; set lock_timeout = '5s';
    select ops.data_health_watch() $job$) $q$;
end
$outer$;

reset lock_timeout;
