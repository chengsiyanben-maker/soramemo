-- 記録帳の便名と、日付＋便名から便を引く関数（PM の指示 11/26 1時30分。チェックイン担当 checkin/flight-suggest #239 の依頼）
--   1. manual_flights.flight_no：記録帳（手入力の過去の便）に便名を持てるようにする（text・任意）。
--      形は毎日の記録 flight_history・国際線の記録 intl_flights と同じ（英数字2文字＋数字1〜4けた＋英字1文字まで。例 JL123・NH1234・JL123A）。
--      RLS は今のまま（本人の行だけ読める・足せる・消せる・直せる）。本人は足すときに入れられ、あとから直すこともできる（fare・seat・airline・price と同じ扱い）
--      印・路線・経営の数には今までどおり入らない（記録帳の行を数えない決まりは変えない）。退会では今までどおり行ごと消える
--   2. flight_lookup(p_date, p_flight)：日付と便名から、出発・到着・時刻・機体を返す読むだけの関数。
--      取り先は毎日の記録 flight_history（約400日。それより前はファイル置き場に移っているので出ない）。
--      flight_history にまだない日（今日・前の日の分）は時刻表 flight_schedule（14日）から返す（src で見分ける）。
--      便名は flight_facts と同じく前の 0 をそろえて比べ（JL0123 ＝ JL123）、共同運航の便名（also）でも見つける。
--      同じ便名で区間が2つ以上ある日（経由便など）は、定刻の順に全部返す（最大6）。
--      権限は flight_facts（flight_history を読む今の関数）と同じ：anon・authenticated が呼べる。表そのものは今までどおり読めない。
--      返すのは航空会社の公開の運航の事実（時刻・機種・登録記号）だけで、利用者の記録は返さない
--   影響：チェックイン（記録帳で便名を残す・過去の便を正しく補う）。経営は関係しない（記録帳は経営の路線に入らない）
--   航路と機体の記録は消さない（列と関数を足すだけ）
set lock_timeout = '5s';

-- 1. 記録帳の便名
alter table public.manual_flights add column if not exists flight_no text;
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'manual_flights_flight_no_format' and conrelid = 'public.manual_flights'::regclass) then
    alter table public.manual_flights add constraint manual_flights_flight_no_format
      check (flight_no is null or flight_no ~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$');
  end if;
end $$;
comment on column public.manual_flights.flight_no is '便名（任意）。例 JL123。形は flight_history と同じ';

-- RLS と権限（前と同じ形をもう一度はっきり書く。本人の行だけ。直せる列に flight_no を足す）
alter table public.manual_flights enable row level security;
revoke update on public.manual_flights from anon, authenticated;
grant update (fare, seat, airline, price, flight_no) on public.manual_flights to authenticated;

-- 2. 日付＋便名から便を引く
create or replace function public.flight_lookup(p_date date, p_flight text) returns jsonb
language sql stable security definer set search_path = public as $$
  with q as (
    select p_date as d, public.flight_no_norm(upper(btrim(p_flight))) as fn
    where p_date is not null and upper(btrim(coalesce(p_flight, ''))) ~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$'
  ),
  h as (
    -- 毎日の記録（その日の行だけを主キーの先頭 svc_date で読む）
    select h.flight, h.dep, h.arr, h.std, h.sta, h.atd, h.ata, h.atd_src, h.ata_src, h.dep_delay, h.arr_delay, h.cancelled, h.diverted_to,
           h.aircraft, h.type, h.reg, h.also, 'history'::text as src
    from q join public.flight_history h on h.svc_date = q.d
    where public.flight_no_norm(h.flight) = q.fn or exists (select 1 from unnest(h.also) o where public.flight_no_norm(o) = q.fn)
  ),
  s as (
    -- 毎日の記録にまだない日だけ、時刻表から（ODPT の実際の時刻があればそれも）
    select f.flight, f.dep, f.arr, f.std, f.sta, f.atd, f.ata,
           case when f.atd is not null then 'odpt' end as atd_src, case when f.ata is not null then 'odpt' end as ata_src,
           null::smallint as dep_delay, null::smallint as arr_delay,
           coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) as cancelled, null::text as diverted_to,
           f.aircraft, null::text as type, null::text as reg, '{}'::text[] as also, 'schedule'::text as src
    -- その運航日の行だけを一意の索引 (svc_date, flight, dep) の先頭で読む
    from q join public.flight_schedule f on f.svc_date = q.d and public.flight_no_norm(f.flight) = q.fn
    where not exists (select 1 from h)
  ),
  r as (select * from h union all select * from s order by std limit 6)
  select jsonb_build_object('date', (select d from q), 'flight', (select fn from q),
    'rows', coalesce((select jsonb_agg(jsonb_build_object('flight', r.flight, 'dep', r.dep, 'arr', r.arr, 'std', r.std, 'sta', r.sta,
        'atd', r.atd, 'ata', r.ata, 'atd_src', r.atd_src, 'ata_src', r.ata_src, 'dep_delay', r.dep_delay, 'arr_delay', r.arr_delay,
        'cancelled', r.cancelled, 'diverted_to', r.diverted_to, 'aircraft', r.aircraft, 'type', r.type, 'reg', r.reg, 'also', to_jsonb(r.also), 'src', r.src)
        order by r.std) from r), '[]'::jsonb))
$$;
revoke all on function public.flight_lookup(date, text) from public;
grant execute on function public.flight_lookup(date, text) to anon, authenticated;

reset lock_timeout;
