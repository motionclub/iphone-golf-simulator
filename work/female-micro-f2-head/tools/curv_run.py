import sys, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, meshlib as ml
src, out = sys.argv[1], sys.argv[2]
V, F, d = ml.load(src)
N, T, fn = ml.vertex_normals(V, F)
idx = np.where(V[:, 2] > 1.395)[0]
t0 = time.time()
k1, k2, d1 = ml.curvature(V, F, N, ring=2, rad=0.014, idx=idx)
print('curvature for', len(idx), 'verts in %.1f s' % (time.time() - t0))
np.savez(out, k1=k1, k2=k2, d1=d1, N=N, idx=idx)
