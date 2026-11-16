-- ODPT のデータの時刻（dc:date）を残す（11/16 PM「見落としの片付け」2。ストアの前に要る：ODPT のデータを出す所にデータの時刻を添える）
-- ・odpt_feed_dates：種類と航空会社ごと（例 FlightInformationDeparture:JAL・FlightSchedule:ANA）に、いちばん新しい dc:date と
--   最後に取り込んだ時刻・件数を1行で持つ。取り込むたびに上書きするだけで行は増えない（航路・機体の記録ではない）
-- ・odpt_feed_date_put：取り込みの関数（odpt-status・timetable-sync・schedule-sync）が呼ぶ。dc:date は前より古くしない
--   （空港ごとに取り込む時刻表は、いちばん新しいものを残す）。件数が0で dc:date がないときは時刻だけ書き直す
-- ・画面（チェックイン担当）は odpt_feed_dates を select して「ODPT のデータ ○時○分 時点」と出す。airport-now は返す flights に dc_date を足した
-- 影響：チェックイン（出典の表示に使える。今の画面は変わらない）。経営は使わない
set lock_timeout = '10s';

create table if not exists public.odpt_feed_dates (
  feed        text primary key check (feed ~ '^[A-Za-z]{1,40}:[A-Za-z0-9]{1,16}$'),
  dc_date     timestamptz,                         -- ODPT の dc:date のいちばん新しいもの（なければ null）
  fetched_at  timestamptz not null default now(),  -- 最後に取り込んだ時刻
  n           int not null default 0 check (n between 0 and 100000)   -- 最後に取り込んだ件数
);
alter table public.odpt_feed_dates enable row level security;
revoke all on public.odpt_feed_dates from public, anon, authenticated;
grant select on public.odpt_feed_dates to anon, authenticated;
drop policy if exists odpt_feed_dates_read on public.odpt_feed_dates;
create policy odpt_feed_dates_read on public.odpt_feed_dates for select to anon, authenticated using (true);
-- 書くのは service_role（下の関数）だけ

-- p は [{feed, dc_date, n}]。入れた・書き直した行の数を返す
create or replace function public.odpt_feed_date_put(p jsonb)
returns int
language plpgsql security definer set search_path = public set lock_timeout = '5s' as $$
declare k int;
begin
  insert into public.odpt_feed_dates as o (feed, dc_date, fetched_at, n)
  select distinct on (x->>'feed') x->>'feed', (x->>'dc_date')::timestamptz, now(), least(greatest(coalesce((x->>'n')::int, 0), 0), 100000)
    from jsonb_array_elements(case when jsonb_typeof(p) = 'array' then p else '[]'::jsonb end) x
   where x->>'feed' ~ '^[A-Za-z]{1,40}:[A-Za-z0-9]{1,16}$'
   order by x->>'feed', (x->>'dc_date')::timestamptz desc nulls last
  on conflict (feed) do update
     set dc_date = greatest(o.dc_date, excluded.dc_date),   -- greatest は null を飛ばす
         fetched_at = excluded.fetched_at,
         n = excluded.n;
  get diagnostics k = row_count;
  return k;
end $$;
revoke all on function public.odpt_feed_date_put(jsonb) from public, anon, authenticated;
grant execute on function public.odpt_feed_date_put(jsonb) to service_role;
