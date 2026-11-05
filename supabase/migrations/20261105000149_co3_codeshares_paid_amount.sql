-- エアライン経営 co-v3：共同運航（co3_codeshares）に、ブロック買い取りで今月払った額 paid_amount を足す（経営の担当からの依頼）
--   いまは払った月（paid_month）しか残らず、退会のときの返金を「いまの収益」から計算している。払った額を残して返金に使えるようにする
--   列を足すだけ。書くのは経営の co3_cs_pay_block（経営の担当が直す）。それまでは空（null）のままで、返金はいまの計算のまま
--   すでにある行は空のまま（過去の払った額は分からないので、作り話の数字を入れない）
--   RLS・権限は変えない（いまのまま：本人が運航会社か販売会社の行だけ読める。書けるのはサーバーの関数だけ）
--   影響：経営だけ（チェックインの表・関数は触らない）
alter table public.co3_codeshares add column if not exists paid_amount bigint check (paid_amount is null or paid_amount >= 0);
comment on column public.co3_codeshares.paid_amount is 'ブロック買い取りで paid_month に払った額（円）。空＝記録がない';
