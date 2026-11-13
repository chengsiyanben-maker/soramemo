-- 関数どうしで使い回す小さな置き場（edge_cache）。11/13 3時15分 PM の指示「速さの見直し」（本人「処理速度を早くして」）
--   今まで airport-now・metar は、取ってきた便（ODPT）・気象通報（METAR）・予報（TAF）を「関数の中の記憶」にだけためていた。
--   Supabase の関数は呼ばれるたびに別の入れ物（isolate）で動くことが多く、記憶はすぐ消える。そのため、ためたはずの値がなく、
--   毎回 ODPT に4回（JAL・ANA × 到着・出発）問い合わせて、遅いと8秒待っていた（11/7：新千歳で 13〜20秒）。
--   ここに入れておけば、どの入れ物からでも1回の読み出し（主キーで引くので数ミリ秒）で使い回せ、配信元に問い合わせる回数も減る。
-- 中身：key（例 'now:fl:HND'・'now:wx:RJTT'・'now:taf:RJTT'・'metar:RJTT'）、body（関数が返す形の JSON。「通報がない」も null として入れる）、at（取ってきた時刻）
--   行は「空港 × 種類」で上書きするだけなので増えない（民間空港86 × 3 ＋ 運用の14 ＝ 約270行、合わせて 1MB 未満）。消す処理は要らない
--   上書きが多いので fillfactor 70（同じページの中で書き換えられ、索引を書き直さずに済む）
-- RLS：有効にして、ポリシーは作らない（anon・authenticated は読めも書けもしない）。読むのも書くのも関数（service_role）だけ
--   中身は公開の情報（便・天気）だが、配信元の利用条件（ODPT の再配布など）を広げないよう、関数を通した形でだけ出す
-- 影響：チェックイン（空港の今・運用の気象通報が速くなるだけ。返す形は変えない）。エアライン経営は使わない

create table if not exists public.edge_cache (
  key  text primary key check (key ~ '^[a-z]+(:[A-Za-z0-9]+)+$' and length(key) <= 40),
  body jsonb not null,
  at   timestamptz not null default now()
) with (fillfactor = 70);

comment on table public.edge_cache is '関数どうしで使い回す外部データの置き場（airport-now・metar）。上書きするだけで増えない。service_role だけが読み書きする';

alter table public.edge_cache enable row level security;
revoke all on public.edge_cache from anon, authenticated;
grant all on public.edge_cache to service_role;
