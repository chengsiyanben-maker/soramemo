# テスト用の搭乗券（IATA BCBP）の画像を、今日の日付に合わせて作る
#   pip install pdf417gen segno
import os
from datetime import date
def make(out_dir):
    import pdf417gen, segno
    os.makedirs(out_dir, exist_ok=True)
    def bcbp(frm, to, car, fno, jd, seat):
        return f"M1{'TANAKA/TARO':<20}E{'ABC123':<7}{frm}{to}{car:<3}{fno:<5}{jd:03d}Y{seat:>4}{'0045':<5}0" + "00"
    t = date.today(); jd_past = (date(t.year, 6, 1) - date(t.year, 1, 1)).days + 1; jd_future = (t - date(t.year, 1, 1)).days + 1 + 3
    codes = {'pdf_past': bcbp('HND','CTS','JL','0501',jd_past,'012A'), 'qr_future': bcbp('HND','OKA','NH','0995',jd_future,'033K'), 'pdf_manual': bcbp('ITM','FUK','JL','2051',jd_past+5,'005C')}
    for k, v in codes.items():
        assert len(v) == 60
        if k.startswith('qr'): segno.make(v, error='m').save(os.path.join(out_dir, f'{k}.png'), scale=8, border=4)
        else: pdf417gen.render_image(pdf417gen.encode(v, columns=6), scale=3, ratio=3, padding=20).save(os.path.join(out_dir, f'{k}.png'))
    open(os.path.join(out_dir, 'jd.txt'), 'w').write(f"{jd_past} {jd_future}")
