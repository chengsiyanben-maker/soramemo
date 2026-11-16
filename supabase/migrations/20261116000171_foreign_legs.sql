-- 海外の航空会社の便の実績を自分で集める（データ担当・11/16）
--   【11/16 本人】海外の会社に加えて、ODPT にない日本の会社（スカイマーク・ピーチ・ジェットスター・ジャパン・ZIPAIR・春秋航空日本など）も集める。
--   ODPT には JAL・ANA の便しかなく、羽田国際線（TIAT）の発着はチャレンジ限定ライセンスで本番に使えない（report-foreign-carriers）。
--   そこで、すでに集めている全機の記録（adsb.lol の機体の位置から毎晩作る airport_tracks_all と reg_legs）から、
--   日本の空港を出た・着いた海外の会社の便を1回ずつ取り出して残す。外への問い合わせは増えない（adsb.lol・adsb.im とも0回）。
--   1. airline_codes：呼び出し符号の記号 → 便名の記号（KAL → KE）。Edge Functions の flight_watch.ts の PREFIX と同じ中身（＋日本貨物航空 NCA）。誰でも読める
--   2. foreign_legs：海外の会社の便の実績。1行＝その便が日本の空港を出た（dep_here=1）か着いた（0）1回。時刻 at は位置からの推定
--      （離陸は 15,000ft 未満の航跡の最初の点、着陸は最後の点。1分ごとの点なので数分ずれる）。登録記号・機種は reg_legs から。
--      相手の空港は、両方とも日本の空港のときだけ分かる（海外の空港は記録の円の外）。event：引き返し（return）・ダイバート（divert）。
--      航路と機体の記録なので消さない（毎晩、今日と前の日の分だけを作り直す。元の airport_tracks_all は400日のあいだ表に残る）
--   3. foreign_usual：いつもの時刻。前の8週の実績から、便・空港・出発／到着・曜日ごと（dow=-1 は曜日を問わない）の時刻の中央値。
--      曜日ごとは3回以上・曜日を問わないものは5回以上、ばらつき（四分位の幅）が60分以下のときだけ作る。毎晩作り直す（実績から作る値なので入れ替えてよい）
--   4. foreign_late(p_flight, p_day)：その日の実績と、いつもの時刻とのずれ（推定）。誰でも呼べる。いつもの時刻がない便はずれを出さない
--   読み書き：foreign_legs・foreign_usual は関数からだけ（RLS を有効にし、anon・authenticated には何も許さない）。作る関数は運営（service_role）だけ
--   影響：チェックイン（乗る便・運用の海外の便で「いつもより○分遅い（推定）」を出すときに foreign_late を使える。画面はまだ変えない）・
--         撮る人（海外の塗装機の記録に使える）。経営は使わない。退会で消すもの（本人の記録）は入っていない

-- 1
create table if not exists public.airline_codes (
  icao  text primary key check (icao ~ '^[A-Z]{3}$'),
  iata  text not null check (iata ~ '^[A-Z0-9]{2}$'),
  odpt  boolean not null default false     -- ODPT の運航情報・時刻表で見られる会社（JL・NH の便名で飛ぶ JAL・ANA グループ）。11/16 本人の決定で、
                                           -- ODPT にない日本の会社（スカイマーク・ピーチ・ジェットスター・ジャパン・春秋航空日本など）は海外の会社と同じく集める
);
alter table public.airline_codes enable row level security;
revoke all on public.airline_codes from public, anon, authenticated;
grant select on public.airline_codes to anon, authenticated;
drop policy if exists airline_codes_read on public.airline_codes;
create policy airline_codes_read on public.airline_codes for select to anon, authenticated using (true);
insert into public.airline_codes (icao, iata, odpt) values
  ('AAL','AA',false), ('AAR','OZ',false), ('ABL','BX',false), ('ACA','AC',false), ('ADO','HD',false), ('AFR','AF',false),
  ('AIC','AI',false), ('AJX','NH',true), ('AKX','NH',true), ('ALK','UL',false), ('ANA','NH',true), ('ANZ','NZ',false),
  ('APJ','MM',false), ('ASV','RS',false), ('AUA','OS',false), ('BAV','QH',false), ('BAW','BA',false), ('BKP','PG',false),
  ('CAL','CI',false), ('CCA','CA',false), ('CDG','SC',false), ('CEB','5J',false), ('CES','MU',false), ('CHH','HU',false),
  ('CPA','CX',false), ('CQH','9C',false), ('CRK','HX',false), ('CSH','FM',false), ('CSN','CZ',false), ('CXA','MF',false),
  ('DAL','DL',false), ('DKH','HO',false), ('DLH','LH',false), ('ESR','ZE',false), ('ETD','EY',false), ('ETH','ET',false),
  ('EVA','BR',false), ('FDA','JH',false), ('FIN','AY',false), ('GCR','GS',false), ('GIA','GA',false), ('HAC','JL',true),
  ('HAL','HA',false), ('HKE','UO',false), ('HVN','VN',false), ('IBX','FW',false), ('IGO','6E',false), ('JAC','3X',true),
  ('JAL','JL',true), ('JJA','7C',false), ('JJP','GK',false), ('JLJ','JL',true), ('JNA','LJ',false), ('JSA','3K',false),
  ('JST','JQ',false), ('JTA','NU',true), ('KAL','KE',false), ('KLM','KL',false), ('LKE','8L',false), ('MAS','MH',false),
  ('MGL','OM',false), ('NCA','KZ',false), ('OMA','WY',false), ('ORC','OC',false), ('PAL','PR',false), ('QFA','QF',false),
  ('QTR','QR',false), ('SAS','SK',false), ('SFJ','7G',false), ('SIA','SQ',false), ('SJO','IJ',false), ('SJX','JX',false),
  ('SKY','BC',false), ('SNJ','6J',false), ('SVA','SV',false), ('SWR','LX',false), ('TGW','TR',false), ('THA','TG',false),
  ('THY','TK',false), ('TTW','IT',false), ('TWB','TW',false), ('TZP','ZG',false), ('UAE','EK',false), ('UAL','UA',false),
  ('VJC','VJ',false), ('XAX','D7',false)
on conflict (icao) do update set iata = excluded.iata, odpt = excluded.odpt;

-- 2
create table if not exists public.foreign_legs (
  day       date not null,                                   -- 日本時間の日（出た・着いた時刻の日）
  callsign  text not null check (callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$'),
  iata      text not null check (iata ~ '^[A-Z]{3}$'),       -- 日本の空港
  dep_here  smallint not null check (dep_here in (0, 1)),    -- 1＝この空港を出た・0＝着いた
  at        timestamptz not null,                            -- 離陸・着陸の時刻（推定）
  flight    text check (flight ~ '^[A-Z0-9]{2}[0-9]{1,4}$'),  -- 便名（呼び出し符号から。表にない会社は null）
  airline   text check (airline ~ '^[A-Z0-9]{2}$'),
  reg       text check (reg ~ '^[A-Z0-9-]{2,10}$'),
  type      text check (length(type) <= 8),
  other     text check (other ~ '^[A-Z]{3}$'),               -- 相手の空港（日本の空港のときだけ）
  event     text check (event in ('return', 'divert')),
  built_at  timestamptz not null default now(),
  primary key (callsign, iata, dep_here, at)
);
-- 便名で引く索引は置かない（foreign_late は主キーの呼び出し符号から引く。大きさを抑える）
create index if not exists foreign_legs_day on public.foreign_legs (day);
alter table public.foreign_legs enable row level security;
revoke all on public.foreign_legs from public, anon, authenticated;

-- 3
create table if not exists public.foreign_usual (
  callsign  text not null check (callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$'),
  iata      text not null check (iata ~ '^[A-Z]{3}$'),
  dep_here  smallint not null check (dep_here in (0, 1)),
  dow       smallint not null check (dow between -1 and 6),  -- 0＝日曜 … 6＝土曜、-1＝曜日を問わない
  mins      smallint not null check (mins between 0 and 1439), -- 日本時間の時刻（0時からの分）
  n         smallint not null check (n > 0),
  spread    smallint not null check (spread between 0 and 60), -- 四分位の幅（分）
  last_day  date not null,
  built_at  timestamptz not null default now(),
  primary key (callsign, iata, dep_here, dow)
);
alter table public.foreign_usual enable row level security;
revoke all on public.foreign_usual from public, anon, authenticated;

-- 2 を作る（1日分。何度流しても同じになる）
create or replace function public.foreign_legs_build(p_day date) returns int
language plpgsql security definer set search_path = public set lock_timeout = '5s' as $$
declare v_n int;
begin
  if p_day is null then return 0; end if;
  with aps as (
    select array_agg(distinct iata) as a from public.airports where iata ~ '^[A-Z]{3}$'
  ), t as (
    select t.iata, t.day, t.callsign, t.at, t.dep_here
      from public.airport_tracks_all t, aps
     where t.iata = any(aps.a) and t.day = p_day          -- 主キー（iata, day, …）で引く
  ), ev as (
    select t.day, t.callsign, t.iata, t.dep_here, t.at, c.iata as airline,
           case when c.iata is not null then c.iata || substring(t.callsign from '^[A-Z]{3}0*([0-9]{1,4})') end as flight,
           r.reg, r.type
      from t
      left join public.airline_codes c on c.icao = left(t.callsign, 3)
      left join lateral (
        select l.reg, l.type from public.reg_legs l
         where l.callsign = t.callsign and l.day between p_day - 1 and p_day
           and l.first_at <= t.at + interval '40 minutes' and l.last_at >= t.at - interval '40 minutes'
         order by abs(extract(epoch from (l.last_at - t.at))) limit 1
      ) r on true
     -- ODPT で見られる会社（JAL・ANA グループ）は入れない。表にない会社は、日本の機体（JA）なら入れない（自家用・官庁など）
     where (c.icao is not null and not c.odpt) or (c.icao is null and coalesce(r.reg, '') !~ '^JA')
  ), del as (
    -- その日の作り直し：元（airport_tracks_all）の判定が変わって、もうない行だけ
    delete from public.foreign_legs f
     where f.day = p_day
       and not exists (select 1 from ev where ev.callsign = f.callsign and ev.iata = f.iata and ev.dep_here = f.dep_here and ev.at = f.at)
  ), ins as (
    insert into public.foreign_legs (day, callsign, iata, dep_here, at, flight, airline, reg, type, built_at)
    select day, callsign, iata, dep_here, at, flight, airline, reg, left(type, 8), now() from ev
    on conflict (callsign, iata, dep_here, at) do update
      set day = excluded.day, flight = excluded.flight, airline = excluded.airline,
          reg = coalesce(excluded.reg, foreign_legs.reg), type = coalesce(excluded.type, foreign_legs.type), built_at = now()
    returning 1
  ) select count(*)::int into v_n from ins;

  -- 相手の空港・引き返し・ダイバートは、作り直すたびに付け直す
  update public.foreign_legs set other = null, event = null where day = p_day and (other is not null or event is not null);
  -- 出た便：あとで日本の別の空港に着いた
  update public.foreign_legs d set other = a.iata
    from public.foreign_legs a
   where d.day = p_day and d.dep_here = 1 and a.callsign = d.callsign and a.dep_here = 0 and a.day between p_day and p_day + 1
     and a.at between d.at + interval '20 minutes' and d.at + interval '8 hours' and a.iata <> d.iata;
  -- 着いた便：日本の別の空港を出ていた。同じ空港を5時間以内に出ていれば引き返し
  update public.foreign_legs a set other = d.iata, event = case when d.iata = a.iata then 'return' end
    from public.foreign_legs d
   where a.day = p_day and a.dep_here = 0 and d.callsign = a.callsign and d.dep_here = 1 and d.day between p_day - 1 and p_day
     and ((d.iata <> a.iata and d.at between a.at - interval '8 hours' and a.at - interval '20 minutes')
       or (d.iata = a.iata and d.at between a.at - interval '5 hours' and a.at - interval '10 minutes'));
  -- ダイバート：前の8週でその便が着いたのが4回以上・8割以上が同じ空港なのに、一度も着いたことのない空港に着いた
  update public.foreign_legs a set event = 'divert'
    from (
      select h.callsign, h.iata, count(*) as k, sum(count(*)) over (partition by h.callsign) as total
        from public.foreign_legs h
       where h.dep_here = 0 and h.day between p_day - 56 and p_day - 1 and h.event is null
         and h.callsign in (select callsign from public.foreign_legs where day = p_day and dep_here = 0)
       group by h.callsign, h.iata
    ) u
   where a.day = p_day and a.dep_here = 0 and a.event is null and u.callsign = a.callsign and u.iata <> a.iata
     and u.total >= 4 and u.k >= 0.8 * u.total
     and not exists (select 1 from public.foreign_legs x where x.callsign = a.callsign and x.iata = a.iata and x.dep_here = 0
                       and x.day between p_day - 56 and p_day - 1);
  return v_n;
end $$;
revoke all on function public.foreign_legs_build(date) from public, anon, authenticated;

-- 3 を作る（全部入れ替え）
create or replace function public.foreign_usual_build() returns int
language plpgsql security definer set search_path = public set lock_timeout = '5s' as $$
declare today date := (now() at time zone 'Asia/Tokyo')::date; v_n int;
begin
  delete from public.foreign_usual where true;
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
  ), ins as (
    insert into public.foreign_usual (callsign, iata, dep_here, dow, mins, n, spread, last_day)
    select callsign, iata, dep_here, dow,
           (case when iqr_a <= iqr_b then round(med_a)::int else (round(med_b)::int + 720) % 1440 end) % 1440,
           n, round(least(iqr_a, iqr_b))::int, last_day
      from g
     where least(iqr_a, iqr_b) <= 60 and ((dow >= 0 and n >= 3) or (dow = -1 and n >= 5))
    returning 1
  ) select count(*)::int into v_n from ins;
  return v_n;
end $$;
revoke all on function public.foreign_usual_build() from public, anon, authenticated;

-- 4 その日の実績と、いつもの時刻とのずれ（推定）
create or replace function public.foreign_late(p_flight text, p_day date default null) returns jsonb
language sql stable security definer set search_path = public as $$
  with f as (
    select upper(trim(p_flight)) as fl, coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date) as d
  ), cs as (
    select c.icao || substring(f.fl from '^[A-Z0-9]{2}0*([0-9]{1,4})$') as callsign
      from f join public.airline_codes c on c.iata = substring(f.fl from '^([A-Z0-9]{2})[0-9]{1,4}$') and not c.odpt
     where f.fl ~ '^[A-Z0-9]{2}[0-9]{1,4}$'
  ), l as (
    select x.*, (extract(hour from x.at at time zone 'Asia/Tokyo') * 60 + extract(minute from x.at at time zone 'Asia/Tokyo'))::int as m,
           u.mins, u.n as un
      from f, public.foreign_legs x
      left join lateral (
        select mins, n from public.foreign_usual u
         where u.callsign = x.callsign and u.iata = x.iata and u.dep_here = x.dep_here and u.dow in (extract(dow from x.day)::int, -1)
         order by u.dow desc limit 1
      ) u on true
     where x.day = f.d and x.callsign in (select callsign from cs)
  )
  select jsonb_build_object(
    'flight', (select fl from f), 'day', (select d from f),
    'legs', coalesce((select jsonb_agg(jsonb_build_object(
        'callsign', callsign, 'iata', iata, 'dir', case when dep_here = 1 then 'dep' else 'arr' end, 'at', at,
        'reg', reg, 'type', type, 'other', other, 'event', event,
        'usual', case when mins is not null then lpad((mins / 60)::text, 2, '0') || ':' || lpad((mins % 60)::text, 2, '0') end,
        'usual_n', un,
        'late_min', case when mins is not null and event is null then ((m - mins + 720 + 2880) % 1440) - 720 end
      ) order by at) from l), '[]'::jsonb),
    'note', '推定です。機体の位置（adsb.lol、ODbL）から読んだ離陸・着陸の時刻と、前の8週の同じ便の時刻をくらべています。定刻や航空会社の発表ではありません')
$$;
revoke all on function public.foreign_late(text, date) from public;
grant execute on function public.foreign_late(text, date) to anon, authenticated;

-- 毎日の仕事：全機の航跡（rwy-learn が3時間ごと、15分）のあとに、今日と前の日を作る。いつもの時刻は毎晩1回（日本時間 3時55分）
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  execute $q$
    select cron.schedule('foreign-legs', '45 */3 * * *', $job$
      set statement_timeout = '2min'; set lock_timeout = '5s';
      select public.foreign_legs_build((now() at time zone 'Asia/Tokyo')::date - 1);
      select public.foreign_legs_build((now() at time zone 'Asia/Tokyo')::date);
    $job$)
  $q$;
  execute $q$
    select cron.schedule('foreign-usual', '55 18 * * *', $job$
      set statement_timeout = '2min'; set lock_timeout = '5s';
      select public.foreign_usual_build();
    $job$)
  $q$;
end
$outer$;
