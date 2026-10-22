"""Rear side-contour plots: plate (sub-pixel) vs renders of several tags, with error stats vs the plate.
python3 profile_plot3.py out.png zlo zhi tag:label:r,g,b [tag:label:r,g,b ...]      (renders from r/<tag>_sil4 ; 'start' = chat-9)"""
import sys, json, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageDraw, ImageFont
from rearcmp import render_edge, pl
out, zlo, zhi = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); series = []
for a in sys.argv[4:]:
    t, lab, col = a.split(':'); series.append((t, lab, tuple(int(c) for c in col.split(','))))
ylo, yhi = 0.03, 0.13
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
F = font(18); Fs = font(15); S = 4200
W_ = int((yhi - ylo) * S) + 110; H_ = int((zhi - zlo) * S) + 150
im = Image.new('RGB', (W_ + 360, H_), (22, 22, 26)); d = ImageDraw.Draw(im)
X = lambda y: 70 + (y - ylo) * S; Y = lambda z: 40 + (zhi - z) * S
for z in np.arange(np.ceil(zlo * 20) / 20, zhi + 1e-9, 0.05): d.line([(60, Y(z)), (W_ - 30, Y(z))], fill=(55, 55, 75)); d.text((6, Y(z) - 9), f'z {z:.2f}', fill=(130, 130, 170), font=Fs)
for y in np.arange(np.ceil(ylo * 100) / 100, yhi, 0.01): d.line([(X(y), 36), (X(y), H_ - 80)], fill=(48, 48, 66)); d.text((X(y) - 12, H_ - 76), f'{y * 1000:.0f}', fill=(130, 130, 170), font=Fs)
d.text((W_ // 2 - 40, H_ - 52), 'rear depth y (mm, + = backwards)', fill=(170, 170, 200), font=Fs)
zs = np.arange(zlo, zhi + 1e-9, 0.002)
def curve(fn, color, w=2):
    pts = [(X(v), Y(z)) for z in zs for v in [fn(z)] if v is not None and np.isfinite(v)]
    if len(pts) > 1: d.line(pts, fill=color, width=w)
curve(lambda z: pl['left'][int(round((z - 0.70) / 0.002))], (255, 205, 70), 3); curve(lambda z: pl['right'][int(round((z - 0.70) / 0.002))], (255, 130, 40), 3)
for t, lab, col in series: curve(lambda z, t=t: render_edge(t, 'left', z), col); curve(lambda z, t=t: render_edge(t, 'right', z), tuple(int(c * .8) for c in col))
def stats(tag, a, b):
    e = []
    for z in np.arange(a, b + 1e-9, 0.004):
        i = int(round((z - 0.70) / 0.002))
        for side in ('left', 'right'):
            p = pl[side][i]; r = render_edge(tag, side, z)
            if p is not None and r is not None: e.append(r - p)
    e = np.array(e) * 1000; return float(np.mean(np.abs(e))), float(np.max(np.abs(e)))
a, b = zlo + 0.02, zhi - 0.02; x0 = W_ + 10; res = {}
d.line([(x0, 60), (x0 + 30, 60)], fill=(255, 205, 70), width=3); d.text((x0 + 38, 51), 'PLATE left (sub-pixel)', fill=(220, 220, 230), font=Fs)
d.line([(x0, 86), (x0 + 30, 86)], fill=(255, 130, 40), width=3); d.text((x0 + 38, 77), 'PLATE right (sub-pixel)', fill=(220, 220, 230), font=Fs)
for k, (t, lab, col) in enumerate(series):
    d.line([(x0, 112 + k * 26), (x0 + 30, 112 + k * 26)], fill=col, width=3); d.text((x0 + 38, 103 + k * 26), lab, fill=(220, 220, 230), font=Fs)
    res[t] = stats(t, a, b)
y0 = 112 + len(series) * 26 + 20; d.text((x0, y0), f'z {a:.2f}-{b:.2f} contour error vs plate', fill=(255, 214, 120), font=F)
for k, (t, lab, col) in enumerate(series): d.text((x0, y0 + 28 + 24 * k), f'{lab}: mean abs {res[t][0]:.1f} mm  max {res[t][1]:.1f}', fill=col, font=Fs)
im.save(out); print(out, im.size, {t: tuple(round(v, 2) for v in r) for t, r in res.items()})
json.dump({t: dict(range=[a, b], mean_abs_mm=r[0], max_abs_mm=r[1]) for t, r in res.items()}, open(out.replace('.png', '.json'), 'w'), indent=1)
