import sys, pickle
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, loft as L, proxy as PX, sculpt as S, stage2 as S2, topo as T
V = np.load(H.W / 'data/V_micro1f.npy'); F = pickle.load(open(H.W / 'data/F.pkl', 'rb'))
Vcc, Fcc = PX.build_proxy(3)
phi = S2.Phi(); phi.attach_cc(Vcc, Fcc)
# L1 mesh everywhere in face zone, no error-driven refinement
Vn, Fn, info = S2.build_final(V, F, phi, eps=1e9, max_level=1, min_face_level=1, verbose=False)
Fq = [f for f in Fn if len(f) == 4]
corners = np.array([[Vn[i] for i in f] for f in Fq])
cen = corners.mean(axis=1)
Pc = phi.stage1(corners.reshape(-1, 3)).reshape(len(Fq), 4, 3)
Pcen = phi.stage1(cen)
err_c = np.linalg.norm(Pcen - Pc.mean(axis=1), axis=1) * 1000
mids = 0.5 * (corners + np.roll(corners, -1, axis=1))
Pm = phi.stage1(mids.reshape(-1, 3)).reshape(len(Fq), 4, 3)
Pe = 0.5 * (Pc + np.roll(Pc, -1, axis=1))
err_m = np.linalg.norm(Pm - Pe, axis=2).max(axis=1) * 1000
err = np.maximum(err_c, err_m)
print('quads', len(Fq), 'err mm: mean %.3f median %.3f p90 %.3f max %.3f' % (err.mean(), np.median(err), np.percentile(err, 90), err.max()))
print('err_c mean %.3f err_m mean %.3f' % (err_c.mean(), err_m.mean()))
x = np.abs(cen[:, 0]); y = cen[:, 1]; z = cen[:, 2]
zones = {'cranium z>1.63': z > 1.63, 'forehead 1.60-1.63 front': (z > 1.60) & (z <= 1.63) & (y < -0.02), 'eyes': (x > 0.014) & (x < 0.062) & (z > 1.563) & (z < 1.607) & (y < -0.02),
         'nose': (x < 0.030) & (z > 1.524) & (z < 1.604) & (y < -0.02), 'cheeks': (x > 0.03) & (z > 1.50) & (z < 1.56) & (y < -0.02) & (x < 0.09), 'mouth': (x < 0.046) & (z > 1.474) & (z < 1.526) & (y < -0.02),
         'ears': (x > 0.062) & (x < 0.118) & (y > -0.042) & (y < 0.018) & (z > 1.518) & (z < 1.606), 'back y>0.02': y > 0.02, 'jaw/chin z<1.50': (z < 1.50) & (y < -0.02)}
for k, m in zones.items():
    if m.any(): print(f'{k:28s} n={int(m.sum()):4d} mean {err[m].mean():.3f} p90 {np.percentile(err[m],90):.3f} max {err[m].max():.3f}')
