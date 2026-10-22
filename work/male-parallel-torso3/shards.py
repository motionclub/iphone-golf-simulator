"""dihedral / sliver scan. python3.13 shards.py <tag> [thresh_deg]"""
import sys, numpy as np
from collections import defaultdict
from zone import *
tag = sys.argv[1]; th = float(sys.argv[2]) if len(sys.argv) > 2 else 55.0
V = V0 if tag == 'base' else np.load(f'data/V_{tag}.npy')
def face_normals(V):
    n = np.zeros((len(F), 3)); a = np.zeros(len(F))
    for i, f in enumerate(F):
        p = V[f]; c = np.zeros(3)
        for k in range(1, len(f) - 1): c += np.cross(p[k] - p[0], p[k + 1] - p[0])
        a[i] = 0.5 * np.linalg.norm(c); n[i] = c / max(np.linalg.norm(c), 1e-18)
    return n, a
fn, fa = face_normals(V)
e2f = defaultdict(list)
for i, f in enumerate(F):
    for k in range(len(f)):
        a, b = f[k], f[(k + 1) % len(f)]; e2f[(min(a, b), max(a, b))].append(i)
bad = []
for e, fs in e2f.items():
    if len(fs) == 2:
        c = np.clip(fn[fs[0]] @ fn[fs[1]], -1, 1); ang = np.degrees(np.arccos(c))
        if ang > th: bad.append((ang, e))
bad.sort(reverse=True)
zm = zone_mask(V0)
print(f'{tag}: edges with dihedral > {th} deg: {len(bad)}')
inzone = [(a, e) for a, e in bad if zm[e[0]] and zm[e[1]]]
print('  both ends in torso zone:', len(inzone))
import collections
cl = collections.Counter()
for a, e in bad:
    m = 0.5 * (V[e[0]] + V[e[1]]); cl[(round(m[2] * 20) / 20, 'Z' if (zm[e[0]] and zm[e[1]]) else 'out', 'head' if m[2] > 1.4 else ('arm/hand' if abs(m[0]) > 0.25 else ('leg' if m[2] < 0.77 else 'torso')))] += 1
for k, v in sorted(cl.items()): print('   z~%.2f %s %s: %d' % (k[0], k[1], k[2], v))
print('  worst 12 in zone:')
for a, e in inzone[:12]:
    m = 0.5 * (V[e[0]] + V[e[1]]); print(f'    {a:5.1f} deg at x {m[0]*1000:6.1f} y {m[1]*1000:6.1f} z {m[2]*1000:6.1f}')
sl = np.where(fa < 1e-7)[0]; print('  faces with area < 0.1 mm2 (slivers):', len(sl), ' in zone:', int(sum(zm[F[i][0]] for i in sl)))
