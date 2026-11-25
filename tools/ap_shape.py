#!/usr/bin/env python3
"""空港の形と滑走路の線のデータ（data/ap-shape・PM の指示 11/26 0時15分）

使い方（くわしくは docs/pm/airport-data-howto.md）
  1. node tools/ap_master_dump.mjs data/ap_shape/raw/master.json
       移行を全部流した模擬のデータベースから airports・terminals を書き出す（本番の表と同じ中身）
  2. python3 tools/ap_shape.py subset <OurAirports の airports.csv> <runways.csv>
       OurAirports（パブリックドメイン）の全世界の CSV から日本の分だけを data/ap_shape/raw/ に切り出す
  3. python3 tools/ap_shape.py build
       data/ap_shape/runway_lines.json（印のカード用の滑走路の線）と data/ap_shape/preview.html（全空港を1枚に並べた確かめ用）を作る
  4. python3 tools/ap_shape.py compare <国土数値情報 C28 の UTF-8 フォルダ>
       今の判定の範囲（円＋ターミナル）と国土数値情報の空港の面を比べる表を docs/pm/ap-shape-compare.md に書く
       国土数値情報は利用約款を読めていないので、配るデータには混ぜない（この表の数字を作るためにだけ読む。元のファイルは置かない）

判定（関数 checkin・_shared/judge.ts）は変えない。このファイルはデータを作るだけ。
"""
import csv, json, math, os, sys, datetime, html

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'data', 'ap_shape')
RAW = os.path.join(OUT, 'raw')
LO, HI = 0.15, 0.85          # 印のカードで線を収める四角
TERM_RADIUS_M = 800          # judge.ts の RULE.termRadiusM（ターミナルから800m以内も空港の範囲）
KIND_JA = {None: '空港', 'glider': '滑空場', 'mil': '基地', 'field': '飛行場', 'heli': 'ヘリポート', 'secret': 'シークレット'}


def load_master():
    p = os.path.join(RAW, 'master.json')
    m = json.load(open(p, encoding='utf-8'))
    return m['airports'], m['terminals']


def local_xy(lat, lon, lat0, lon0):
    """空港の中心を原点にした平面（m）。横は緯度で縮める（cos 補正）。北が上"""
    return ((lon - lon0) * math.cos(math.radians(lat0)) * 111_320.0, (lat - lat0) * 110_574.0)


def dist_m(a_lat, a_lon, b_lat, b_lon):
    r = math.pi / 180
    h = math.sin((b_lat - a_lat) * r / 2) ** 2 + math.cos(a_lat * r) * math.cos(b_lat * r) * math.sin((b_lon - a_lon) * r / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def heading(l):
    """線の向き（0〜180度。どちら向きかは区別しない）"""
    la1, lo1, la2, lo2 = l[:4]
    x, y = local_xy(la2, lo2, la1, lo1)
    return math.degrees(math.atan2(x, y)) % 180


def normalize(lines, lat0, lon0):
    """緯度経度の線を 0.15〜0.85 の四角に収めた [u1,v1,u2,v2] に。縦横の比は保つ（長い辺に合わせ、短い辺は真ん中に）。v は下向き（SVG と同じ）"""
    pts = [(local_xy(l[0], l[1], lat0, lon0), local_xy(l[2], l[3], lat0, lon0)) for l in lines]
    xs = [p[0] for ab in pts for p in ab]; ys = [p[1] for ab in pts for p in ab]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    w, h = xmax - xmin, ymax - ymin
    s = max(w, h)
    if s < 1:
        return None, 0
    k = (HI - LO) / s
    ox, oy = (s - w) / 2, (s - h) / 2
    out = []
    for (x1, y1), (x2, y2) in pts:
        u1 = LO + (x1 - xmin + ox) * k; v1 = HI - (y1 - ymin + oy) * k
        u2 = LO + (x2 - xmin + ox) * k; v2 = HI - (y2 - ymin + oy) * k
        out.append([round(u1, 3), round(v1, 3), round(u2, 3), round(v2, 3)])
    return out, round(s)


# ---------- 1. 日本の分だけ切り出す ----------
def cmd_subset(ap_csv, rw_csv):
    os.makedirs(RAW, exist_ok=True)
    with open(ap_csv, encoding='utf-8') as f:
        rd = csv.DictReader(f); cols = rd.fieldnames
        aps = [r for r in rd if r['iso_country'] == 'JP']
    refs = {r['id'] for r in aps}
    with open(rw_csv, encoding='utf-8') as f:
        rd = csv.DictReader(f); rcols = rd.fieldnames
        rws = [r for r in rd if r['airport_ref'] in refs]
    for name, c, rows in (('oa_airports_jp.csv', cols, aps), ('oa_runways_jp.csv', rcols, rws)):
        with open(os.path.join(RAW, name), 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=c); w.writeheader(); w.writerows(rows)
    print(f'日本の空港 {len(aps)} 行・滑走路 {len(rws)} 行を {RAW} に書いた')


# ---------- 2. 滑走路の線 ----------
def load_aip():
    """AIP から作った今の線（_shared/ops_core.js の rwy。tools/ap_master_dump.mjs が aip_rwy.json に写す）"""
    p = os.path.join(RAW, 'aip_rwy.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    return {v['icao']: [[r[1], r[2], r[4], r[5], r[6] or f'{r[0]}/{r[3]}'] for r in v['rwy']] for v in d.values() if v.get('rwy')}


def load_oa():
    aps = list(csv.DictReader(open(os.path.join(RAW, 'oa_airports_jp.csv'), encoding='utf-8')))
    rws = {}
    for r in csv.DictReader(open(os.path.join(RAW, 'oa_runways_jp.csv'), encoding='utf-8')):
        rws.setdefault(r['airport_ref'], []).append(r)
    return aps, rws


def match_oa(a, oa_aps):
    """OurAirports の空港を探す：ICAO（ident・icao_code・gps_code）→ IATA → 2km 以内でいちばん近いもの"""
    icao = (a.get('icao') or '').strip()
    if icao:
        for r in oa_aps:
            if icao in (r['ident'], r['icao_code'], r['gps_code']):
                return r, 'icao'
    iata = (a.get('iata') or '').strip()
    if iata and len(iata) == 3:
        for r in oa_aps:
            if r['iata_code'] == iata:
                return r, 'iata'
    best, bd = None, 2000.0
    for r in oa_aps:
        try:
            d = dist_m(a['lat'], a['lon'], float(r['latitude_deg']), float(r['longitude_deg']))
        except ValueError:
            continue
        if d < bd:
            best, bd = r, d
    return (best, f'near{round(bd)}m') if best else (None, None)


def declination_w(lat):
    """日本の西偏（度）のおおよそ：沖縄 約5°・東京 約7.5°・北海道 約9°。滑走路の番号（磁方位）から真方位を出すときだけ使う"""
    return 5.0 + max(0.0, lat - 24.0) * 0.22


def dest_ll(lat, lon, brg, m):
    x, y = m * math.sin(math.radians(brg)), m * math.cos(math.radians(brg))
    return lat + y / 110_574.0, lon + x / (111_320.0 * math.cos(math.radians(lat)))


def oa_lines(rows, ap=None):
    """OurAirports の滑走路を線に。両端の座標があればそのまま（est=False）。
    どの滑走路にも両端の座標がない空港だけ、空港の点を真ん中に「長さ・向き」から線を作る（est=True）。
    向きは le_heading_degT（真方位）、なければ滑走路の番号×10（磁方位）から西偏を引く"""
    out, est = [], []
    for r in rows:
        if r['closed'] == '1':
            continue
        try:
            l = [float(r['le_latitude_deg']), float(r['le_longitude_deg']), float(r['he_latitude_deg']), float(r['he_longitude_deg'])]
            if dist_m(*l) >= 100:      # 端が同じ所（ヘリパッドなど）は線にしない
                out.append(l + [f"{r['le_ident']}/{r['he_ident']}"])
            continue
        except ValueError:
            pass
        if ap is None:
            continue
        try:
            length = float(r['length_ft']) * 0.3048
        except ValueError:
            continue
        lat0, lon0 = float(ap['latitude_deg']), float(ap['longitude_deg'])
        try:
            hdg = float(r['le_heading_degT'])
        except ValueError:
            num = ''.join(ch for ch in r['le_ident'] if ch.isdigit())
            if not num or length < 100:
                continue
            hdg = (int(num) * 10 - declination_w(lat0)) % 360
        a = dest_ll(lat0, lon0, (hdg + 180) % 360, length / 2); b = dest_ll(lat0, lon0, hdg, length / 2)
        est.append([a[0], a[1], b[0], b[1], f"{r['le_ident']}/{r['he_ident']}"])
    if out:
        return out, False
    return est, bool(est)


def load_overrides():
    p = os.path.join(OUT, 'overrides.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def cmd_build():
    airports, _ = load_master()
    aip = load_aip(); oa_aps, oa_rws = load_oa(); ov = load_overrides().get('airports', {})
    rows, problems, checks = [], [], []
    for a in airports:
        key = a.get('icao') or str(a['id'])
        o = ov.get(key) or ov.get(str(a['id'])) or {}
        oa, how = match_oa(a, oa_aps)
        ol, ol_est = oa_lines(oa_rws.get(oa['id'], []), oa) if oa else ([], False)
        src, lines = 'none', []
        if a.get('icao') in aip:
            src, lines = 'aip', aip[a['icao']]
            # 確かめ：AIP の線と OurAirports の線の向きを突き合わせる（本数・向きのずれ）
            if ol and not ol_est:
                hs = sorted(heading(l) for l in ol)
                for l in lines:
                    h = heading(l); dd = min(min(abs(h - x), 180 - abs(h - x)) for x in hs)
                    if dd > 3:
                        checks.append(f"{a['iata'] or key} {l[4]}：OurAirports に同じ向きの線がない（いちばん近い向きと {dd:.1f}°）")
                # AIP の線にない向きの滑走路（運用タブで使わない短い横風用など）は OurAirports から足す
                ah = [heading(l) for l in lines]
                extra = [l for l in ol if min(min(abs(heading(l) - x), 180 - abs(heading(l) - x)) for x in ah) > 3]
                if extra:
                    lines = lines + extra; src = 'aip+ourairports'
                    checks.append(f"{a['iata'] or key}：AIP にない向きの滑走路 {'・'.join(l[4] for l in extra)} を OurAirports から足した")
                if len(ol) != len(lines):
                    checks.append(f"{a['iata'] or key}：本数が AIP（足したあと）{len(lines)}・OurAirports {len(ol)}（AIP を使う）")
        elif ol:
            src, lines = ('ourairports-est' if ol_est else 'ourairports'), ol
        drop = set(o.get('exclude', []))
        lines = [l for l in lines if l[4] not in drop] + [list(x) for x in o.get('add', [])]
        if o.get('add'):
            src = src + '+manual' if src != 'none' else 'manual'
        norm, span = normalize(lines, a['lat'], a['lon']) if lines else (None, 0)
        rec = {'id': a['id'], 'iata': a.get('iata'), 'icao': a.get('icao'), 'name': a['name'], 'kind': a.get('extra_kind') or 'airport',
               'game_target': bool(a.get('game_target')), 'src': src, 'lines': norm or [], 'names': [l[4] for l in lines] if norm else [],
               'span_m': span}
        if oa:
            rec['oa_ident'] = oa['ident']; rec['oa_match'] = how
        if o.get('note'):
            rec['note'] = o['note']
        rows.append(rec)
        if not norm and a.get('extra_kind') != 'heli':
            problems.append(f"{a['id']} {a['name']}（{KIND_JA.get(a.get('extra_kind'), a.get('extra_kind'))}）：線がない（{('OurAirports ' + oa['ident'] + ' に滑走路の両端がない') if oa else 'OurAirports に見つからない'}）")
    # 確かめ：数字の範囲・86空港に1本以上
    for r in rows:
        for l in r['lines']:
            assert all(LO - 1e-9 <= x <= HI + 1e-9 for x in l), (r['name'], l)
    no86 = [r['name'] for r in rows if r['game_target'] and not r['lines']]
    doc = {
        'version': datetime.date.today().strftime('%Y%m%d'),
        'about': '印のカード用の滑走路の線。空港ごとに、線をまとめて 0.15〜0.85 の四角に収めた [u1,v1,u2,v2]（左上が 0,0・v は下向き・北が上・縦横の比は保つ）。長さは空港の大きさによらず四角いっぱい。span_m は四角の1辺が実際に何 m か',
        'sources': {'aip': '国の AIP の座標から作った今の線（_shared/ops_core.js）', 'aip+ourairports': 'AIP の線に、AIP の線にない向きの滑走路を OurAirports から足したもの', 'ourairports': 'OurAirports runways.csv（パブリックドメイン）の両端の座標',
                    'ourairports-est': 'OurAirports に両端の座標がない空港：長さと向き（なければ滑走路の番号×10から西偏を引いた向き）から、空港の点を真ん中に作った線（推定。向きは数度ずれることがある）',
                    'manual': 'data/ap_shape/overrides.json で手で足した線'},
        'airports': rows,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'runway_lines.json'), 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))
    write_preview(rows)
    from collections import Counter
    c = Counter(r['src'] for r in rows)
    sz = os.path.getsize(os.path.join(OUT, 'runway_lines.json'))
    print(f'{len(rows)} か所・出どころ {dict(c)}・{sz} バイト')
    print(f'86空港で線がない：{no86 or "なし"}')
    print('線がない番外編：'); [print('  ' + p) for p in problems if True]
    print('AIP と OurAirports の突き合わせ：'); [print('  ' + x) for x in checks]
    with open(os.path.join(OUT, 'build_log.txt'), 'w', encoding='utf-8') as f:
        f.write(f'{len(rows)} か所・出どころ {dict(c)}・{sz} バイト\n86空港で線がない：{no86 or "なし"}\n\n線がない所\n' + '\n'.join(problems)
                + '\n\nAIP と OurAirports の突き合わせ\n' + '\n'.join(checks) + '\n')
    if no86:
        sys.exit('86空港に線のない空港がある')


def svg(r):
    ls = ''.join(f'<line x1="{l[0]*160:.1f}" y1="{l[1]*160:.1f}" x2="{l[2]*160:.1f}" y2="{l[3]*160:.1f}"/>' for l in r['lines'])
    code = html.escape(r['iata'] or r['icao'] or '')
    return f'<svg viewBox="0 0 160 160" role="img" aria-label="{html.escape(r["name"])}の滑走路"><rect x="24" y="24" width="112" height="112" rx="6" class="box"/>{ls}<text x="80" y="152" text-anchor="middle">{code}</text></svg>'


def write_preview(rows):
    def cards(rs):
        out = []
        for r in rs:
            badge = {'aip': 'AIP', 'aip+ourairports': 'AIP+OA', 'ourairports': 'OA', 'ourairports-est': 'OA推定', 'none': 'なし'}.get(r['src'], r['src'])
            nm = ' '.join(r['names'])
            out.append(f'<figure class="c {"empty" if not r["lines"] else ""}">{svg(r)}<figcaption><b>{html.escape(r["name"])}</b>'
                       f'<span class="pill s-{r["src"].split("+")[0]}">{badge}</span><small>{len(r["lines"])}本・1辺 {r["span_m"]:,}m<br>{html.escape(nm)}</small></figcaption></figure>')
        return ''.join(out)
    main = [r for r in rows if r['game_target']]
    groups = [('86空港', main)] + [(KIND_JA[k], [r for r in rows if not r['game_target'] and (r['kind'] if r['kind'] != 'airport' else None) == k])
                                   for k in ('field', 'glider', 'mil', 'secret', 'heli')]
    rest = [r for r in rows if not r['game_target'] and r['kind'] == 'airport']
    if rest:
        groups.append(('そのほか', rest))
    body = ''.join(f'<h2>{t}<span>{len(rs)}か所・線あり {sum(1 for r in rs if r["lines"])}</span></h2><div class="g">{cards(rs)}</div>' for t, rs in groups if rs)
    page = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>滑走路の線の確かめ</title><style>
:root{{--bg:#f4f5f7;--card:#fff;--ink:#2b2f36;--sub:#8a919c;--line:#2b2f36;--box:#eef0f3;--aip:#1f6feb;--oa:#6b7280}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#14161a;--card:#1e2127;--ink:#e6e8eb;--sub:#8a919c;--line:#e6e8eb;--box:#272b32}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Sans JP",system-ui,sans-serif}}
main{{max-width:1200px;margin:0 auto;padding:16px}} h1{{font-size:20px;margin:8px 0}} p.lead{{color:var(--sub);font-size:13px;line-height:1.7}}
h2{{font-size:16px;margin:28px 0 10px}} h2 span{{font-size:12px;color:var(--sub);font-weight:400;margin-left:8px}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}}
.c{{margin:0;background:var(--card);border-radius:16px;box-shadow:0 1px 3px rgba(0,0,0,.08);padding:10px}} .c.empty{{opacity:.55}}
svg{{width:100%;height:auto;display:block}} .box{{fill:var(--box)}} line{{stroke:var(--line);stroke-width:5;stroke-linecap:round}}
svg text{{fill:var(--ink);font-size:14px;font-weight:800;letter-spacing:.08em}}
figcaption{{font-size:12px;line-height:1.5}} figcaption b{{display:block;font-size:12px}} small{{color:var(--sub);font-size:11px}}
.pill{{display:inline-block;margin:2px 0;padding:0 8px;border-radius:999px;font-size:10px;color:#fff;background:var(--oa)}} .s-aip{{background:var(--aip)}} .s-none{{background:#c2c7cf}} .s-ourairports-est{{background:#9a6b2f}} .s-manual{{background:#b7791f}}
</style></head><body><main><h1>滑走路の線の確かめ（{len(rows)}か所）</h1>
<p class="lead">tools/ap_shape.py build が作る確かめ用のページ。灰色の四角が 0.15〜0.85 の範囲。北が上。札：AIP＝運用タブと同じ AIP の座標から作った線／OA＝OurAirports（パブリックドメイン）の両端の座標／OA推定＝OurAirports の長さと向きから作った線（推定）／なし＝線が作れなかった。長さは空港の大きさによらず四角いっぱい（1辺が実際に何 m かを下に書いた）。</p>
{body}</main></body></html>'''
    with open(os.path.join(OUT, 'preview.html'), 'w', encoding='utf-8') as f:
        f.write(page)


# ---------- 3. 今の判定の範囲と国土数値情報の面を比べる ----------
def cmd_compare(c28_dir):
    from shapely.geometry import shape, Point, Polygon
    from shapely.ops import unary_union
    airports, terminals = load_master()
    gj = lambda n: json.load(open(os.path.join(c28_dir, f'C28-21_{n}.geojson'), encoding='utf-8'))['features']
    polys = gj('Airport'); tb = {f['properties']['C28_000']: f['geometry']['coordinates'] for f in gj('TerminalBuilding')}
    civil = [a for a in airports if a.get('game_target')]

    def to_local(geom, lat0, lon0):
        import shapely
        return shapely.transform(geom, lambda c: [local_xy(y, x, lat0, lon0) for x, y in c])

    def judge_area(a):
        """今の判定の範囲（judge.ts）：空港の点から radius_m の円 ∪ その空港のターミナルから 800m の円。平面（m）で"""
        parts = [Point(0, 0).buffer(a['radius_m'], 64)]
        for t in terminals:
            if t['airport_id'] == a['id']:
                parts.append(Point(*local_xy(t['lat'], t['lon'], a['lat'], a['lon'])).buffer(TERM_RADIUS_M, 64))
        return unary_union(parts)

    rows, used = [], set()
    for a in civil:
        p = Point(a['lon'], a['lat'])
        best, bd = None, 1e18
        for i, f in enumerate(polys):
            g = shape(f['geometry'])
            d = 0 if g.contains(p) else g.distance(p)
            if d < bd:
                best, bd = (i, f, g), d
        i, f, g = best
        dm = bd * 111_000
        if dm > 3000:
            rows.append({'a': a, 'poly': None}); continue
        used.add(i)
        loc = to_local(g, a['lat'], a['lon'])
        area = judge_area(a)
        cov = loc.intersection(area).area / loc.area if loc.area else 0
        far = max(math.hypot(x, y) for x, y in loc.exterior.coords)
        tid = f['properties'].get('C28_102', '').lstrip('#')
        tp = tb.get(tid)
        tdist = tin = None
        if tp:
            tx, ty = local_xy(tp[1], tp[0], a['lat'], a['lon'])
            tdist = math.hypot(tx, ty); tin = area.contains(Point(tx, ty)); r_tp = (tp[1], tp[0])
        else:
            r_tp = None
        # 面の外周を 300m 広げた形（Gemini の案の「バッファ」）が今の円にどれだけ入るか（参考）
        cov_b = loc.buffer(300).intersection(area).area / loc.buffer(300).area
        rows.append({'a': a, 'poly': f['properties'].get('C28_005'), 'dist_poly': round(dm), 'cov': cov, 'cov_b': cov_b, 'far': far,
                     'tdist': tdist, 'tin': tin, 'tpos': r_tp, 'area_km2': loc.area / 1e6})
    # 近い空港の重なり（番外編も入れる。判定は民間空港の範囲を先に見る＝locate）
    pairs = []
    for i, a in enumerate(airports):
        for b in airports[i + 1:]:
            d = dist_m(a['lat'], a['lon'], b['lat'], b['lon'])
            ov = a['radius_m'] + b['radius_m'] - d
            if ov > 0 and (a.get('game_target') or b.get('game_target')):
                pairs.append((ov, d, a, b))
    pairs.sort(key=lambda x: -x[0])

    def nm(a):
        return f"{a['name']}（{a.get('iata') or a.get('icao') or a['id']}）"
    L = ['# 今の判定の範囲と国土数値情報の空港の面の比べ（data/ap-shape・tools/ap_shape.py compare が作る）', '',
         '- 今の判定（関数 checkin・_shared/judge.ts の locate）：**円**。空港の点から radius_m 以内、またはその空港のターミナル（terminals の表・14か所）から 800m 以内なら範囲の中。民間空港の範囲を先に見て、外なら番外編の円を見る。複数の範囲に入るときは、ターミナルを含めていちばん近い民間空港',
         '- 比べた面：国土数値情報 空港データ（C28・令和3年）の空港の区域の面と、ターミナルビルの点。**利用約款を読めていないので、配るデータには使わず、この表の数字を作るためにだけ読んだ**（元のファイルはリポジトリに置いていない）',
         '- 「面のうち範囲に入る割合」は、空港の区域のうち今の円に入っている面積の割合。滑走路の端や誘導路の先が外れていても、印を押す人がいる所ではないので困らないことが多い。大事なのは「ターミナルビルの点」',
         '- **判定は変えていない**。下の「直し方の案」は案だけ（変えるのは本人の OK のあと）', '',
         '## 1. 86空港の表', '',
         '| 空港 | 半径 | 区域の面積 | 面のうち範囲に入る割合 | 面を300m広げた形の割合 | 点から面のいちばん遠い所 | ターミナルビルの点まで | ビルは範囲の中か |',
         '|---|---:|---:|---:|---:|---:|---:|---|']
    outside, low = [], []
    for r in sorted(rows, key=lambda r: (r.get('cov', 2), r['a']['id'])):
        a = r['a']
        if not r['poly']:
            L.append(f"| {nm(a)} | {a['radius_m']:,}m | 面が見つからない | | | | | |"); continue
        tin = '—' if r['tin'] is None else ('中' if r['tin'] else '**外**')
        if r['tin'] is False:
            outside.append(r)
        if r['cov'] < 0.6:
            low.append(r)
        td = '' if r['tdist'] is None else f"{r['tdist']:,.0f}m"
        L.append(f"| {nm(a)} | {a['radius_m']:,}m | {r['area_km2']:.2f}km² | {r['cov']*100:.0f}% | {r['cov_b']*100:.0f}% | {r['far']:,.0f}m | {td} | {tin} |")
    L += ['', '## 2. 範囲から外れる所', '']
    if outside:
        for r in outside:
            L.append(f"- **{nm(r['a'])}**：国土数値情報のターミナルビルの点が空港の点から {r['tdist']:,.0f}m（半径 {r['a']['radius_m']:,}m）。範囲の外")
    else:
        L.append('- 国土数値情報のターミナルビルの点は、86空港すべてで今の範囲の中')
    L += ['', '面のうち今の円に入るのが6割より少ない空港（滑走路が長い・区域が細長い所。ターミナルは中に入っている）：' + ('、'.join(f"{nm(r['a'])} {r['cov']*100:.0f}%" for r in low) or 'なし'), '',
          '展望デッキ・地下駅：国土数値情報には点がない。ターミナルビルの点が範囲の中で、展望デッキと地下駅はたいていターミナルビルの上か下にあるので、外れるおそれは小さい。'
          '本人の実地の記録（判定ルールの見直しの rejections：断った理由・最寄り空港・距離）で out_of_range が空港の近くで多い所があれば、そこを個別に見る（読むだけの SQL は報告の 3）', '',
          '## 3. 近い空港の重なり（円が重なる組。少なくとも片方が86空港）', '',
          '| 組 | 点どうしの距離 | 重なりの幅 | 今の判定での扱い |', '|---|---:|---:|---|']
    for ov, d, a, b in pairs:
        ca, cb = bool(a.get('game_target')), bool(b.get('game_target'))
        how = 'どちらも民間空港：重なる所では近い方（ターミナルを含めて）' if ca and cb else '民間空港の範囲を先に見る：重なる所はいつも民間空港の印'
        L.append(f"| {nm(a)} と {nm(b)} | {d:,.0f}m | {ov:,.0f}m | {how} |")
    if not pairs:
        L.append('| なし | | | |')
    L += ['', '## 4. 直し方の案（案だけ。判定は変えていない）', '',
          '- 案1（今のまま）：ターミナルビルが外れる空港がなければ、円のままでよい。円は端末でもサーバーでも同じ式で、屋内の位置のずれにも強い（半径が十分大きい）',
          '- 案2（外れる空港だけ・おすすめ）：外れる空港だけ terminals の表に1行足す（ターミナルから800m も範囲の中になる）。表の行を足すだけで判定の式は同じ。'
          '**radius_m を広げる形はすすめない**（radius_m は経営の空港の大きさ airport_size・co_size にも使われていて、経営の数字が動く）。'
          'terminals の行を足すと、その空港にも「ターミナルの印」（はじめてのターミナル）が出るので、出したくなければ stamp_m を小さく（例 1）して印は出さず範囲だけ広げる',
          '- 案3（面にする）：国土数値情報の面を 150〜300m 広げて判定に使う。重なる組（3節）がはっきり分かれる良さはあるが、約款の確認・端末とサーバーの両方の式の作り直し・テストが要る。今の円で困っている所が出てから',
          '- 重なる組は、今の「民間空港を先に・近い方」で決まっている。滑空場・基地と民間空港の重なりは、民間空港の印になる（番外編の印は民間空港の範囲の外でだけ押せる）']
    if outside:
        L += ['', '外れる空港に足す行の案（緯度経度は国土数値情報のターミナルビルの点。足す前に本人の実地か地図で確かめる）：', '']
        for r in outside:
            la, lo = r['tpos']
            L.append(f"- {nm(r['a'])}：terminals に id `{r['a']['iata']}-T`・airport_id {r['a']['id']}・緯度 {la:.6f}・経度 {lo:.6f}・stamp_m 1 の1行（ほかの列は今の行の形に合わせる）。ビルから800m が範囲に加わる")
        L.append('- 足すときは、画面の先の判定（src/index.html の nearest・ckJudge）も terminals を読んで同じ範囲になるかをチェックイン担当と確かめる（端末で先に「範囲の外」と出ないように）')
    p = os.path.join(ROOT, 'docs', 'pm', 'ap-shape-compare.md')
    with open(p, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print(f'{p} に書いた。外れる空港 {len(outside)}・6割未満 {len(low)}・重なる組 {len(pairs)}・面が見つからない {sum(1 for r in rows if not r["poly"])}')


if __name__ == '__main__':
    c = sys.argv[1] if len(sys.argv) > 1 else ''
    if c == 'subset':
        cmd_subset(sys.argv[2], sys.argv[3])
    elif c == 'build':
        cmd_build()
    elif c == 'compare':
        cmd_compare(sys.argv[2])
    else:
        print(__doc__)
