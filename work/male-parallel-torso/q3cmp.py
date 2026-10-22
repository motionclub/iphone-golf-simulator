"""plate-sheet 3/4 torso crops vs mesh yaw renders. python3.13 q3cmp.py out.png <dir with yaw*.png> """
import sys
from PIL import Image
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
SH = Image.open(R + 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
d = sys.argv[2]; out = sys.argv[1]
# (label, plate centre x, bottom-row sole y, mesh file)
ITEMS = [('3/4 front L', 183, 672, 'yaw38_2.0_0.95'), ('3/4 front R', 480, 672, 'yaw-38_2.0_0.95'), ('3/4 back L', 788, 672, 'yaw142_2.0_0.95'), ('3/4 back R', 1090, 672, 'yaw-142_2.0_0.95')]
K = 0.00582; ZT, ZB = 1.42, 0.74
cols = []
for lab, cx, sole, f in ITEMS:
    y0 = int(sole - ZT / K); y1 = int(sole - ZB / K); pl = SH.crop((cx - 62, y0, cx + 62, y1)); H = 560
    pl = pl.resize((int(pl.width * H / pl.height), H), Image.LANCZOS)
    m = Image.open(f'{d}/{f}.png').convert('RGB')           # 1000px = 2.0 m ; target z 0.95 at row 500
    py = lambda z: 500 - (z - 0.95) / 0.002
    mm_ = m.crop((500 - 62 * K / 0.002, int(py(ZT)), 500 + 62 * K / 0.002, int(py(ZB)))); mm_ = mm_.resize((int(mm_.width * H / mm_.height), H), Image.LANCZOS)
    col = Image.new('RGB', (pl.width + mm_.width + 6, H)); col.paste(pl, (0, 0)); col.paste(mm_, (pl.width + 6, 0)); cols.append(col)
s = Image.new('RGB', (sum(c.width for c in cols) + 10 * 3, H), (0, 0, 0)); x = 0
for c in cols: s.paste(c, (x, 0)); x += c.width + 10
s.save(out); print(out, s.size)
