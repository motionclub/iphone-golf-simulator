"""plate sheet 3/4 | baseline | candidate(s) for 4 yaw views, torso crop. python3.13 q3three.py out.png tag1 [tag2]  (needs r/<tag>q/yaw*.png from rt.py)"""
import sys
from PIL import Image
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
SH = Image.open(R + 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
out = sys.argv[1]; tags = sys.argv[2:]
K = 0.00582; ZT, ZB = 1.42, 0.74
ITEMS = [('3/4 front L', 183, 672, 'yaw38_2.0_0.95'), ('3/4 front R', 480, 672, 'yaw-38_2.0_0.95'), ('3/4 back L', 788, 672, 'yaw142_2.0_0.95'), ('3/4 back R', 1090, 672, 'yaw-142_2.0_0.95')]
cols = []
for lab, cx, sole, f in ITEMS:
    y0 = int(sole - ZT / K); y1 = int(sole - ZB / K); pl = SH.crop((cx - 62, y0, cx + 62, y1)); H = 470; pl = pl.resize((int(pl.width * H / pl.height), H), Image.LANCZOS)
    col = [pl]
    for t in tags:
        m = Image.open(f'r/{t}q/{f}.png').convert('RGB'); py = lambda z: 500 - (z - 0.95) / 0.002
        mm = m.crop((int(500 - 62 * K / 0.002), int(py(ZT)), int(500 + 62 * K / 0.002), int(py(ZB)))); mm = mm.resize((int(mm.width * H / mm.height), H), Image.LANCZOS); col.append(mm)
    c = Image.new('RGB', (sum(i.width for i in col) + 4 * (len(col) - 1), H)); x = 0
    for i in col: c.paste(i, (x, 0)); x += i.width + 4
    cols.append(c)
a = Image.new('RGB', (cols[0].width * 2 + 10, H * 2 + 8)); a.paste(cols[0], (0, 0)); a.paste(cols[1], (cols[0].width + 10, 0)); a.paste(cols[2], (0, H + 8)); a.paste(cols[3], (cols[0].width + 10, H + 8))
a.save(out); print(a.size)
