import sys; sys.path.insert(0, '.')
from pmo_t import *
from slab import slab_fix_iter
V = np.load('data/V_base.npy'); T = Torso(V); raw = np.load('data/V_g1_raw.npy')
for tag, n, sg, tol in (('h1', 1, 0.014, 0.0), ('h2', 2, 0.010, 0.0), ('h3', 1, 0.008, 0.0), ('h4', 3, 0.012, 0.0), ('h5', 1, 0.020, 0.0)):
    P, a, b = slab_fix_iter(raw, V, T.wf, T.wb, n=n, sigma=sg, tol=tol); np.save(f'data/V_{tag}.npy', P); print(tag, n, sg, tol, 'extreme drift %.2f/%.2f' % (a, b))
