-- AAL176（N791AN）が 11/22 19:30〜21:30（日本時間）に記録に載っていたかを見る。読むだけ（書き換えなし）
-- 本人が SQL Editor に貼って流す。どれも索引で引くので軽い
-- ※ track_points（航跡の点）は36時間で消える。11/24 朝8時半（日本時間）までに流すこと。それより後は ① が 0 件になる（記録は daily-archive のファイル置き場に残る）
set statement_timeout = '20s';

-- ① 航跡の点（呼び出し符号 AAL176。索引 track_points_cs_t）：最初と最後の時刻・点の数・高さ
select '①航跡' as k, count(*) as n,
       min(t) at time zone 'Asia/Tokyo' as first_jst, max(t) at time zone 'Asia/Tokyo' as last_jst,
       min(alt) * 100 as min_alt_ft, max(alt) * 100 as max_alt_ft
from public.track_points
where callsign = 'AAL176'
  and t >= timestamptz '2026-11-22 19:30+09' and t < timestamptz '2026-11-22 21:30+09';

-- ② 機体ごとの便の記録（登録記号 N791AN。主キー reg, day, callsign）
select '②reg_legs' as k, reg, callsign, day, type, dep, arr,
       first_at at time zone 'Asia/Tokyo' as first_jst, last_at at time zone 'Asia/Tokyo' as last_jst
from public.reg_legs
where reg = 'N791AN' and day between date '2026-11-21' and date '2026-11-23';

-- ③ 海外の会社の便の実績（主キーの先頭 callsign）
select '③foreign_legs' as k, day, callsign, iata, dep_here, at at time zone 'Asia/Tokyo' as at_jst, flight, reg, type, other, event
from public.foreign_legs
where callsign = 'AAL176' and at >= timestamptz '2026-11-22 00:00+09' and at < timestamptz '2026-11-23 06:00+09';

-- ④ 特別塗装機の知らせを送った記録（いまの一覧に N791AN がないので、0 件のはず）
select '④livery_notified' as k, reg, iata, notified_at at time zone 'Asia/Tokyo' as at_jst
from public.livery_notified where reg = 'N791AN';

-- ⑤ いまの位置（15分で消えるので、ふつうは 0 件。念のため）
select '⑤live_positions' as k, callsign, reg, type, alt_ft, seen_at at time zone 'Asia/Tokyo' as seen_jst
from public.live_positions where callsign = 'AAL176' or reg = 'N791AN';
