-- 乗る便の機体（inbound_aircraft）：前の便が見つからないとき、その機体が前の日の夜に着いて泊まった
-- 「この日の最初の便」と分かるなら first_of_day: true を返す（11/19 チェックイン担当の依頼・PR #128 で画面は受ける作りになっている）
--   決め方（どちらか）
--   1. 今日の登録記号が分かっている（flight_watch の reg）：その機体の前の日の最後の便（flight_history）がこの便の出発空港に着いていて、
--      今日この便より前に同じ機体の便（flight_schedule × flight_watch）がない → first_src 'reg'。泊まった便を overnight に返す
--   2. 前の60日の記録（flight_history の同じ便名・同じ出発空港・登録記号つき・欠航でない日、新しい30日まで）で、
--      「その日の機体の最初の便で、前の日の最後の便がこの空港に着いていた」日が3日以上かつ7割以上 → first_src 'history'
--   どちらでもなければ false（分からないときは今までどおりの1行が出る）。前の便が見つかったときは false
--   返すのに足すのは first_of_day・first_src・first_stay・first_of・overnight だけ。今までの値と形は変えない
-- 引き方：flight_history は主キー (svc_date, flight, dep) を 60 個の日付で直接引く（便名の索引を足さない）。
--         機体ごとは flight_history_reg (reg, svc_date) で引く。1回の呼び出しで最大 30 日 × 2 回の索引の引き
-- 表・列・RLS・権限は変えない（関数の中身だけ。anon・authenticated は実行だけのまま）
-- 影響：チェックイン（乗る便のカードの「朝一番の便です」の1行が出るようになる）。経営は使っていない
create or replace function public.inbound_aircraft(p_flight text, p_dep text) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare
  today date := (now() at time zone 'Asia/Tokyo')::date;
  s record; p record; w jsonb; pw jsonb; turn int; arr_at timestamptz; arr_src text; ready timestamptz;
  v_reg text; y record; f_first boolean := false; f_src text; f_stay int := 0; f_of int := 0; f_night jsonb;
begin
  if p_flight is null or p_flight !~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$' or (p_dep is not null and p_dep !~ '^[A-Z]{3}$') then return null; end if;
  select f.*, fw.state as st into s
  from public.flight_schedule f left join public.flight_watch fw on fw.schedule_id = f.id
  where f.svc_date in (today, today + 1) and (p_dep is null or f.dep = p_dep) and public.flight_no_norm(f.flight) = public.flight_no_norm(p_flight)
    and f.std > now() - interval '3 hours'
  order by f.std limit 1;
  if s is null then return jsonb_build_object('flight', p_flight, 'found', false); end if;
  w := coalesce(s.st, '{}'::jsonb);

  -- 前の便の候補（前の60日の記録で多いもの）
  select q.flight, q.dep, q.arr, q.std, q.sta, q.atd, q.eta, q.ata, q.aircraft, q.cancelled, q.st, q.score, q.total into p
  from (
    select f.flight, f.dep, f.arr, f.std, f.sta, f.atd, f.eta, f.ata, f.aircraft, fw.state as st,
           coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) as cancelled,
           sum(case when extract(dow from o.svc_date) = extract(dow from s.svc_date) then 2 else 1 end) as score,
           (select sum(case when extract(dow from o2.svc_date) = extract(dow from s.svc_date) then 2 else 1 end)
              from public.rotation_obs o2 where o2.next_flight = s.flight and o2.svc_date >= today - 60) as total
    from public.rotation_obs o
    join public.flight_schedule f on f.flight = o.prev_flight and f.svc_date = s.svc_date and f.arr = s.dep
    left join public.flight_watch fw on fw.schedule_id = f.id
    where o.next_flight = s.flight and o.svc_date >= today - 60
      and f.sta between s.std - interval '6 hours' and s.std - interval '15 minutes'
    group by f.flight, f.dep, f.arr, f.std, f.sta, f.atd, f.eta, f.ata, f.aircraft, fw.state, f.dep_status, f.arr_status
    order by score desc, f.sta desc limit 1
  ) q;

  if p is null then
    -- 1. 今日の登録記号から（前の日の最後の便がここに着いて、今日この便より前に同じ機体の便がない）
    v_reg := nullif(w ->> 'reg', '');
    if v_reg is not null and v_reg ~ '^[A-Z0-9-]{2,10}$' then
      select h.flight, h.dep, h.arr, coalesce(h.ata, h.sta) as arr_at, h.ata is not null as actual into y
      from public.flight_history h
      where h.reg = v_reg and h.svc_date = s.svc_date - 1 and not h.cancelled
      order by h.std desc limit 1;
      if y.arr = s.dep and not exists (
        select 1 from public.flight_schedule f2 join public.flight_watch fw2 on fw2.schedule_id = f2.id
        where f2.svc_date = s.svc_date and f2.std < s.std and f2.id <> s.id and fw2.state ->> 'reg' = v_reg
          and not coalesce(f2.dep_status ~* 'cancel', false)) then
        f_first := true; f_src := 'reg';
        f_night := jsonb_build_object('flight', y.flight, 'dep', y.dep, 'arr', y.arr, 'arr_at', y.arr_at,
          'arr_src', case when y.actual then 'actual' else 'sched' end, 'reg', v_reg);
      end if;
    end if;
    -- 2. 前の60日の記録から
    if not f_first then
      select count(*)::int, count(*) filter (where d.first and d.stay)::int into f_of, f_stay
      from (
        select not exists (select 1 from public.flight_history e
                           where e.reg = h.reg and e.svc_date = h.svc_date and e.std < h.std and not e.cancelled) as first,
               (select l.arr from public.flight_history l
                 where l.reg = h.reg and l.svc_date = h.svc_date - 1 and not l.cancelled
                 order by l.std desc limit 1) = h.dep as stay
        from public.flight_history h
        where h.svc_date = any (array(select (today - g)::date from generate_series(1, 60) g))
          and h.flight = s.flight and h.dep = s.dep and h.reg is not null and not h.cancelled
        order by h.svc_date desc limit 30
      ) d;
      if f_of >= 3 and f_stay * 10 >= f_of * 7 then f_first := true; f_src := 'history'; end if;
    end if;
    return jsonb_build_object('flight', s.flight, 'found', true, 'dep', s.dep, 'arr', s.arr, 'std', s.std, 'etd', s.etd, 'atd', s.atd,
      'reg', w ->> 'reg', 'phase', w ->> 'phase', 'inbound', null,
      'first_of_day', f_first, 'first_src', f_src, 'first_stay', f_stay, 'first_of', f_of, 'overnight', f_night);
  end if;
  pw := coalesce(p.st, '{}'::jsonb);
  turn := case when coalesce(p.aircraft, s.aircraft, '') ~* '^(7[6-8]|77|78|35|B7[678]|A35|A33)' then 45 else 35 end;
  if p.ata is not null then arr_at := p.ata; arr_src := 'actual';
  elsif p.eta is not null then arr_at := p.eta; arr_src := 'est';
  elsif pw ->> 'landed_iata' = p.arr and public.inferred_time(pw, 'landed_at') is not null then arr_at := public.inferred_time(pw, 'landed_at'); arr_src := 'landed';
  elsif pw ->> 'phase' = 'air' and public.inferred_time(pw, 'eta') is not null then arr_at := public.inferred_time(pw, 'eta'); arr_src := 'predicted';
  else arr_at := p.sta; arr_src := 'sched';
  end if;
  ready := greatest(s.std, arr_at + make_interval(mins => turn));
  return jsonb_build_object('flight', s.flight, 'found', true, 'dep', s.dep, 'arr', s.arr, 'std', s.std, 'etd', s.etd, 'atd', s.atd,
    'reg', coalesce(w ->> 'reg', pw ->> 'reg'), 'phase', w ->> 'phase',
    'inbound', jsonb_build_object('flight', p.flight, 'dep', p.dep, 'arr', p.arr, 'std', p.std, 'sta', p.sta, 'atd', p.atd, 'eta', p.eta, 'ata', p.ata,
      'cancelled', p.cancelled, 'phase', pw ->> 'phase', 'reg', pw ->> 'reg', 'type', pw ->> 'type',
      'takeoff', case when coalesce((pw ->> 'takeoff_est')::boolean, true) = false then public.inferred_time(pw, 'takeoff_at') end,
      'pos', case when pw ->> 'phase' = 'air' and pw -> 'last' is not null then jsonb_build_object('lat', pw -> 'last' -> 'lat', 'lon', pw -> 'last' -> 'lon', 'alt', pw -> 'last' -> 'alt_ft',
               'at', public.inferred_time(pw -> 'last', 'at')) end,
      'share', round(p.score::numeric / greatest(p.total, 1), 2), 'seen', p.score),
    'arr_at', arr_at, 'arr_src', arr_src, 'turn', turn, 'ready', ready,
    'late', greatest(0, round(extract(epoch from (ready - s.std)) / 60)),
    'first_of_day', false);
end
$$;
revoke all on function public.inbound_aircraft(text, text) from public;
grant execute on function public.inbound_aircraft(text, text) to anon, authenticated;
