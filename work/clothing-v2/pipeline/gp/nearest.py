"""GARMENT PIPELINE: vectorised nearest point on a triangle mesh (numpy only, no BVH loops).
Grid nearest-vertex search (multi-level cells), then the exact closest point on the triangles around that vertex (and its one-ring)."""
import numpy as np


class PointGrid:
    def __init__(self, X, h):
        self.X, self.h = X, h
        c = np.floor(X / h).astype(np.int64)
        self.key = self._key(c)
        self.order = np.argsort(self.key, kind='stable')
        self.sk = self.key[self.order]

    @staticmethod
    def _key(c):
        c = c + (1 << 20)
        return (c[:, 0] << 42) | (c[:, 1] << 21) | c[:, 2]

    def nearest(self, Q, k2=False, budget=3_000_000):
        """-> nearest index (-1 if none in the 27 cells), distance[, second nearest index]. Vectorised over (query, point) pairs,
        processed in chunks of at most `budget` pairs so coarse cells never blow up memory."""
        n = len(Q); best = np.full(n, -1); bd = np.full(n, np.inf); sec = np.full(n, -1)
        if n == 0: return (best, bd, sec) if k2 else (best, bd)
        offs = np.array([(x, y, z) for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1)])
        cq_all = np.floor(Q / self.h).astype(np.int64)
        S = np.empty((n, 27), np.int64); E = np.empty((n, 27), np.int64)
        for o in range(27):
            k = self._key(cq_all + offs[o])
            S[:, o] = np.searchsorted(self.sk, k, 'left'); E[:, o] = np.searchsorted(self.sk, k, 'right')
        per = (E - S).sum(1)
        cum = np.cumsum(per)
        c0 = 0
        while c0 < n:
            base = cum[c0 - 1] if c0 else 0
            c1 = int(np.searchsorted(cum, base + budget, 'right'))
            c1 = max(c1, c0 + 1); c1 = min(c1, n)
            s = S[c0:c1].ravel(); cnt = (E[c0:c1] - S[c0:c1]).ravel()
            tot = int(cnt.sum())
            if tot:
                m = c1 - c0
                qid = np.repeat(np.arange(m * 27) // 27, cnt)          # non-decreasing
                start = np.repeat(s - np.cumsum(np.r_[0, cnt[:-1]]), cnt)
                pid = self.order[start + np.arange(tot)]
                d = np.linalg.norm(Q[c0:c1][qid] - self.X[pid], axis=1)
                segs = np.nonzero(np.r_[True, qid[1:] != qid[:-1]])[0]
                qs = qid[segs]
                dmin = np.minimum.reduceat(d, segs)
                seg_of = np.repeat(np.arange(len(segs)), np.diff(np.r_[segs, len(d)]))
                hit = d == dmin[seg_of]
                first = np.full(len(segs), -1); idx = np.nonzero(hit)[0]
                first[seg_of[idx[::-1]]] = idx[::-1]                   # first hit per segment
                best[c0 + qs] = pid[first]; bd[c0 + qs] = dmin
                if k2:
                    d2 = d.copy(); d2[first] = np.inf
                    dmin2 = np.minimum.reduceat(d2, segs)
                    ok = np.isfinite(dmin2)
                    hit2 = (d2 == dmin2[seg_of]) & ok[seg_of]
                    sec_i = np.full(len(segs), -1); idx2 = np.nonzero(hit2)[0]
                    sec_i[seg_of[idx2[::-1]]] = idx2[::-1]
                    sec[c0 + qs[ok]] = pid[sec_i[ok]]
            c0 = c1
        return (best, bd, sec) if k2 else (best, bd)


def closest_on_tris(p, a, b, c):
    """vectorised closest point on triangles (Ericson). -> point, barycentric (n,3)."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b; d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c; d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    n = len(p); bc = np.zeros((n, 3))
    den = np.where(np.abs(va + vb + vc) > 1e-30, va + vb + vc, 1e-30)
    v = vb / den; w = vc / den; bc[:] = np.stack([1 - v - w, v, w], 1)
    sd = lambda x, y: np.where(np.abs(y) > 1e-30, x / np.where(np.abs(y) > 1e-30, y, 1), 0)
    # edge regions (later assignments win in priority order reversed below)
    r = (vb <= 0) & (d5 - d6 >= 0) & False
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = sd(d4 - d3, (d4 - d3) + (d5 - d6)); bc[m] = np.stack([0 * t, 1 - t, t], 1)[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    t = sd(d2, d2 - d6); bc[m] = np.stack([1 - t, 0 * t, t], 1)[m]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    t = sd(d1, d1 - d3); bc[m] = np.stack([1 - t, t, 0 * t], 1)[m]
    m = (d6 >= 0) & (d5 <= d6); bc[m] = [0, 0, 1]
    m = (d3 >= 0) & (d4 <= d3); bc[m] = [0, 1, 0]
    m = (d1 <= 0) & (d2 <= 0); bc[m] = [1, 0, 0]
    pt = bc[:, :1] * a + bc[:, 1:2] * b + bc[:, 2:] * c
    return pt, bc


class Surface:
    """nearest point queries against a triangle mesh whose vertex positions may change per pose (topology fixed)."""
    def __init__(self, tri, nverts):
        self.tri = np.asarray(tri, np.int64)
        # faces around each vertex (padded) + faces around its one-ring neighbours
        vf = [[] for _ in range(nverts)]
        for f, t in enumerate(self.tri):
            for v in t: vf[v].append(f)
        mx = max((len(x) for x in vf), default=1)
        self.vf = np.full((nverts, mx), -1, np.int64)
        for v, x in enumerate(vf): self.vf[v, :len(x)] = x
        used = np.zeros(nverts, bool); used[self.tri.ravel()] = True
        self.used = np.nonzero(used)[0]

    def _grids(self, P, levels):
        """grids over the current vertex positions, cached while the same position array is queried again (solver rounds)."""
        if getattr(self, '_gkey', None) is not P:
            self._gkey, self._gcache = P, {}
        for h in levels:
            if h not in self._gcache: self._gcache[h] = PointGrid(P[self.used], h)
        return self._gcache

    def query(self, P, Q, levels=(.008, .016, .032, .064, .128, .4)):
        """P current vertex positions; -> dist, point, face, bary, normal (face normal at the hit)."""
        n = len(Q); best = np.full(n, -1); bd = np.full(n, np.inf); sec = np.full(n, -1)
        todo = np.arange(n)
        grids = self._grids(P, levels)
        for h in levels:
            i, d, i2 = grids[h].nearest(Q[todo], k2=True)
            ok = (i >= 0) & (d <= h)
            best[todo[ok]] = self.used[i[ok]]; bd[todo[ok]] = d[ok]
            sec[todo[ok]] = np.where(i2[ok] >= 0, self.used[np.clip(i2[ok], 0, None)], self.used[i[ok]])
            todo = todo[~ok]
            if not len(todo): break
        if len(todo):  # brute force leftovers (rare)
            for q in todo:
                d = np.linalg.norm(P[self.used] - Q[q], axis=1); j = int(d.argmin()); best[q] = self.used[j]; bd[q] = d[j]; sec[q] = best[q]
        # candidate faces around the two nearest vertices: one vectorised closest-point call over all (query, face) pairs
        F = np.concatenate([self.vf[best], self.vf[sec]], 1)
        qi, col = np.nonzero(F >= 0)
        ff = F[qi, col]
        pt, bc = closest_on_tris(Q[qi], P[self.tri[ff, 0]], P[self.tri[ff, 1]], P[self.tri[ff, 2]])
        d = np.linalg.norm(Q[qi] - pt, axis=1)
        segs = np.nonzero(np.r_[True, qi[1:] != qi[:-1]])[0]
        dmin = np.minimum.reduceat(d, segs)
        seg_of = np.repeat(np.arange(len(segs)), np.diff(np.r_[segs, len(d)]))
        hit = np.nonzero(d == dmin[seg_of])[0]
        pick = np.full(len(segs), -1); pick[seg_of[hit[::-1]]] = hit[::-1]
        bestd = np.full(n, np.inf); bp = np.zeros((n, 3)); bf = np.full(n, -1); bb = np.zeros((n, 3))
        q = qi[segs]
        bestd[q] = dmin; bp[q] = pt[pick]; bf[q] = ff[pick]; bb[q] = bc[pick]
        fn = np.cross(P[self.tri[bf, 1]] - P[self.tri[bf, 0]], P[self.tri[bf, 2]] - P[self.tri[bf, 0]])
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        return bestd, bp, bf, bb, fn

    def signed(self, P, Q, vnormals=None):
        """signed distance (>0 outside) using the interpolated vertex normal at the hit (smooth sign near edges)."""
        d, pt, f, bc, fn = self.query(P, Q)
        if vnormals is not None:
            nn = (bc[:, :, None] * vnormals[self.tri[f]]).sum(1)
            nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
        else: nn = fn
        s = np.sign(((Q - pt) * nn).sum(1)); s[s == 0] = 1
        return s * d, pt, f, bc, nn
