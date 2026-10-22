import numpy as np, pickle
A = np.load('baseline/mesh.npz')['co']; B = np.load('baseline/artdir_current_mesh.npz')['co']; n = len(A); Bn = B[:n]
def xlim(z): return np.where(z < 1.20, 0.205, np.where(z < 1.24, 0.205 + (z - 1.20) / 0.04 * 0.075, 0.28))
z = A[:, 2]; Zm = (z >= 0.77) & (z < 1.40) & (np.abs(A[:, 0]) <= xlim(z))
mv = np.any(A != Bn, axis=1); m = mv & Zm; P = A[m]; D = (Bn - A)[m] * 1000
print('moved-in-zone', m.sum())
ax = np.abs(P[:, 0]); print('|x| range %.3f..%.3f  z range %.3f..%.3f' % (ax.min(), ax.max(), P[:, 2].min(), P[:, 2].max()))
print('disp mm: max %.2f mean %.2f ; components mean |dx| %.2f |dy| %.2f |dz| %.2f' % (np.linalg.norm(D, axis=1).max(), np.linalg.norm(D, axis=1).mean(), np.abs(D[:, 0]).mean(), np.abs(D[:, 1]).mean(), np.abs(D[:, 2]).mean()))
# histogram of |x| of moved-in-zone
h, e = np.histogram(ax, bins=[0, .1, .15, .18, .2, .205, .22, .24, .26, .28, .3]); print('|x| hist', list(zip(np.round(e[:-1], 3), h)))
h, e = np.histogram(P[:, 2], bins=np.arange(0.77, 1.42, 0.05)); print('z hist', list(zip(np.round(e[:-1], 2), h)))
# top 10 largest
o = np.argsort(-np.linalg.norm(D, axis=1))[:8]
for i in o: print('  x %.3f y %.3f z %.3f  d (%.2f %.2f %.2f) mm' % (P[i, 0], P[i, 1], P[i, 2], *D[i]))
# FORM2 delta: do they overlap with FORM2-moved verts?
Dz = np.load('../male-parallel-torso2/export/form2_zone_delta.npz'); idx = Dz['indices']; print('FORM2 delta size', len(idx), 'keys', list(Dz.keys()))
f2 = np.zeros(n, bool); f2[idx] = True
print('moved-in-zone that are in the FORM2 delta set:', int((m & f2).sum()), '; moved-in-zone not in FORM2 set:', int((m & ~f2).sum()))
