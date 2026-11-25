-- 定期の手入れ 11/26（データ担当・maint/2026-11-26）
--   SQL の関数ごとに「索引を使わず表を全部読む所」を、全部読みを禁じた計画（enable_seqscan off）で洗い出した結果から2つ直す
--   1. rwy_sample_counts()：rwy_samples（滑走路の記録。消さずに増える表）を毎回まるごと数える関数が、ログインなし（anon）でも呼べた。
--      画面・Edge Functions・道具のどこからも呼ばれていない（作ったとき 10/21 の確かめ用の残り）。だれでも何度でも呼べると、
--      そのたびに大きな表を全部読むので、ほかの処理を巻き込むおそれがある → anon・authenticated から呼ぶ権利を外す。
--      関数そのものは残す（本人の SQL Editor と service_role では今までどおり呼べる）。本文は変えない
--   2. airports (iata) の索引：airport_board（運用タブの案内板。開くたび）が便1つごとに「相手の空港が国内か」を airports の iata で引くが、
--      iata の索引がなく毎回 airports を全部読んでいた。verify_arrivals・world_flight_counts・is_japan_iata も同じ。
--      airports は小さな表（約190行・iata のある行は約90）なので索引も小さい。iata のない行（飛行場・基地など）は入れない部分索引
--   影響：チェックイン（運用タブの案内板が少し速くなるだけ。値・画面は変わらない）。経営は関係しない（経営の関数の airports の読み方は経営担当の持ち場なので触らない）
--   表・列・RLS・方針は変えない。記録は消さない
set lock_timeout = '5s';

revoke execute on function public.rwy_sample_counts() from anon, authenticated;
grant execute on function public.rwy_sample_counts() to service_role;

create index if not exists airports_iata on public.airports (iata) where iata is not null;

reset lock_timeout;
