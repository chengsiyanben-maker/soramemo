# tools/ap_shape.py の滑走路の線のテスト（ネットにはつながない）
#   python3 -m unittest discover -s tests/tools
import json, math, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import ap_shape as ap

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


class NormalizeTest(unittest.TestCase):
    def test_box_and_aspect(self):
        # 南北 2km・東西 1km の2本：長い辺（南北）が 0.15〜0.85 いっぱい、東西は真ん中に寄る
        lat0, lon0 = 35.0, 139.0
        dlat = 1000 / 110_574.0
        dlon = 500 / (111_320.0 * math.cos(math.radians(lat0)))
        lines = [[lat0 - dlat, lon0 - dlon, lat0 + dlat, lon0 - dlon, "a"], [lat0 - dlat, lon0 + dlon, lat0 + dlat, lon0 + dlon, "b"]]
        out, span = ap.normalize(lines, lat0, lon0)
        self.assertAlmostEqual(span, 2000, delta=2)
        for l in out:
            for x in l:
                self.assertTrue(0.15 - 1e-9 <= x <= 0.85 + 1e-9)
        self.assertAlmostEqual(out[0][1], 0.85, places=3)   # 南の端が下（v は下向き）
        self.assertAlmostEqual(out[0][3], 0.15, places=3)
        self.assertAlmostEqual(out[0][0], 0.325, places=2)  # 東西 1km は 0.35 の幅で真ん中に
        self.assertAlmostEqual(out[1][0], 0.675, places=2)

    def test_cos_correction_keeps_angle(self):
        # 北緯43度で北東45度の線：横を縮めないと角度がずれる。補正すれば u と v の差が同じ
        lat0, lon0 = 43.0, 141.0
        a = ap.dest_ll(lat0, lon0, 225, 1000); b = ap.dest_ll(lat0, lon0, 45, 1000)
        out, _ = ap.normalize([[a[0], a[1], b[0], b[1], "x"]], lat0, lon0)
        u1, v1, u2, v2 = out[0]
        self.assertAlmostEqual(abs(u2 - u1), abs(v2 - v1), places=2)

    def test_degenerate(self):
        self.assertEqual(ap.normalize([[35, 139, 35, 139, "p"]], 35, 139), (None, 0))


class OaLinesTest(unittest.TestCase):
    def row(self, **k):
        base = {"closed": "0", "le_ident": "12", "he_ident": "30", "length_ft": "6562", "le_heading_degT": "",
                "le_latitude_deg": "", "le_longitude_deg": "", "he_latitude_deg": "", "he_longitude_deg": ""}
        base.update(k); return base

    def test_ends_win_and_closed_skipped(self):
        r1 = self.row(le_latitude_deg="35.0", le_longitude_deg="139.0", he_latitude_deg="35.01", he_longitude_deg="139.01")
        r2 = self.row(closed="1", le_latitude_deg="35.0", le_longitude_deg="139.0", he_latitude_deg="35.02", he_longitude_deg="139.0")
        r3 = self.row()   # 端なし：両端のある滑走路があれば推定は使わない
        out, est = ap.oa_lines([r1, r2, r3], {"latitude_deg": "35.0", "longitude_deg": "139.0"})
        self.assertEqual(len(out), 1); self.assertFalse(est)

    def test_estimate_from_number(self):
        out, est = ap.oa_lines([self.row()], {"latitude_deg": "35.5", "longitude_deg": "139.0"})
        self.assertTrue(est); self.assertEqual(len(out), 1)
        h = ap.heading(out[0])
        self.assertAlmostEqual(h, (120 - ap.declination_w(35.5)) % 180, delta=0.5)   # 番号12＝磁方位120°から西偏を引く
        self.assertAlmostEqual(ap.dist_m(*out[0][:4]), 6562 * 0.3048, delta=5)


class BuiltDataTest(unittest.TestCase):
    """data/ap_shape/runway_lines.json（コミットした出来上がり）の確かめ"""
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(ROOT, "data", "ap_shape", "runway_lines.json"), encoding="utf-8"))
        cls.by = {r["iata"]: r for r in cls.d["airports"] if r["iata"]}

    def test_all_86_have_lines_in_box(self):
        main = [r for r in self.d["airports"] if r["game_target"]]
        self.assertEqual(len(main), 86)
        for r in main:
            self.assertTrue(r["lines"], r["name"])
        for r in self.d["airports"]:
            for l in r["lines"]:
                self.assertEqual(len(l), 4)
                self.assertTrue(all(0.15 - 1e-9 <= x <= 0.85 + 1e-9 for x in l), r["name"])

    def test_aip_preferred(self):
        self.assertEqual(self.by["HND"]["src"], "aip"); self.assertEqual(len(self.by["HND"]["lines"]), 4)
        self.assertEqual(len(self.by["FUK"]["lines"]), 2)       # 第2滑走路（AIP の線）
        self.assertEqual(self.by["SDJ"]["src"], "aip+ourairports"); self.assertEqual(len(self.by["SDJ"]["lines"]), 2)

    def test_small(self):
        self.assertLess(os.path.getsize(os.path.join(ROOT, "data", "ap_shape", "runway_lines.json")), 60_000)


if __name__ == "__main__":
    unittest.main()
