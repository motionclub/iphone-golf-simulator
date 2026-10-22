"""Lip colour ratios in REAL Unity captures (face_front.png: 1280x720, ortho half-height 0.16 m, target x 0 / z 1.565).  python3.13 lipcolor_unity.py <captures_dir> [<captures_dir2> ...]"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_lib import *
C = json.load(open(W / 'r2_analysis/lip_curves_v0.json'))
cv = lambda k: (lambda p: (lambda x: np.interp(abs(x), p[:, 0], p[:, 1])))(np.array(C[k], float))
seam, up, lo = cv('seam'), cv('up'), cv('lo'); PXM = 720 / 0.32
def pix(x_mm, z_mm): return int(round(360 + (1565.0 - z_mm) * PXM / 1000.0 - 0.5)), int(round(640 + x_mm * PXM / 1000.0))
def sample(a, f_lo, f_hi, x0, x1):
    vals = []
    for xm in np.arange(x0, x1, 0.5):
        for sgn in (1, -1):
            x = sgn * xm
            for zz in np.arange(f_lo(x), f_hi(x), 0.3):
                r, c = pix(x, zz); vals.append(a[r, c])
    return np.array(vals).mean(axis=0)
def box(a, xa, xb, za, zb):
    r0, c0 = pix(xa, zb); r1, c1 = pix(xb, za); return a[r0:r1, c0:c1].reshape(-1, 3).mean(axis=0)
ts = 1.9
PL = dict(upper=np.array([0.90, 0.83, 0.82]), lower=np.array([1.11, 1.09, 1.18]))
print('plate target ratios  upper/cheek', PL['upper'], ' lower/cheek', PL['lower'], ' (lower/upper', np.round(PL['lower'] / PL['upper'], 2), ')')
for d in sys.argv[1:]:
    a = np.asarray(Image.open(d + '/face_front.png').convert('RGB')).astype(float)
    u = sample(a, lambda x: seam(x) + ts + 0.5, lambda x: up(x) - 0.5, 0, 18); l = sample(a, lambda x: lo(x) + 0.5, lambda x: seam(x) - ts - 0.5, 0, 18); ch = box(a, 30, 45, 1520, 1540)
    print(f'{d.split("/")[-2] if d.endswith("/") else d.split("/")[-1]:34s} upper {np.round(u).astype(int)} lower {np.round(l).astype(int)} cheek {np.round(ch).astype(int)} | upper/cheek {np.round(u / ch, 2)} lower/cheek {np.round(l / ch, 2)}')
