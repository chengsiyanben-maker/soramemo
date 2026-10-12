-- チェックインしたときの空港の天気（気象通報から、サーバーのチェックイン処理が書く）。印の「雨の日の印」や、空模様の実績に使う
--   weather：clear（晴れ）・cloudy（くもり）・rain（雨）・snow（雪）・fog（霧）・thunder（雷）。取れなかったときは null
--   wind_kt：風速（ノット）
alter table public.checkins add column if not exists weather text check (weather in ('clear', 'cloudy', 'rain', 'snow', 'fog', 'thunder'));
alter table public.checkins add column if not exists wind_kt smallint check (wind_kt between 0 and 200);
