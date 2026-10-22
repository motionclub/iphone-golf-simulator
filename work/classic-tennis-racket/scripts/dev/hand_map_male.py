"""ASCII occupancy map of the male right hand in its PCA frame (u fingers, v across (+ = thumb side), w palm normal)."""
import numpy as np

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/'
d = np.load(W + 'data/male_body.npz')
co, tris = d['co'], d['tris']
sel = np.where((co[:, 0] < -0.50) & (co[:, 2] < 1.0))[0]
P = co[sel]
c = P.mean(0)
U, S, Vt = np.linalg.svd(P - c, full_matrices=False)
u, v, w = Vt[0], Vt[1], Vt[2]
if u[2] > 0: u = -u               # fingers point down
if v[1] > 0: v = -v               # +v = front (-Y) = thumb side
w = np.cross(u, v)                # right-handed (u, v, w)
print('u', u.round(3), 'v', v.round(3), 'w', w.round(3), 'w.x', w[0].round(3))
Q = np.stack([(P - c) @ u, (P - c) @ v, (P - c) @ w], 1)
print('u range', Q[:, 0].min().round(3), Q[:, 0].max().round(3), 'v range', Q[:, 1].min().round(3), Q[:, 1].max().round(3), 'w range', Q[:, 2].min().round(3), Q[:, 2].max().round(3))
du, dv = 0.006, 0.004
U0, U1 = -0.14, Q[:, 0].max() + 0.01
V0, V1 = Q[:, 1].min() - 0.005, Q[:, 1].max() + 0.005
nu = int((U1 - U0) / du) + 1; nv = int((V1 - V0) / dv) + 1
grid = np.full((nu, nv), ' ')
wmin = np.full((nu, nv), np.inf); wmax = np.full((nu, nv), -np.inf)
for q in Q:
    i = int((q[0] - U0) / du); j = int((q[1] - V0) / dv)
    wmin[i, j] = min(wmin[i, j], q[2]); wmax[i, j] = max(wmax[i, j], q[2])
for i in range(nu):
    row = ''
    for j in range(nv):
        row += '#' if np.isfinite(wmin[i, j]) else '.'
    print(f'u={U0 + i * du:+.3f} {row}')
print('v columns: from', round(V0, 3), 'to', round(V1, 3), 'step', dv, ' (+v = thumb/front side on the right)')
