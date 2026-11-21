# -*- coding: utf-8 -*-
# 一覧ページ（index.html）を作る。使い方：python3 make_index.py flight|shugyo <出力先>
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CSS_DAY, CSS
kind, OUT = sys.argv[1], sys.argv[2]
D = {
 'flight': ('フライトの改善案', 'design/flight-book', [
   ('4版（11/10 改善担当 review-3 の直し）', [('A1-log-v4', 'A1 日誌（空の上 45時間21分）'), ('A1y-log-years-v4', 'A1y 年をまたぐ所（1本につながる）'), ('A1p-year-pick-v4', 'A1p 年を選ぶ（その年の頭へ）'), ('A2s-share-v4', 'A2s 画像で共有（券の下を段に）'), ('A2s2-share-seat-on-v4', 'A2s2 座席を ON'),
     ('A2s3-share-long-v4', 'A2s3 いちばん長い機種名'), ('A3-year-v4', 'A3 年のまとめ（年の切り替えを同じ場所に）'), ('R1-no-route-v4', 'R1 「車など」の数え方'), ('N1-log-night-v4', 'N1 夜の日誌')],
    '券の下を段に分け、長い機種名でも「そらメモ（非公式アプリ）」が折れない。日誌は年をまたいで1本、「2024年へ」は年の終わりだけ。名前は「車など」の1つに。見本の旅程を直した',
    '決めてほしいこと：車などは案1か案2（おすすめ）か・名前は「車など」でよいか・点線の太さ'),
   ('ここから下は3版（記録）', [], '', ''),
   ('3版（11/10 改善担当 review-2 の必ず直す3つ）', [('A1-log-v3', 'A1 日誌（年の切り替え・数字1行）'), ('A1y-log-years-v3', 'A1y 年をまたぐ所と続き'), ('A1p-year-pick-v3', 'A1p 年を選ぶ'), ('A2s-share-v3', 'A2s 画像で共有（座席は OFF で始める）'), ('A2s2-share-seat-on-v3', 'A2s2 座席を ON にしたところ'),
     ('A3-year-v3', 'A3 年のまとめ'), ('R1-no-route-v3', 'R1 「航路なし」の数え方（案1・案2）'), ('N1-log-night-v3', 'N1 夜の日誌')],
    '共有は「登録記号（はじめ ON）」「座席（はじめ OFF）」の2つ・「会社のロゴは入りません」・券の下に「各航空会社とは関係ありません」。年の切り替え（‹ 2026年 ›）と年をまたぐ帯・続き。航路なしの移動は日誌の行と数え方を2案で',
    '決めてほしいこと：航路なしは案1（便に入れる）か案2（別に数える・おすすめ）か。地図（M1・M2）・1便（A2）は2版のまま'),
   ('ここから下は2版（記録）', [], '', ''),
   ('2版（11/10）A 航空日誌＋糸の地図', [('A1-log-v2', 'A1 日誌（1画面・本命）'), ('A1s-log-sheet-v2', 'A1s 日誌（シートの版・比べる用）'), ('A2-flight-v2', 'A2 1便'), ('A2s-share-v2', 'A2s 共有：搭乗券の1枚'),
     ('A3-year-v2', 'A3 年のまとめ'), ('M1-map-v2', 'M1 地図（太さ＝回数）'), ('M2-route-v2', 'M2 1区間を押したところ'), ('N1-log-night-v2', 'N1 夜の日誌'), ('N1m-map-night-v2', 'N1m 夜の地図'), ('N2-route-night-v2', 'N2 夜の1区間')],
    '本人の決定「A に地図を入れる」の形。時間は「2時間20分」、出発の時刻を2行目に。上の段は図鑑と同じ。地図は今の地図の線の太さだけを回数にし、色は1色',
    '決めてほしいこと：1画面（A1）かシート（A1s）か。地図の「航路なし」の点線をどう太さにするか（見本にはない）'),
   ('ここから下は1版（記録）', [], '', ''),
   ('今', [('01-now-problems', '01 今の見にくい所')], '', ''),
   ('A 正攻法「航空日誌」', [('A1-log', 'A1 日誌（一覧）'), ('A2-flight', 'A2 1便の詳しい所'), ('A3-year', 'A3 年のまとめ')],
    '1便1行で 844 に5便・667 に2便。日付が左で月の見出しがあり「いつの便か」が追える。見方が3つに減り、決まりをどれも外さない',
    '新しさは少ない。搭乗券のカードの楽しさは一覧から消える（共有の画像に残す）'),
   ('B 斬新「1本の長い紙の航跡」', [('B1-tape', 'B1 1年の紙'), ('B2-tape-flight', 'B2 紙の上の1便')],
    '1年を送って眺める楽しさ。長い便ほど高い山で、旅の多い月がひと目で分かる。下の帯でどこを見ているか分かる',
    '横に送る操作はタブを左右にはらう操作とぶつかりやすい。1便ずつ探すのは日誌より遅い。紙の地・細い線は決まりの外'),
   ('C 斬新「時計の文字盤」', [('C1-clock', 'C1 時計'), ('C2-clock-hour', 'C2 時を押したところ')],
    '「朝の便ばかり」など、自分の乗り方の癖が1枚で分かる。数が増えても図の大きさは変わらない',
    '時刻のない記録（記録帳で足した便）は描けない。図を読むのに少し慣れがいる。一覧の代わりにはならない（見方の1つ）'),
   ('D 斬新「糸の日本地図」', [('D1-threads', 'D1 糸の地図'), ('D2-thread-route', 'D2 糸を押したところ')],
    '同じ路線を何度も乗った人ほど太い糸になり、記録帳の1ページのような満足感。路線の見方をまとめられる',
    '本番の地図（航空図風・会社の色）と2枚になる。羽田のまわりは糸が重なる。生成りの地は決まりの外'),
   ('まとめ', [('07-views', '07 見方をまとめる'), ('N1-log-night', 'N1 夜の画面（A）')], '', '')]),
 'shugyo': ('修行の改善案', 'design/shugyo-book', [
   ('今', [('01-now-problems', '01 今の見にくい所')], '', ''),
   ('E 正攻法「道のりの1枚」', [('E1-overview', 'E1 道のり'), ('E2-flight', 'E2 1便の内訳'), ('E3-months', 'E3 月ごと')],
    '「1年の何割」と並ぶのでペースが分かる。2つの道を同じ形に。空の行がなくなり、届くかが1画面目に出る。決まりをどれも外さない',
    '路線の運航を外すのは修行担当の今の画面と食い違う（予定の便のカードへ移す相談がいる）'),
   ('F 斬新「山登りの高度」', [('F1-mountain', 'F1 山'), ('F2-mountain-log', 'F2 山行記録')],
    'ステイタスが山小屋なので、あとどれだけ登るかが体で分かる。予定・計画は別の道で、実績と重ならない',
    '2つ目の道（回数）は山では描けない。空の地・山なみは決まりの外。山の言葉は好みが分かれる'),
   ('G 斬新「残りから数える」', [('G1-countdown', 'G1 残りから'), ('G2-countdown-year', 'G2 年の見通し')],
    '「あといくら」が主役で、乗るたびに減るのが分かりやすい。年末の残りを推定で出せる',
    '数が減っていく見せ方は、届かない年は重たく感じる。点線とぎざぎざは決まりの外。家計簿でも円は出さない'),
   ('H 斬新「回数のマス目」', [('H1-cells', 'H1 マス目'), ('H2-cell', 'H2 マスを押したところ')],
    '30回の道が目で数えられる。乗った日がマスに入るので、記録を見返す楽しさもある',
    'FOP だけの道には向かない（切り替えがいる）。50回・120回の段ではマスが多すぎる。金の使い方が決まりの外'),
   ('まとめ', [('07-views', '07 見方をまとめる'), ('N1-overview-night', 'N1 夜の画面（E）')], '', '')]),
}
title, br, G = D[kind]
css = """.wrap{padding:16px 16px 60px}.g{margin-top:22px}.g h2{font-size:18px;margin:0 4px 8px;color:var(--strong)}
.th{display:flex;gap:10px;overflow-x:auto;padding-bottom:6px}.th a{flex:none;width:150px;text-decoration:none;color:var(--ink);font-size:13px;font-weight:700}
.th img{width:150px;border-radius:14px;box-shadow:var(--shadow);display:block;margin-bottom:6px}
.pc{display:grid;grid-template-columns:1fr;gap:6px;margin-top:8px}.pc div{background:var(--card);border-radius:14px;padding:10px 12px;font-size:13px;line-height:1.6;box-shadow:var(--shadow)}.pc b{display:block;font-size:13px}"""
s = '<div class="wrap"><h1 style="font-size:24px;margin:8px 4px 0;color:var(--strong)">%s</h1><p class="note">ブランチ %s。画面案だけでアプリには入れない。幅390・高さ844で作り、png/ に 844（2倍）と 667 の写真。見本の記録は 2026年の26便（JAL グループ20・ANA 6）。</p>' % (title, br)
for name, items, good, bad in G:
    s += '<div class="g"><h2>%s</h2><div class="th">' % name
    for fn, lab in items:
        s += '<a href="%s.html"><img src="png/%s.png" alt="%s" loading="lazy">%s</a>' % (fn, fn, lab, lab)
    s += '</div>'
    if good:
        s += '<div class="pc"><div><b>良い点</b>%s</div><div><b>困る点</b>%s</div></div>' % (good, bad)
    s += '</div>'
s += '</div>'
html = '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>%s（画面案の一覧）</title>\n<style>%s%s%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (title, CSS_DAY, CSS, css, s)
open(OUT + '/index.html', 'w').write(html)
print('ok')
