# -*- coding: utf-8 -*-
# フライトと修行で使う 01・07 の部品
from common import *
def shots(L):
    from PIL import Image
    out = '<div class="shots">'
    k = 358 / 390
    for path, t, b, lab, mk in L:
        im = Image.open(path).crop((0, t, 390, b)); tmp = '/tmp/claude-0/crop.png'; im.save(tmp)
        out += '<div class="shot"><img src="%s" alt="%s">%s<p>%s</p></div>' % (img64(tmp, 72), lab, ''.join(mark(n, x * k, (y - t) * k) for n, x, y in mk), lab)
    return out + '</div>'
def mark(n, x, y):
    return '<i class="mk" style="left:%dpx;top:%dpx">%d</i>' % (x, y, n)


CSS01 = """.shots{margin-top:8px}.shot{position:relative;margin-top:10px}.shot img{width:100%;border-radius:18px;box-shadow:var(--shadow);display:block}
.shot p{font-size:13px;color:var(--sub);margin:6px 2px 0;text-align:center}
.mk{position:absolute;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;background:#C2410C;color:#fff;font:800 14px/26px var(--gothic);text-align:center;font-style:normal;box-shadow:0 0 0 3px #fff}
ol.pb{margin:16px 0 0;padding:0;list-style:none;counter-reset:p}ol.pb li{counter-increment:p;position:relative;padding:12px 14px 12px 50px;background:var(--card);border-radius:18px;box-shadow:var(--shadow);margin-top:8px;font-size:14px;line-height:1.65}
ol.pb li::before{content:counter(p);position:absolute;left:14px;top:12px;width:26px;height:26px;border-radius:50%;background:#C2410C;color:#fff;font:800 14px/26px var(--gothic);text-align:center}
ol.pb b{color:var(--strong)}"""
CSS07 = """.mp{display:grid;grid-template-columns:1fr 22px 1fr;gap:6px 6px;align-items:center;padding:12px 14px;font-size:14px}.mp .a{color:var(--sub)}.mp .b{font-weight:800;color:var(--strong)}.mp svg{color:var(--pale)}
.vrow{display:flex;align-items:center;gap:12px;min-height:60px;padding:6px 16px}.vrow + .vrow{box-shadow:inset 0 1px 0 var(--line2)}.vrow .n{font-family:var(--sign);font-weight:700;font-size:18px;color:var(--sub);width:16px}.vrow .tx{flex:1}.vrow .tx b{display:block;font-size:15px;color:var(--strong)}.vrow .tx small{font-size:13px;color:var(--sub)}"""
