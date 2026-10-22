"""compare lip tones (relative to the cheek skin) plate vs renders at the plate front camera.  python3 lip_colors.py render_front.png [render_front2.png ...]"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, fl
from PIL import Image
src = np.asarray(Image.open(fl.PLATES / 'female_head_detail.jpg').convert('RGB')).astype(float)
BOX = (85, 55, 430, 342); UP = 3
def plate_px(x_mm, z, rad=1):
    c = int(round(fl.CXF + x_mm / 1000 / fl.K)); r = int(round(float(fl.rowz(z))))
    return src[r - rad:r + rad + 1, c - rad:c + rad + 1].reshape(-1, 3).mean(0)
def render_px(img, x_mm, z, rad=3):
    c = (fl.CXF + x_mm / 1000 / fl.K - BOX[0]) * UP; r = (float(fl.rowz(z)) - BOX[1]) * UP
    c = int(round(c)); r = int(round(r)); a = img[r - rad:r + rad + 1, c - rad:c + rad + 1]
    return a.reshape(-1, 4)[:, :3].mean(0)
pts = {'upper lip (x0,z1.4790)': (0, 1.4790), 'upper lip (x8)': (8, 1.4793), 'seam (x0)': (0, 1.4758), 'lower lip top (x0,z1.4715)': (0, 1.4715), 'lower lip mid (x0,z1.4685)': (0, 1.4685),
       'lower lip low (x0,z1.4655)': (0, 1.4655), 'lower lip (x12,z1.4685)': (12, 1.4685), 'skin cheek (x25,z1.4650)': (25, 1.4650), 'chin (x0,z1.4450)': (0, 1.4450)}
imgs = []
for p in sys.argv[1:]:
    im = Image.open(p).convert('RGBA'); a = np.asarray(im).astype(float); imgs.append((p, a))
skin_p = plate_px(25, 1.4650)
print('%-30s %-22s' % ('landmark', 'PLATE rgb | ratio-to-skin'), *[' %-26s' % p.split('/')[-1] for p, _ in imgs])
for nm, (x, z) in pts.items():
    pp = plate_px(x, z); row = '%-30s (%3.0f %3.0f %3.0f) (%.2f %.2f %.2f)' % (nm, *pp, *(pp / skin_p))
    for p, a in imgs:
        sk = render_px(a, 25, 1.4650); v = render_px(a, x, z)
        row += '   (%3.0f %3.0f %3.0f) (%.2f %.2f %.2f)' % (*v, *(v / sk))
    print(row)
