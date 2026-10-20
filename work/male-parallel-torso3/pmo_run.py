import sys, time, json
sys.path.insert(0, '.')
from pmo_t import *
tag = sys.argv[1]; lam = float(sys.argv[2]); hmax = float(sys.argv[3]) if len(sys.argv) > 3 else 7.0
psig = float(sys.argv[4]) if len(sys.argv) > 4 else 2.5; hp = int(sys.argv[5]) if len(sys.argv) > 5 else 3
V = np.load('data/V_base.npy'); T = Torso(V, plate_sigma=psig, hp_iters=hp); T.make_basis(0.012, 0.009)
z = np.zeros(T.m); r0 = T.residual(z, z)
print(tag, 'm', T.m, 'n_res', T.m_res, 'start data rms %.3f' % math.sqrt((r0 @ r0) / T.m_res), 'score', {k: round(v, 3) for k, v in T.score(z, z).items()})
lamv = 1.0 + 3.0 * (T.C[:, 1] < 0.90) + 1.0 * (T.C[:, 1] > 1.33)
t0 = time.time(); cF, cB = solve_lm(T, z, z, lam=lam, lam_vec=lamv, hmax=hmax, iters=12)
dy = T.dy_mm(cF, cB); P = T.positions(dy); np.save(f'data/V_{tag}.npy', P); np.savez(f'data/c_{tag}.npz', cF=cF, cB=cB, C=T.C)
inner = (np.abs(T.V0[T.zi, 0]) < 0.14) & (T.V0[T.zi, 2] > 0.82) & (T.V0[T.zi, 2] < 1.34)
print(tag, 'solve %.0fs' % (time.time() - t0), 'dy rms(inner) %.2f mm max %.2f mm' % (np.sqrt((dy[inner] ** 2).mean()), np.abs(dy).max()), 'score after', {k: round(v, 3) for k, v in T.score(cF, cB).items()})
