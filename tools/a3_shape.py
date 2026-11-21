# 羽田の3D の形のファイル（web/3d/hnd.json）を、OpenStreetMap のデータから1回だけ作る。
#   使い方：python3 tools/a3_shape.py <OSM の .osm ファイルを入れたフォルダ> web/3d/hnd.json
#   OSM のファイルは api.openstreetmap.org の /api/0.6/map?bbox=… で羽田のまわりを小分けに取ったもの（11/21 に1回だけ取った）。
#   出したファイルは OSM の「派生データベース」なので ODbL 1.0 で公開する（ファイルの中にも書く）。
#   座標は羽田の中心（A3_C）からの m。x＝東・z＝南（three.js の向きに合わせる）。整数に丸める。
#   滑走路はここに入れない（AIP JAPAN をもとにした HND_RWY をアプリが正にする）。
import sys, os, glob, json, math, xml.etree.ElementTree as ET

C = (35.5533, 139.7811)
KX = 111320 * math.cos(C[0] * math.pi / 180); KZ = 110574
def xz(lat, lon): return ((lon - C[1]) * KX, (C[0] - lat) * KZ)

def load(folder):
    nodes, ways, rels = {}, {}, {}
    for f in sorted(glob.glob(os.path.join(folder, '*.osm'))):
        try: root = ET.parse(f).getroot()
        except Exception: continue   # 「多すぎる」と断られたファイルは飛ばす
        for el in root:
            tg = {t.get('k'): t.get('v') for t in el.findall('tag')}
            if el.tag == 'node': nodes[el.get('id')] = (float(el.get('lat')), float(el.get('lon')))
            elif el.tag == 'way': ways[el.get('id')] = ([n.get('ref') for n in el.findall('nd')], tg)
            elif el.tag == 'relation': rels[el.get('id')] = ([(m.get('type'), m.get('ref'), m.get('role')) for m in el.findall('member')], tg)
    return nodes, ways, rels

def dp(pts, tol):   # ダグラス・ポイカーで点を減らす
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz)
    best, bi = 0, 0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        d = abs((p[0] - a[0]) * dz - (p[1] - a[1]) * dx) / L if L else math.hypot(p[0] - a[0], p[1] - a[1])
        if d > best: best, bi = d, i
    if best <= tol: return [a, b]
    return dp(pts[:bi + 1], tol)[:-1] + dp(pts[bi:], tol)

def ring(pts, tol):
    if len(pts) > 2 and pts[0] == pts[-1]: pts = pts[:-1]
    if len(pts) < 3: return None
    # 閉じた輪は、いちばん遠い2点で分けてから減らす
    far = max(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]))
    r = dp(pts[:far + 1], tol)[:-1] + dp(pts[far:] + [pts[0]], tol)[:-1]
    return r if len(r) >= 3 else None

def area(r): return abs(sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r)))) / 2
def flat(r): return [v for p in r for v in (round(p[0]), round(p[1]))]
def inside(p, poly):
    x, y = p; c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c

def chain(seqs):   # 端がつながる線を1本にする（向きが逆のものもつなぐ）
    seqs = [list(s) for s in seqs if s]; out = []
    while seqs:
        cur = seqs.pop(0); grown = True
        while grown and cur[0] != cur[-1]:
            grown = False
            for i, s in enumerate(seqs):
                if s[0] == cur[-1]: cur += s[1:]
                elif s[-1] == cur[-1]: cur += s[::-1][1:]
                elif s[-1] == cur[0]: cur = s + cur[1:]
                elif s[0] == cur[0]: cur = s[::-1] + cur[1:]
                else: continue
                seqs.pop(i); grown = True; break
        out.append(cur)
    return out

def main(folder, out):
    nodes, ways, rels = load(folder)
    P = lambda nd: [xz(*nodes[n]) for n in nd if n in nodes]
    full = lambda nd: all(n in nodes for n in nd)
    res = {'v': 1, 'license': 'ODbL-1.0', 'attribution': '© OpenStreetMap contributors',
           'note': 'OpenStreetMap のデータを加工して作成（2026-11-21 取得）。羽田の中心 35.5533,139.7811 からの m（x＝東・z＝南）。滑走路は含まない',
           'origin': list(C)}
    # 海岸線：閉じた輪は島（D 滑走路の島など）。羽田の島から大田区・川崎へ続く開いた線は、西の内陸を回って閉じる（陸は線の左）
    coast = chain([ways[w][0] for w in ways if ways[w][1].get('natural') == 'coastline' and full(ways[w][0])])
    land = []
    for s in coast:
        pts = P(s)
        if s[0] == s[-1]: r = ring(pts, 4)
        else:
            if len(pts) < 50: continue   # 取った範囲の端で切れた小さな線は使わない
            a, b = pts[0], pts[-1]
            # 終わり（北）から西へ、南へ回って始め（南）に戻る。取った範囲の外は大まかな四角（遠くは霞で見えない）
            far = [(b[0], -9000), (-14000, -9000), (-14000, 7000), (a[0] - 2500, 7000), (a[0] - 2500, a[1])]
            r = ring(pts + far, 4)
        if r: land.append(flat(r))
    res['land'] = land
    # 川と運河（多摩川・京浜運河など）。関係（multipolygon）の外側の線をつなぐ
    water = []
    for rid, (mem, t) in rels.items():
        if t.get('natural') != 'water' and t.get('waterway') != 'riverbank': continue
        outs = [ways[r][0] for ty, r, role in mem if ty == 'way' and role == 'outer' and r in ways]   # 取った範囲の外の点は落とす（範囲の端でまっすぐ切れる）
        for s in chain(outs):
            if s[0] != s[-1] and t.get('water') != 'river': continue
            r = ring(P(s), 4)
            if r and area(r) > 20000: water.append(flat(r))
    for w, (nd, t) in ways.items():
        if t.get('natural') == 'water' and nd and nd[0] == nd[-1] and full(nd):
            r = ring(P(nd), 4)
            if r and area(r) > 20000: water.append(flat(r))
    res['water'] = water
    # 空港の範囲
    ad = next((w for w, (nd, t) in ways.items() if t.get('aeroway') == 'aerodrome' and t.get('iata') == 'HND'), None)
    if not ad:
        rel = next(m for m, t in rels.values() if t.get('aeroway') == 'aerodrome' and t.get('iata') == 'HND')
        ad = next(r for ty, r, role in rel if role == 'outer')
    adr = ring(P(ways[ad][0]), 3); res['aero'] = flat(adr)
    within = lambda nd: (lambda p: bool(p) and inside((sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p)), adr))(P(nd))
    # 芝生・駐機場（エプロン）
    res['grass'] = [flat(r) for nd, t in ways.values() if (t.get('landuse') == 'grass' or t.get('surface') == 'grass') and nd and nd[0] == nd[-1] and full(nd) and within(nd) for r in [ring(P(nd), 3)] if r and area(r) > 1500]
    aprons = [ways[w][0] for w in ways if ways[w][1].get('aeroway') == 'apron']
    for m, t in rels.values():
        if t.get('aeroway') == 'apron': aprons += [ways[r][0] for ty, r, role in m if role == 'outer' and r in ways]
    res['apron'] = [flat(r) for nd in aprons if nd and full(nd) for s in chain([nd]) if s[0] == s[-1] for r in [ring(P(s), 2)] if r]
    # 誘導路（線と幅 m）
    twy = []
    for nd, t in ways.values():
        a = t.get('aeroway')
        if a not in ('taxiway', 'taxilane') or nd[0] == nd[-1] and t.get('area') == 'yes': continue
        pts = P(nd)
        if len(pts) < 2 or not within(nd): continue
        try: wd = float((t.get('width') or '').replace('m', '').strip())
        except ValueError: wd = 0
        wd = wd if 5 <= wd <= 60 else (23 if a == 'taxiway' else 15)
        twy.append([round(wd)] + flat(dp(pts, 2)))
    res['twy'] = twy
    # 建物（空港の中）：高さは height → 階数×4.2m → 種類ごとのおおよそ
    bld = []; tower = None
    for w, (nd, t) in ways.items():
        if not ('building' in t or t.get('aeroway') in ('terminal', 'hangar')) or not nd or nd[0] != nd[-1] or not full(nd) or not within(nd): continue
        if 'building:part' in t and 'building' not in t: continue
        r = ring(P(nd), 1.5)
        if not r or area(r) < 60: continue
        h = None
        try: h = float((t.get('height') or '').replace('m', '').strip())
        except ValueError: pass
        if h is None and t.get('building:levels'):
            try: h = float(t['building:levels']) * 4.2
            except ValueError: pass
        kind = 't' if t.get('aeroway') == 'terminal' else 'h' if t.get('aeroway') == 'hangar' or t.get('building') == 'hangar' else 'b'
        if t.get('man_made') == 'tower' and '管制塔' in (t.get('name') or ''):
            tower = [round(sum(p[0] for p in r) / len(r)), round(sum(p[1] for p in r) / len(r))]; continue
        if h is None: h = 26 if kind == 't' else 28 if kind == 'h' else 12
        bld.append([kind, round(min(h, 60), 1)] + flat(r))
    # 第2旅客ターミナル（関係で描かれている）
    for m, t in rels.values():
        if t.get('aeroway') == 'terminal' or (t.get('building') and 'ターミナル' in (t.get('name') or '')):
            for s in chain([ways[r][0] for ty, r, role in m if role == 'outer' and r in ways and full(ways[r][0])]):
                if s[0] == s[-1]:
                    r = ring(P(s), 1.5)
                    if r: bld.append(['t', 26] + flat(r))
    res['bld'] = bld; res['tower'] = tower
    s = json.dumps(res, ensure_ascii=False, separators=(',', ':'))
    os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'w', encoding='utf-8').write(s)
    print(out, len(s), 'bytes', {k: len(v) for k, v in res.items() if isinstance(v, list)})

if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
