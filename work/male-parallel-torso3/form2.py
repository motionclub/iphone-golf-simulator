"""FORM2 canonical build: photometric torso fit (front/back plain plate), depth guard, saves data/V_<tag>.npy (+ raw, coefficients, params).
python3.13 form2.py <tag> [json overrides]"""
import sys, json, time
sys.path.insert(0, '.')
from pmo_t import *
from slab import slab_fix_iter
P_ = dict(lam=0.1, psig=2.5, hp=3, sp=0.012, sg=0.009, lo=1.0, hi=1.0, chestF=0.25, chestB=0.12, zr=[1.12, 1.32], hmax=10.0, iters=14, guard_n=1, guard_sigma=0.020, guard_tol=0.0, chest_gain=1.0, chest_gain_z=[1.13, 1.25], cleft=0, cleft_lamB=0.3, top_taper=[1.33, 0.06], guard_zhi=1.36)
tag = sys.argv[1]
if len(sys.argv) > 2: P_.update(json.loads(sys.argv[2]))
V = np.load('data/V_base.npy'); T = Torso(V, plate_sigma=P_['psig'], hp_iters=P_['hp'], top_taper=tuple(P_['top_taper'])); T.make_basis(P_['sp'], P_['sg'], cleft=bool(P_['cleft'])); z = np.zeros(T.m)
lamv = 1.0 + (P_['lo'] - 1.0) * (T.C[:, 1] < 0.90) + P_['hi'] * (T.C[:, 1] > 1.33); chm = (T.C[:, 1] > P_['zr'][0]) & (T.C[:, 1] < P_['zr'][1])
lamF = lamv * np.where(chm, P_['chestF'], 1.0); lamB = lamv * np.where(chm, P_['chestB'], 1.0)
if P_['cleft']:
    ex = np.arange(T.m) >= T.n_main; lamF = np.where(ex, 1e4, lamF); lamB = np.where(ex, P_['cleft_lamB'], lamB)
t0 = time.time(); cF, cB = solve_lm(T, z, z, lam=P_['lam'], lam_vec=np.concatenate([lamF, lamB]), hmax=P_['hmax'], iters=P_['iters'], verbose=False)
gm = (T.C[:, 1] > P_['chest_gain_z'][0]) & (T.C[:, 1] < P_['chest_gain_z'][1]); cF = np.where(gm, cF * P_['chest_gain'], cF)
Praw = T.positions(T.dy_mm(cF, cB)); np.save(f'data/V_{tag}_raw.npy', Praw); np.savez(f'data/c_{tag}.npz', cF=cF, cB=cB, C=T.C)
Pg, a, b = slab_fix_iter(Praw, V, T.wf, T.wb, n=P_['guard_n'], sigma=P_['guard_sigma'], tol=P_['guard_tol'], zhi=P_['guard_zhi']); np.save(f'data/V_{tag}.npy', Pg); json.dump(P_, open(f'data/params_{tag}.json', 'w'), indent=1)
print(tag, 'solve+guard %.0fs' % (time.time() - t0), '| guard residual extreme drift front %.2f back %.2f mm' % (a, b), '| fit score', {k: round(v, 3) for k, v in T.score(cF, cB).items()})
d = (Pg[:, 1] - V[:, 1]) * 1000; inner = T.Z & (np.abs(V[:, 0]) < 0.14) & (V[:, 2] > 0.82) & (V[:, 2] < 1.34)
print(tag, 'dy: rms(inner) %.2f mm max %.2f mm; moved verts %d' % (np.sqrt((d[inner] ** 2).mean()), np.abs(d).max(), int(np.any(Pg != V, axis=1).sum())))
