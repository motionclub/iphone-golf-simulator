"""silhouette feedback: update data/a_corr.json (front widths, rows outside the ear) and data/prof_corr.json (midline profile) from the last render.
python3.13 feedback.py <tag> [gain]"""
import sys, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
import fl
tag = sys.argv[1] if len(sys.argv) > 1 else 'b3u'; gain = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
sil = json.load(open(fl.W/'data/sil.json'))
def mask(view):
    return np.asarray(Image.open(fl.W/f'renders/{tag}_{view}.png').convert('RGBA'))[..., 3] > 128
# ---- front widths
m = mask('front'); x0, y0 = fl.PANELS['front']['box'][:2]
rows = np.arange(72, 251); da = np.zeros(len(rows)); ok = np.ones(len(rows), bool)
for i, r in enumerate(rows):
    if 150 <= r <= 203: ok[i] = False; continue
    yy = int((r - y0 + 0.5) * 3); xs = np.where(m[yy])[0]
    if len(xs) == 0: ok[i] = False; continue
    mw = (xs.max() + 1 - xs.min()) / 3.0; pc = sil['front'][str(r)]; pw = pc[1] + 1 - pc[0]
    da[i] = -0.5 * (mw - pw) * fl.K * gain                       # metres to ADD to the half width
z = fl.zrow(rows)
# interpolate over the ear rows, smooth, clip
zk = np.arange(1.40, 1.71, 0.002); dk = np.interp(zk, z[ok][::-1], da[ok][::-1])
sm = np.convolve(np.pad(dk, 6, mode='edge'), np.ones(13) / 13, mode='valid')
old = json.load(open(fl.W/'data/a_corr.json')) if (fl.W/'data/a_corr.json').exists() else None
if old: sm = sm + np.interp(zk, old['z'], old['da'])
sm = np.clip(sm, -0.012, 0.012)
json.dump(dict(z=zk.tolist(), da=sm.tolist()), open(fl.W/'data/a_corr.json', 'w'))
print('front half-width corrections (mm) at rows 100,130,210,225,240:', [round(float(np.interp(fl.zrow(r), zk, sm)) * 1000, 2) for r in (100, 130, 210, 225, 240)])
# ---- left profile: front contour (rows 90..250)
m = mask('left'); x0, y0 = fl.PANELS['left']['box'][:2]
rows = np.arange(100, 251); dy = np.zeros(len(rows)); ok = np.ones(len(rows), bool)
for i, r in enumerate(rows):
    yy = int((r - y0 + 0.5) * 3); xs = np.where(m[yy])[0]
    if len(xs) == 0: ok[i] = False; continue
    mcol = xs.min() / 3.0 + x0; pcol = sil['left'][str(r)][0]
    dy[i] = (mcol - pcol) * fl.K * gain                          # model contour is dy (m) BEHIND the plate (image-right = +y): add dy of forward displacement
zz = fl.zrow(rows)
zk2 = np.arange(1.42, 1.62, 0.002); d2 = np.interp(zk2, zz[ok][::-1], dy[ok][::-1])
sm2 = np.convolve(np.pad(d2, 4, mode='edge'), np.ones(9) / 9, mode='valid')
old = json.load(open(fl.W/'data/prof_corr.json')) if (fl.W/'data/prof_corr.json').exists() else None
if old: sm2 = sm2 + np.interp(zk2, old['z'], old['dy'])
sm2 = np.clip(sm2, -0.015, 0.015)
json.dump(dict(z=zk2.tolist(), dy=sm2.tolist()), open(fl.W/'data/prof_corr.json', 'w'))
print('profile corrections (mm) at rows 140,150,196,205,212,225,240:', [round(float(np.interp(fl.zrow(r), zk2, sm2)) * 1000, 2) for r in (140, 150, 196, 205, 212, 225, 240)])
