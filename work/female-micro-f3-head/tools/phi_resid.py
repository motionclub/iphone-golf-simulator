import sys, json, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, geo, fl
t0 = time.time()
H = geo.Head()
st = np.load(fl.W / 'data/b17_state.npz'); U = st['U']; P = st['P'][:len(U)]
print('patch verts', len(P), 'U', U.shape, 'build %.1fs' % (time.time() - t0))
n = len(P)
t0 = time.time()
Pphi = H.phi(U[:n])
print('phi eval %.1fs' % (time.time() - t0))
res = P - Pphi
dn = np.linalg.norm(res, axis=1)
np.savez(fl.W / 'data/phi_resid_b17.npz', P=P, U=U, Pphi=Pphi, res=res)
zone = {'all': np.ones(n, bool), 'z<1.52 front': (P[:, 2] < 1.52) & (P[:, 1] < -0.03), 'chin z<1.46 |x|<.05': (P[:, 2] < 1.46) & (P[:, 2] > 1.42) & (np.abs(P[:, 0]) < 0.05) & (P[:, 1] < -0.06),
        'cheek band 1.46-1.52 |x| .045-.08': (P[:, 2] > 1.46) & (P[:, 2] < 1.52) & (np.abs(P[:, 0]) > 0.045) & (np.abs(P[:, 0]) < 0.08) & (P[:, 1] < -0.03),
        'mouth zone': (np.abs(P[:, 0]) < 0.045) & (P[:, 2] > 1.455) & (P[:, 2] < 1.50) & (P[:, 1] < -0.09)}
for k, m in zone.items():
    if m.sum() == 0: continue
    print(f'{k:36s} n={m.sum():6d}  |res| mean {dn[m].mean()*1000:6.2f} mm  p50 {np.median(dn[m])*1000:6.2f}  p95 {np.percentile(dn[m],95)*1000:6.2f}  max {dn[m].max()*1000:6.2f}')
