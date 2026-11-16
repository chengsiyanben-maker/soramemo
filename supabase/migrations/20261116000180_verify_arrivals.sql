-- OpenSky の置き換えの1歩目（11/16 PM「見落としの片付け」3。ストアの前に要る：OpenSky は研究・非商用向け）
-- ・毎晩の照合（運航確認）は OpenSky の /flights/arrival で「その空港・時間帯に着いた機体」を見ていた。
--   同じ形の一覧を、私たちの全機の記録（reg_legs。adsb.lol・ODbL）から返す読む関数 verify_arrivals を足す
-- ・返す形は OpenSky の1件と同じ（icao24 の代わりに登録記号、空港は ICAO）。照合の決まり（verify.ts の match）は変えない
-- ・照合の関数（verify-flights・tools/verify_flights.ts）は、秘密の設定 VERIFY_SOURCE=adsb のときだけこれを使う。
--   設定しなければ今までどおり OpenSky（本人が「置き換え」に決めたら設定を変える。コードの直しは要らない）
-- ・表・RLS は変えない。reg_legs を日付の索引（reg_legs_day）で引くだけ（一時ファイルなし）
-- 影響：チェックイン（フライトの記録の「確認済み」の付き方。設定を変えるまでは変わらない）。経営は使わない
set lock_timeout = '10s';

-- p_arr_icao：到着の空港（ICAO）。p_begin〜p_end に最後に見えた機体（着陸のころ）を返す。窓は2日まで
create or replace function public.verify_arrivals(p_arr_icao text, p_begin timestamptz, p_end timestamptz)
returns json
language sql stable security definer set search_path = public as $$
  with ap as (
    select iata from public.airports where icao = upper(p_arr_icao) and iata ~ '^[A-Z]{3}$' limit 1
  ), w as (
    select p_begin as b, least(p_end, p_begin + interval '2 days') as e
  )
  select coalesce(json_agg(json_build_object(
           'icao24', l.reg,
           'callsign', l.callsign,
           'estDepartureAirport', (select a.icao from public.airports a where a.iata = l.dep and a.icao is not null order by a.id limit 1),
           'estArrivalAirport', upper(p_arr_icao),
           'firstSeen', floor(extract(epoch from l.first_at))::bigint,
           'lastSeen', ceil(extract(epoch from l.last_at))::bigint
         ) order by l.last_at), '[]'::json)
    from w, ap, public.reg_legs l
   where l.day between ((w.b at time zone 'Asia/Tokyo')::date - 1) and (w.e at time zone 'Asia/Tokyo')::date
     and l.arr = ap.iata
     and l.dep is not null
     and l.last_at between w.b and w.e
$$;
revoke all on function public.verify_arrivals(text, timestamptz, timestamptz) from public, anon, authenticated;
grant execute on function public.verify_arrivals(text, timestamptz, timestamptz) to service_role;
