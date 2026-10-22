import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
from fitbody import *
from fitcheck import *
gender, nm, bname = sys.argv[sys.argv.index('--')+1:][:3]
bodies = load_set(gender.split('_')[0])
b = [x for x in bodies if x['name']==bname][0]
d = np.load(f'{WORK}/data/{nm}_{gender}.npz')
V, F = d['V'], d['F']
T = d['T'] if 'T' in d.files else None
names = list(d['tagnames']) if 'tagnames' in d.files else None
pairs = overlap_pairs(V, F, b['V'], b['F'])
gi = sorted(set(p[0] for p in pairs))
print(f"{nm} vs {bname}: {len(pairs)} pairs, {len(gi)} garment tris")
from collections import Counter
if T is not None: print('  by tag:', dict(Counter(names[T[i]] for i in gi)))
C = V[F[gi]].mean(1)
cells = {}
for i, c in zip(gi, C):
    cells.setdefault(tuple((c/0.02).astype(int)), []).append(i)
for k, ids in sorted(cells.items(), key=lambda kv: -len(kv[1]))[:10]:
    cc = V[F[ids]].mean((0,1))
    print(f"  n={len(ids):3d} centre {cc.round(3).tolist()} " + (f"tag {names[T[ids[0]]]}" if T is not None else ''))
