import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
from fitbody import *
gender = sys.argv[sys.argv.index('--')+1]
bodies = load_set(gender, which=['male_authority'] if gender=='male' else ['female_authority'])
b = bodies[0]
V, F = b['V'], b['F']
N = vertex_normals(V, F)
suffix = 'male' if gender=='male' else 'female_auth'
sock = np.load(f'{WORK}/data/sock_{suffix}.npz'); shoe = np.load(f'{WORK}/data/shoe_{suffix}.npz')
ts = bvh_from(sock['V'], sock['F']); th = bvh_from(shoe['V'], shoe['F'])
feet = (V[:,2] < (0.27 if gender=='male' else 0.25)) & (np.abs(V[:,0]) > (0.05 if gender=='male' else 0.03))
miss = []
for i in np.nonzero(feet)[0]:
    p = V[i] + N[i]*1e-4
    hit = False
    for t in (ts, th):
        l, n, fi, d = t.ray_cast(p.tolist(), N[i].tolist(), 0.08)
        if fi is not None: hit = True; break
    if not hit: miss.append(i)
print("missed", len(miss))
for i in miss[:12]:
    p = V[i]
    # nearest sock/shoe distance + signed
    best=None
    for nm,t in (('sock',ts),('shoe',th)):
        l,n,fi,d = t.find_nearest(p.tolist())
        s = np.dot(p - np.array(l), np.array(n))
        if best is None or d<best[1]: best=(nm,d,s)
    print(i, p.round(4), "normal", N[i].round(3), "nearest", best[0], round(best[1]*1000,2), "mm signed", round(best[2]*1000,2))
