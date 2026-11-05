# 明朝体（Shippori Mincho）・ドット文字（DotGothic16）・標識の書体（Barlow Condensed）から、アプリに出てくる文字だけを抜き出した小さなフォントを作る（どちらも SIL Open Font License 1.1）
#   python3 tools/build_font.py <文字の一覧のファイル> <出力フォルダ> [mincho|dot]
# 文字を「英数字・かな・記号」と「漢字（文字コードの順に約100字ずつ）」の小分けのファイルに分ける。
# 出力は1行に1ファイル「ファイル名<TAB>unicode-range」。ブラウザは、画面に実際に出た文字を含むファイルだけを取りに行く。
# 元のフォント（約8.5MB）がなければ Google Fonts のリポジトリから取ってくる。fonttools と brotli が必要：pip install fonttools brotli
# 取得は raw.githubusercontent.com を先に使い、だめなら github.com に切り替える。一時的な失敗（504 など）は待ってから取り直す
import hashlib, os, sys, time, urllib.error, urllib.request
from fontTools import subset
FONTS = {
    "mincho": ("ShipporiMincho-ExtraBold.ttf", "ofl/shipporimincho/ShipporiMincho-ExtraBold.ttf"),
    "dot": ("DotGothic16-Regular.ttf", "ofl/dotgothic16/DotGothic16-Regular.ttf"),
    # 案内標識のような細長い書体（3レターコードと大きな数字だけに使う）。英数字と記号だけを抜き出す
    "sign": ("BarlowCondensed-Bold.ttf", "ofl/barlowcondensed/BarlowCondensed-Bold.ttf"),
}
# 取りに行く先（上から順に試す）。パスは Google Fonts のリポジトリの中の場所
MIRRORS = ["https://raw.githubusercontent.com/google/fonts/main/", "https://github.com/google/fonts/raw/main/"]
TRIES = 4            # 1つの取得先で試す回数
WAITS = [5, 15, 30]  # 取り直す前に待つ秒数（回を重ねるほど長く）
# ブラウザが標準で使う組版の機能だけ残す（縦書きなどは使わない）
FEATURES = ["kern", "liga", "clig", "calt", "ccmp", "locl", "mark", "mkmk", "palt", "tnum"]
CHUNK = 100
HERE = os.path.dirname(os.path.abspath(__file__))

def is_kanji(c):
    o = ord(c)
    return 0x3400 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF

def ranges(cps):
    cps = sorted(cps); out = []; a = b = cps[0]
    for c in cps[1:]:
        if c == b + 1: b = c; continue
        out.append((a, b)); a = b = c
    out.append((a, b))
    return ",".join(f"U+{a:X}" if a == b else f"U+{a:X}-{b:X}" for a, b in out)

def is_temporary(e):
    """待てば直りそうな失敗か（5xx・429・つながらない・切れた）。404 などは取り直しても同じなので別の取得先へ回す"""
    if isinstance(e, urllib.error.HTTPError): return e.code >= 500 or e.code == 429
    return isinstance(e, (urllib.error.URLError, TimeoutError, ConnectionError, OSError))

def fetch(path, dest, sleep=time.sleep, opener=urllib.request.urlopen):
    """フォントを dest に保存する。一時ファイルに落としてから置き換えるので、途中で切れても壊れたファイルは残らない"""
    errors = []
    for base in MIRRORS:
        url = base + path
        for n in range(TRIES):
            try:
                with opener(url, timeout=60) as r: data = r.read()
                if not data: raise ConnectionError("空の返事")
                tmp = dest + ".part"
                with open(tmp, "wb") as f: f.write(data)
                os.replace(tmp, dest)
                return url
            except Exception as e:
                errors.append(f"{url}（{n + 1}回目）：{e}")
                print(f"フォントの取得に失敗：{url}（{n + 1}/{TRIES}回目）：{e}", file=sys.stderr)
                if not is_temporary(e): break
                if n + 1 < TRIES: sleep(WAITS[min(n, len(WAITS) - 1)])
    raise RuntimeError("フォントを取れなかった：\n" + "\n".join(errors))

def main():
    chars_file, out_dir = sys.argv[1], sys.argv[2]
    kind = sys.argv[3] if len(sys.argv) > 3 else "mincho"
    fname, path = FONTS[kind]
    src = os.path.join(HERE, "fonts", fname)
    if not os.path.exists(src):
        os.makedirs(os.path.dirname(src), exist_ok=True); fetch(path, src)
    text = sorted(set(open(chars_file, encoding="utf-8").read()))
    if kind == "sign": text = [c for c in text if 0x20 <= ord(c) < 0x7f]   # 英数字と記号だけ（日本語の文字はゴシックのまま）
    kanji = [c for c in text if is_kanji(c)]
    groups = [[c for c in text if not is_kanji(c)]] + [kanji[i:i + CHUNK] for i in range(0, len(kanji), CHUNK)]
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for i, g in enumerate(groups):
        if not g: continue
        opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = FEATURES; opts.name_IDs = ["*"]
        opts.notdef_outline = True; opts.desubroutinize = True; opts.hinting = False
        font = subset.load_font(src, opts); sub = subset.Subsetter(opts); sub.populate(text="".join(g)); sub.subset(font)
        tmp = os.path.join(out_dir, f"_{kind}.woff2"); subset.save_font(font, tmp, opts)
        data = open(tmp, "rb").read(); name = f"{kind}{i}-{hashlib.sha256(data).hexdigest()[:10]}.woff2"
        os.replace(tmp, os.path.join(out_dir, name))
        rng = ranges([ord(c) for c in g])
        if i == 0 and kind != "sign": rng = "U+0-7F," + rng if not rng.startswith("U+20-7E") else "U+0-7F" + rng[len("U+20-7E"):]
        made.append((name, rng))
    keep = {n for n, _ in made}
    for f in os.listdir(out_dir):   # 古い版は消す
        if f.startswith(kind) and f.endswith(".woff2") and f not in keep: os.remove(os.path.join(out_dir, f))
    for n, r in made: print(f"{n}\t{r}")

if __name__ == "__main__": main()
