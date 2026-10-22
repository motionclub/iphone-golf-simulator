import sys; sys.path.insert(0, '.')
from pmo_t import *
from slab import slab_fix_iter
V = np.load('data/V_base.npy'); T = Torso(V); raw = np.load('data/V_g1_raw.npy')
for tag, n, sg, tol in (('h6', 1, 0.030, 0.0), ('h7', 1, 0.040, 0.0), ('h8', 2, 0.025, 0.0), ('h9', 1, 0.060, 0.0)):
    P, a, b = slab_fix_iter(raw, V, T.wf, T.wb, n=n, sigma=sg, tol=tol); np.save(f'data/V_{tag}.npy', P); print(tag, n, sg, tol, 'extreme drift %.2f/%.2f' % (a, b))
