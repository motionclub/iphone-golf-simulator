"""Radial disagreement between the existing (cage CC) surface and the plate loft, by z and direction.  python3.13 (Blender's) w/ numpy only is not enough for bpy; run via Blender."""
import sys
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, loft as L, proxy as PX

V, F = PX.build_proxy(3)
lf = L.Loft()
z = V[:, 2]; p = lf.at(z)
dx = V[:, 0]; dy = V[:, 1] - p['yw']
th = np.degrees(np.arctan2(dy, dx)); rp = np.hypot(dx, dy); rl = lf.radius(np.arctan2(dy, dx), z)
sect = {'front(-90)': (-100, -80), 'fL(-135)': (-145, -125), 'side(180)': (170, 190), 'back(90)': (80, 100), 'fR(-45)': (-55, -35)}
print('z     ' + '  '.join(f'{k:>11s}' for k in sect))
for zc in np.arange(1.42, 1.70, 0.01):
    row = []
    for k, (a, b) in sect.items():
        t = th.copy()
        if a > 0 or b < 0:
            pass
        m = (np.abs(z - zc) < 0.0025) & (t > a) & (t < b)
        if k.startswith('side'):
            m = (np.abs(z - zc) < 0.0025) & ((np.abs(t) > 170))
        row.append(f'{(rl[m] - rp[m]).mean() * 1000:+7.1f}mm' if m.any() else '     --   ')
    print(f'{zc:.2f}  ' + '  '.join(row))
