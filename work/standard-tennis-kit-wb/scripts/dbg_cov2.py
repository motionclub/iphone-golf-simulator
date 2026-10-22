import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
from fitbody import *
bodies = load_set('male', which=['male_authority'])
b = bodies[0]; V, F = b['V'], b['F']
polo = np.load(f'{WORK}/data/polo_male.npz'); tp = bvh_from(polo['V'], polo['F'])
sh = (V[:,2] > 1.22) & (V[:,2] < 1.36) & (np.abs(V[:,0]) < 0.26)
dirs = {'+x':(1,0,0),'-x':(-1,0,0),'+y':(0,1,0),'-y':(0,-1,0)}
from collections import Counter
cnt = Counter(); samples = {}
for i in np.nonzero(sh)[0]:
    for nm, d in dirs.items():
        l, n, fi, dist = tp.ray_cast((V[i] + np.array(d)*1e-4).tolist(), list(d), 0.5)
        if fi is None:
            cnt[nm] += 1
            samples.setdefault(nm, []).append(V[i])
print("fail counts", dict(cnt))
for nm, arr in samples.items():
    a = np.array(arr); print(nm, "n", len(a), "bbox", a.min(0).round(3), a.max(0).round(3))
