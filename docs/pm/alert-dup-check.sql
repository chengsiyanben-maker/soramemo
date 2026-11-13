-- 遅れの通知の重なりを確かめる（読むだけ。SQL Editor に全部貼って流す。お知らせは2日分しか残らないので軽い）
-- 結果の1行目の「名前」ごとに数が出る。数が0でない所が、今の仕組みで二重に届きうる所

-- ① 1つの便で、出発の遅れと到着の遅れの両方が出た（今は別々に2回届く）
select '① 出発と到着の両方' as 名前, count(*) as 便の数
  from (select schedule_id from public.flight_alerts
         where kind in ('delay_dep', 'delay_arr') and schedule_id is not null
         group by schedule_id having count(distinct kind) = 2) x
union all
-- ② 推定（flight-watch）と航空会社の運航情報（odpt-status）の両方が同じ便に出た（文に「推定」と「航空会社の運航情報」）
select '② 推定と運航情報の両方', count(*)
  from (select schedule_id from public.flight_alerts where schedule_id is not null
         group by schedule_id
        having bool_or(message like '%推定%') and bool_or(message like '%航空会社の運航情報%')) x
union all
-- ③ 同じ出発・到着・定刻の予定の便が2行以上あって、そのどちらにもお知らせが出た（共同運航・時刻表の重なり）
select '③ 同じ便の別の行', count(*)
  from (select s.dep, s.arr, s.std from public.flight_alerts a join public.flight_schedule s on s.id = a.schedule_id
         group by s.dep, s.arr, s.std having count(distinct s.id) > 1) x
union all
-- ④ 同じ便名・同じ日に、別の予定の便の行でお知らせが出た（同じ便名で2区間、または時刻表のずれ）
select '④ 同じ便名で別の行', count(*)
  from (select s.flight, s.svc_date from public.flight_alerts a join public.flight_schedule s on s.id = a.schedule_id
         group by s.flight, s.svc_date having count(distinct s.id) > 1) x
union all
-- ⑤ お知らせの総数（2日分）と、そのうち遅れ
select '⑤ お知らせの総数（2日）', count(*) from public.flight_alerts
union all
select '⑤ そのうち遅れ', count(*) from public.flight_alerts where kind in ('delay_dep', 'delay_arr')
union all
-- ⑥ 通知の購読：「この便に乗る」を選んでいる購読・空港を選んでいる購読・両方
select '⑥ 乗る便を選んでいる購読', count(*) from public.push_subs where cardinality(flights) > 0
union all
select '⑥ 空港を選んでいる購読', count(*) from public.push_subs where cardinality(airports) > 0
union all
select '⑥ 両方を選んでいる購読（同じ便が空港と乗る便の両方で当たる人）', count(*) from public.push_subs where cardinality(flights) > 0 and cardinality(airports) > 0;

-- ⑦ 二重の例を10件（便名・種類・時刻・文の頭）。①〜④で数があったら、この結果も貼ってほしい
select s.flight, s.svc_date, s.dep, s.arr, a.kind, to_char(a.created_at at time zone 'Asia/Tokyo', 'MM-DD HH24:MI') as 出た時刻, left(a.message, 60) as 文
  from public.flight_alerts a join public.flight_schedule s on s.id = a.schedule_id
 where a.schedule_id in (select schedule_id from public.flight_alerts where schedule_id is not null group by schedule_id having count(*) > 1)
 order by s.svc_date desc, s.flight, a.created_at
 limit 10;
