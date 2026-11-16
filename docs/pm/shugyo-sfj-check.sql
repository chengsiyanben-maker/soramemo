-- 修行：ANA の時刻表に、スターフライヤー（SFJ）運航の共同運航便が入っているかを見る（読むだけ。本人が SQL Editor で流す）
-- SFJ が運航する ANA の便名はおもに NH38xx・NH39xx の帯。SFJ の飛ぶ路線（北九州・山口宇部・福岡・関西・那覇と羽田・中部）に絞って見る
-- 入っていれば、羽田の乗り継ぎを SFJ 用の 50分に分ける必要がある（いまは ANA の便を全部 35分で組んでいる）
select flight, dep, arr, dep_time, aircraft, valid_from, valid_to
from public.timetable
where operator = 'ANA'
  and (flight ~ '^NH3[89][0-9]{2}$'
       or (dep in ('HND','NGO') and arr in ('KKJ','UBJ','FUK','KIX','OKA') and aircraft ilike '%320%'))
order by flight, valid_from
limit 100;

-- まとめ：便名の帯ごとの数（NH38xx・NH39xx が 0 なら、SFJ の便は入っていない見込み）
select substr(flight, 1, 4) as band, count(*) from public.timetable
where operator = 'ANA' and flight ~ '^NH3[0-9]{3}$' group by 1 order by 1;
