import sys, pickle
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1e')
import h1lib as H, loft as L, proxy as PX, sculpt as S, stage2 as S2, topo as T
V = np.load(H.W / 'data/V_micro1f.npy'); F = pickle.load(open(H.W / 'data/F.pkl', 'rb'))
Vcc, Fcc = PX.build_proxy(3)
phi = S2.Phi(); phi.attach_cc(Vcc, Fcc)
kw = eval(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else {}
Vn, Fn, info = S2.build_final(V, F, phi, verbose=False, **kw)
P1 = phi.stage1(Vn)
cen = np.array([P1[f].mean(axis=0) for f in Fn]); tri = np.array([len(f) - 2 for f in Fn])
x = np.abs(cen[:, 0]); y = cen[:, 1]; z = cen[:, 2]
zones = {
 'ears(L+R)': (x > 0.060) & (x < 0.118) & (y > -0.045) & (y < 0.02) & (z > 1.51) & (z < 1.61),
 'eyes': (x > 0.012) & (x < 0.066) & (z > 1.560) & (z < 1.610) & (y < -0.02),
 'nose': (x < 0.030) & (z > 1.522) & (z < 1.604) & (y < -0.02),
 'mouth': (x < 0.048) & (z > 1.472) & (z < 1.528) & (y < -0.02),
 'forehead>1.61 front': (z >= 1.61) & (y < -0.02),
 'cranium top/back (y>-0.02,z>1.50)': (y >= -0.02) & (z > 1.50),
 'neck/jaw z<1.50 (all)': (z < 1.50),
}
used = np.zeros(len(Fn), bool); tot = tri.sum()
print('head tris', tot)
for k, m in zones.items():
    m2 = m & ~used; used |= m2
    print(f'{k:36s} faces {int(m2.sum()):5d}  tris {int(tri[m2].sum()):6d}')
rest = ~used
print(f'{"rest of face (cheeks, temples)":36s} faces {int(rest.sum()):5d}  tris {int(tri[rest].sum()):6d}')
