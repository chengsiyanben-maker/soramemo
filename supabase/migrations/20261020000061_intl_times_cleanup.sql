-- 直す：海外の空港側の運航情報の時刻（見込み・実際）を日本時間として読んでいたため、ずれた時刻が残っている。
-- 直近の国際線の、海外の空港側の時刻を消す（運航情報の取り込み odpt-status が、現地時刻として読み直して入れ直す）
update public.flight_schedule f set eta = null, ata = null
where f.svc_date >= current_date - 3 and not exists (select 1 from public.airports a where a.iata = f.arr);
update public.flight_schedule f set etd = null, atd = null
where f.svc_date >= current_date - 3 and not exists (select 1 from public.airports a where a.iata = f.dep);
