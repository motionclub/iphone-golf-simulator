import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit/scripts')
import numpy as np, bpy
from kitlib import *
from checklib import *
g = 'female'
f = 'R'
sh = np.load(f'{WORK}/data/shoe{f}_{g}.npz'); sk = np.load(f'{WORK}/data/sock{f}_{g}.npz')
tg = [str(t) for t in sh['tagnames']]
tsh, tsk = bvh(sh['V'], sh['F']), bvh(sk['V'], sk['F'])
pairs = tsh.overlap(tsk)
ti = tg.index('tongue')
tong = [a for a, b in pairs if sh['T'][a] == ti]
cen = sh['V'][sh['F'][tong]].mean(1)
print('tongue overlap triangles', len(tong), 'centroid z range', cen[:, 2].min().round(4), cen[:, 2].max().round(4), 'y range', cen[:, 1].min().round(4), cen[:, 1].max().round(4), 'x range', cen[:, 0].min().round(4), cen[:, 0].max().round(4))
# the tongue's vertex set: signed distance to the sock
tv = np.unique(sh['F'][sh['T'] == ti])
Vt = sh['V'][tv]
sd = signed_dist(tsk, Vt)
print('tongue vertices', len(tv), 'signed distance to sock (mm): min', round(sd.min() * 1000, 2), 'p05', round(np.percentile(sd, 5) * 1000, 2), 'n<0.5mm', int((sd < 0.0005).sum()), 'n<0', int((sd < 0).sum()))
# where are the vertices with small distance
# penetration depth of the overlapping triangles: dense barycentric samples of each triangle against the sock (signed)
worst = 0
for a in tong:
    tri = sh['V'][sh['F'][a]]
    pts = []
    for u in np.linspace(0, 1, 7):
        for v in np.linspace(0, 1 - u, max(2, int(7 * (1 - u)) + 1)):
            pts.append(tri[0] * (1 - u - v) + tri[1] * u + tri[2] * v)
    d = signed_dist(tsk, np.array(pts))
    worst = min(worst, d.min())
print('worst triangle-sample signed distance to the sock among overlapping tongue triangles (mm):', round(worst * 1000, 3))
print('tongue triangle edge lengths (mm): median', round(float(np.median(np.linalg.norm(sh['V'][sh['F'][sh['T'] == ti][:, 0]] - sh['V'][sh['F'][sh['T'] == ti][:, 1]], axis=1)) * 1000), 1), 'max', round(float(np.linalg.norm(sh['V'][sh['F'][sh['T'] == ti][:, 0]] - sh['V'][sh['F'][sh['T'] == ti][:, 1]], axis=1).max() * 1000), 1))
print('sock top', sk['V'][:, 2].max().round(4))
