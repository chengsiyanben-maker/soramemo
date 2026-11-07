-- 機体の位置（live_positions）に進行方向（trk、度）を足す（11/7 全体のデバッグ）
--   見る人の airport-traffic の呼び出しを、adsb.lol に問い合わせず、記録の処理（30秒ごと）が残したこの表から作るため。
--   着陸・離陸の見分けで「ほかの空港へ向かう機体」を除くのに進行方向を使う（前は adsb.lol の track をその場で使っていた）。
--   表の中身は消さない・書き換えない（新しい列は空で始まり、次の記録から入る）。
--   RLS：今のまま（有効・public／anon／authenticated からは読めも書けもしない。読むのはサーバーの関数だけ）。
--   影響：チェックイン・経営のどちらのコードも、この表を直接は読まない（flight-watch・airport-foreign・atc-ingest は列を名前で選んでいるので変わらない。airport-foreign はすでに同じやり方でこの表から機体を出している）
alter table public.live_positions add column if not exists trk smallint check (trk between 0 and 359);
alter table public.live_positions enable row level security;
revoke all on public.live_positions from public, anon, authenticated;
