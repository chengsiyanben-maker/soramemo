#!/usr/bin/env python3
"""番外編（基地・滑空場・民間の飛行場・ヘリポート）の判定範囲の見直し案を作る（データ担当・11/26 本人の OK ②）

考え方：「敷地や門に近づかず、公道や見学できる所から押せる」こと。
  判定は「中心の点から半径 radius_m の円の中」だけなので、円が敷地の外の道まで届いていれば、門に近づく必要はない。
  そこで、敷地の端の見込み（中心から滑走路のいちばん遠い端まで＋種類ごとの余白）を出し、
  今の半径がそれより小さい所だけ広げる案にする（狭める案は出さない＝今押せる所は押せたまま）。

  余白：基地（mil・secret）＝ 端の先の柵まで 300m ＋ 外の道 200m ＝ 500m
        民間の飛行場・滑空場（field・glider）＝ 柵まで 100m ＋ 外の道 200m ＝ 300m
        ヘリポート（heli）＝ 発着場の敷地 100m ＋ 外の道 200m ＝ 300m（滑走路がないので中心から）
  滑走路の端の座標：OurAirports runways.csv（パブリックドメイン。data/ap_shape/raw/oa_runways_jp.csv）。
    両端の座標がないときは長さの半分を中心からの距離とする（推定）。長さもないときは種類の決まり（下の DEFAULT_HALF）
  上限：3,000m（広げすぎると、近くの別の番外編との境目が分かりにくい）

使い方：python3 tools/extra_safe_range.py <番外編の行の json> <表の md の出力先> <移行の案の出力先>
  番外編の行の json は、模擬のデータベースから
    select id, name, icao, iata, lat, lon, radius_m, extra_kind, game_target from public.airports where extra_kind is not null
  を書き出したもの（tests/sql の道具で作る）
"""
import csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '..', 'data', 'ap_shape', 'raw')
LINES = os.path.join(HERE, '..', 'data', 'ap_shape', 'runway_lines.json')
MARGIN = {'mil': 500, 'secret': 500, 'field': 300, 'glider': 300, 'heli': 300}
DEFAULT_HALF = {'mil': 1000, 'secret': 1000, 'field': 300, 'glider': 300, 'heli': 0}
KIND_JA = {'mil': '基地', 'secret': '基地（隠し）', 'field': '民間の飛行場', 'glider': '滑空場', 'heli': 'ヘリポート'}
CAP = 3000


def dist_m(a_lat, a_lon, b_lat, b_lon):
    r = math.pi / 180
    dl, dn = (b_lat - a_lat) * r, (b_lon - a_lon) * r
    h = math.sin(dl / 2) ** 2 + math.cos(a_lat * r) * math.cos(b_lat * r) * math.sin(dn / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def runway_reach(ap, rws):
    """中心からいちばん遠い滑走路の端までの距離(m)と、その出どころ"""
    best, src = None, None
    for r in rws:
        if r.get('closed') == '1':
            continue
        ends = [(num(r['le_latitude_deg']), num(r['le_longitude_deg'])), (num(r['he_latitude_deg']), num(r['he_longitude_deg']))]
        if all(e[0] is not None and e[1] is not None for e in ends):
            d = max(dist_m(ap['lat'], ap['lon'], e[0], e[1]) for e in ends)
            s = 'OA の両端'
        elif num(r['length_ft']):
            d = num(r['length_ft']) * 0.3048 / 2
            s = 'OA の長さの半分（推定）'
        else:
            continue
        if best is None or d > best:
            best, src = d, s
    return best, src


def plan(rows):
    lines = {a['id']: a for a in json.load(open(LINES, encoding='utf-8'))['airports']}
    by_ident = {}
    for r in csv.DictReader(open(os.path.join(RAW, 'oa_runways_jp.csv'), encoding='utf-8')):
        by_ident.setdefault(r['airport_ident'], []).append(r)
    out = []
    for ap in sorted(rows, key=lambda x: (list(MARGIN).index(x['extra_kind']), x['id'])):
        if ap.get('game_target'):
            continue  # 86空港（民間）は対象外
        k = ap['extra_kind']
        ident = (lines.get(ap['id']) or {}).get('oa_ident')
        # ヘリポートは滑走路を見ない（広島ヘリポートは元の広島西飛行場で、OurAirports に昔の滑走路が残っている）
        reach, src = runway_reach(ap, by_ident.get(ident, [])) if ident and k != 'heli' else (None, None)
        if reach is None:
            reach, src = DEFAULT_HALF[k], '決まりの値（滑走路のデータなし）' if k != 'heli' else '中心から（滑走路なし）'
        need = reach + MARGIN[k]
        need_r = int(math.ceil(need / 100.0) * 100)
        new = min(CAP, max(ap['radius_m'], need_r))
        if new > ap['radius_m']:
            why = f'敷地の端の見込み {int(round(reach))}m ＋ 余白 {MARGIN[k]}m ＝ {int(round(need))}m に今の半径が届かない'
        else:
            why = f'今の半径で、敷地の端の見込み {int(round(reach))}m ＋ 余白 {MARGIN[k]}m ＝ {int(round(need))}m に届いている'
        if need_r > CAP:
            why += f'（上限 {CAP}m で止めた。外の道の一部は円の外）'
        out.append({'id': ap['id'], 'name': ap['name'], 'kind': k, 'icao': ap.get('icao'), 'iata': ap.get('iata'), 'lat': ap['lat'], 'lon': ap['lon'],
                    'radius_m': ap['radius_m'], 'reach_m': int(round(reach)), 'src': src, 'need_m': int(round(need)), 'new_m': new, 'why': why})
    return out


def md(out):
    ch = [x for x in out if x['new_m'] > x['radius_m']]
    s = ['| 場所 | 種類 | 今の範囲 | 新しい範囲 | 理由 | 端の出どころ |', '|---|---|---|---|---|---|']
    for x in out:
        mark = '**' if x['new_m'] > x['radius_m'] else ''
        s.append(f"| {x['name']}（{x['id']}） | {KIND_JA[x['kind']]} | {x['radius_m']:,}m | {mark}{x['new_m']:,}m{mark} | {x['why']} | {x['src']} |")
    return '\n'.join(s), ch


def migration(ch):
    vals = ',\n'.join(f"  ({x['id']}, {x['radius_m']}, {x['new_m']})" for x in ch)
    return f"""-- 番外編の判定範囲を「近づかずに公道から押せる」形に広げる（案。PM が見てから出す。本人の OK：11/26）
--   作り方：tools/extra_safe_range.py（敷地の端の見込み＝中心から滑走路のいちばん遠い端＋種類ごとの余白。今より小さくはしない）
--   一覧と理由：docs/pm/report-extra-safe-range.md
--   番外編（game_target でない・extra_kind のある行）だけを変える。86空港の radius_m は変えない（経営の airport_size・co_size は動かない）
--   今の値が案を作ったときと違う行は変えない（手で直した値を上書きしない）
--   RLS・権限は airports の今のまま（だれでも読める・anon / authenticated は書けない）
--   影響：チェックイン（番外編の印を押せる範囲が少し広がる）。経営は関係しない（番外編は便にも路線にもならない）

update public.airports a set radius_m = v.new_m
  from (values
{vals}
  ) as v(id, old_m, new_m)
 where a.id = v.id and a.radius_m = v.old_m and a.extra_kind is not null and not a.game_target;
"""


if __name__ == '__main__':
    rows = json.load(open(sys.argv[1], encoding='utf-8'))
    out = plan(rows)
    table, ch = md(out)
    open(sys.argv[2], 'w', encoding='utf-8').write(table + '\n')
    open(sys.argv[3], 'w', encoding='utf-8').write(migration(ch))
    json.dump(out, open(sys.argv[2] + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(f'{len(out)} か所・広げる {len(ch)} か所')
