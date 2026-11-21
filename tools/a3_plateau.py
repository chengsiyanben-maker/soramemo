# 羽田の3D の形のファイル（web/3d/hnd.json）に、国土交通省 PLATEAU（3D都市モデル）の建物を足す。
#   使い方：python3 tools/a3_plateau.py web/3d/hnd.json   （先に tools/a3_shape.py で OSM の形を作っておく）
#   取るもの：G空間情報センターの「3D都市モデル（Project PLATEAU）」大田区（2025年度）・川崎市（2022年度）の CityGML の建物（bldg）。
#     zip 全体（約540MB）は落とさず、羽田のまわりの3次メッシュのファイルだけを HTTP の範囲指定で読む（1回だけ。作業用のフォルダに置く）
#   利用条件：PLATEAU のサイトポリシー「3. コンテンツの利用」＝公共データ利用規約（PDL1.0）。CC BY 4.0 と互換、ODbL での利用も妨げない（2026-11-21 に原文で確かめた）。
#     出典：「3D都市モデル（Project PLATEAU）大田区（2025年度）・川崎市（2022年度）」（国土交通省）を加工して作成
#   使うのは建物の外形（lod0RoofEdge / lod0FootPrint）と計測高さ（measuredHeight）と用途（usage）だけ。テクスチャの絵は使わない
#   出すもの：
#     bld  … 空港の中の建物（OSM の空港の範囲の中）。[種類, 高さ, x, z, x, z, …]。種類は OSM のターミナル・格納庫に重なれば t・h、ほかは b
#     city … 空港の外の街（大田区・川崎の海沿い）。[用途, 高さ, x0, z0, dx, dz, …]（2点目からは前の点との差）。用途 0＝住宅 1＝事務所・店など 2＝工場・倉庫
#   小さな建物は落とす（中心から 3.5km までは 40m²、その先は 100m² 未満。高さ 20m 以上は残す）
import sys, os, io, json, math, zipfile, urllib.request, tempfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a3_shape import ring, area, inside

C = (35.5533, 139.7811); KX = 111320 * math.cos(C[0] * math.pi / 180); KZ = 110574
SRC = [  # (名前, CityGML の zip, 取る半径 m)
    ('大田区（2025年度）', 'https://assets.cms.plateau.reearth.io/assets/4d/0c7256-c7e6-40b9-ae86-5fd6d2d6bfd9/13111_ota-ku_pref_2025_citygml_1_op.zip', 7000),
    ('川崎市（2022年度）', 'https://assets.cms.plateau.reearth.io/assets/40/25bd0a-f174-4f55-a9bd-0e6868ece0ae/14130_kawasaki-shi_city_2022_citygml_4_op.zip', 6000),
]
B = '{http://www.opengis.net/citygml/building/2.0}'; G = '{http://www.opengis.net/gml}'

class Ranged(io.RawIOBase):   # zip の中の必要なファイルだけを範囲指定で読む
    def __init__(s, url):
        s.url, s.pos = url, 0
        s.size = int(urllib.request.urlopen(urllib.request.Request(url, method='HEAD')).headers['Content-Length'])
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s, o, w=0): s.pos = o if w == 0 else s.pos + o if w == 1 else s.size + o; return s.pos
    def readinto(s, b):
        if s.pos >= s.size or not len(b): return 0
        end = min(s.size, s.pos + len(b)) - 1
        d = urllib.request.urlopen(urllib.request.Request(s.url, headers={'Range': f'bytes={s.pos}-{end}'})).read()
        b[:len(d)] = d; s.pos += len(d); return len(d)

def mesh_center(code):   # 3次メッシュの中心
    p, u, q, v, r, w = int(code[0:2]), int(code[2:4]), int(code[4]), int(code[5]), int(code[6]), int(code[7])
    return (p + q / 8 + (r + .5) / 80) / 1.5, 100 + u + v / 8 + (w + .5) / 80
def dist(lat, lon): return math.hypot((lon - C[1]) * KX, (lat - C[0]) * KZ)

def fetch(url, R, folder):
    z = zipfile.ZipFile(io.BufferedReader(Ranged(url), buffer_size=1 << 20)); out = []
    for i in z.infolist():
        if '/bldg/' in i.filename and i.filename.endswith('.gml') and dist(*mesh_center(os.path.basename(i.filename)[:8])) <= R:
            p = os.path.join(folder, os.path.basename(i.filename))
            if not os.path.exists(p): open(p, 'wb').write(z.read(i))
            out.append(p)
    return out

def parse(path):
    for ev, el in ET.iterparse(path, events=('end',)):
        if el.tag != B + 'Building': continue
        h, use, pl = el.findtext(B + 'measuredHeight'), el.findtext(B + 'usage'), None
        for tag in ('lod0RoofEdge', 'lod0FootPrint'):
            e = el.find(B + tag)
            if e is not None and e.find('.//' + G + 'posList') is not None: pl = e.find('.//' + G + 'posList').text; break
        zs = [z for s in (el.find(B + 'lod1Solid'),) if s is not None for p in s.iter(G + 'posList') for z in list(map(float, p.text.split()))[2::3]]
        if pl is None and el.find(B + 'lod1Solid') is not None:   # 外形がなければ lod1 の箱のいちばん低い面
            low = min((p for p in el.find(B + 'lod1Solid').iter(G + 'posList')), key=lambda p: sum(list(map(float, p.text.split()))[2::3]), default=None)
            pl = low.text if low is not None else None
        if pl:
            v = list(map(float, pl.split()))
            pts = [((v[i + 1] - C[1]) * KX, (C[0] - v[i]) * KZ) for i in range(0, len(v), 3)]
            hh = float(h) if h and float(h) > 0 else (max(zs) - min(zs) if zs else 0) or 6
            yield pts, hh, use
        el.clear()

def kind_of(use): return 0 if use in ('411', '412', '413', '414', '415') else 2 if use in ('431', '441', '442', '443', '452', '454') else 1
def enc_delta(r):
    q = [(round(x), round(z)) for x, z in r]; o = [q[0][0], q[0][1]]
    for i in range(1, len(q)): o += [q[i][0] - q[i - 1][0], q[i][1] - q[i - 1][1]]
    return o
def poly(flat): return [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]

def main(shape_path, work=None):
    S = json.load(open(shape_path, encoding='utf-8'))
    work = work or os.path.join(tempfile.gettempdir(), 'a3-plateau'); os.makedirs(work, exist_ok=True)
    aero = poly(S['aero'])
    osm_t = [poly(b[2:]) for b in S['bld'] if b[0] == 't']; osm_h = [poly(b[2:]) for b in S['bld'] if b[0] == 'h']
    tw = S.get('tower')
    bld, city = [], []
    for si, (name, url, R) in enumerate(SRC):
        sub = os.path.join(work, str(si)); os.makedirs(sub, exist_ok=True)   # 大田区と川崎市でファイル名（メッシュ番号）が重なるので分ける
        for f in fetch(url, R, sub):
            for pts, h, use in parse(f):
                if len(pts) > 3 and pts[0] == pts[-1]: pts = pts[:-1]
                if len(pts) < 3: continue
                cx, cz = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts); A = area(pts)
                if tw and inside(tuple(tw), pts): continue   # 管制塔はアプリが形を作る
                if inside((cx, cz), aero):
                    r = ring(pts, 1.0)
                    if not r or A < 30: continue
                    k = 't' if any(inside((cx, cz), t) for t in osm_t) or any(inside((sum(p[0] for p in t) / len(t), sum(p[1] for p in t) / len(t)), pts) for t in osm_t) else 'h' if any(inside((cx, cz), t) for t in osm_h) else 'b'
                    bld.append([k, round(min(h, 120), 1)] + [v for p in r for v in (round(p[0]), round(p[1]))]); continue
                d = math.hypot(cx, cz)
                if d > R: continue
                if A < (40 if d < 3500 else 100) and h < 20: continue
                r = ring(pts, 1.5)
                if r: city.append([kind_of(use), round(min(h, 250))] + enc_delta(r))
    if len([b for b in bld if b[0] == 't']) < 3:   # 念のため：ターミナルが取れなければ OSM の建物のまま
        print('PLATEAU の空港の建物にターミナルが足りないので、空港の中は OSM のまま'); bld = S['bld']
    S['v'] = 2; S['bld'] = bld; S['city'] = city
    S['attribution'] = '© OpenStreetMap contributors／「3D都市モデル（Project PLATEAU）大田区（2025年度）・川崎市（2022年度）」（国土交通省）を加工して作成'
    S['note'] = 'OpenStreetMap のデータ（2026-11-21 取得）と PLATEAU の建物（外形・計測高さ・用途。2026-11-21 取得）を加工して作成。羽田の中心 35.5533,139.7811 からの m（x＝東・z＝南）。滑走路は含まない。city は2点目から前の点との差'
    S['plateau'] = 'PDL1.0（CC BY 4.0 互換・ODbL での利用も可）https://www.mlit.go.jp/plateau/site-policy/'
    s = json.dumps(S, ensure_ascii=False, separators=(',', ':'))
    open(shape_path, 'w', encoding='utf-8').write(s)
    import gzip
    print(shape_path, len(s), 'bytes / 圧縮', len(gzip.compress(s.encode(), 9)), {k: len(v) for k, v in S.items() if isinstance(v, list)})

if __name__ == '__main__': main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
