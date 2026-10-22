"""Torso outline profile plate-vs-mesh. python3.13 prof.py <renderdir> [out.json]
front/back: central run (containing body centre) left/right extents per z (mm, +x = model +x).  left/right: front(-y)/back(+y) extents of whole silhouette."""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work'); M = R / 'male-silhouette'
CAM = {c['name']: c for c in json.load(open(M / 'reference-cameras.json'))['views']}
def mask(p):
    a = np.array(Image.open(p).convert('RGBA')); return (a[:, :, 3] > 127) if a[:, :, 3].min() < 250 else (a[:, :, 0] > 127)
def runs(row):
    d = np.diff(np.concatenate([[0], row.astype(int), [0]])); s = np.where(d == 1)[0]; e = np.where(d == -1)[0] - 1; return list(zip(s, e))
ZS = np.arange(0.78, 1.401, 0.02)
def front_back(m, cam, back):
    c = CAM[cam]; mpp = c['metres_per_pixel']; out = {}
    for z in ZS:
        y = int(round(c['sole_y'] - z / mpp)); rs = runs(m[y]); cx = c['centre_x']
        cand = [r for r in rs if r[0] <= cx <= r[1]]
        if not cand: out[round(z, 2)] = None; continue
        a, b = cand[0]
        # in image px; convert to model x (front: +px = +x; back: +px = -x)
        xa = (a - cx) * mpp * (-1 if back else 1); xb = (b + 1 - cx) * mpp * (-1 if back else 1)
        lo, hi = sorted((xa, xb)); out[round(z, 2)] = (lo * 1000, hi * 1000)
    return out
def side(m, cam):
    c = CAM[cam]; mpp = c['metres_per_pixel']; out = {}
    for z in ZS:
        y = int(round(c['sole_y'] - z / mpp)); xs = np.where(m[y, c['roi'][0]:c['roi'][2]])[0]
        if len(xs) == 0: out[round(z, 2)] = None; continue
        a = c['roi'][0] + xs[0]; b = c['roi'][0] + xs[-1] + 1; cx = c['centre_x']
        # left cam (angle 90): image right = -y?  report image-relative extents in mm from centre; sign resolved by caller
        out[round(z, 2)] = ((a - cx) * mpp * 1000, (b - cx) * mpp * 1000)
    return out
def profile(d):
    t = lambda v: mask(M / f'{v}_target.png'); r = lambda v: mask(Path(d) / f'{v}.png')
    P = {}
    for v, back in (('bald_front', False), ('bald_back', True)):
        P[v] = dict(plate=front_back(t(v), v, back), mesh=front_back(r(v), v, back))
    for v in ('left', 'right'):
        P[v] = dict(plate=side(t(v), v), mesh=side(r(v), v))
    return P
if __name__ == '__main__':
    P = profile(sys.argv[1])
    if len(sys.argv) > 2: json.dump(P, open(sys.argv[2], 'w'), indent=1)
    for v in P:
        print(v)
        for z in sorted(P[v]['plate']):
            a, b = P[v]['plate'][z], P[v]['mesh'][z]
            if a is None or b is None: print(f'  z {z:.2f} plate {a} mesh {b}'); continue
            print(f'  z {z:.2f} plate [{a[0]:+7.1f},{a[1]:+7.1f}] mesh [{b[0]:+7.1f},{b[1]:+7.1f}]  d [{b[0]-a[0]:+6.1f},{b[1]-a[1]:+6.1f}]')
