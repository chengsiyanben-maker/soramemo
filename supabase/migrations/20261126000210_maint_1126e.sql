-- 定期の手入れ（11/26 の5回目）：消すときに連動する外部キーに索引を足す。記録は1行も消さない
--   退会（auth.users の行を消す）や受信の協力者を外すとき、Postgres は外部キーでつながった表を
--   「その列 = 消した行の id」で探して、消す（cascade）か空にする（set null）。
--   その列が先頭の索引がないと、1回ごとに表を丸ごと読む。模擬のデータベースで全部の外部キーを
--   全部読み禁止の計画にかけて、索引が使えなかった6か所だけに足す：
--     ・atc_msgs.feeder（協力者を外すと空にする。交信は7日分を残す表）
--     ・co3_invest.investor・co3_invest.target（今ある co3_invest_one は status で絞った部分索引なので、退会の削除には使えない）
--     ・co3_market.seller_id・co3_market.buyer_id（売り買いの記録。日数で増える）
--     ・co3_alliances.leader（小さい表だが、同じ形なので一緒に）
--   空の列（null）は探されないので、空になりうる列は「null でない行だけ」の小さい索引にする。
--   RLS：表は作らない・権限も RLS も変えない（索引だけ）。
--   影響：チェックイン・経営の画面とロジックは変わらない（返す値も同じ）。経営の表には索引が増えるだけで、書き込みの重さはほとんど変わらない。
--   作るときは表を1回読む（どれも小さいか7日分なので短い）。

create index if not exists atc_msgs_feeder on public.atc_msgs (feeder) where feeder is not null;
create index if not exists co3_invest_investor on public.co3_invest (investor);
create index if not exists co3_invest_target on public.co3_invest (target);
create index if not exists co3_market_seller on public.co3_market (seller_id);
create index if not exists co3_market_buyer on public.co3_market (buyer_id) where buyer_id is not null;
create index if not exists co3_alliances_leader on public.co3_alliances (leader);
