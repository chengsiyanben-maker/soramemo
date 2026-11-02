-- エアライン経営 co-v3：空港ごとの運用時間（利用時間）で、スケジュールとおまかせの便数をしぼる（11/02 企画者「各空港の時間制限を守って」）
--   出どころ：国土交通省「空港一覧」の各空港の空港概況（令和8年9月1日現在）の「運用時間（利用時間）」。かっこの中の利用時間を使う
--             （福岡は運用24時間・利用7時〜22時なので 7時〜22時）。会社管理の4空港（成田・中部・関西・伊丹）は一覧に載らないので、
--             航空路誌（AIP JAPAN 2026年10月1日版 AD 2.3。アプリの運用の画面と同じ）
--   ・喜界・沖永良部・与論は 10/1〜3/31 は 17:30 まで（winter_close_min）。礼文は供用休止中（closed）
--   ・それまでの「羽田・関西は24時間、成田6〜24時、伊丹7〜21時、福岡7〜22時、ほかは8〜20時」の決め打ちをやめる
--   ・自分で組む便：出る空港が開いているあいだに出て、着く空港が開いているあいだに着く（両方を確かめる）
--   ・おまかせの便数：両方の空港が開いている時間で、往復できる数まで（24時間どうしは今までどおり）
--   表：co3_ap_hours（だれでも読める・アプリからは書けない。直すのは運営だけ）

create table if not exists public.co3_ap_hours (
  iata text primary key check (iata ~ '^[A-Z]{3}$'),
  open_min integer not null check (open_min between 0 and 1440),
  close_min integer not null check (close_min between 0 and 1440),
  winter_close_min integer check (winter_close_min between 0 and 1440),   -- 10/1〜3/31 の終わり（ある空港だけ）
  closed boolean not null default false,                                   -- 供用休止中など
  note text,
  source text,
  updated_at timestamptz not null default now()
);
alter table public.co3_ap_hours enable row level security;
revoke all on public.co3_ap_hours from public, anon, authenticated;
grant select on public.co3_ap_hours to anon, authenticated;
drop policy if exists co3_ap_hours_read on public.co3_ap_hours;
create policy co3_ap_hours_read on public.co3_ap_hours for select to anon, authenticated using (true);

insert into public.co3_ap_hours (iata, open_min, close_min, winter_close_min, closed, note, source) values
  ('AGJ', 480, 1080, null, false, '10時間（8:00～18:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('AKJ', 480, 1260, null, false, '13時間（8:00～21:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('AOJ', 450, 1320, null, false, '14.5時間（7:30～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('ASJ', 480, 1170, null, false, '11.5時間（8:00～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('AXJ', 460, 1230, null, false, '12時間50分（7:40～20:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('AXT', 420, 1320, null, false, '15時間（7:00～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('CTS', 0, 1440, null, false, '24時間', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('FKJ', 540, 1020, null, false, '8時間 （9:00～17:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('FKS', 480, 1260, null, false, '13時間（8:00～21:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('FSZ', 450, 1320, null, false, '14.5時間（7:30～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('FUJ', 480, 1170, null, false, '11.5時間（8:00～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('FUK', 420, 1320, null, false, '24時間（7:00～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('GAJ', 480, 1200, null, false, '12時間（8:00～20:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('HAC', 480, 1080, null, false, '10時間（8:00～18:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('HIJ', 450, 1350, null, false, '15時間（7:30～22:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('HKD', 450, 1230, null, false, '13時間（7:30～20:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('HNA', 480, 1170, null, false, '11.5時間（8:00～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('HND', 0, 1440, null, false, '24時間', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('HSG', 390, 1440, null, false, '17.5時間 （6:30～24:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('HTR', 480, 1080, null, false, '10時間（8:00～18:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('IBR', 450, 1260, null, false, '13.5時間（7:30～21:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('IEJ', 735, 1005, null, false, '土曜日 4.5時間（12:15～16:45）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('IKI', 480, 1140, null, false, '11時間（8:00～19:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('ISG', 480, 1260, null, false, '13時間（8:00～21:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('ITM', 420, 1260, null, false, '7:00～21:00（AIP JAPAN AD 2.3）', 'AIP JAPAN（2026年10月1日版）'),
  ('IWJ', 480, 1170, null, false, '11.5時間（8:00～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('IWK', 450, 1350, null, false, '15時間（7:30～22:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('IZO', 450, 1230, null, false, '13時間（7:30～20:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KCZ', 420, 1260, null, false, '14時間（7:00～21:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KIJ', 450, 1290, null, false, '14時間（7:30～21:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KIX', 0, 1440, null, false, '24時間（AIP JAPAN AD 2.3）', 'AIP JAPAN（2026年10月1日版）'),
  ('KJP', 540, 1020, null, false, '8時間（9:00～17:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KKJ', 0, 1440, null, false, '24時間', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KKX', 510, 1110, 1050, false, '4/1～9/30 10時間（8:30～18:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KMI', 450, 1290, null, false, '14時間（7:30～21:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KMJ', 450, 1290, null, false, '14時間（7:30～21:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KMQ', 450, 1350, null, false, '15時間（7:30～22:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KOJ', 420, 1320, null, false, '15時間 （7:00～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KTD', 480, 1080, null, false, '10時間（8:00～18:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KUH', 480, 1260, null, false, '13時間（8:00～21:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('KUM', 510, 1170, null, false, '11時間（8:30～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('MBE', 540, 1020, null, false, '8時間（9:00～17:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('MMB', 480, 1260, null, false, '13時間（8:00～21:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('MMD', 480, 1080, null, false, '10時間（8:00～18:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('MMJ', 510, 1140, null, false, '10.5時間 （8:30～19:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('MMY', 480, 1260, null, false, '13時間（8:00～21:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('MSJ', 510, 1200, null, false, '11.5時間（8:30～20:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('MYE', 540, 1020, null, false, '8時間（9:00～17:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('MYJ', 420, 1320, null, false, '15時間（7:00～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('NGO', 0, 1440, null, false, '24時間（AIP JAPAN AD 2.3）', 'AIP JAPAN（2026年10月1日版）'),
  ('NGS', 420, 1320, null, false, '15時間（7:00～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('NKM', 420, 1320, null, false, '15時間（7:00～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('NRT', 360, 1440, null, false, '6:00～24:00（AIP JAPAN AD 2.3）', 'AIP JAPAN（2026年10月1日版）'),
  ('NTQ', 480, 1170, null, false, '11.5時間 （8:00～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('OBO', 480, 1260, null, false, '13時間（8:00～21:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('OGN', 480, 1170, null, false, '11.5時間（8:00～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('OIM', 510, 990, null, false, '8時間（8:30～16:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('OIR', 540, 1020, null, false, '8時間（9:00～17:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('OIT', 450, 1350, null, false, '15時間（7:30～22:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('OKA', 0, 1440, null, false, '24時間', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('OKD', 450, 1230, null, false, '13時間 (7:30～20:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('OKE', 510, 1110, 1050, false, '4/1～9/30 10時間（8:30～18:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('OKI', 540, 1020, null, false, '8時間（9:00～17:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('OKJ', 420, 1320, null, false, '15時間（7:00～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('ONJ', 480, 1170, null, false, '11.5時間（8:00～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('RBJ', 0, 0, null, true, '供用休止中', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('RIS', 540, 1020, null, false, '8時間（9:00～17:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('RNJ', 510, 1110, 1050, false, '4/1～9/30 10時間（8:30～18:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('SDJ', 450, 1320, null, false, '14.5時間（7:30～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('SDS', 525, 1035, null, false, '8.5時間（8:45～17:15）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('SHB', 510, 1110, null, false, '10時間 （8:30～18:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('SHI', 480, 1170, null, false, '11.5時間（8:00～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('SHM', 510, 1200, null, false, '11.5時間 （8:30～20:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('SYO', 420, 1320, null, false, '15時間（7:00～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('TAK', 420, 1320, null, false, '15時間（7:00～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('TJH', 510, 1110, null, false, '10時間（8:30～18:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('TKN', 510, 1170, null, false, '11時間（8:30～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('TKS', 420, 1290, null, false, '14.5時間（7:00～21:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('TNE', 510, 1110, null, false, '10時間（8:30～18:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('TOY', 420, 1290, null, false, '14.5時間 （7:00～21:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('TRA', 480, 1080, null, false, '10時間（8:00～18:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('TSJ', 450, 1260, null, false, '13.5時間（7:30～21:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('TTJ', 420, 1290, null, false, '14.5時間 （7:00～21:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('UBJ', 450, 1290, null, false, '14時間（7:30～21:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('UEO', 480, 1170, null, false, '11.5時間（8:00～19:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('UKB', 420, 1380, null, false, '16時間 （7:00～23:00）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('WKJ', 510, 1110, null, false, '10時間（8:30～18:30）', '国土交通省 空港一覧（令和8年9月1日現在）'),
  ('YGJ', 420, 1320, null, false, '15時間 (7:00～22:00）', '国土交通省 空港一覧（令和8年9月1日現在）')
on conflict (iata) do update set open_min = excluded.open_min, close_min = excluded.close_min, winter_close_min = excluded.winter_close_min,
  closed = excluded.closed, note = excluded.note, source = excluded.source, updated_at = now();

-- 運営：運用時間を直す
create or replace function public.admin_co3_ap_hours(p_iata text, p_open integer, p_close integer, p_closed boolean default false, p_note text default null) returns integer
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  insert into co3_ap_hours (iata, open_min, close_min, closed, note, source) values (upper(p_iata), p_open, p_close, coalesce(p_closed, false), p_note, '運営')
    on conflict (iata) do update set open_min = excluded.open_min, close_min = excluded.close_min, closed = excluded.closed, note = excluded.note, source = excluded.source, updated_at = now();
  return 1;
end;
$$;
revoke all on function public.admin_co3_ap_hours(text, integer, integer, boolean, text) from public, anon;
grant execute on function public.admin_co3_ap_hours(text, integer, integer, boolean, text) to authenticated;

-- 開く・閉まる（日本時間の分）。表にない空港（海外）は24時間。休止中は 0〜0
create or replace function co3.ap_open(p_iata text) returns integer
language sql stable set search_path = public as $$
  select coalesce((select case when h.closed then 0 else h.open_min end from co3_ap_hours h where h.iata = p_iata), 0)
$$;
create or replace function co3.ap_close(p_iata text) returns integer
language sql stable set search_path = public as $$
  select coalesce((select case when h.closed then 0
                               when h.winter_close_min is not null and extract(month from co3.today()) not between 4 and 9 then h.winter_close_min
                               else h.close_min end from co3_ap_hours h where h.iata = p_iata), 1440)
$$;
revoke all on function co3.ap_open(text), co3.ap_close(text) from public, anon, authenticated;

-- 両方の空港が開いている時間で、おまかせの機体が飛べる1日の便（往復の数×2）。どちらも24時間なら 99（しぼらない）
create or replace function co3.hours_legs(p_a text, p_b text, p_km numeric, p_type text, p_policy text) returns integer
language sql stable set search_path = public as $$
  with w as (select greatest(co3.ap_open(p_a), co3.ap_open(p_b)) as o, least(co3.ap_close(p_a), co3.ap_close(p_b)) as c,
                    co3.sched_block(coalesce(p_km, 800), coalesce(p_type, 'nb')) as blk, co3.turn_min(coalesce(p_type, 'nb'), p_policy) as tn)
  select case when w.c - w.o >= 1440 then 99
              when w.c - w.o < w.blk then 0
              else (floor((w.c - w.o + w.tn)::numeric / (w.blk + w.tn))::int / 2) * 2 end
    from w
$$;
revoke all on function co3.hours_legs(text, text, numeric, text, text) from public, anon, authenticated;

-- 路線の両端（route_key は「空港の番号-空港の番号」か「IATA-IATA」）
create or replace function co3.route_ends(p_route text, out a text, out b text)
language sql stable set search_path = public as $$
  select case when p_route ~ '^[0-9]+-[0-9]+$' then (select x.iata from airports x where x.id = split_part(p_route, '-', 1)::int) else split_part(p_route, '-', 1) end,
         case when p_route ~ '^[0-9]+-[0-9]+$' then (select x.iata from airports x where x.id = split_part(p_route, '-', 2)::int) else split_part(p_route, '-', 2) end
$$;
revoke all on function co3.route_ends(text) from public, anon, authenticated;

-- おまかせの便数：今までの数（決めた便数・距離で決まる数）と、運用時間で飛べる数の少ないほう
create or replace function public.co3_auto_fl(p_uid uuid, p_route text, p_km numeric, p_policy text) returns integer
language sql stable security definer set search_path = public as $$
  select case when a.id is null or co3_is_freighter(a.id) or co3_is_bizjet(a.id) or p_policy in ('cargo', 'pj') then 0
              else least(coalesce((select p.flights from co3_plans p where p.user_id = p_uid and p.route_key = p_route), 99), co3.legs_per_day(p_km),
                         co3.hours_legs(e.a, e.b, p_km, (select x.type from aircraft x where x.id = a.id), p_policy)) end
    from (select co3_assigned_ac(p_uid, p_route) as id) a, co3.route_ends(p_route) e
$$;
revoke all on function public.co3_auto_fl(uuid, text, numeric, text) from public, anon, authenticated;

-- 自分で組むスケジュール：出る空港・着く空港の両方の運用時間を確かめる（ほかは今までどおり）
create or replace function public.co3_set_schedule(p_aircraft bigint, p_legs jsonb) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); ac aircraft; pol text; n int; i int; l jsonb; prev_arr text; prev_t int; r record;
        v_dep text; v_arr text; t int; blk int; first_dep text; turn int; ms int;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 2 then raise exception 'rating required 2'; end if;
  select * into ac from aircraft where id = p_aircraft and user_id = uid;
  if not found then raise exception 'aircraft not found'; end if;
  select policy into pol from companies where user_id = uid;
  if pol in ('cargo', 'pj') or co3_is_freighter(ac.id) or co3_is_bizjet(ac.id) then raise exception 'not a passenger aircraft'; end if;
  n := coalesce(jsonb_array_length(p_legs), 0);
  if n < 1 or n > 16 then raise exception 'legs 1 to 16'; end if;
  turn := co3.turn_min(ac.type, pol);
  ms := (ac_spec(ac.type)).min_size;
  delete from co3_sched where aircraft_id = ac.id;
  for i in 0..n - 1 loop
    l := p_legs->i; v_dep := upper(l->>'dep'); v_arr := upper(l->>'arr'); t := (l->>'t')::int;
    select * into r from co_routes(uid) x where (x.a = v_dep and x.b = v_arr) or (x.a = v_arr and x.b = v_dep) limit 1;
    if not found then raise exception 'route not found %-%', v_dep, v_arr; end if;
    if r.min_size < ms then raise exception 'airport too small %-%', v_dep, v_arr; end if;
    if r.intl and not ac.intl then raise exception 'not intl'; end if;
    blk := co3.sched_block(r.km, ac.type);
    if i = 0 then first_dep := v_dep; end if;
    if i > 0 and v_dep <> prev_arr then raise exception 'not connected at %', i + 1; end if;
    if i > 0 and t < prev_t + turn then raise exception 'turn too short at %', i + 1; end if;
    if t < 0 or t < co3.ap_open(v_dep) or t >= co3.ap_close(v_dep)
       or t + blk < co3.ap_open(v_arr) or t + blk > co3.ap_close(v_arr) or t + blk > 1440 then raise exception 'outside hours at %', i + 1; end if;
    insert into co3_sched (user_id, aircraft_id, seq, route_key, dep, arr, dep_min, arr_min) values (uid, ac.id, i + 1, r.route_key, v_dep, v_arr, t, t + blk);
    prev_arr := v_arr; prev_t := t + blk;
  end loop;
  if prev_arr <> first_dep then raise exception 'must end at %', first_dep; end if;
  update aircraft set route_key = null where id = ac.id;    -- おまかせの路線からは外す
  return co_state();
end;
$$;
revoke all on function public.co3_set_schedule(bigint, jsonb) from public, anon;
grant execute on function public.co3_set_schedule(bigint, jsonb) to authenticated;
