-- 海外の空港の止まり具合（11/15 本人「OK」：report-world-ops-sources の案1・2。決定事項【11/15】）
-- ・world_airport_status：アメリカ（ハワイ・グアム含む）の FAA NAS Status を2分に1回読み、日本から直行便のある空港の
--   地上待機・出発の間引き・閉鎖・15分以上の遅れ・除氷を残す（取り込みは関数 world-status）。終わったものは3日で消す
--   （航路・機体の記録ではない）。取れないとき・古いとき（FAA の Update_Time か取った時刻が10分より前）は出さない
-- ・world_status_put：1回分の取り込みを入れる（続いているものは時刻を書き直す・なくなったものは終わりにする）。新しく始まったものを返す
-- ・world_status_now：いま出してよいもの（新しい・終わっていない）。通知（alert_merge）と画面が使う
-- ・world_flight_counts：今ある JAL・ANA の国際線（flight_schedule）を、海外の空港ごとに「欠航○便・30分以上の遅れ○便」に数える
-- ・world_airport_ops：画面で使う。空港ごとに FAA の止まり具合と便の数をまとめ、出典の文を付けて返す
-- ・alert_push_log に world（通知に足した止まり具合の印）と rank 0（止まり具合だけの通知。「この便に乗る」の人だけ）を足し、
--   alert_push_claim は止まり具合がはじめて分かったときにも同じ便の通知を上書きして知らせる（新しい通知は増やさない）
-- 影響：チェックイン（運用タブ・乗る便の通知）。経営は使わない
set lock_timeout = '10s';

create table if not exists public.world_airport_status (
  id          bigint generated always as identity primary key,
  iata        text not null check (iata ~ '^[A-Z]{3}$'),
  source      text not null default 'faa' check (source in ('faa')),
  kind        text not null check (kind in ('ground_stop', 'gdp', 'closure', 'delay_arr', 'delay_dep', 'deicing')),
  reason      text check (length(reason) <= 300),
  starts      timestamptz,                 -- 始まり（閉鎖の Start。分からなければ null）
  ends        timestamptz,                 -- 終わりの見込み（地上待機の End_Time・閉鎖の Reopen。分からなければ null）
  avg_delay   int check (avg_delay is null or avg_delay between 0 and 1440),   -- 平均の遅れ（分。出発の間引き）
  max_delay   int check (max_delay is null or max_delay between 0 and 1440),   -- いちばん大きい遅れ（分）
  trend       text check (trend in ('increasing', 'decreasing', 'steady')),
  first_seen  timestamptz not null default now(),
  feed_at     timestamptz not null,        -- FAA の Update_Time
  fetched_at  timestamptz not null default now(),
  ended_at    timestamptz                  -- 次の取り込みで出てこなかった時刻（終わった）
);
-- 続いているものは、空港・種類ごとに1行
create unique index if not exists world_airport_status_live on public.world_airport_status (source, iata, kind) where ended_at is null;
create index if not exists world_airport_status_iata on public.world_airport_status (iata) where ended_at is null;
alter table public.world_airport_status enable row level security;
revoke all on public.world_airport_status from public, anon, authenticated;
grant select on public.world_airport_status to anon, authenticated;
drop policy if exists world_airport_status_read on public.world_airport_status;
create policy world_airport_status_read on public.world_airport_status for select to anon, authenticated using (true);
-- 書くのは service_role（関数 world-status）だけ

-- 1回分を入れる。p は [{iata, kind, reason, starts, ends, avg_delay, max_delay, trend}]（同じ空港・種類は1つ）。
-- 新しく始まったものの (iata, kind) を返す
-- 届いた一覧（jsonb）を行にする。同じ空港・種類は1つ
create or replace function public.world_status_rows(p jsonb)
returns table (iata text, kind text, reason text, starts timestamptz, ends timestamptz, avg_delay int, max_delay int, trend text)
language sql immutable set search_path = public as $$
  select distinct on (upper(x->>'iata'), x->>'kind') upper(x->>'iata'), x->>'kind', left(x->>'reason', 300),
         (x->>'starts')::timestamptz, (x->>'ends')::timestamptz,
         least(greatest((x->>'avg_delay')::int, 0), 1440), least(greatest((x->>'max_delay')::int, 0), 1440),
         nullif(x->>'trend', '')
    from jsonb_array_elements(case when jsonb_typeof(p) = 'array' then p else '[]'::jsonb end) x
   where x->>'iata' ~ '^[A-Za-z]{3}$'
   order by upper(x->>'iata'), x->>'kind'
$$;
revoke all on function public.world_status_rows(jsonb) from public, anon, authenticated;
grant execute on function public.world_status_rows(jsonb) to service_role;

create or replace function public.world_status_put(p_source text, p_feed_at timestamptz, p jsonb)
returns table (iata text, kind text)
language plpgsql security definer set search_path = public as $$
begin
  -- 一時の表は使わない（システムの表に書かない）。届いた一覧は jsonb のまま各文で読む
  -- なくなったもの：終わりにする
  update public.world_airport_status w set ended_at = now()
   where w.source = p_source and w.ended_at is null
     and not exists (select 1 from public.world_status_rows(p) n where n.iata = w.iata and n.kind = w.kind);
  -- 続いているもの：中身と時刻を書き直す
  update public.world_airport_status w
     set reason = n.reason, starts = n.starts, ends = n.ends, avg_delay = n.avg_delay, max_delay = n.max_delay,
         trend = n.trend, feed_at = p_feed_at, fetched_at = now()
    from public.world_status_rows(p) n
   where w.source = p_source and w.ended_at is null and w.iata = n.iata and w.kind = n.kind;
  -- 新しく始まったもの
  return query
  insert into public.world_airport_status as w (iata, source, kind, reason, starts, ends, avg_delay, max_delay, trend, feed_at)
  select n.iata, p_source, n.kind, n.reason, n.starts, n.ends, n.avg_delay, n.max_delay, n.trend, p_feed_at
    from public.world_status_rows(p) n
   where not exists (select 1 from public.world_airport_status o
                      where o.source = p_source and o.ended_at is null and o.iata = n.iata and o.kind = n.kind)
  returning w.iata, w.kind;
end $$;
revoke all on function public.world_status_put(text, timestamptz, jsonb) from public, anon, authenticated;
grant execute on function public.world_status_put(text, timestamptz, jsonb) to service_role;

-- いま出してよいもの：終わっていない・FAA の Update_Time も取った時刻も10分以内
create or replace function public.world_status_now(p_iata text[] default null)
returns table (iata text, source text, kind text, reason text, starts timestamptz, ends timestamptz,
               avg_delay int, max_delay int, trend text, first_seen timestamptz, feed_at timestamptz)
language sql stable security definer set search_path = public as $$
  select w.iata, w.source, w.kind, w.reason, w.starts, w.ends, w.avg_delay, w.max_delay, w.trend, w.first_seen, w.feed_at
    from public.world_airport_status w
   where w.ended_at is null
     and w.feed_at > now() - interval '10 minutes' and w.fetched_at > now() - interval '10 minutes'
     and (p_iata is null or w.iata = any(p_iata))
   order by w.iata, w.kind
$$;
revoke all on function public.world_status_now(text[]) from public;
grant execute on function public.world_status_now(text[]) to anon, authenticated, service_role;

-- 今ある JAL・ANA の国際線を、海外の空港（日本の空港の表にない記号）ごとに数える。p_date は運航日（日本時間）。
-- 共同運航・時刻表の重なり（同じ出発・到着・定刻）は1便に数える。遅れは出発（実際か見込み）か到着（実際か見込み）が定刻より30分以上
create or replace function public.world_flight_counts(p_date date default null)
returns table (iata text, flights int, cancelled int, late30 int)
language sql stable security definer set search_path = public as $$
  with d as (select coalesce(p_date, (now() at time zone 'Asia/Tokyo')::date) as day),
  f as (
    select distinct on (s.dep, s.arr, s.std) s.dep, s.arr,
           coalesce(s.dep_status ~* 'cancel' or s.arr_status ~* 'cancel', false) as cx,
           (coalesce(s.atd, s.etd) >= s.std + interval '30 minutes' or coalesce(s.ata, s.eta) >= s.sta + interval '30 minutes') as lt
      from public.flight_schedule s, d
     where s.svc_date = d.day
     order by s.dep, s.arr, s.std, (s.dep_status is null and s.arr_status is null), s.id
  ),
  x as (
    select ap, cx, lt from f, lateral (values (f.dep), (f.arr)) v(ap)
     where not exists (select 1 from public.airports a where a.iata = v.ap)
  )
  select ap, count(*)::int, count(*) filter (where cx)::int, count(*) filter (where lt and not cx)::int
    from x group by ap order by ap
$$;
revoke all on function public.world_flight_counts(date) from public;
grant execute on function public.world_flight_counts(date) to anon, authenticated, service_role;

-- 画面で使う：空港ごとの止まり具合（FAA）と今日の便の数。p_iata を渡せばその空港だけ。
-- 返す形：{ source, note, airports: [{ iata, faa: [{kind, reason, starts, ends, avg_delay, max_delay, trend, since}], flights, cancelled, late30 }] }
create or replace function public.world_airport_ops(p_iata text default null)
returns jsonb
language sql stable security definer set search_path = public as $$
  with st as (
    select s.iata, jsonb_agg(jsonb_build_object('kind', s.kind, 'reason', s.reason, 'starts', s.starts, 'ends', s.ends,
             'avg_delay', s.avg_delay, 'max_delay', s.max_delay, 'trend', s.trend, 'since', s.first_seen) order by s.kind) faa
      from public.world_status_now(case when p_iata is null then null else array[upper(p_iata)] end) s group by s.iata
  ), ct as (
    select * from public.world_flight_counts(null) c where p_iata is null or c.iata = upper(p_iata)
  ), j as (
    select coalesce(st.iata, ct.iata) iata, coalesce(st.faa, '[]'::jsonb) faa,
           coalesce(ct.flights, 0) flights, coalesce(ct.cancelled, 0) cancelled, coalesce(ct.late30, 0) late30
      from st full join ct on ct.iata = st.iata
  )
  select jsonb_build_object(
    'source', 'FAA NAS Status',
    'note', '出典：FAA NAS Status。運航の判断には使えません。遅れることがあります。便の数は JAL・ANA の運航情報（ODPT）から数えたものです',
    'airports', coalesce((select jsonb_agg(jsonb_build_object('iata', iata, 'faa', faa, 'flights', flights, 'cancelled', cancelled, 'late30', late30)
                                 order by jsonb_array_length(faa) desc, cancelled desc, late30 desc, iata) from j), '[]'::jsonb))
$$;
revoke all on function public.world_airport_ops(text) from public;
grant execute on function public.world_airport_ops(text) to anon, authenticated;

-- 通知：止まり具合の印（world）と、止まり具合だけの通知（rank 0）
alter table public.alert_push_log add column if not exists world text check (world is null or length(world) <= 80);
alter table public.alert_push_log drop constraint if exists alert_push_log_rank_check;
alter table public.alert_push_log add constraint alert_push_log_rank_check check (rank between 0 and 5);

-- 送ってよいものを決めて記録する（168 の決まりに「止まり具合がはじめて分かった・変わった」を足す）。
-- p は [{sub_id, gkey, svc_date, rank, late, official, body, world}]
create or replace function public.alert_push_claim(p jsonb) returns table (sub_id bigint, gkey text, again boolean)
language sql security definer set search_path = public as $$
  insert into public.alert_push_log as t (sub_id, gkey, svc_date, rank, late, official, body, world)
  select (x->>'sub_id')::bigint, x->>'gkey', (x->>'svc_date')::date, (x->>'rank')::smallint, (x->>'late')::int,
         coalesce((x->>'official')::boolean, false), left(x->>'body', 400), left(nullif(x->>'world', ''), 80)
    from jsonb_array_elements(coalesce(p, '[]'::jsonb)) x
   where exists (select 1 from public.push_subs s where s.id = (x->>'sub_id')::bigint)
  on conflict on constraint alert_push_log_pkey do update
     set rank = greatest(t.rank, excluded.rank),
         late = case when excluded.rank >= 1 then excluded.late else t.late end,   -- 止まり具合だけの通知は遅れの記録を変えない
         official = t.official or excluded.official,
         body = excluded.body, world = coalesce(excluded.world, t.world), n = t.n + 1, sent_at = now()
   where excluded.rank > t.rank                                                       -- 欠航・ダイバート・引き返しになった（止まり具合だけ → 遅れも）
      or (excluded.official and not t.official and excluded.rank >= t.rank)            -- 航空会社の運航情報がはじめて届いた
      or (excluded.rank between 1 and 2 and excluded.rank = t.rank and coalesce(excluded.late, 0) >= coalesce(t.late, 0) + 30)   -- 遅れが30分以上ふえた
      or (excluded.world is not null and excluded.world is distinct from t.world and excluded.rank >= least(t.rank, 1))   -- 着く・出る空港の止まり具合がはじめて分かった・変わった
  returning t.sub_id, t.gkey, (t.n > 1) as again
$$;
revoke all on function public.alert_push_claim(jsonb) from public, anon, authenticated;
grant execute on function public.alert_push_claim(jsonb) to service_role;

do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron')
     or not exists (select 1 from pg_available_extensions where name = 'pg_net') then
    raise notice 'pg_cron / pg_net がないため、FAA の取り込みと掃除は設定しない';
    return;
  end if;
  execute 'create extension if not exists pg_net with schema extensions';
  execute 'create extension if not exists pg_cron';
  -- FAA NAS Status を2分に1回（1日720回。外へ問い合わせるのは関数の中で1回だけ）
  execute $q$
    select cron.schedule('world-status', '*/2 * * * *', $job$
      set statement_timeout = '10s'; set lock_timeout = '5s';
      select net.http_get(
        url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/world-status',
        headers := '{"User-Agent": "soramemo (world-status)"}'::jsonb,
        timeout_milliseconds := 40000)
    $job$)
  $q$;
  -- 終わってから3日たったもの・3日取れていないものを消す
  execute $q$
    select cron.schedule('world-status-cleanup', '35 19 * * *', $job$
      set statement_timeout = '30s'; set lock_timeout = '5s';
      delete from public.world_airport_status
       where ended_at < now() - interval '3 days' or fetched_at < now() - interval '3 days';
    $job$)
  $q$;
end
$outer$;
