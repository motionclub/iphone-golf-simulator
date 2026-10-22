import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
from fitbody import *
bodies = load_set('male', which=['male_authority'])
b = bodies[0]; V, F = b['V'], b['F']
tb = bvh_from(V, F)
polo = np.load(f'{WORK}/data/polo_male.npz'); tp = bvh_from(polo['V'], polo['F'])
def hits(tree, o, d):
    out = []; o = np.array(o, float)
    for _ in range(20):
        l, n, fi, dist = tree.ray_cast(o.tolist(), list(d), 2.0)
        if fi is None: break
        out.append(round(float(l[0]), 4) if d[0] != 0 else round(float(l[1]), 4))
        o = np.array(l) + np.array(d) * 1e-4
    return out
for z in (1.24, 1.28, 1.32, 1.34):
    for y in (-0.08, -0.03, 0.01):
        print(f"z={z} y={y}: body hits along -x from x=+0.6:", hits(tb, (0.6, y, z), (-1, 0, 0)), " polo hits:", hits(tp, (0.6, y, z), (-1, 0, 0)))
