import numpy as np
from collections import defaultdict
from zone import *
V1 = np.load('data/V_final.npy'); D = V1 - V0
dx = np.abs(D[:, 0]) * 1000
idx = np.argsort(-dx)[:12]
print('largest |dx| verts (mm): x y z at base ->  dx dy dz')
for i in idx: print(f'  v{i:5d} base ({V0[i,0]*1000:7.1f},{V0[i,1]*1000:7.1f},{V0[i,2]*1000:7.1f})  d=({D[i,0]*1000:6.1f},{D[i,1]*1000:6.1f},{D[i,2]*1000:6.1f})')
print('count |dx|>5mm:', int((dx > 5).sum()), ' >3mm:', int((dx > 3).sum()), ' >2mm:', int((dx>2).sum()))
# where are |dx|>3 in z
zz = V0[dx > 3, 2]; print('z histogram (cm) of |dx|>3mm verts:', np.unique(np.round(zz * 100).astype(int), return_counts=True))
# stretched / compressed edges
E = set()
for f in F:
    for k in range(len(f)):
        a, b = f[k], f[(k + 1) % len(f)]; E.add((min(a, b), max(a, b)))
E = np.array(sorted(E)); L0 = np.linalg.norm(V0[E[:, 0]] - V0[E[:, 1]], axis=1); L1 = np.linalg.norm(V1[E[:, 0]] - V1[E[:, 1]], axis=1)
r = L1 / np.maximum(L0, 1e-9); zm = zone_mask(V0); ez = zm[E[:, 0]] | zm[E[:, 1]]
bad = np.where(ez & ((r > 1.6) | (r < 0.6)))[0]
print('stretched/compressed edges:', len(bad))
for i in bad: 
    a, b = E[i]; m = 0.5 * (V0[a] + V0[b]); print(f'  ratio {r[i]:.2f}  L0 {L0[i]*1000:5.1f}mm -> L1 {L1[i]*1000:5.1f}mm at ({m[0]*1000:6.1f},{m[1]*1000:6.1f},{m[2]*1000:6.1f})')
