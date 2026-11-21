-- 呼び出し符号の記号 → 便名の記号の表（airline_codes、移行171）に会社を足す（データ担当・11/21 data/livery-dest2）
--   11/21 本人「便の名前から行き先を判別して、判定を強化して」。Edge Functions の flight_watch.ts の PREFIX に足した会社と同じ中身にそろえる。
--   日本の小さい会社（トキエア TOK→BV・天草エアライン AHX→MZ）と、日本に来るほかの会社・貨物の会社。
--   足すだけ（今ある行は変えない：on conflict do nothing）。表の形と RLS（誰でも読める・書くのは service_role）は移行171 のまま。
--   影響：毎晩の foreign_legs・foreign_usual に、これらの会社の便の実績といつもの時刻が入るようになる（行き先の判定・「いつもより○分遅い（推定）」に使える）。
--         トキエア・天草は JA の機体なので、前は「表にない日本の機体」として入れていなかった（11/16 本人：ODPT にない日本の会社も集める）。
--         チェックイン（運用タブ・知らせの行き先）に効く。画面の形は変えない。経営は使わない。本人の記録は入っていない
set lock_timeout = '5s';

insert into public.airline_codes (icao, iata, odpt) values
  ('TOK','BV',false), ('AHX','MZ',false),
  ('EOK','RF',false), ('APZ','YP',false), ('HGB','HB',false), ('AMU','NX',false), ('CSC','3U',false), ('CSZ','ZH',false),
  ('CDC','GJ',false), ('APG','Z2',false), ('TAX','XJ',false), ('TLM','SL',false), ('MDA','AE',false), ('ASA','AS',false),
  ('AMX','AM',false), ('VOZ','VA',false), ('THT','TN',false), ('ACI','SB',false), ('ANG','PX',false), ('UZB','HY',false),
  ('RBA','BI',false), ('IBE','IB',false), ('ITY','AZ',false), ('LOT','LO',false), ('WJA','WS',false), ('FDX','FX',false),
  ('UPS','5X',false), ('CLX','CV',false), ('GTI','5Y',false), ('PAC','PO',false), ('CKS','K4',false), ('CKK','CK',false),
  ('AHK','LD',false), ('CSS','O3',false)
on conflict (icao) do nothing;

reset lock_timeout;
