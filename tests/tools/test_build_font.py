# tools/build_font.py のフォントの取得のテスト（本物のネットにはつながない）
#   python3 -m unittest discover -s tests/tools
import io, os, sys, tempfile, unittest, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
try:
    import build_font as bf
except ImportError as e:   # fonttools が入っていないとき
    raise unittest.SkipTest(f"fonttools がない：{e}")

def err(code): return urllib.error.HTTPError("u", code, "x", {}, None)

class Opener:
    """決めた順に失敗か成功を返す作り物の取得"""
    def __init__(self, plan): self.plan, self.urls = list(plan), []
    def __call__(self, url, timeout=None):
        self.urls.append(url); x = self.plan.pop(0)
        if isinstance(x, Exception): raise x
        return io.BytesIO(x)

class FetchTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(); self.dest = os.path.join(self.dir, "f.ttf"); self.waits = []
    def run_fetch(self, plan):
        op = Opener(plan); url = bf.fetch("ofl/x/X.ttf", self.dest, sleep=self.waits.append, opener=op); return op, url

    def test_1_最初に_raw_から取る(self):
        op, url = self.run_fetch([b"FONT"])
        self.assertTrue(url.startswith("https://raw.githubusercontent.com/google/fonts/main/"))
        self.assertEqual(open(self.dest, "rb").read(), b"FONT"); self.assertEqual(self.waits, [])

    def test_2_504_は待ってから取り直す(self):
        op, url = self.run_fetch([err(504), err(502), b"FONT"])
        self.assertEqual(len(op.urls), 3); self.assertEqual(self.waits, [5, 15])
        self.assertIn("raw.githubusercontent.com", url)

    def test_3_raw_が続けてだめなら_github_com_へ切り替える(self):
        op, url = self.run_fetch([err(504)] * bf.TRIES + [b"FONT"])
        self.assertTrue(url.startswith("https://github.com/google/fonts/raw/main/"))
        self.assertEqual(open(self.dest, "rb").read(), b"FONT")

    def test_4_404_は取り直さず次の取得先へ(self):
        op, url = self.run_fetch([err(404), b"FONT"])
        self.assertEqual(len(op.urls), 2); self.assertEqual(self.waits, []); self.assertIn("github.com/google", url)

    def test_5_つながらない・空の返事も取り直す(self):
        op, url = self.run_fetch([urllib.error.URLError("timeout"), b"", b"FONT"])
        self.assertEqual(len(op.urls), 3)

    def test_6_全部だめならエラーで止まり_壊れたファイルを残さない(self):
        with self.assertRaises(RuntimeError) as c:
            self.run_fetch([err(504)] * (bf.TRIES * len(bf.MIRRORS)))
        self.assertIn("504", str(c.exception))
        self.assertFalse(os.path.exists(self.dest)); self.assertFalse(os.path.exists(self.dest + ".part"))

    def test_7_取得先の場所が正しい形(self):
        for fname, path in bf.FONTS.values():
            self.assertTrue(path.startswith("ofl/") and path.endswith(fname))

if __name__ == "__main__": unittest.main()
