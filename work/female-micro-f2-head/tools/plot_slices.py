import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, meshlib as ml, slices as sl
from PIL import Image, ImageDraw, ImageFont
src = sys.argv[1]; out = sys.argv[2]
extra = sys.argv[3:]   # optional extra npz to overlay
V, F, d = ml.load(src); T = ml.tri_fan(F)
meshes = [(V, T, (255, 90, 60))]
cols = [(80, 200, 255), (120, 255, 120)]
for k, e in enumerate(extra):
    V2, F2, _ = ml.load(e); meshes.append((V2, ml.tri_fan(F2), cols[k]))
zs = [1.430, 1.440, 1.450, 1.460, 1.470, 1.480, 1.495, 1.510]
S = 9.0      # px per mm
x0, x1, y0, y1 = -110, 110, -135, 30     # mm window (x right, y: front (neg) at bottom)
Wd, Ht = int((x1 - x0) * S), int((y1 - y0) * S)
cells = []
for z in zs:
    im = Image.new('RGB', (Wd, Ht), (24, 24, 26)); dr = ImageDraw.Draw(im)
    for gx in range(-100, 101, 20): dr.line([((gx - x0) * S, 0), ((gx - x0) * S, Ht)], fill=(45, 45, 50))
    for gy in range(-120, 21, 20): dr.line([(0, (gy - y0) * S), (Wd, (gy - y0) * S)], fill=(45, 45, 50))
    for (Vm, Tm, col) in meshes:
        segs = sl.slice_axis(Vm, Tm, 2, z)
        for p, q in segs:
            dr.line([((p[0] * 1000 - x0) * S, (p[1] * 1000 - y0) * S), ((q[0] * 1000 - x0) * S, (q[1] * 1000 - y0) * S)], fill=col, width=2)
    dr.text((8, 6), f'z = {z:.3f} m   (grid 20 mm; +y toward the back; face at the top)', fill=(255, 255, 255))
    cells.append(im.transpose(Image.FLIP_TOP_BOTTOM))     # y negative (face front) up
cols_n = 2
rows_n = (len(cells) + 1) // 2
sheet = Image.new('RGB', (Wd * cols_n, Ht * rows_n), (10, 10, 10))
for k, c in enumerate(cells): sheet.paste(c, ((k % cols_n) * Wd, (k // cols_n) * Ht))
sheet.thumbnail((2400, 2400)); sheet.save(out); print(sheet.size)
