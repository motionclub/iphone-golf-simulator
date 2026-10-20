"""Fit a tilted ellipsoid so its x=0 front profile follows the plate nose profile (rows 163..195).
python3.13 (Blender's) numpy only."""
import sys
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, ellip as E
rows = np.array([165, 170, 175, 180, 185, 190, 195, 198])
ycols = np.array([550.0, 547.8, 543.7, 540.3, 537.0, 533.7, 530.9, 530.3])
yp = H.ycol(ycols); zp = H.zrow(rows)
print('plate profile y:', yp.round(4))
best = None
rng = np.random.default_rng(1)
def err(p):
    cy, cz, au, aw, th = p
    y = E.ell_front_y(np.zeros_like(zp), zp, 0.0, cy, cz, 0.011, au, aw, th)
    if np.isnan(y).any(): return 1e9
    return float(np.sqrt(np.mean((y - yp) ** 2)))
for _ in range(60000):
    p = (rng.uniform(-0.16, -0.12), rng.uniform(1.52, 1.60), rng.uniform(0.04, 0.12), rng.uniform(0.012, 0.030), np.radians(rng.uniform(15, 45)))
    e = err(p)
    if best is None or e < best[0]: best = (e, p)
e, p = best
# local refinement
step = np.array([0.003, 0.003, 0.004, 0.001, np.radians(1.5)])
for it in range(4000):
    q = np.array(p) + rng.normal(0, 1, 5) * step * (0.97 ** (it / 80))
    ee = err(q)
    if ee < e: e, p = ee, tuple(q)
print('rms mm', e * 1000, 'cy %.4f cz %.4f au %.4f aw %.4f theta %.1f deg' % (p[0], p[1], p[2], p[3], np.degrees(p[4])))
y = E.ell_front_y(np.zeros_like(zp), zp, 0.0, p[0], p[1], 0.011, p[2], p[3], p[4])
print('fit y:', y.round(4))
