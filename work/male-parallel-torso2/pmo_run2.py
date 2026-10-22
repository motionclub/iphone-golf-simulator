"""PMO + depth guard.  usage: pmo_run2.py tag lam hmax [plate_sigma hp_iters spacing sigma_rbf slab(0/1)]"""
import sys, time
sys.path.insert(0, '.')
from pmo_t import *
from slab import slab_fix
tag = sys.argv[1]; lam = float(sys.argv[2]); hmax = float(sys.argv[3])
psig = float(sys.argv[4]) if len(sys.argv) > 4 else 2.5; hp = int(sys.argv[5]) if len(sys.argv) > 5 else 3
sp = float(sys.argv[6]) if len(sys.argv) > 6 else 0.012; sg = float(sys.argv[7]) if len(sys.argv) > 7 else 0.009; slab = int(sys.argv[8]) if len(sys.argv) > 8 else 1
V = np.load('data/V_base.npy'); T = Torso(V, plate_sigma=psig, hp_iters=hp); T.make_basis(sp, sg)
z = np.zeros(T.m); r0 = T.residual(z, z)
lamv = 1.0 + 3.0 * (T.C[:, 1] < 0.90) + 1.0 * (T.C[:, 1] > 1.33)
t0 = time.time(); cF, cB = solve_lm(T, z, z, lam=lam, lam_vec=lamv, hmax=hmax, iters=14, verbose=False)
dy = T.dy_mm(cF, cB); P = T.positions(dy); np.savez(f'data/c_{tag}.npz', cF=cF, cB=cB, C=T.C)
r1 = T.residual(cF, cB)
if slab:
    P2, dF, dB = slab_fix(P, V, T.wf, T.wb); print(tag, 'depth guard: max |shift| front %.2f back %.2f mm' % (np.abs(dF).max() * 1000, np.abs(dB).max() * 1000)); P = P2
np.save(f'data/V_{tag}.npy', P)
inner = (np.abs(V[T.zi, 0]) < 0.14) & (V[T.zi, 2] > 0.82) & (V[T.zi, 2] < 1.34)
d2 = (P[T.zi, 1] - V[T.zi, 1]) * 1000
print(tag, 'm=%d solve %.0fs data rms %.3f -> %.3f | dy rms(inner) %.2f max %.2f mm | score' % (T.m, time.time() - t0, math.sqrt(r0 @ r0 / T.m_res), math.sqrt(r1 @ r1 / T.m_res), np.sqrt((d2[inner] ** 2).mean()), np.abs(d2).max()), {k: round(v, 3) for k, v in T.score(cF, cB).items()})
