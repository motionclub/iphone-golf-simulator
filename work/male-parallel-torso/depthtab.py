import json, numpy as np
from zone import *
P = json.load(open('r/prof_base.json'))
zs = sorted(P['left']['plate'], key=float)
print('z    meshFront  meshBack | depth deficit L  R  avg(mm) | plate front/back deficits L(front,back) R(front,back)')
for z in zs:
    zf = float(z)
    m = (np.abs(V0[:, 2] - zf) < 0.006) & (np.abs(V0[:, 0]) < 0.06)
    if not m.any(): continue
    fy, by = V0[m, 1].min() * 1000, V0[m, 1].max() * 1000
    L = P['left']; R = P['right']
    def dep(d): a = d['plate'][z]; b = d['mesh'][z]; return (a[1] - a[0]) - (b[1] - b[0]) if a and b else float('nan')
    dl, dr = dep(L), dep(R)
    # front/back split: left view: lo=front(-y), hi=back; right view: lo=back, hi=front
    def sp(d, flip):
        a = d['plate'][z]; b = d['mesh'][z]
        if not (a and b): return (float('nan'),) * 2
        fl, bk = (a[0] - b[0], a[1] - b[1]); fr, bc = ((bk, fl) if flip else (-fl, bk))
        return (-fl if not flip else bk, bk if not flip else -fl)
    print(f'{zf:.2f} {fy:8.1f} {by:8.1f} | {dl:6.1f} {dr:6.1f} {np.nanmean([dl, dr]):6.1f}')
