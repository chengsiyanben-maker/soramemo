-- アプリ全体の見直し 2回目（kaizen/sweep-1125・report-sweep-1125.md）の4番。PM の指示 11/25 5時10分
--   特別塗装機の知らせを1便で1つにまとめ、夜の静かな時間を選べるようにする
--   1. push_subs.quiet_night：夜の静かな時間（23〜7時、日本時間）に、特別塗装機（予定・飛んでいる・着陸に向かっている・海外の機体）・
--      撮影の知らせ（着陸・離陸の数分前）・運用が変わった知らせを止めるか。はじめは true（止める）。今いる購読も true になる
--      乗る便・空港の遅れ・欠航・ダイバートの知らせは止めない。ゴーアラウンドは前からの ga_quiet のまま
--   2. livery_plans.quiet_push_at：夜の間に見つかった予定の便を、7時すぎに静かな時間を選んだ人へ1回だけ送った時刻（二重に送らないため）
--   表の権限は前と同じ（どちらも利用者からは読めない・書けない。書くのは裏の処理（service_role）と push-subscribe だけ）
--   影響：チェックイン（知らせの設定の画面に「夜は知らせない」の行を足す依頼を出す）。経営は関係しない
--   航路と機体の記録は消さない（列を足すだけ）
set lock_timeout = '5s';

alter table public.push_subs add column if not exists quiet_night boolean not null default true;
comment on column public.push_subs.quiet_night is '夜の静かな時間（23〜7時、日本時間）に特別塗装機・撮影・運用の変化の知らせを止めるか（はじめ true）。乗る便・空港の遅れは止めない';

alter table public.livery_plans add column if not exists quiet_push_at timestamptz;
comment on column public.livery_plans.quiet_push_at is '夜の間に見つかった予定を、朝に静かな時間を選んだ人へ送った時刻';

-- RLS と権限（前と同じ形をもう一度はっきり書く）
alter table public.push_subs enable row level security;
alter table public.livery_plans enable row level security;
revoke all on public.push_subs from public, anon, authenticated;
revoke all on public.livery_plans from public, anon, authenticated;
reset lock_timeout;
