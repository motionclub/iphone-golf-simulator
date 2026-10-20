"""angle (deg) between vertex normals (area-weighted, as the renderer uses) and a locally fitted smooth normal (plane+quadric, ring 2) -> npz scalar 'ang'. python3 normal_err.py mesh.npz out.npz"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, meshlib as ml
V, F, d = ml.load(sys.argv[1]); N, T, fn = ml.vertex_normals(V, F)
n = len(V); adj = ml.vertex_adj(F, n)
ang = np.zeros(n)
idx = np.where(V[:, 2] > 1.41)[0]
for v in idx:
    nb = ml.rings(adj, v, 3)
    if len(nb) < 8: continue
    d_ = V[nb] - V[v]; r = np.linalg.norm(d_, axis=1); m = r < 0.016
    if m.sum() < 8: continue
    d_ = d_[m]; r = r[m]
    # fit height field over the vertex normal frame, solve for the gradient (tilt) of the best-fit surface
    nv = N[v]; t1 = np.cross(nv, [0.0, 0.0, 1.0] if abs(nv[2]) < 0.9 else [1.0, 0.0, 0.0]); t1 /= np.linalg.norm(t1); t2 = np.cross(nv, t1)
    u = d_ @ t1; w = d_ @ t2; h = d_ @ nv
    A = np.stack([u, w, u * u, u * w, w * w], 1); wt = np.exp(-(r / 0.008) ** 2) + 1e-3
    sol = np.linalg.lstsq(A * wt[:, None], h * wt, rcond=None)[0]
    nf = nv - sol[0] * t1 - sol[1] * t2; nf /= np.linalg.norm(nf)
    ang[v] = np.degrees(np.arccos(np.clip(nv @ nf, -1, 1)))
np.savez(sys.argv[2], ang=ang)
sel = (V[:, 2] > 1.43) & (V[:, 2] < 1.52) & (np.abs(V[:, 0]) < 0.09) & (V[:, 1] < -0.02)
print('lower-face verts', int(sel.sum()), ' normal error deg: mean %.2f p90 %.2f p99 %.2f max %.2f' % (ang[sel].mean(), np.percentile(ang[sel], 90), np.percentile(ang[sel], 99), ang[sel].max()))
