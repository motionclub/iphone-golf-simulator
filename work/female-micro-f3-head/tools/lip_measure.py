"""measure the plate's lip borders per column: top border (upper vermilion), seam (luminance minimum), bottom border (lower vermilion) in front-plate rows -> z.  python3 lip_measure.py -> data/lip_plate.json"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, fl
from PIL import Image
a = np.asarray(Image.open(fl.PLATES / 'female_head_detail.jpg').convert('RGB')).astype(float)
RG = a[..., 0] - a[..., 1]; L = a.mean(2)
THR = 55.0
res = []
for dc in range(-24, 25):                                  # columns around the centre, 1.537 mm each (+-37 mm)
    c = int(round(fl.CXF)) + dc; x = dc * fl.K
    col_rg = RG[205:240, c - 1:c + 2].mean(1); col_l = L[205:240, c - 1:c + 2].mean(1); rows = np.arange(205, 240)
    # seam: luminance minimum in rows 213..222 ; vermilion rows = contiguous R-G > THR around the seam
    win = (rows >= 213) & (rows <= 222)
    rs = rows[win][np.argmin(col_l[win])]
    k = int(rs - 205)
    top = k
    while top > 0 and col_rg[top - 1] > THR: top -= 1
    bot = k
    while bot < len(rows) - 1 and col_rg[bot + 1] > THR: bot += 1
    # sub-pixel crossings
    def cross(i0, i1):
        y0, y1 = col_rg[i0] - THR, col_rg[i1] - THR
        return rows[i0] + (y0 / (y0 - y1) if y0 != y1 else 0.5) * (rows[i1] - rows[i0])
    top_s = cross(max(top - 1, 0), top); bot_s = cross(bot, min(bot + 1, len(rows) - 1))
    # seam sub-pixel: parabola on luminance
    kk = int(np.clip(k, 1, len(rows) - 2)); l0, l1, l2 = col_l[kk - 1], col_l[kk], col_l[kk + 1]
    den = (l0 - 2 * l1 + l2); off = 0.5 * (l0 - l2) / den if abs(den) > 1e-9 else 0.0
    seam_s = rows[kk] + off
    res.append(dict(x=x, top=float(fl.zrow(top_s)), seam=float(fl.zrow(seam_s)), bot=float(fl.zrow(bot_s + 0.5))))
json.dump(res, open(fl.W / 'data/lip_plate_raw.json', 'w'), indent=0)
for r in res[::3]: print('x %+6.1f  top %.4f seam %.4f bot %.4f   thick up %.1f lo %.1f mm' % (r['x'] * 1000, r['top'], r['seam'], r['bot'], (r['top'] - r['seam']) * 1000, (r['seam'] - r['bot']) * 1000))
