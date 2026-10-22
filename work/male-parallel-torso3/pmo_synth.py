"""Synthetic validation: plant a known displacement, synthesise the plate from the model, recover it."""
import sys, time
sys.path.insert(0, '.')
from pmo_t import *
V = np.load('data/V_base.npy'); T = Torso(V)
print('zone', T.nz, 'sel', {k: len(v['sel']) for k, v in T.views.items()}, 'light fit coeffs', {k: np.round(v['c'], 1) for k, v in T.views.items()})
print('basis m', T.make_basis(0.012, 0.009))
rng = np.random.default_rng(1)
# planted truth: a few smooth bumps (pec-like on front, scapula-like on back), symmetric
cF_t = np.zeros(T.m); cB_t = np.zeros(T.m)
for (cx, cz, a, grp) in ((0.08, 1.24, 3.0, 0), (0.0, 1.0, -2.0, 0), (0.1, 1.05, 2.5, 0), (0.08, 1.22, 3.0, 1), (0.0, 1.1, -2.0, 1), (0.09, 0.9, 3.0, 1)):
    k = np.argmin((T.C[:, 0] - cx) ** 2 + (T.C[:, 1] - cz) ** 2); (cF_t if grp == 0 else cB_t)[k] = a * 4.0
dy_t = T.dy_mm(cF_t, cB_t); print('planted max |dy| %.2f mm' % np.abs(dy_t).max())
# synthesise the plate luminance at the selected vertices from the model with the planted shape
P = T.positions(dy_t); N = T.normals(P)
for name, v in T.views.items():
    v['I'] = sh2s(N[v['sel']]) @ v['c'] + rng.normal(0, 1.0, len(v['sel']))
z = np.zeros(T.m)
print('score at start', T.score(z, z))
t0 = time.time(); cF, cB = solve_lm(T, z, z, lam=float(sys.argv[1]) if len(sys.argv)>1 else 20.0, iters=10, hmax=9.0); print('solve %.0fs' % (time.time() - t0))
dy = T.dy_mm(cF, cB); sel = T.zi[(np.abs(T.V0[T.zi, 0]) < 0.14) & (T.V0[T.zi, 2] > 0.82) & (T.V0[T.zi, 2] < 1.34)]
loc = T.zloc[sel]; print('recovery: corr(dy, planted) %.3f ; rms planted %.2f mm, rms recovered %.2f mm, rms error %.2f mm' % (np.corrcoef(dy[loc], dy_t[loc])[0, 1], np.sqrt((dy_t[loc] ** 2).mean()), np.sqrt((dy[loc] ** 2).mean()), np.sqrt(((dy[loc] - dy_t[loc]) ** 2).mean())))
print('score after', T.score(cF, cB))
