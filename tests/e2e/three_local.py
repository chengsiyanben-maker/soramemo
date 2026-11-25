# 3D のテストが使う three.js を、各テストが自分で用意する（11/26 test-steady）。
#   前は t142 が作業用フォルダに置いたものを、ほかの 3D のテストが借りていた（t142 を先に・同じ作業用フォルダで流さないと飛ばしていた）。
#   作業用フォルダに無ければ CDN から1回だけ取る。同時に流しても壊れないよう、別名で書いてから名前を付け替える。
import os, urllib.request, tempfile
THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js'
def ensure_three(path):
    if os.path.exists(path) and os.path.getsize(path) > 100000: return True
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    try:
        with urllib.request.urlopen(THREE_URL, timeout=30) as r: data = r.read()
        if len(data) <= 100000: return False
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or '.', suffix='.part')
        with os.fdopen(fd, 'wb') as f: f.write(data)
        os.replace(tmp, path)
        return True
    except Exception as e:
        print('three.js を取れない:', e); return False
