-- 乗る便に選んだ海外の会社・ODPT にない日本の会社の便の見張り（11/16 決定事項・PM の指示 ②。本人「おすすめ」）
--   ODPT の時刻表（flight_schedule）にない便は、今の見張り（flight-watch）と通知（alert_merge）の入口に乗らない。
--   そこで「この便に乗る」（push_subs.flights の「便名@運航日」）で選ばれた、時刻表にない便だけを小さな表 foreign_watch に持ち、
--   いつもの時刻（foreign_usual。前の8週の実績の中央値）を定刻の代わりにして、機体の位置（live_positions）から推定で見張る。
--   知らせるのは「いつもより○分遅い（推定）」「門限ギリギリ（推定）」「ダイバート」「引き返し」だけ（出発前の遅れと欠航は出せない）。
--   通知は今の決まり（alert_push_log・alert_push_claim：1便1件・重くなったら上書き）にそのまま乗せる（gkey は 便名@運航日@出発空港、
--   出発空港が分からない海外からの便は '---'）。
--   ・foreign_watch：見張りの途中の状態（記録ではない）。運航日の3日後に消す。航路と機体の記録は foreign_legs と全機の記録に残る
--   ・foreign_watch_sync()：選ばれた便のうち、時刻表になく、ODPT で見られる会社でない便を足す（呼び出し符号・いつもの到着空港と時刻つき）。
--     選ばれなくなった便は消す。5分ごと（cron foreign-watch-sync）
--   ・foreign_watch_put(p)：見張りの関数が状態を書く（service_role だけ）
--   ・foreign_watch_rows()：見張りの関数が読む（service_role だけ）
--   画面は変えない（「いつもより○分遅い（推定）」の画面は、デザインの画面案のあと）。読み書きは関数からだけ（RLS は有効、anon・authenticated には何も許さない）
--   影響：チェックイン（乗る便の通知が、時刻表にない便にも届くようになる。見張りの関数をつないだあと）。経営は使わない。
--   退会：push_subs は端末ごとの申し込みで、退会で消える。foreign_watch は便ごとの状態で、誰が選んだかは持たない
set lock_timeout = '10s';

create table if not exists public.foreign_watch (
  flight      text not null check (flight ~ '^[A-Z0-9]{2}[0-9]{1,4}$'),   -- 便名（先頭の0なし。例 BA5）
  svc_date    date not null,                                             -- 運航日（日本時間。選んだときの日）
  callsign    text not null check (callsign ~ '^[A-Z]{3}[0-9]{1,4}$'),   -- 見張る呼び出し符号（BAW5）
  dep         text check (dep ~ '^[A-Z]{3}$'),                           -- 日本の出発空港（いつも日本を出る便のとき）
  arr         text check (arr ~ '^[A-Z]{3}$'),                           -- 日本の到着空港（いつも着く空港）
  usual_dep   smallint check (usual_dep between 0 and 1439),             -- いつもの出発時刻（日本時間の分）
  usual_arr   smallint check (usual_arr between 0 and 1439),             -- いつもの到着時刻（日本時間の分）
  usual_n     smallint,                                                  -- いつもの時刻のもとになった回数
  state       jsonb not null default '{}'::jsonb check (pg_column_size(state) <= 4000),
  late        int check (late between -1440 and 1440),                   -- いつもとのずれの見込み（分）
  event       text check (event in ('return', 'divert')),
  eta         timestamptz,                                               -- 到着の見込み
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  primary key (flight, svc_date)
);
alter table public.foreign_watch enable row level security;
revoke all on public.foreign_watch from public, anon, authenticated;

-- 選ばれた便を足す・選ばれなくなった便と古い便を消す。足した数を返す
create or replace function public.foreign_watch_sync() returns int
language plpgsql security definer set search_path = public set lock_timeout = '5s' as $$
declare v_n int; today date := (now() at time zone 'Asia/Tokyo')::date;
begin
  with k as (
    -- 「この便に乗る」の便（今日の前後1日だけ）。先頭の0を除く
    select distinct regexp_replace(split_part(f, '@', 1), '^([A-Z0-9]{2})0+([0-9])', '\1\2') as flight, split_part(f, '@', 2)::date as svc_date
      from public.push_subs s, unnest(s.flights) f
     where f ~ '^[A-Z0-9]{2}[0-9]{1,4}@[0-9]{4}-[0-9]{2}-[0-9]{2}$'
       and split_part(f, '@', 2)::date between today - 1 and today + 1
  ), t as (
    select k.flight, k.svc_date, c.icao || substring(k.flight from '^[A-Z0-9]{2}([0-9]{1,4})$') as callsign, extract(dow from k.svc_date)::int as dow
      from k
      join lateral (
        -- 便名の記号 → 呼び出し符号の記号（ODPT で見られる会社は外す。同じ記号が2つあれば名前の順で先）
        select icao from public.airline_codes c where c.iata = substring(k.flight from '^([A-Z0-9]{2})') and not c.odpt order by icao limit 1
      ) c on true
     where not exists (select 1 from public.flight_schedule fs where fs.svc_date = k.svc_date
                         and regexp_replace(fs.flight, '^([A-Z0-9]{2})0+([0-9])', '\1\2') = k.flight)
  ), del as (
    delete from public.foreign_watch w
     where w.svc_date < today - 2
        or (w.svc_date >= today - 1 and not exists (select 1 from t where t.flight = w.flight and t.svc_date = w.svc_date))
  ), ins as (
    insert into public.foreign_watch (flight, svc_date, callsign, dep, arr, usual_dep, usual_arr, usual_n)
    select t.flight, t.svc_date, t.callsign, d.iata, a.iata, d.mins, a.mins, coalesce(a.n, d.n)
      from t
      -- いつも着く日本の空港と時刻（その曜日 → 曜日を問わない、の順。回数の多いもの）
      left join lateral (
        select u.iata, u.mins, u.n from public.foreign_usual u
         where u.callsign = t.callsign and u.dep_here = 0 and u.dow in (t.dow, -1)
         order by (u.dow = -1), u.n desc, u.iata limit 1
      ) a on true
      left join lateral (
        select u.iata, u.mins, u.n from public.foreign_usual u
         where u.callsign = t.callsign and u.dep_here = 1 and u.dow in (t.dow, -1)
         order by (u.dow = -1), u.n desc, u.iata limit 1
      ) d on true
    on conflict (flight, svc_date) do update
      set callsign = excluded.callsign, dep = excluded.dep, arr = excluded.arr,
          usual_dep = excluded.usual_dep, usual_arr = excluded.usual_arr, usual_n = excluded.usual_n
      where (foreign_watch.dep, foreign_watch.arr, foreign_watch.usual_dep, foreign_watch.usual_arr)
            is distinct from (excluded.dep, excluded.arr, excluded.usual_dep, excluded.usual_arr)
    returning 1
  ) select count(*)::int into v_n from ins;
  return v_n;
end $$;
revoke all on function public.foreign_watch_sync() from public, anon, authenticated;
grant execute on function public.foreign_watch_sync() to service_role;

-- 見張りの関数が読む：今日の前後1日の行
create or replace function public.foreign_watch_rows() returns setof public.foreign_watch
language sql stable security definer set search_path = public as $$
  select * from public.foreign_watch
   where svc_date between (now() at time zone 'Asia/Tokyo')::date - 1 and (now() at time zone 'Asia/Tokyo')::date + 1
   order by svc_date, flight
$$;
revoke all on function public.foreign_watch_rows() from public, anon, authenticated;
grant execute on function public.foreign_watch_rows() to service_role;

-- 見張りの関数が書く。p は [{flight, svc_date, state, late, event, eta}]。書いた数を返す（ない便は無視）
create or replace function public.foreign_watch_put(p jsonb) returns int
language plpgsql security definer set search_path = public set lock_timeout = '10s' as $$
declare v_n int;
begin
  with x as (
    select distinct on (x->>'flight', x->>'svc_date') x->>'flight' as flight, (x->>'svc_date')::date as svc_date,
           case when jsonb_typeof(x->'state') = 'object' then x->'state' else '{}'::jsonb end as state,
           least(greatest((x->>'late')::int, -1440), 1440) as late,
           case when x->>'event' in ('return', 'divert') then x->>'event' end as event,
           (x->>'eta')::timestamptz as eta
      from jsonb_array_elements(case when jsonb_typeof(p) = 'array' then p else '[]'::jsonb end) x
     where x->>'flight' ~ '^[A-Z0-9]{2}[0-9]{1,4}$' and x->>'svc_date' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
  ), u as (
    update public.foreign_watch w set state = x.state, late = x.late, event = x.event, eta = x.eta, updated_at = now()
      from x where w.flight = x.flight and w.svc_date = x.svc_date
    returning 1
  ) select count(*)::int into v_n from u;
  return v_n;
end $$;
revoke all on function public.foreign_watch_put(jsonb) from public, anon, authenticated;
grant execute on function public.foreign_watch_put(jsonb) to service_role;

-- 5分ごとに選ばれた便を足す（軽い。push_subs は全部で数件〜数千件）
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  execute $q$
    select cron.schedule('foreign-watch-sync', '*/5 * * * *', $job$
      set statement_timeout = '30s'; set lock_timeout = '5s';
      select public.foreign_watch_sync();
    $job$)
  $q$;
end
$outer$;
