"""GARMENT PIPELINE: sparse graph tools in plain numpy (no scipy): welded 'sewn' graph of a garment, weighted Laplacian, block CG,
diffusion. Rows are vertices; edges are stored sorted by source so A @ X is one np.add.reduceat."""
import numpy as np


def weld_groups(P, tol=2e-4):
    """vertices closer than tol (UV splits, sewn seams) -> group id per vertex."""
    q = np.round(P / tol).astype(np.int64)
    key = (q[:, 0] * 73856093) ^ (q[:, 1] * 19349663) ^ (q[:, 2] * 83492791)
    _, inv = np.unique(key, return_inverse=True)
    return inv


class Graph:
    def __init__(self, P, tri, extra_edges=None, weld_tol=2e-4, length_weight=True, weld=True):
        n = len(P); self.n = n
        e = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
        g = weld_groups(P, weld_tol)
        # weld: connect every vertex to the first vertex of its group (both ways)
        order = np.argsort(g, kind='stable'); gs = g[order]
        first = np.r_[True, gs[1:] != gs[:-1]]
        rep = order[np.maximum.accumulate(np.where(first, np.arange(n), 0))]
        w_ = np.stack([order, rep], 1)            # (vertex, first vertex of its weld group)
        w_ = w_[w_[:, 0] != w_[:, 1]]
        parts = [e, w_] if weld else [e]
        if extra_edges is not None and len(extra_edges): parts.append(np.asarray(extra_edges))
        e = np.concatenate(parts)
        e = np.concatenate([e, e[:, ::-1]])
        e = np.unique(e, axis=0)
        e = e[e[:, 0] != e[:, 1]]
        self.i, self.j = e[:, 0], e[:, 1]
        L = np.linalg.norm(P[self.i] - P[self.j], axis=1)
        welded = L < weld_tol * 2
        self.w = np.where(welded, 1.0 / max(np.median(L[~welded]) if (~welded).any() else 1e-3, 1e-4), 1.0 / np.maximum(L, 1e-4)) if length_weight else np.ones(len(L))
        self.elen = L
        o = np.argsort(self.i, kind='stable'); self.i, self.j, self.w, self.elen = self.i[o], self.j[o], self.w[o], self.elen[o]
        self.starts = np.searchsorted(self.i, np.arange(n))
        self.has = np.bincount(self.i, minlength=n) > 0
        self.deg = np.zeros(n); np.add.at(self.deg, self.i, self.w)
        self.group = g

    def A(self, X):
        """adjacency-weighted sum (n, k)."""
        X2 = X if X.ndim == 2 else X[:, None]
        prod = self.w[:, None] * X2[self.j]
        out = np.zeros((self.n, X2.shape[1]))
        if len(prod):
            s = np.add.reduceat(prod, self.starts[self.has], axis=0)
            out[self.has] = s
        return out if X.ndim == 2 else out[:, 0]

    def average(self, X):
        d = np.maximum(self.deg, 1e-12)
        return self.A(X) / (d[:, None] if X.ndim == 2 else d)

    def smooth(self, X, iters, lam=.5, mask=None):
        """explicit diffusion; mask (n,) in [0,1] scales the step per vertex."""
        m = 1.0 if mask is None else mask[:, None]
        for _ in range(iters):
            X = X + lam * m * (self.average(X) - X)
        return X

    def harmonic(self, X, known, iters=600, tol=1e-6):
        """fill unknown rows of X so that each is the weighted mean of its neighbours (Dirichlet = known rows). Block CG on L_uu."""
        unk = ~known
        if not unk.any(): return X
        X = X.copy()
        d = np.maximum(self.deg, 1e-12)

        def Luu(Y):
            full = np.zeros((self.n, Y.shape[1])); full[unk] = Y
            return (d[unk, None] * Y) - self.A(full)[unk]
        kn = X.copy(); kn[unk] = 0
        b = self.A(kn)[unk]                       # A_uk X_k
        Y = self.average(kn)[unk]                 # start: one averaging step
        r = b - Luu(Y); p = r.copy(); rs = (r * r).sum(0)
        b2 = np.maximum((b * b).sum(0), 1e-30)
        for _ in range(iters):
            Ap = Luu(p)
            a = rs / np.maximum((p * Ap).sum(0), 1e-30)
            Y += a * p; r -= a * Ap
            rn = (r * r).sum(0)
            if (rn / b2).max() < tol * tol: break
            p = r + (rn / np.maximum(rs, 1e-30)) * p; rs = rn
        X[unk] = Y
        return X

    def components(self):
        """connected components (labels) by label propagation (min label), vectorised."""
        lab = np.arange(self.n)
        while True:
            m = lab.copy()
            np.minimum.at(m, self.i, lab[self.j])
            m = m[m]                              # pointer jumping
            if (m == lab).all(): return np.unique(lab, return_inverse=True)[1]
            lab = m
