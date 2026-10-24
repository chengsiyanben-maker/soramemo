-- 番外編の新しい枠「一般の人が行けない飛行場」（extra_kind = 'secret'）。全国制覇や全クリには数えない、押せた人だけの枠。
--   最初は硫黄島と南鳥島（どちらも自衛隊の基地で、一般の人は行けない）。位置は OurAirports（パブリックドメイン）。
--   ほかの番外編と同じく、民間空港より優先度が低く、フライトにはしない（checkin 関数は extra_kind で番外編を見分ける）。
alter table public.airports drop constraint if exists airports_extra_kind_check;
alter table public.airports add constraint airports_extra_kind_check check (extra_kind in ('mil', 'glider', 'field', 'secret'));
insert into public.airports (id, name, icao, iata, category, prefecture, lat, lon, radius_m, rare, game_target, extra_kind) values
  (4001, '硫黄島航空基地', 'RJAW', null, 'secret', '東京都', 24.784, 141.3228, 2000, false, false, 'secret'),
  (4002, '南鳥島航空基地', 'RJAM', null, 'secret', '東京都', 24.2897, 153.9794, 1500, false, false, 'secret')
on conflict (id) do nothing;
