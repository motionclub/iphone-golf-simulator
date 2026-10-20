"""first graded build: cage -> refine -> Phi -> preview npz.  blender -b --factory-startup --python build0.py"""
import sys, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, geo, cage, mesher, zones, loftf
t0 = time.time()
d = np.load(fl.W / 'data/ring.npz'); ring_pos = d['pos']
cg = cage.build_cage(ring_pos, geo.C)
H = geo.Head()
U, F, depth, n_orig = mesher.refine(cg, H, zones.level_fn, max_level=2)
print('time refine', time.time() - t0)
P = H.phi(U)
for v, p in cg['pinned'].items(): P[v] = p
tris = sum(len(f) - 2 for f in F)
print('verts', len(P), 'faces', len(F), 'tris', tris)
el = np.array([np.linalg.norm(P[f[i]] - P[f[(i + 1) % len(f)]]) for f in F for i in range(len(f))])
print('edge mm mean %.2f min %.2f max %.2f' % (el.mean() * 1000, el.min() * 1000, el.max() * 1000))
loftf.save_npz(str(fl.W / 'data/build0.npz'), P, F)
