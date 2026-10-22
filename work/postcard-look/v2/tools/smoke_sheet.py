import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, lab
gl = lab.gl
d = lab.gen('Smoke')
S = d['Smoke_C.png']
m = gl.smoke_metrics(S)
print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()})
a = S[..., 3].astype(np.float32) / 255
gx = np.abs(np.diff(a, axis=1)).max(); gy = np.abs(np.diff(a, axis=0)).max()
print('max alpha gradient per px', round(float(max(gx, gy)), 4))
ys, xs = np.mgrid[0:512, 0:512]
w = a.sum(); cx = (a * xs).sum() / w; cy = (a * ys).sum() / w
cov = np.array([[(a * (xs - cx) ** 2).sum(), (a * (xs - cx) * (ys - cy)).sum()], [(a * (xs - cx) * (ys - cy)).sum(), (a * (ys - cy) ** 2).sum()]]) / w
ev = np.linalg.eigvalsh(cov)
print('second-moment aspect', round(float(np.sqrt(ev[1] / ev[0])), 2))
red = np.array([180, 60, 30]) / 255; gry = np.array([90, 80, 85]) / 255; sky = np.array([40, 60, 110]) / 255
c = S[..., :3].astype(np.float32) / 255
tiles = []
for bg in (red, gry, sky):
    tiles.append(np.concatenate([c * a[..., None] + bg * (1 - a[..., None])], 0))
alpha_img = np.repeat(a[..., None], 3, -1)
sheet = lab.hstack([lab.label(tiles[0], 'OVER RED 180,60,30'), lab.label(tiles[1], 'OVER GREY 90,80,85'), lab.label(tiles[2], 'OVER SKY'), lab.label(alpha_img / max(a.max(), 1e-6), 'ALPHA (NORMALISED)')])
lab.write(sys.argv[1], sheet)
