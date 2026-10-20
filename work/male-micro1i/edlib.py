"""Micro1i edit library: smooth, topology-preserving vertex edits on the Micro1h Body_M (pure numpy)."""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i')
from m1i_lib import *
import contours as C

mm = 1e-3


def sstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def vertex_normals(V, F):
    n = np.zeros_like(V)
    tri = np.array([f for f in F if len(f) == 3], np.int64); quad = np.array([f for f in F if len(f) == 4], np.int64)
    for G in (tri, quad):
        if not len(G): continue
        if G.shape[1] == 4:
            a, b, c, d = (V[G[:, k]] for k in range(4)); fn = np.cross(c - a, d - b)
        else:
            a, b, c = (V[G[:, k]] for k in range(3)); fn = np.cross(b - a, c - a)
        for k in range(G.shape[1]): np.add.at(n, G[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


class Mesh:
    def __init__(self, V, F):
        self.F = F; self.n = len(V)
        E = edges_of(F); self.E = E
        self.deg = np.bincount(np.concatenate([E[:, 0], E[:, 1]]), minlength=self.n).astype(float)

    def nbr_mean(self, P):
        s = np.zeros_like(P)
        np.add.at(s, self.E[:, 0], P[self.E[:, 1]]); np.add.at(s, self.E[:, 1], P[self.E[:, 0]])
        return s / np.maximum(self.deg, 1)[:, None]

    def taubin(self, P, w, iters=4, lam=0.5, mu=-0.53):
        """Taubin smoothing weighted per vertex by w in [0,1]"""
        P = P.copy(); w = np.asarray(w, float)[:, None]
        for _ in range(iters):
            for step in (lam, mu):
                P = P + w * step * (self.nbr_mean(P) - P)
        return P

    def laplacian_smooth_disp(self, D, w, iters=10):
        """smooth a displacement field (n,3) with umbrella smoothing, vertices with w=0 stay fixed"""
        D = D.copy(); w = np.asarray(w, float)[:, None]
        for _ in range(iters):
            D = D + w * 0.5 * (self.nbr_mean(D) - D)
        return D


def poly_smooth(x, y, sig):
    """gaussian smoothing of a sampled function y(x) (x increasing, uniform-ish)"""
    x = np.asarray(x, float); y = np.asarray(y, float)
    out = np.empty_like(y)
    for i in range(len(x)):
        w = np.exp(-0.5 * ((x - x[i]) / sig) ** 2); out[i] = (w * y).sum() / w.sum()
    return out


def q3_tangent_lines(rows, which='L'):
    """plate tangent lines per z for the far-side (left, which='L') or near-side (right 'R') contour of both 3/4 plates.
    returns dict name -> (zs, u_line) with u in metres relative to the camera frame u = x cos a + (y+0.1254) sin a"""
    out = {}
    for name in ('q3L', 'q3R'):
        v = Q3[name]
        pe = C.plate_extent(name, rows)
        rr = sorted(pe)
        zs = np.array([C.row_z(name, r) for r in rr])
        col = np.array([pe[r][0 if which == 'L' else 1] for r in rr])
        out[name] = (zs, (col - v['pm']) * K)
    return out
