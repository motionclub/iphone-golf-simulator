import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
from fitbody import *
from fitcheck import *
gender, nm, bname = sys.argv[sys.argv.index('--')+1:][:3]
thr = float(sys.argv[sys.argv.index('--')+4]) if len(sys.argv) > sys.argv.index('--')+4 else 0.0
bodies = load_set(gender.split('_')[0])
b = [x for x in bodies if x['name']==bname][0]
d = np.load(f'{WORK}/data/{nm}_{gender}.npz')
V, F = d['V'], d['F']
T = d['T'] if 'T' in d.files else None
names = list(d['tagnames']) if 'tagnames' in d.files else None
dd = clearance(V, b['tree'])
bad = np.nonzero(dd < thr)[0]
print(f"{nm} vs {bname}: {len(bad)} verts below {thr*1000:.1f} mm of {len(V)}")
if T is not None and len(bad):
    vt = {}
    for fi, tri in enumerate(F):
        for v in tri: vt[v] = T[fi]
    from collections import Counter
    cnt = Counter(names[vt[i]] for i in bad)
    print('  by tag:', dict(cnt))
if len(bad):
    P = V[bad]
    # crude clustering by rounding to 3 cm cells
    cells = {}
    for i, p in zip(bad, P):
        k = tuple((p/0.03).astype(int))
        cells.setdefault(k, []).append(i)
    for k, ids in sorted(cells.items(), key=lambda kv: -len(kv[1]))[:12]:
        pp = V[ids]
        print(f"  cluster n={len(ids):4d} centre {pp.mean(0).round(3).tolist()} min d {dd[ids].min()*1000:+.1f} mm  z {pp[:,2].min():.3f}..{pp[:,2].max():.3f}")
