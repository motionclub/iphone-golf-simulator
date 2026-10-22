"""FORM3 experiment A: gain-driven photometric refit from the FORM2 mesh with extreme-bounded solve.
python3.13 form3a.py <tag> [json overrides]"""
import sys, json, time
sys.path.insert(0, '.')
from pmo3 import *
P_ = dict(lam=0.1, sp=0.012, sg=0.009, hmax=14.0, iters=12, tol=0.4,
          gF=[1.0, 1.0, 1.0], gB=[1.0, 1.0, 1.0],          # gains front [chest(1.12-1.28), abdomen(0.90-1.12), pelvis(0.80-0.90)], back [upper(1.12-1.32), lumbar(0.90-1.12), glute(0.78-0.92)]
          lamF=[0.25, 0.5, 1.0], lamB=[0.2, 0.5, 0.5],      # ridge multipliers per region (same split)
          guard_sigma=0.008, guard_n=3, guard_zhi=1.318, zfloor=[0.782, 0.03])
tag = sys.argv[1]
if len(sys.argv) > 2: P_.update(json.loads(sys.argv[2]))
V = np.load('data/V_base.npy')
def gfn(name, x, z):
    g = P_['gF'] if name == 'front' else P_['gB']
    if name == 'front': zr = [(1.12, 1.135, 1.265, 1.285), (0.90, 0.92, 1.10, 1.13), (0.78, 0.80, 0.89, 0.915)]
    else: zr = [(1.12, 1.14, 1.30, 1.33), (0.90, 0.93, 1.10, 1.13), (0.77, 0.79, 0.90, 0.935)]
    out = np.ones_like(z)
    for gi, (a, b, c, d) in zip(g, zr): out = out + (gi - 1.0) * ramp(z, a, b, c, d)
    return out
T = Torso3(V, gain_fn=gfn, zfloor=tuple(P_['zfloor'])); T.make_basis(P_['sp'], P_['sg']); zc = T.C[:, 1]
def lam_region(mult, zr):
    out = np.ones(T.m)
    for mi, (a, b, c, d) in zip(mult, zr): out = out * (1 + (mi - 1.0) * ramp(zc, a, b, c, d))
    return out
lamF = lam_region(P_['lamF'], [(1.12, 1.135, 1.265, 1.285), (0.90, 0.92, 1.10, 1.13), (0.78, 0.80, 0.89, 0.915)])
lamB = lam_region(P_['lamB'], [(1.12, 1.14, 1.30, 1.33), (0.90, 0.93, 1.10, 1.13), (0.77, 0.79, 0.90, 0.935)])
lo, hi = extreme_bounds(T, P_['hmax'], tol_mm=P_['tol'])
z0 = np.zeros(T.m); t0 = time.time()
cF, cB = solve_lm3(T, z0, z0, lam=P_['lam'], lam_vec=np.concatenate([lamF, lamB]), lo=lo, hi=hi, iters=P_['iters'], verbose=True)
Praw = T.positions(T.dy_mm(cF, cB)); np.save(f'data/V_{tag}_raw.npy', Praw); np.savez(f'data/c_{tag}.npz', cF=cF, cB=cB, C=T.C)
Pg, dF, dB = deficit_guard(Praw, V, T, sigma=P_['guard_sigma'], n=P_['guard_n'], zhi=P_['guard_zhi'])
np.save(f'data/V_{tag}.npy', Pg); json.dump(P_, open(f'data/params_{tag}.json', 'w'), indent=1)
d = (Pg[:, 1] - V[:, 1]) * 1000; print(tag, 'time %.0fs' % (time.time() - t0), '| dy raw [%.1f, %.1f] guard-final [%.1f, %.1f] mm | moved verts %d | extreme drift front max %.2f back max %.2f mm' % ((Praw[:, 1] - V[:, 1]).min() * 1000, (Praw[:, 1] - V[:, 1]).max() * 1000, d.min(), d.max(), int(np.any(Pg != V, axis=1).sum()), np.nanmax(np.abs(dF)) * 1000, np.nanmax(np.abs(dB)) * 1000))
print(tag, 'plate-lit HP corr:', {k: round(v, 3) for k, v in T.score_hp(Pg, {'chest': (1.15, 1.32), 'abd': (0.90, 1.15), 'pel': (0.80, 0.90)}).items()})
