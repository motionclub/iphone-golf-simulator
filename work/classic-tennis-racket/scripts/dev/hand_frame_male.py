"""Male right-hand local frame by PCA + cross-section profile along the finger axis (numpy only)."""
import numpy as np

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/'
d = np.load(W + 'data/male_body.npz')
co, tris, nrm = d['co'], d['tris'], d['nrm']
sel = np.where((co[:, 0] < -0.50) & (co[:, 2] < 1.0))[0]
P = co[sel]
c = P.mean(0)
U, S, Vt = np.linalg.svd(P - c, full_matrices=False)
print('centroid', c.round(4), 'sv', S.round(3))
for i in range(3):
    print('axis', i, Vt[i].round(3))
# finger axis = most "down" principal direction of the hand+fingers: take the lowest points
tipc = P[P[:, 2] < 0.82].mean(0)
print('finger-tip centroid', tipc.round(4))
# Use the direction from the wrist (arm cross-section min) to fingertip centroid.
# Arm axis from the forearm: points with z 1.00..1.10
F = co[(co[:, 0] < -0.35) & (co[:, 2] >= 1.0) & (co[:, 2] < 1.15)]
cF = F.mean(0)
u, s, vt = np.linalg.svd(F - cF, full_matrices=False)
print('forearm centroid', cF.round(4), 'axis', vt[0].round(3), 'sv', s.round(3))
axis_fore = vt[0] if vt[0][2] < 0 else -vt[0]
# profile along forearm axis for the hand region
t = (P - cF) @ axis_fore
print('t range', t.min().round(3), t.max().round(3))
for t0 in np.arange(t.min(), t.max(), 0.01):
    m = (t >= t0) & (t < t0 + 0.01)
    if m.sum() < 3: continue
    Q = P[m]
    # cross-section extents in the plane perpendicular to axis: use two perpendicular axes (palm normal guess)
    e1 = np.cross(axis_fore, [0, 1, 0]); e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis_fore, e1)
    a = (Q - cF) @ e1; b = (Q - cF) @ e2
    print(f'  t[{t0:.3f}] n={m.sum():3d} ext_e1(x-ish)={a.max()-a.min():.3f} ext_e2(y-ish)={b.max()-b.min():.3f} z={Q[:,2].mean():.3f}')
