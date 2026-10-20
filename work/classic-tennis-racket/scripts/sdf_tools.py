"""Small SDF toolkit (numpy only): swept super-ellipse tube fields, polynomial smooth-min, surface nets, Taubin smoothing.
The surface-nets routine follows the approach used in work/standard-tennis-kit-wb/scripts/sdf.py (re-implemented here so this
folder has no cross-chat dependency)."""
import numpy as np


class Grid:
    def __init__(self, lo, hi, h):
        self.h = float(h)
        self.lo = np.asarray(lo, float)
        self.n = (np.ceil((np.asarray(hi, float) - self.lo) / self.h).astype(int) + 1)

    def axes(self):
        return [self.lo[a] + self.h * np.arange(self.n[a]) for a in range(3)]


def resample_path(path, hw, hd, step):
    """Densify a polyline (m,2) with per-vertex hw/hd to ~step spacing (linear). Returns pts (k,2), hw (k,), hd (k,)."""
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    k = max(int(np.ceil(s[-1] / step)) + 1, 2)
    su = np.linspace(0, s[-1], k)
    pts = np.stack([np.interp(su, s, path[:, 0]), np.interp(su, s, path[:, 1])], axis=1)
    return pts, np.interp(su, s, hw), np.interp(su, s, hd)


def _tangent2d(pts, closed):
    if closed:
        T = np.roll(pts, -1, axis=0) - np.roll(pts, 1, axis=0)
    else:
        T = np.empty_like(pts)
        T[1:-1] = pts[2:] - pts[:-2]
        T[0] = pts[1] - pts[0]
        T[-1] = pts[-1] - pts[-2]
    return T / np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)


def tube_field(grid, path, hw, hd, P, closed=False, step=0.0008, chunk=20000):
    """Approximate signed distance (m) to a planar swept super-ellipse tube (path in XY, depth along Z).
    d ~ (r-1)/|grad r|  with r = ((|n|/hw)^P + (|z|/hd)^P)^(1/P) in the local cross-section frame."""
    pts, hws, hds = resample_path(path if not closed else np.vstack([path, path[:1]]), hw if not closed else np.append(hw, hw[0]),
                                  hd if not closed else np.append(hd, hd[0]), step)
    if closed:
        pts, hws, hds = pts[:-1], hws[:-1], hds[:-1]
    T = _tangent2d(pts, closed)
    Nn = np.stack([-T[:, 1], T[:, 0]], axis=1)
    x, y, z = grid.axes()
    X, Y = np.meshgrid(x, y, indexing='ij')
    q = np.stack([X.ravel(), Y.ravel()], axis=1)
    idx = np.empty(len(q), np.int64)
    for a in range(0, len(q), chunk):
        d2 = ((q[a:a + chunk, None, :] - pts[None, :, :]) ** 2).sum(-1)
        idx[a:a + chunk] = d2.argmin(1)
    dq = q - pts[idx]
    n = (dq * Nn[idx]).sum(1)
    ax = (dq * T[idx]).sum(1)
    hwq, hdq = hws[idx], hds[idx]
    an = np.abs(n)[:, None]                                  # (M,1)
    az = np.abs(z)[None, :]                                  # (1,nz)
    fn = (an / hwq[:, None]) ** P
    fz = (az / hdq[:, None]) ** P
    f = fn + fz
    r = np.maximum(f, 1e-18) ** (1.0 / P)
    gn = (an ** (P - 1)) / (hwq[:, None] ** P)
    gz = (az ** (P - 1)) / (hdq[:, None] ** P)
    gr = np.sqrt(gn ** 2 + gz ** 2) / np.maximum(r, 1e-9) ** (P - 1)
    gr = np.maximum(gr, 1.0 / (1.3 * np.maximum(hwq, hdq))[:, None])
    d = (r - 1.0) / gr
    if not closed:
        # flat caps at both ends (only matter where an end is not buried inside another tube)
        over = np.zeros(len(q))
        first = idx == 0
        last = idx == len(pts) - 1
        over[first] = np.maximum(-ax[first], 0)
        over[last] = np.maximum(ax[last], 0)
        ov = over[:, None]
        d = np.where(ov > 0, np.maximum(d, ov), d)
    return d.reshape(len(x), len(y), len(z)).astype(np.float32)


def smin(a, b, k):
    """Polynomial smooth minimum (distance-like, blend radius k)."""
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


# ---------------------------------------------------------------- surface nets
_CORNERS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
_EDGES = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]


def surface_nets(F, grid, level=0.0):
    F = F - level
    nx, ny, nz = F.shape
    cx, cy, cz = nx - 1, ny - 1, nz - 1
    inside = F < 0
    cnt = np.zeros((cx, cy, cz), np.int8)
    for dx, dy, dz in _CORNERS:
        cnt += inside[dx:dx + cx, dy:dy + cy, dz:dz + cz]
    mask = (cnt > 0) & (cnt < 8)
    ci, cj, ck = np.nonzero(mask)
    ncell = len(ci)
    vid = -np.ones((cx, cy, cz), np.int64)
    vid[ci, cj, ck] = np.arange(ncell)
    cv = np.stack([F[ci + dx, cj + dy, ck + dz] for dx, dy, dz in _CORNERS], 0).astype(np.float64)
    acc = np.zeros((ncell, 3))
    num = np.zeros(ncell)
    for a, b in _EDGES:
        fa, fb = cv[a], cv[b]
        cross = (fa < 0) != (fb < 0)
        t = np.where(cross, fa / np.where(cross, fa - fb, 1.0), 0.0)
        pa, pb = np.array(_CORNERS[a], float), np.array(_CORNERS[b], float)
        acc += np.where(cross[:, None], pa[None, :] + t[:, None] * (pb - pa)[None, :], 0.0)
        num += cross
    Vg = acc / num[:, None] + np.stack([ci, cj, ck], 1)
    V = grid.lo + grid.h * Vg
    quads = []
    for axis in range(3):
        a0 = [slice(None)] * 3
        a1 = [slice(None)] * 3
        a0[axis] = slice(0, F.shape[axis] - 1)
        a1[axis] = slice(1, F.shape[axis])
        lo_in, hi_in = inside[tuple(a0)], inside[tuple(a1)]
        sc = lo_in != hi_in
        sel = [slice(None)] * 3
        for b in range(3):
            if b != axis:
                sel[b] = slice(1, F.shape[b] - 1)
        sc_full = np.zeros_like(sc)
        sc_full[tuple(sel)] = sc[tuple(sel)]
        ii, jj, kk = np.nonzero(sc_full)
        if len(ii) == 0:
            continue
        idx = [ii, jj, kk]
        o1, o2 = [b for b in range(3) if b != axis]

        def cell(d1, d2):
            c = list(idx)
            c[o1] = idx[o1] - 1 + d1
            c[o2] = idx[o2] - 1 + d2
            return vid[c[0], c[1], c[2]]
        q = np.stack([cell(0, 0), cell(1, 0), cell(1, 1), cell(0, 1)], 1)
        outward_pos = lo_in[ii, jj, kk]
        P4 = V[q]
        nrm = np.cross(P4[:, 2] - P4[:, 0], P4[:, 3] - P4[:, 1])
        s = nrm[:, axis] * np.where(outward_pos, 1.0, -1.0)
        flip = s < 0
        q[flip] = q[flip][:, ::-1]
        quads.append(q)
    quads = np.concatenate(quads, 0)
    return V, quads


def edge_list(F):
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 0)
    E.sort(axis=1)
    return np.unique(E, axis=0)


def taubin(V, F, iters=8, lam=0.5, mu=-0.53):
    E = edge_list(F)
    deg = np.bincount(E.ravel(), minlength=len(V)).astype(float)
    deg[deg == 0] = 1
    V = V.copy()
    for _ in range(iters):
        for w in (lam, mu):
            acc = np.zeros_like(V)
            np.add.at(acc, E[:, 0], V[E[:, 1]])
            np.add.at(acc, E[:, 1], V[E[:, 0]])
            V += w * (acc / deg[:, None] - V)
    return V


# ---------------------------------------------------------------- sampling helpers
def sample(F, grid, P):
    """Trilinear sample of node field F at points P (N,3)."""
    g = (np.asarray(P, float) - grid.lo) / grid.h
    i0 = np.clip(np.floor(g).astype(int), 0, grid.n - 2)
    f = np.clip(g - i0, 0.0, 1.0)
    out = np.zeros(len(P))
    for dx in (0, 1):
        wx = f[:, 0] if dx else 1 - f[:, 0]
        for dy in (0, 1):
            wy = f[:, 1] if dy else 1 - f[:, 1]
            for dz in (0, 1):
                wz = f[:, 2] if dz else 1 - f[:, 2]
                out += wx * wy * wz * F[i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz]
    return out


def gradient(F, grid, P, eps=None):
    eps = eps or grid.h
    P = np.asarray(P, float)
    g = np.zeros_like(P)
    for a in range(3):
        d = np.zeros(3)
        d[a] = eps
        g[:, a] = (sample(F, grid, P + d) - sample(F, grid, P - d)) / (2 * eps)
    return g


def quads_to_tris(V, Q):
    d02 = np.linalg.norm(V[Q[:, 0]] - V[Q[:, 2]], axis=1)
    d13 = np.linalg.norm(V[Q[:, 1]] - V[Q[:, 3]], axis=1)
    a = d02 <= d13
    T1 = np.where(a[:, None], Q[:, [0, 1, 2]], Q[:, [1, 2, 3]])
    T2 = np.where(a[:, None], Q[:, [0, 2, 3]], Q[:, [1, 3, 0]])
    return np.concatenate([T1, T2], 0)
