# -*- coding: utf-8 -*-
# フライトと修行の改善案（design/flight-book・design/shugyo-book）の共通部品
# 空港の表は main の src/index.html の RAW（/tmp/claude-0/ap.json）、日本の輪郭は JP_OUTLINE（/tmp/claude-0/jp.txt）
import json, base64, math, os
AP = json.load(open('/tmp/claude-0/ap.json'))
JP = open('/tmp/claude-0/jp.txt').read().strip()
SIGN = base64.b64encode(open('/home/claude/soramemo/web/fonts/sign0-046a5a18b8.woff2', 'rb').read()).decode()
BY = {a[2]: dict(id=a[0], name=a[1], code=a[2], pref=a[3], lat=a[4], lon=a[5]) for a in AP if a[2] != '—'}

def short(code):
    n = BY[code]['name']
    if code in ('HND', 'ITM', 'NKM'): return n[n.index('（') + 1:n.index('）')]
    if '（' in n: n = n[:n.index('（')]
    return n.replace('空港', '').replace('国際', '') or n

def km(a, b):
    A, B = BY[a], BY[b]
    p1, p2 = math.radians(A['lat']), math.radians(B['lat'])
    dl = math.radians(B['lon'] - A['lon'])
    return 6371 * math.acos(min(1, math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)))

# 本番の地図と同じ投影（proj）。viewBox 0 0 400 420
def proj(code):
    a = BY[code]
    return ((a['lon'] - 122.5) * 16.4 * 0.82 + 20, (46.2 - a['lat']) * 17.6 + 14)

# 区間マイル（見本。計算ルールの文書の式に入れる値）
TPM = {('HND', 'CTS'): 510, ('HND', 'FUK'): 567, ('HND', 'OKA'): 984, ('OKA', 'ISG'): 247, ('HND', 'ITM'): 280,
       ('HND', 'KMJ'): 568, ('HND', 'HIJ'): 414, ('HND', 'KOJ'): 601, ('HND', 'MYJ'): 438, ('ITM', 'CTS'): 666,
       ('HND', 'NGS'): 610, ('HND', 'AKJ'): 576, ('HND', 'OIT'): 499, ('FUK', 'OKA'): 537, ('HND', 'HKD'): 424}
def tpm(a, b): return TPM.get((a, b)) or TPM.get((b, a))

# 見本の記録：2026年（今日は 11/9）。会社・便名・機種・登録記号・座席・出発と到着の時刻・運賃
WD = '月火水木金土日'
import datetime
F = []
def fl(m, d, a, b, co, no, typ, reg, dep, arr, seat, fare='セイバー'):
    dt = datetime.date(2026, m, d)
    k = km(a, b)
    h1, m1 = map(int, dep.split(':')); h2, m2 = map(int, arr.split(':'))
    mins = (h2 * 60 + m2) - (h1 * 60 + m1)
    F.append(dict(m=m, d=d, wd=WD[dt.weekday()], a=a, b=b, co=co, no=no, typ=typ, reg=reg, dep=dep, arr=arr,
                  mins=mins, km=round(k), seat=seat, fare=fare, tpm=tpm(a, b)))
fl(1, 12, 'HND', 'CTS', 'JAL', 'JL503', 'B767-300ER', 'JA654J', '07:30', '09:05', '23A')
fl(1, 14, 'CTS', 'HND', 'JAL', 'JL516', 'B767-300ER', 'JA656J', '17:30', '19:10', '24K')
fl(2, 7, 'HND', 'FUK', 'JAL', 'JL313', 'A350-900', 'JA06XJ', '07:00', '08:55', '31A')
fl(2, 8, 'FUK', 'HND', 'JAL', 'JL330', 'A350-900', 'JA09XJ', '18:00', '19:35', '30K')
fl(3, 1, 'HND', 'OKA', 'JAL', 'JL903', 'B767-300ER', 'JA615J', '06:25', '09:10', '22A')
fl(3, 1, 'OKA', 'ISG', 'JTA', 'NU603', 'B737-800', 'JA05RK', '10:30', '11:30', '8A')
fl(3, 3, 'ISG', 'OKA', 'JTA', 'NU612', 'B737-800', 'JA02RK', '12:10', '13:05', '9F')
fl(3, 3, 'OKA', 'HND', 'JAL', 'JL918', 'B767-300ER', 'JA619J', '14:00', '16:20', '25K')
fl(3, 20, 'HND', 'ITM', 'JAL', 'JL103', 'B787-8', 'JA840J', '07:30', '08:40', '18A')
fl(3, 20, 'ITM', 'HND', 'JAL', 'JL110', 'B787-8', 'JA843J', '19:00', '20:10', '19K')
fl(4, 18, 'HND', 'KMJ', 'ANA', 'NH641', 'B767-300', 'JA8674', '07:45', '09:35', '26A', 'スタンダード')
fl(4, 19, 'KMJ', 'HND', 'ANA', 'NH648', 'B767-300', 'JA8677', '18:40', '20:15', '27K', 'スタンダード')
fl(5, 23, 'HND', 'OIT', 'ANA', 'NH795', 'A321', 'JA131A', '07:20', '08:55', '12A', 'スタンダード')
fl(5, 25, 'OIT', 'HND', 'ANA', 'NH796', 'A321', 'JA136A', '08:04', '09:40', '14K', 'スタンダード')
fl(6, 13, 'HND', 'HIJ', 'JAL', 'JL253', 'B737-800', 'JA330J', '07:25', '08:50', '20A')
fl(6, 14, 'HIJ', 'HND', 'JAL', 'JL262', 'B737-800', 'JA337J', '19:30', '20:55', '21K')
fl(7, 4, 'HND', 'OKA', 'JAL', 'JL905', 'A350-900', 'JA03XJ', '07:15', '09:55', '35A')
fl(7, 5, 'OKA', 'HND', 'JAL', 'JL920', 'A350-900', 'JA11XJ', '15:00', '17:20', '34K')
fl(8, 10, 'HND', 'KOJ', 'ANA', 'NH619', 'B787-8', 'JA805A', '06:50', '08:45', '22A', 'スタンダード')
fl(8, 12, 'KOJ', 'HND', 'ANA', 'NH628', 'B787-8', 'JA812A', '19:45', '21:30', '23K', 'スタンダード')
fl(9, 21, 'HND', 'MYJ', 'JAL', 'JL431', 'B737-800', 'JA345J', '07:40', '09:10', '15A')
fl(9, 22, 'MYJ', 'HND', 'JAL', 'JL438', 'B737-800', 'JA349J', '18:10', '19:35', '16K')
fl(10, 11, 'HND', 'CTS', 'JAL', 'JL507', 'A350-900', 'JA07XJ', '08:30', '10:05', '30A')
fl(10, 12, 'CTS', 'HND', 'JAL', 'JL524', 'A350-900', 'JA08XJ', '20:00', '21:35', '31K')
fl(11, 1, 'HND', 'OKA', 'JAL', 'JL907', 'B787-9', 'JA861J', '07:50', '10:35', '24A')
fl(11, 3, 'OKA', 'HND', 'JAL', 'JL924', 'B787-9', 'JA866J', '16:00', '18:20', '25K')
F.reverse()   # 新しいものが上
# 予定（うすい金）と計画（うすい青）
YOTEI = [dict(m=11, d=22, a='HND', b='OKA', co='JAL', no='JL903', fare='セイバー'), dict(m=11, d=24, a='OKA', b='HND', co='JAL', no='JL918', fare='セイバー')]
KEIKAKU = [dict(m=12, d=6, a='HND', b='OKA', co='JAL', fare='セイバー'), dict(m=12, d=6, a='OKA', b='ISG', co='JTA', fare='セイバー'),
           dict(m=12, d=7, a='ISG', b='OKA', co='JTA', fare='セイバー'), dict(m=12, d=7, a='OKA', b='HND', co='JAL', fare='セイバー'),
           dict(m=12, d=19, a='HND', b='FUK', co='JAL', fare='セイバー'), dict(m=12, d=20, a='FUK', b='HND', co='JAL', fare='セイバー')]
def fop(f):
    # 計算ルール：FOP ＝ フライトマイル × 2 ＋ 搭乗ボーナス（セイバー 75%・200）
    t = tpm(f['a'], f['b'])
    return int(t * 0.75) * 2 + 200
JALF = [f for f in F if f['co'] in ('JAL', 'JTA')]
FOP_NOW = sum(fop(f) for f in JALF)
CNT_NOW = len(JALF)
FOP_Y = sum(fop(f) for f in YOTEI); FOP_K = sum(fop(f) for f in KEIKAKU)
def c(n): return '{:,}'.format(n)
TOTAL_KM = sum(f['km'] for f in F)
TOTAL_MIN = sum(f['mins'] for f in F)
CO_COL = {'JAL': '#C8102E', 'JTA': '#C8102E', 'ANA': '#1C4FA0'}

CSS_DAY = """
:root{--bg:#EEF1F5;--card:#FFFFFF;--ink:#1F2937;--strong:#111827;--sub:#4B5563;--mute:#5F6875;--pale:#7A8390;--wash:#F6F7F9;
--navy:#16233A;--acc:#2563EB;--jal:#C8102E;--ana:#1C4FA0;--line2:#E6E9EE;
--shadow:0 1px 2px rgba(17,24,39,.04),0 10px 26px -14px rgba(17,24,39,.22);
--yotei:#F3E3B5;--yotei-ink:#6B5414;--keikaku:#D6E4F7;--keikaku-ink:#24426E;--jisseki:#16233A}
"""
CSS_NIGHT = """
:root{--bg:#05070B;--card:#0D1218;--ink:#BCC6D1;--strong:#DCE3EA;--sub:#8996A7;--mute:#7D8A9B;--pale:#6E7B8C;--wash:#0A0F14;
--navy:#141B24;--acc:#DCE3EA;--jal:#BCC6D1;--ana:#BCC6D1;--line2:#1A222C;
--shadow:0 14px 30px -18px rgba(0,0,0,.9),inset 0 0 0 1px rgba(150,170,195,.10);
--glow1:#5FD993;--glow2:#F0AC4E;--sel-ring:rgba(220,227,234,.72);
--yotei:#2A2414;--yotei-ink:#D9C58E;--keikaku:#142033;--keikaku-ink:#A9C2E6;--jisseki:#DCE3EA;color-scheme:dark}
"""
CSS = """
@font-face{font-family:"Sign";src:url(data:font/woff2;base64,%s) format("woff2");font-weight:600 800;unicode-range:U+20-7E}
:root{--gothic:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Yu Gothic","Meiryo","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;--sign:"Sign","Barlow Condensed","Arial Narrow",var(--gothic)}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--bg);color:var(--ink);font-family:var(--gothic);font-size:15px;line-height:1.6;-webkit-text-size-adjust:100%%}
.phone{position:relative;max-width:420px;margin:0 auto;overflow:hidden;min-height:100vh}
.wrap{padding:6px 16px 120px}
.card{background:var(--card);border-radius:22px;box-shadow:var(--shadow)}
.u{font-family:var(--gothic);font-size:12px;font-weight:600;color:var(--mute);margin-left:3px;letter-spacing:0}
.num{font-family:var(--sign);font-weight:700;color:var(--strong);line-height:1;letter-spacing:.01em}
.top{display:flex;align-items:center;gap:8px;height:60px}
.top h1{font-size:26px;margin:0 auto 0 2px;color:var(--strong);letter-spacing:.04em}
.pill{min-height:44px;display:inline-flex;align-items:center;justify-content:center;gap:6px;font-size:14px;font-weight:700;color:var(--ink);background:var(--card);box-shadow:var(--shadow);border-radius:999px;padding:0 16px;flex:none;text-decoration:none}
.pill.dark{background:var(--navy);color:#fff}
.pill.ic{width:44px;padding:0}
.vband{display:flex;gap:6px;align-items:center;margin:10px 0 0}
.vband .pill{box-shadow:none;background:transparent;color:var(--sub);padding:0 14px;min-width:52px}
.vband .pill.on{background:var(--navy);color:#fff}
.vband .ed{margin-left:auto;width:44px;padding:0}
.seg{display:flex;background:#E2E6EC;border-radius:999px;padding:4px}
.seg b{flex:1;min-height:40px;display:flex;align-items:center;justify-content:center;border-radius:999px;font-size:14px;color:var(--sub);padding:0 14px}
.seg b.on{background:var(--card);color:var(--strong);box-shadow:var(--shadow)}
svg.i{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.tabs{position:fixed;left:50%%;transform:translateX(-50%%);bottom:14px;width:calc(min(420px,100vw) - 28px);height:64px;border-radius:999px;background:rgba(255,255,255,.96);box-shadow:0 10px 30px -8px rgba(17,24,39,.22),0 0 0 1px rgba(17,24,39,.04);display:flex;z-index:40}
.tabs b{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;font-size:13px;font-weight:700;color:#5F6875;position:relative}
.tabs b.on{color:#1F2937}.tabs b.on::after{content:"";position:absolute;bottom:5px;width:5px;height:5px;border-radius:50%%;background:var(--acc)}
.tabs svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.tabs b.on svg{stroke:var(--acc)}
.sec-h{display:flex;align-items:baseline;gap:8px;margin:22px 4px 8px;font-size:15px;font-weight:800;color:var(--strong)}
.sec-h small{font-size:13px;color:var(--sub);font-weight:600}
.sec-h .r{margin-left:auto;font-size:13px;color:var(--sub);font-weight:700}
.note{font-size:13px;color:var(--sub);margin:8px 4px 0;line-height:1.6}
.ann{position:relative;z-index:10;margin:24px 0 0;font:13px/1.7 var(--gothic);background:#FFF6DC;color:#4A3D10;padding:12px 14px;border-radius:16px}
.ann b{display:block}.ann ul{margin:4px 0 0;padding-left:1.2em}
.chip{display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;font-size:13px;font-weight:700;background:var(--wash);color:var(--sub)}
.row{display:flex;align-items:center;gap:12px;min-height:56px;padding:6px 16px}
.row .tx{flex:1;min-width:0}.row .tx b{display:block;color:var(--strong);font-size:15px;line-height:1.4}.row .tx small{display:block;color:var(--sub);font-size:13px;line-height:1.5}
.btn{min-height:52px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:800;background:var(--navy);color:#fff;margin-top:14px}
.btn.w{background:var(--card);color:var(--strong);box-shadow:var(--shadow)}
.dim{position:fixed;inset:0;background:rgba(15,23,42,.42);z-index:50}
.sheet{position:fixed;left:50%%;transform:translateX(-50%%);bottom:0;width:min(420px,100vw);background:var(--card);border-radius:28px 28px 0 0;box-shadow:0 -10px 40px -10px rgba(15,23,42,.4);z-index:60;padding:10px 16px 28px}
.grab{width:40px;height:5px;border-radius:3px;background:#D5DAE1;margin:2px auto 10px}
.sw{width:68px;height:34px;border-radius:999px;display:flex;align-items:center;flex:none;position:relative;font-size:13px;font-weight:800}
.sw.on{background:#16233A;color:#fff;padding-left:12px}
.sw.on::after{content:"";position:absolute;right:4px;top:4px;width:26px;height:26px;border-radius:50%%;background:#fff}
.sw.off{background:#E5E8EE;color:#4B5563;box-shadow:inset 0 0 0 1.5px #768090;justify-content:flex-end;padding-right:10px}
.sw.off::after{content:"";position:absolute;left:4px;top:4px;width:26px;height:26px;border-radius:50%%;background:#fff;box-shadow:inset 0 0 0 1.5px #768090}
.tag-y{background:var(--yotei);color:var(--yotei-ink)}.tag-k{background:var(--keikaku);color:var(--keikaku-ink)}
.mi{display:inline-block;width:4px;height:16px;border-radius:2px;vertical-align:-2px;margin-right:6px}
""" % SIGN
NIGHT_EXTRA = """
.pill{background:var(--card)}.pill.dark,.vband .pill.on{background:#141B24;color:var(--strong);box-shadow:inset 0 0 0 1.5px var(--sel-ring)}
.seg{background:#0A0F14;box-shadow:inset 0 0 0 1px rgba(150,170,195,.10)}
.seg b.on{background:#141B24;box-shadow:inset 0 0 0 1.5px var(--sel-ring)}
.tabs{background:#0D1218;box-shadow:0 10px 30px -6px rgba(0,0,0,.8),inset 0 0 0 1px rgba(150,170,195,.10)}
.tabs b{color:var(--sub)}.tabs b.on{color:var(--strong)}.tabs b.on svg{stroke:var(--strong)}.tabs b.on::after{background:var(--strong)}
.chip{background:#141B24;color:var(--ink)}
.ann{background:#1A1A10;color:#E9DFB8;box-shadow:inset 0 0 0 1px #4A4220}
.lit{color:var(--glow1)!important;text-shadow:0 0 6px rgba(95,217,147,.45)}
.amb{color:var(--glow2)!important}
.btn{background:transparent;color:var(--strong);box-shadow:inset 0 0 0 1.5px var(--sel-ring)}
"""
TAB_ICONS = [
 ('ホーム', '<path d="M3.5 10.5 12 4l8.5 6.5"/><path d="M5.5 9v10h4.5v-5.5h4V19h4.5V9"/>'),
 ('図鑑', '<path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5c-.8 0-1.5.5-1.5 1.2V5.5Z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5.5 1.5 1.2V5.5Z"/>'),
 ('フライト', '<path d="M10.5 13.5 4 11l1.4-1.4 7 1.1 3.9-3.9c.8-.8 2.1-.8 2.9 0s.8 2.1 0 2.9l-3.9 3.9 1.1 7L15 22l-2.5-6.5-3 3v2.5L8 22.5 6.5 19l-3.5-1.5L4.5 16h2.5l3-3"/>'),
 ('運用', '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="M12 12 18 6"/>'),
 ('修行', '<path d="M3.5 19.5h5v-5h5v-5h5v-5"/><path d="M15.5 4.5h3v3"/>')]
def tabs(on):
    return '<nav class="tabs" aria-label="画面の切り替え">' + ''.join('<b class="%s"><svg viewBox="0 0 24 24">%s</svg>%s</b>' % ('on' if k == on else '', v, k) for k, v in TAB_ICONS) + '</nav>'
I = {
 'scan': '<svg class="i" viewBox="0 0 24 24"><path d="M4 8V5.5C4 4.7 4.7 4 5.5 4H8M16 4h2.5c.8 0 1.5.7 1.5 1.5V8M20 16v2.5c0 .8-.7 1.5-1.5 1.5H16M8 20H5.5C4.7 20 4 19.3 4 18.5V16"/><path d="M7 12h10"/></svg>',
 'plus': '<svg class="i" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
 'back': '<svg class="i" viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg>',
 'pen': '<svg class="i" viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16z"/></svg>',
 'grip': '<svg class="i" viewBox="0 0 24 24"><path d="M5 9h14M5 15h14"/></svg>',
 'arrow': '<svg class="i" viewBox="0 0 24 24" style="width:18px;height:18px"><path d="M5 12h13M13 6l6 6-6 6"/></svg>',
 'share': '<svg class="i" viewBox="0 0 24 24"><path d="M12 15V4M7 9l5-5 5 5"/><path d="M5 14v5h14v-5"/></svg>',
}
def page(path, title, body, night=False, extra_css='', theme=''):
    html = ('<!doctype html>\n<html lang="ja"%s><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '<title>%s</title>\n<style>%s%s%s%s</style></head>\n<body><main class="phone">%s</main></body></html>\n') % (
        ' data-night="1"' if night else '', title, CSS_NIGHT if night else CSS_DAY, CSS, NIGHT_EXTRA if night else '', extra_css, body)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(html)

def jpmap(w=400, h=420, vb='0 0 400 420', night=False, land=None, coast=None):
    land = land or ('#0E151D' if night else '#F4F1E8')
    coast = coast or ('#2A3644' if night else '#C9C3B2')
    return '<path d="%s" fill="%s" stroke="%s" stroke-width=".8" stroke-linejoin="round"/>' % (JP, land, coast)

def img64(p, q=72, w=None):
    from PIL import Image
    import io
    im = Image.open(p).convert('RGB')
    if w: im = im.resize((w, round(im.height * w / im.width)))
    b = io.BytesIO(); im.save(b, 'JPEG', quality=q)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

def hm(mins): return '%d:%02d' % (mins // 60, mins % 60)
