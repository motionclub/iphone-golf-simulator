"""Rear-contour plots (sub-pixel plate vs BEFORE vs AFTER) with error stats. python3 profile_plot.py out.png zlo zhi [ylo yhi]  (renders from r/start_sil4 and r/FIN2_sil4)"""
import sys, json, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageDraw, ImageFont
from rearcmp import *
out, zlo, zhi = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); ylo = float(sys.argv[4]) if len(sys.argv) > 4 else 0.03; yhi = float(sys.argv[5]) if len(sys.argv) > 5 else 0.13
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
F = font(18); Fs = font(15)
S = 4200     # px per metre
W_ = int((yhi - ylo) * S) + 110; H_ = int((zhi - zlo) * S) + 150
im = Image.new('RGB', (W_ + 330, H_), (22, 22, 26)); d = ImageDraw.Draw(im)
def X(y): return 70 + (y - ylo) * S
def Y(z): return 40 + (zhi - z) * S
for z in np.arange(np.ceil(zlo * 20) / 20, zhi + 1e-9, 0.05):
    d.line([(60, Y(z)), (W_ - 30, Y(z))], fill=(55, 55, 75)); d.text((6, Y(z) - 9), f'z {z:.2f}', fill=(130, 130, 170), font=Fs)
for y in np.arange(np.ceil(ylo * 100) / 100, yhi, 0.01):
    d.line([(X(y), 36), (X(y), H_ - 80)], fill=(48, 48, 66)); d.text((X(y) - 12, H_ - 76), f'{y * 1000:.0f}', fill=(130, 130, 170), font=Fs)
d.text((W_ // 2 - 40, H_ - 52), 'rear depth y (mm, + = backwards)', fill=(170, 170, 200), font=Fs)
zs = np.arange(zlo, zhi + 1e-9, 0.002)
def curve(fn, color, w=2):
    pts = [(X(v), Y(z)) for z in zs for v in [fn(z)] if v is not None and np.isfinite(v)]
    if len(pts) > 1: d.line(pts, fill=color, width=w)
def plate(side):
    return lambda z: pl[side][int(round((z - 0.70) / 0.002))]
curve(plate('left'), (255, 205, 70), 3); curve(plate('right'), (255, 130, 40), 3)
curve(lambda z: render_edge('start', 'left', z), (110, 190, 255)); curve(lambda z: render_edge('start', 'right', z), (80, 150, 230))
curve(lambda z: render_edge('FIN2', 'left', z), (110, 255, 150)); curve(lambda z: render_edge('FIN2', 'right', z), (60, 215, 120))
# stats
def stats(tag, a, b):
    e = []
    for z in np.arange(a, b + 1e-9, 0.004):
        i = int(round((z - 0.70) / 0.002))
        for side, v in (('left', 'left'), ('right', 'right')):
            p = pl[side][i]; r = render_edge(tag, v, z)
            if p is not None and r is not None: e.append(r - p)
    e = np.array(e) * 1000; return float(np.mean(np.abs(e))), float(np.max(np.abs(e)))
a, b = (zlo + 0.02, zhi - 0.02)
sb, sa = stats('start', a, b), stats('FIN2', a, b)
x0 = W_ + 10
for k, (txt, col) in enumerate([('PLATE left (sub-pixel)', (255, 205, 70)), ('PLATE right (sub-pixel)', (255, 130, 40)), ('BEFORE (start) left', (110, 190, 255)), ('BEFORE (start) right', (80, 150, 230)), ('AFTER left', (110, 255, 150)), ('AFTER right', (60, 215, 120))]):
    d.line([(x0, 60 + k * 26), (x0 + 30, 60 + k * 26)], fill=col, width=3); d.text((x0 + 38, 51 + k * 26), txt, fill=(220, 220, 230), font=Fs)
d.text((x0, 240), f'z {a:.2f}-{b:.2f} contour error vs plate', fill=(255, 214, 120), font=F)
d.text((x0, 268), f'BEFORE  mean abs err {sb[0]:.1f} mm   max {sb[1]:.1f}', fill=(110, 190, 255), font=Fs)
d.text((x0, 292), f'AFTER   mean abs err {sa[0]:.1f} mm   max {sa[1]:.1f}', fill=(110, 255, 150), font=Fs)
d.text((x0, 330), '(plate edges: 50 % crossing of the', fill=(150, 150, 170), font=Fs); d.text((x0, 350), 'JPEG, sub-pixel; renders: 4x alpha)', fill=(150, 150, 170), font=Fs)
im.save(out); print(out, im.size, 'before', sb, 'after', sa)
json.dump(dict(range=[a, b], before_mean_abs_mm=sb[0], before_max_abs_mm=sb[1], after_mean_abs_mm=sa[0], after_max_abs_mm=sa[1]), open(out.replace('.png', '.json'), 'w'))
