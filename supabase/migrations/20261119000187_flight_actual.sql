-- フライトの「実際の出発・到着」（11/20 PM：「空の上」を実際の飛行時間に・地図に実際の飛行ルート）
-- ・今の flights.dep_at・arr_at はチェックインの時刻。画面の「空の上」はその差の合計だった
-- ・便名が分かったフライトに、実際に運航した便の出発・到着の時刻を足す：
--     act_dep_at・act_arr_at … 実際の出発・到着（どちらも入るか、どちらも空）
--     act_src                … どこから取ったか
--         'odpt'      ＝ 航空会社の運航情報（ODPT）の実際の時刻（出発・到着とも）
--         'adsb'      ＝ 片方か両方が機体の位置（adsb.lol・ODbL）からの推定の離陸・着陸の時刻（毎日の記録 flight_history）
--         'timetable' ＝ 実績がなく、時刻表の定刻（出発・到着とも）
--   実績と定刻はまぜない（出発だけ実績・到着は定刻、にはしない）。取れない便は空のまま（画面は今までどおりチェックインの時刻）
-- ・まだ来ていない時刻は入れない（atd-future・移行186と同じ守り）。照合の関数がまちがえても、入れる前の守り（trg）で外す
-- ・入れるのは照合（verify-flights・tools/verify_flights.ts）と毎晩の記録（daily-archive）が呼ぶ flights_fill_actual だけ。
--   利用者は書けない（flights への insert・update・delete の権限はもともと外してある）。読むのは本人の分だけ（今の "own flights" のまま）
-- ・航跡：flights.track（[[緯度, 経度], ...]）は、毎晩の記録の便ごとの航跡（flight_tracks。adsb.lol・ODbL、31日分）から、
--   その日だけでなく31日前までさかのぼって埋める（flights_track_todo → daily-archive が書く）。OpenSky の航跡はもう使わない
--   （OpenSky は研究・非商用だけの条件。ストアと そらメモ＋ の前に外す）
-- 影響：チェックイン（フライトの画面の「空の上」と地図。列の名前はチェックイン担当へ渡す）。経営は使わない（経営の路線・距離は今のまま）
set lock_timeout = '10s';

alter table public.flights
  add column if not exists act_dep_at timestamptz,
  add column if not exists act_arr_at timestamptz,
  add column if not exists act_src    text;

do $$ begin
  alter table public.flights add constraint flights_act_src check (act_src in ('odpt', 'adsb', 'timetable'));
exception when duplicate_object then null; end $$;
-- 3つはそろって入るか、そろって空。到着は出発より後、20時間まで
do $$ begin
  alter table public.flights add constraint flights_act_pair check (
    (act_dep_at is null and act_arr_at is null and act_src is null)
    or (act_dep_at is not null and act_arr_at is not null and act_src is not null
        and act_arr_at > act_dep_at and act_arr_at - act_dep_at <= interval '20 hours'));
exception when duplicate_object then null; end $$;

-- まだ来ていない時刻は入れない（時計のずれの1分は認める）。来ていなければ3つとも空にする
create or replace function public.flights_act_guard() returns trigger
language plpgsql set search_path = public as $$
begin
  if new.act_dep_at > now() + interval '1 minute' or new.act_arr_at > now() + interval '1 minute' then
    new.act_dep_at := null; new.act_arr_at := null; new.act_src := null;
  end if;
  return new;
end $$;
drop trigger if exists flights_act_guard on public.flights;
create trigger flights_act_guard before insert or update of act_dep_at, act_arr_at, act_src on public.flights
  for each row execute function public.flights_act_guard();
revoke all on function public.flights_act_guard() from public, anon, authenticated;

-- 毎晩見る対象（便名があり、まだ航空会社の実際の時刻が入っていないフライト）
create index if not exists flights_act_todo on public.flights (arr_at)
  where flight_no is not null and (act_src is null or act_src <> 'odpt');

-- 実際の時刻を入れる。p_days：到着のチェックインが何日前までのフライトを見るか（1〜400）。p_limit：1回に見る数（新しい順）
--   取り先の順：毎日の記録（flight_history。400日）→ 時刻表（flight_schedule。14日、ODPT の実際の時刻つき）。
--   同じ便名（0を取ってくらべる。共同運航の便名も）・同じ区間で、定刻が「出発のチェックインの2時間前〜到着のチェックイン」の便。
--   いくつかあれば、定刻が出発のチェックインにいちばん近い便、同じなら確かな方（odpt → adsb → timetable）。欠航の便は使わない
--   書き直すのは、前より確かな取り先になったときと、同じ取り先で時刻が変わったときだけ。何度呼んでも同じ結果
create or replace function public.flights_fill_actual(p_days int default 3, p_limit int default 2000)
returns jsonb
language plpgsql security definer set search_path = public
set statement_timeout = '60s' set lock_timeout = '5s' as $$
declare r jsonb;
begin
  with f as (
    select f.id, f.dep_at, f.arr_at, public.flight_no_norm(f.flight_no) as fn, a1.iata as dep, a2.iata as arr,
           (f.dep_at at time zone 'Asia/Tokyo')::date as d0,
           case f.act_src when 'odpt' then 3 when 'adsb' then 2 when 'timetable' then 1 else 0 end as cur,
           f.act_dep_at as cur_d, f.act_arr_at as cur_a
      from public.flights f
      join public.airports a1 on a1.id = f.from_airport
      join public.airports a2 on a2.id = f.to_airport
     where f.flight_no is not null and (f.act_src is null or f.act_src <> 'odpt')
       and f.arr_at >= now() - make_interval(days => least(greatest(coalesce(p_days, 3), 1), 400))
       and f.arr_at < now()
       and a1.iata ~ '^[A-Z]{3}$' and a2.iata ~ '^[A-Z]{3}$'
     order by f.arr_at desc
     limit least(greatest(coalesce(p_limit, 2000), 1), 20000)
  ), pick as (
    select f.id, f.cur, f.cur_d, f.cur_a, c.d, c.a, c.src, c.rk
      from f
      join lateral (
        select x.d, x.a, x.src, case x.src when 'odpt' then 3 when 'adsb' then 2 else 1 end as rk
          from (
            select h.std,
                   case when h.atd is not null and h.ata is not null then h.atd else h.std end as d,
                   case when h.atd is not null and h.ata is not null then h.ata else h.sta end as a,
                   case when h.atd is not null and h.ata is not null
                        then case when h.atd_src = 'odpt' and h.ata_src = 'odpt' then 'odpt' else 'adsb' end
                        else 'timetable' end as src
              from public.flight_history h
             where h.svc_date between f.d0 - 1 and f.d0 + 1
               and h.dep = f.dep and h.arr = f.arr and not h.cancelled
               and (public.flight_no_norm(h.flight) = f.fn or exists (select 1 from unnest(h.also) o where public.flight_no_norm(o) = f.fn))
               and h.std between f.dep_at - interval '2 hours' and f.arr_at
            union all
            select s.std,
                   case when s.atd is not null and s.ata is not null then s.atd else s.std end,
                   case when s.atd is not null and s.ata is not null then s.ata else s.sta end,
                   case when s.atd is not null and s.ata is not null then 'odpt' else 'timetable' end
              from public.flight_schedule s
             where s.svc_date between f.d0 - 1 and f.d0 + 1
               and s.dep = f.dep and s.arr = f.arr and public.flight_no_norm(s.flight) = f.fn
               and coalesce(s.dep_status, '') !~* 'cancel' and coalesce(s.arr_status, '') !~* 'cancel'
               and s.std between f.dep_at - interval '2 hours' and f.arr_at
          ) x
         where x.d <= now() and x.a <= now() and x.a > x.d and x.a - x.d <= interval '20 hours'
         order by abs(extract(epoch from x.std - f.dep_at)), case x.src when 'odpt' then 3 when 'adsb' then 2 else 1 end desc
         limit 1
      ) c on true
  ), up as (
    update public.flights t
       set act_dep_at = p.d, act_arr_at = p.a, act_src = p.src
      from pick p
     where t.id = p.id
       and (p.rk > p.cur or (p.rk = p.cur and (p.cur_d is distinct from p.d or p.cur_a is distinct from p.a)))
    returning p.src
  )
  select jsonb_build_object(
           'checked', (select count(*) from f),
           'found',   (select count(*) from pick),
           'updated', (select count(*) from up),
           'odpt',      (select count(*) from up where src = 'odpt'),
           'adsb',      (select count(*) from up where src = 'adsb'),
           'timetable', (select count(*) from up where src = 'timetable'))
    into r;
  return r;
end $$;
revoke all on function public.flights_fill_actual(int, int) from public, anon, authenticated;
grant execute on function public.flights_fill_actual(int, int) to service_role;

-- 航跡のまだないフライトに、毎晩の記録の便ごとの航跡（flight_tracks・polyline。31日分）を渡す（daily-archive が間引いて書く）
--   便の決め方は flights_fill_actual と同じ（毎日の記録の便。欠航は除く）。航跡がある便だけ返す
create or replace function public.flights_track_todo(p_limit int default 300)
returns table (id bigint, pts text)
language sql stable security definer set search_path = public
set statement_timeout = '30s' as $$
  select f.id, t.pts
    from public.flights f
    join public.airports a1 on a1.id = f.from_airport
    join public.airports a2 on a2.id = f.to_airport
    join lateral (
      select h.svc_date, h.flight, h.dep
        from public.flight_history h
       where h.svc_date between (f.dep_at at time zone 'Asia/Tokyo')::date - 1 and (f.dep_at at time zone 'Asia/Tokyo')::date + 1
         and h.dep = a1.iata and h.arr = a2.iata and not h.cancelled
         and (public.flight_no_norm(h.flight) = public.flight_no_norm(f.flight_no)
              or exists (select 1 from unnest(h.also) o where public.flight_no_norm(o) = public.flight_no_norm(f.flight_no)))
         and h.std between f.dep_at - interval '2 hours' and f.arr_at
       order by abs(extract(epoch from h.std - f.dep_at))
       limit 1
    ) h on true
    join public.flight_tracks t on t.svc_date = h.svc_date and t.flight = h.flight and t.dep = h.dep
   where f.track is null and f.flight_no is not null
     and f.dep_at >= now() - interval '32 days'
     and a1.iata ~ '^[A-Z]{3}$' and a2.iata ~ '^[A-Z]{3}$'
   order by f.dep_at desc
   limit least(greatest(coalesce(p_limit, 300), 1), 1000)
$$;
revoke all on function public.flights_track_todo(int) from public, anon, authenticated;
grant execute on function public.flights_track_todo(int) to service_role;

-- RLS：flights の決まりは変えない（本人だけ読める "own flights"。利用者の書き込み権限なし）。新しい列もこの決まりのまま
alter table public.flights enable row level security;
revoke insert, update, delete on public.flights from anon, authenticated;

-- 今までのフライトにもさかのぼって入れる（入れられる分だけ。毎日の記録は400日・時刻表は14日）。
-- 時間がかかりすぎたら止めて移行は通す（残りは毎晩の照合の分と、次の手での呼び出しで入る）
do $$
declare r jsonb;
begin
  r := public.flights_fill_actual(400, 20000);
  raise notice 'flights_fill_actual backfill %', r;
exception when query_canceled then
  raise notice 'flights_fill_actual backfill stopped (timeout)';
end $$;
