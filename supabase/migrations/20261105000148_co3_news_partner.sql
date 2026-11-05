-- エアライン経営 co-v3：会社の新聞（co3_news）の種類に 'partner'（相手の会社の退会の知らせ）を足す（経営の担当からの依頼）
--   co3_leave_news は 'partner' で書き、表の決まりに無いときだけ 'event' に落とす。この移行のあとは 'partner' で入る
--   すでにある行は変えない（'event' で入った知らせもそのまま残す）。RLS・権限は変えない
--   影響：経営だけ（チェックインの表・関数は触らない）
alter table public.co3_news drop constraint if exists co3_news_kind_check;
alter table public.co3_news add constraint co3_news_kind_check
  check (kind in ('route', 'god', 'rating', 'value', 'slots', 'event', 'partner'));
