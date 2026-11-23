-- 定期の手入れ 11/23（データ担当）：関数の中の「表を全部読む文」を、索引で引ける形にする
--   模擬のデータベース（main の移行を全部流したもの）で、関数の where に出る列と索引の先頭の列を突き合わせて洗い出した。
--   1. airport_day（空港ページの「あの日の空」）：rwy_samples・ga_events を「(at の日本時間)::date = 日」で絞っていたので、
--      (iata, at) の索引の at が使えず、その空港の400日分の行を毎回全部読んでいた。同じ意味の時刻の幅（その日の0時〜次の日の0時）に直す。
--      返す値は変わらない（timestamptz の日本時間の日付が p_day ⇔ p_day 0時(日本) ≦ at < p_day+1 0時(日本)）。
--   2. flights の「航跡のまだない便」を出発の時刻で引く部分索引：毎晩の daily-archive が呼ぶ flights_track_todo と archive_user_flights が、
--      dep_at の索引がなく flights を全部読んでいた。track が入れば索引から外れるので、索引は小さいまま。
--   3. rot_predict（運用予想。毎晩の採点で数千回呼ばれる）：livery_plans を「(std の日本時間)::date = 日」で絞っていたのを、
--      1 と同じ時刻の幅に直す（std の索引が使える）。関数の本文はこの1か所だけを置き換え、ほかは一字も変えない（置き換えた数が1でなければ止まる）。
--   表・列・RLS・権限は変えない。記録は消さない。チェックイン（空港ページの値・便の航跡）・運用予想の値は変わらず、速くなるだけ。経営は関係しない。
set lock_timeout = '5s';

-- 1. airport_day
create or replace function public.airport_day(p_iata text, p_day date) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('iata', p_iata, 'day', p_day,
    'daily', (select jsonb_build_object('flights', flights, 'arr', arr, 'dep', dep, 'late', late, 'cancelled', cancelled, 'modes', modes, 'max_wind', max_wind)
              from public.airport_daily where iata = p_iata and day = p_day),
    'rwy', coalesce((select jsonb_object_agg(dir || ':' || rwy, n) from (
              select dir, rwy, count(*) as n from public.rwy_samples
              where iata = p_iata and (src = 'live' or iata not in ('HND', 'NRT'))
                and at >= (p_day::timestamp at time zone 'Asia/Tokyo') and at < ((p_day + 1)::timestamp at time zone 'Asia/Tokyo')
              group by 1, 2) r), '{}'::jsonb),
    'ga', (select count(*) from public.ga_events where iata = p_iata
              and at >= (p_day::timestamp at time zone 'Asia/Tokyo') and at < ((p_day + 1)::timestamp at time zone 'Asia/Tokyo')))
$$;
revoke all on function public.airport_day(text, date) from public;
grant execute on function public.airport_day(text, date) to anon, authenticated;

-- 2. 航跡のまだない便の部分索引
create index if not exists flights_track_todo_dep on public.flights (dep_at desc)
  where track is null and flight_no is not null;

-- 3. rot_predict の livery_plans の日付
do $do$
declare
  v_old constant text := $s$(lp.std at time zone 'Asia/Tokyo')::date = p_day$s$;
  v_new constant text := $s$lp.std >= (p_day::timestamp at time zone 'Asia/Tokyo') and lp.std < ((p_day + 1)::timestamp at time zone 'Asia/Tokyo')$s$;
  v_def text; v_n int;
begin
  select pg_get_functiondef('public.rot_predict(text, text, date, text, text, time, int)'::regprocedure) into v_def;
  v_n := (length(v_def) - length(replace(v_def, v_old, ''))) / length(v_old);
  if v_n = 0 and strpos(v_def, v_new) > 0 then
    return; -- もう直してある
  end if;
  if v_n <> 1 then
    raise exception 'rot_predict の置き換える所が % か所（1か所のはず）', v_n;
  end if;
  execute replace(v_def, v_old, v_new);
end
$do$;

reset lock_timeout;
