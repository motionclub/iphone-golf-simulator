import sys, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/scripts')
import numpy as np, bpy
from kitlib import *
from mathutils import Vector
body = load_body(MALE_BLEND, 'Body_M')
V, F = mesh_arrays(body)
t0=time.time(); tree = bvh_from(V, F); print("bvh build", time.time()-t0)
rng = np.random.default_rng(1)
P = rng.uniform([-0.3,-0.25,0.0],[0.3,0.15,1.7], size=(100000,3))
t0=time.time()
out=[]
for p in P.tolist():
    loc,n,idx,d = tree.find_nearest(p)
    out.append((d, (Vector(p)-loc).dot(n)))
dt=time.time()-t0
print("100k queries list-input:", dt, "-> per query us", dt/100000*1e6)
t0=time.time()
Pv = [Vector(p) for p in P.tolist()]
out=[tree.find_nearest(v) for v in Pv]
print("100k queries Vector input:", time.time()-t0)
