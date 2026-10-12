# 明朝体（Shippori Mincho）とドット文字（DotGothic16）から、アプリに出てくる文字だけを抜き出した小さなフォントを作る（どちらも SIL Open Font License 1.1）
#   python3 tools/build_font.py <文字の一覧のファイル> <出力フォルダ> [mincho|dot]
# 元のフォント（約8.5MB）がなければ Google Fonts のリポジトリから取ってくる。fonttools と brotli が必要：pip install fonttools brotli
import hashlib, os, sys, urllib.request
from fontTools import subset
FONTS = {
    "mincho": ("ShipporiMincho-ExtraBold.ttf", "https://github.com/google/fonts/raw/main/ofl/shipporimincho/ShipporiMincho-ExtraBold.ttf"),
    "dot": ("DotGothic16-Regular.ttf", "https://github.com/google/fonts/raw/main/ofl/dotgothic16/DotGothic16-Regular.ttf"),
}
HERE = os.path.dirname(os.path.abspath(__file__))
def main():
    chars_file, out_dir = sys.argv[1], sys.argv[2]
    kind = sys.argv[3] if len(sys.argv) > 3 else "mincho"
    fname, url = FONTS[kind]
    src = os.path.join(HERE, "fonts", fname)
    if not os.path.exists(src):
        os.makedirs(os.path.dirname(src), exist_ok=True); urllib.request.urlretrieve(url, src)
    text = open(chars_file, encoding="utf-8").read()
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]; opts.name_IDs = ["*"]; opts.notdef_outline = True; opts.desubroutinize = True
    font = subset.load_font(src, opts); sub = subset.Subsetter(opts); sub.populate(text=text); sub.subset(font)
    tmp = os.path.join(out_dir, f"_{kind}.woff2"); os.makedirs(out_dir, exist_ok=True); subset.save_font(font, tmp, opts)
    data = open(tmp, "rb").read(); name = f"{kind}-{hashlib.sha256(data).hexdigest()[:10]}.woff2"
    for f in os.listdir(out_dir):
        if f.startswith(f"{kind}-") and f.endswith(".woff2") and f != name: os.remove(os.path.join(out_dir, f))   # 古い版は消す
    os.replace(tmp, os.path.join(out_dir, name)); print(name)
if __name__ == "__main__": main()
