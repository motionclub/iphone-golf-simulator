import sys, pickle
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1e')
import h1lib as H, loft as L, proxy as PX, sculpt as S, stage2 as S2, topo as T, wire
V = np.load(H.W / 'data/V_micro1f.npy'); F = pickle.load(open(H.W / 'data/F.pkl', 'rb'))
phi = S2.Phi()
for jt in (False, True):
    Vn, Fn, info = S2.build_final(V, F, phi, max_level=2, verbose=False, join_tris=jt)
    print('join', jt, {k: v for k, v in info.items() if k not in ('used', 'depth')})
    if jt:
        P1 = phi.stage1(Vn)
        E = set()
        for f in Fn:
            for i in range(len(f)):
                a, b = f[i], f[(i + 1) % len(f)]; E.add((min(a, b), max(a, b)))
        E = np.array(sorted(E))
        wire.plot(P1, E, P1[:, 1] < -0.045, (0, 2), (-0.075, 0.075, 1.44, 1.64), 1400, str(H.W / 'r/wire_join.png'), pts=False)
