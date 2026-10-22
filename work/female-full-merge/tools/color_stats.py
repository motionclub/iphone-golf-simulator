"""Plate vs model colour statistics at the SAME camera (F3's plate-aligned head panels).  ./py.sh tools/color_stats.py <tag> [outjson]
Detector (skin-liveliness chat): skinish pixels = hue 8-45 deg, S>.2, V>.3.  Patches: small windows at identical plate pixel positions."""
import sys, json, colorsys
import numpy as np
from PIL import Image
tag = sys.argv[1] if len(sys.argv) > 1 else 'col'; outj = sys.argv[2] if len(sys.argv) > 2 else f'color/color_stats_{tag}.json'
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
plate = np.asarray(Image.open(f'{ROOT}/ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')).astype(float)
def render(view):
    im = Image.open(f'color/raw/{tag}_{view}.png').convert('RGBA'); a = np.asarray(im).astype(float); return a[..., :3], a[..., 3] / 255.0
PANEL = {'front': (85, 55, 430, 342), 'left': (440, 55, 800, 342), 'q3L': (85, 385, 430, 656)}
def hsv(c): h, s, v = colorsys.rgb_to_hsv(*(np.asarray(c, float) / 255)); return (round(h * 360, 1), round(s, 3), round(v, 3))
def skin_stats(px):
    hh = np.array([colorsys.rgb_to_hsv(*(p / 255)) for p in px]); m = (hh[:, 0] * 360 >= 8) & (hh[:, 0] * 360 <= 45) & (hh[:, 1] > 0.2) & (hh[:, 2] > 0.3)
    return dict(n=int(m.sum()), median_rgb=[int(v) for v in np.median(px[m], axis=0)], median_hsv=[round(float(np.median(hh[m, 0])) * 360, 1), round(float(np.median(hh[m, 1])), 3), round(float(np.median(hh[m, 2])), 3)], mean_S=round(float(hh[m, 1].mean()), 3), mean_V=round(float(hh[m, 2].mean()), 3))
res = {}
# ---- skin: face region of the front panel (plate px box 180,95,340,255), model rendered at 3x the panel
x0, y0, x1, y1 = PANEL['front']; fb = (180, 95, 340, 255)
pr = plate[fb[1]:fb[3], fb[0]:fb[2]].reshape(-1, 3)
rgb, al = render('front')
mb = tuple(int((v - o) * 3) for v, o in zip(fb, (x0, y0, x0, y0)))
mr = rgb[mb[1]:mb[3], mb[0]:mb[2]]; ma = al[mb[1]:mb[3], mb[0]:mb[2]]
mpx = mr[ma > 0.99].reshape(-1, 3)
res['skin_face_front'] = dict(plate=skin_stats(pr), model=skin_stats(mpx))
# ---- feature patches at identical positions (plate px -> model px = (p - panel origin) * 3)
P = {'forehead': (260, 120), 'cheek L': (222, 188), 'cheek R': (297, 188), 'chin': (258, 240), 'brow L': (225, 141), 'brow R': (290, 141), 'sclera L': (214, 165), 'sclera R': (305, 166), 'upper lip': (258, 213), 'lower lip': (258, 221), 'pupil L': (229, 167)}
patch = {}
for k, (x, y) in P.items():
    pc = plate[y - 2:y + 3, x - 2:x + 3].reshape(-1, 3).mean(0); mx, my = (x - x0) * 3, (y - y0) * 3
    mc = rgb[my - 4:my + 5, mx - 4:mx + 5].reshape(-1, 3).mean(0)
    patch[k] = dict(plate_rgb=[int(round(v)) for v in pc], model_rgb=[int(round(v)) for v in mc], plate_hsv=hsv(pc), model_hsv=hsv(mc))
res['patches'] = patch
# ---- iris: brown pixels (hue 12-35, S>.35, .12<V<.6) in the eye boxes (plate px), same boxes in the render
def iris_stats(px):
    hh = np.array([colorsys.rgb_to_hsv(*(p / 255)) for p in px]); m = (hh[:, 0] * 360 >= 12) & (hh[:, 0] * 360 <= 35) & (hh[:, 1] > 0.35) & (hh[:, 2] > 0.12) & (hh[:, 2] < 0.6)
    return dict(n=int(m.sum()), median_rgb=[int(v) for v in np.median(px[m], axis=0)] if m.any() else None, median_hsv=[round(float(np.median(hh[m, 0])) * 360, 1), round(float(np.median(hh[m, 1])), 3), round(float(np.median(hh[m, 2])), 3)] if m.any() else None)
iris = {}
for nm, (ex0, ey0, ex1, ey1) in {'iris L': (217, 156, 242, 180), 'iris R': (278, 156, 303, 180)}.items():
    pp = plate[ey0:ey1, ex0:ex1].reshape(-1, 3); rm = rgb[(ey0 - y0) * 3:(ey1 - y0) * 3, (ex0 - x0) * 3:(ex1 - x0) * 3].reshape(-1, 3)
    iris[nm] = dict(plate=iris_stats(pp), model=iris_stats(rm))
res['iris'] = iris
json.dump(res, open(outj, 'w'), indent=1)
print('SKIN face (front panel)  plate:', res['skin_face_front']['plate']); print('                         model:', res['skin_face_front']['model'])
for k, v in patch.items(): print(f"{k:10s} plate {tuple(v['plate_rgb'])} {v['plate_hsv']}   model {tuple(v['model_rgb'])} {v['model_hsv']}")
for k, v in iris.items(): print(k, 'plate', v['plate'], ' model', v['model'])
