"""Finger layout of the male right hand in the hand frame (numpy only): clusters along v at several u, finger tips, thumb."""
import numpy as np

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/'
d = np.load(W + 'data/male_body.npz')
co, tris = d['co'], d['tris']
sel = np.where((co[:, 0] < -0.50) & (co[:, 2] < 1.0))[0]
P = co[sel]
c = P.mean(0)
U_, S_, Vt = np.linalg.svd(P - c, full_matrices=False)
u, v = Vt[0], Vt[1]
if u[2] > 0: u = -u
if v[1] > 0: v = -v
p = np.cross(v, u)
Q = np.stack([(P - c) @ u, (P - c) @ v, (P - c) @ p], 1)       # (U, V, Wp) with Wp>0 = palm side
print('U range', Q[:, 0].min().round(3), Q[:, 0].max().round(3), 'V range', Q[:, 1].min().round(3), Q[:, 1].max().round(3), 'Wp range', Q[:, 2].min().round(3), Q[:, 2].max().round(3))
for u0 in (0.015, 0.025, 0.035, 0.045, 0.055, 0.065, 0.075, 0.085):
    m = (Q[:, 0] >= u0 - 0.003) & (Q[:, 0] < u0 + 0.003)
    vs = np.sort(Q[m, 1])
    if len(vs) == 0:
        print(f'u={u0:.3f}: none'); continue
    gaps = np.where(np.diff(vs) > 0.0025)[0]
    cl, s = [], 0
    for g in list(gaps) + [len(vs) - 1]:
        seg = vs[s:g + 1]
        cl.append((round(float(seg.min()), 3), round(float(seg.max()), 3)))
        s = g + 1
    # Wp extents per cluster
    print(f'u={u0:.3f}: clusters(v range)=', cl)
# finger tips: for each cluster at u = 0.035 find max U among vertices with v in the cluster range
m = (Q[:, 0] >= 0.032) & (Q[:, 0] < 0.038)
vs = np.sort(Q[m, 1]); gaps = np.where(np.diff(vs) > 0.0025)[0]
rngs, s = [], 0
for g in list(gaps) + [len(vs) - 1]:
    rngs.append((vs[s], vs[g])); s = g + 1
print('clusters at u=0.035:', [(round(a, 3), round(b, 3)) for a, b in rngs])
for i, (a, b) in enumerate(rngs):
    mm = (Q[:, 1] >= a - 0.001) & (Q[:, 1] <= b + 0.001) & (Q[:, 0] > 0.0)
    tip = Q[mm][np.argmax(Q[mm, 0])]
    cen_v = 0.5 * (a + b)
    print(f'cluster {i}: v=[{a:.3f},{b:.3f}] centre {cen_v:.3f} tip U={tip[0]:.3f} V={tip[1]:.3f} Wp={tip[2]:.3f}; palm-side surface Wp max near u=.035: ',
          Q[mm & (np.abs(Q[:, 0] - 0.035) < 0.004), 2].max().round(4), 'min', Q[mm & (np.abs(Q[:, 0] - 0.035) < 0.004), 2].min().round(4))
