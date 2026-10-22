"""Signed-distance-field toolkit (numpy + mathutils BVH): grids, body SDF, blur, surface nets, implicit clipping, smoothing.

Conventions: field F < 0 inside the solid, > 0 outside (a distance in metres where possible).  All grids are node-centred:
node (i,j,k) sits at lo + h*(i,j,k).
"""
import time
import numpy as np
from mathutils import Vector


# ------------------------------------------------------------------------------------------------ grid
class Grid:
    def __init__(self, lo, hi, h):
        self.h = float(h)
        self.lo = np.asarray(lo, float)
        self.n = (np.ceil((np.asarray(hi, float) - self.lo) / self.h).astype(int) + 1)
        self.hi = self.lo + self.h * (self.n - 1)

    def axes(self):
        return [self.lo[a] + self.h * np.arange(self.n[a], dtype=np.float32) for a in range(3)]

    def coords(self):
        x, y, z = self.axes()
        return x[:, None, None], y[None, :, None], z[None, None, :]

    def points(self, mask=None):
        x, y, z = self.axes()
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        P = np.stack([X, Y, Z], axis=-1)
        return P[mask] if mask is not None else P.reshape(-1, 3)

    def sample(self, F, P):
        """Trilinear sample of a node field at points P (N,3)."""
        g = (np.asarray(P, float) - self.lo) / self.h
        i0 = np.floor(g).astype(int)
        i0 = np.clip(i0, 0, self.n - 2)
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

    def gradient(self, F, P, eps=None):
        eps = eps or self.h
        P = np.asarray(P, float)
        g = np.zeros_like(P)
        for a in range(3):
            d = np.zeros(3)
            d[a] = eps
            g[:, a] = (self.sample(F, P + d) - self.sample(F, P - d)) / (2 * eps)
        return g


# ------------------------------------------------------------------------------------------------ body SDF
def _eval_points(tree, P):
    """exact signed distance (sign from the nearest face normal) of points P (N,3) to one BVH tree."""
    out = np.empty(len(P), np.float32)
    find = tree.find_nearest
    for i, p in enumerate(P.tolist()):
        loc, n, idx, d = find(p)
        if idx is None:
            out[i] = 1e3
            continue
        out[i] = d if (p[0] - loc[0]) * n[0] + (p[1] - loc[1]) * n[1] + (p[2] - loc[2]) * n[2] >= 0 else -d
    return out


def _upsample(Fc, stride, n_fine):
    """linear upsample of a coarse node field (stride in fine nodes) to the fine node count."""
    out = Fc
    for a in range(3):
        nc = out.shape[a]
        xs = np.arange(n_fine[a], dtype=np.float32) / stride
        i0 = np.clip(np.floor(xs).astype(int), 0, nc - 2)
        f = np.clip(xs - i0, 0.0, 1.0).astype(np.float32)
        sl0 = [slice(None)] * 3
        sl1 = [slice(None)] * 3
        sl0[a] = i0
        sl1[a] = i0 + 1
        shape = [1, 1, 1]
        shape[a] = -1
        out = out[tuple(sl0)] * (1 - f).reshape(shape) + out[tuple(sl1)] * f.reshape(shape)
    return out.astype(np.float32)


def body_sdf(trees, grid, band=0.09, stride=3, verbose=True):
    """Signed distance of `grid` to the union of the bodies in `trees` (list of BVHTree).  Exact within |d|<band."""
    t0 = time.time()
    n = grid.n
    x, y, z = [a[::stride] for a in grid.axes()]
    Xc, Yc, Zc = np.meshgrid(x, y, z, indexing='ij')
    Pc = np.stack([Xc, Yc, Zc], -1).reshape(-1, 3)
    dc = None
    for tr in trees:
        d = _eval_points(tr, Pc)
        dc = d if dc is None else np.minimum(dc, d)
    dc = dc.reshape(Xc.shape)
    F = _upsample(dc, stride, n)
    # exact pass in the band
    m = np.abs(F) < (band + stride * grid.h * 0.9)
    idx = np.nonzero(m)
    if verbose:
        print(f"  body_sdf: grid {tuple(n)} = {np.prod(n)/1e6:.2f}M nodes, coarse {len(Pc)/1e3:.0f}k, band {m.sum()/1e6:.2f}M  ({time.time()-t0:.1f}s so far)")
    P = np.stack([grid.lo[0] + grid.h * idx[0], grid.lo[1] + grid.h * idx[1], grid.lo[2] + grid.h * idx[2]], 1)
    best = None
    for tr in trees:
        d = _eval_points(tr, P)
        best = d if best is None else np.minimum(best, d)
    F[idx] = best
    if verbose:
        print(f"  body_sdf done in {time.time()-t0:.1f}s")
    return F


# ------------------------------------------------------------------------------------------------ filtering
def gauss_kernel(sigma_vox):
    r = max(1, int(np.ceil(3 * sigma_vox)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_vox) ** 2)
    return (k / k.sum()).astype(np.float32), r


def gauss3(F, sigma_vox):
    if sigma_vox <= 0:
        return F
    k, r = gauss_kernel(sigma_vox)
    out = F
    for a in range(3):
        pad = [(0, 0)] * 3
        pad[a] = (r, r)
        P = np.pad(out, pad, mode='edge')
        acc = np.zeros_like(out)
        for j, w in enumerate(k):
            sl = [slice(None)] * 3
            sl[a] = slice(j, j + out.shape[a])
            acc += w * P[tuple(sl)]
        out = acc
    return out


# ------------------------------------------------------------------------------------------------ surface nets
_CORNERS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
_EDGES = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]


def surface_nets(F, grid, level=0.0):
    """Iso-surface F==level as a quad mesh (outward normals toward increasing F).  Returns V (n,3) float64, quads (m,4)."""
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
    if ncell == 0:
        return np.zeros((0, 3)), np.zeros((0, 4), int)
    vid = -np.ones((cx, cy, cz), np.int64)
    vid[ci, cj, ck] = np.arange(ncell)
    cv = np.stack([F[ci + dx, cj + dy, ck + dz] for dx, dy, dz in _CORNERS], 0).astype(np.float64)   # (8, ncell)
    acc = np.zeros((ncell, 3))
    num = np.zeros(ncell)
    for a, b in _EDGES:
        fa, fb = cv[a], cv[b]
        cross = (fa < 0) != (fb < 0)
        t = np.where(cross, fa / np.where(cross, fa - fb, 1.0), 0.0)
        pa = np.array(_CORNERS[a], float)
        pb = np.array(_CORNERS[b], float)
        pos = pa[None, :] + t[:, None] * (pb - pa)[None, :]
        acc += np.where(cross[:, None], pos, 0.0)
        num += cross
    Vg = acc / num[:, None] + np.stack([ci, cj, ck], 1)
    V = grid.lo + grid.h * Vg
    quads = []
    # x-edges: node (i,j,k)->(i+1,j,k); cells (i, j-1..j, k-1..k)
    for axis in range(3):
        a0 = [slice(None)] * 3
        a1 = [slice(None)] * 3
        a0[axis] = slice(0, F.shape[axis] - 1)
        a1[axis] = slice(1, F.shape[axis])
        lo_in = inside[tuple(a0)]
        hi_in = inside[tuple(a1)]
        sc = lo_in != hi_in
        # restrict to edges with a full ring of 4 cells
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
        # four cells around the edge, cyclic in the (o1,o2) plane
        def cell(d1, d2):
            c = list(idx)
            c[o1] = idx[o1] - 1 + d1
            c[o2] = idx[o2] - 1 + d2
            return vid[c[0], c[1], c[2]]
        q = np.stack([cell(0, 0), cell(1, 0), cell(1, 1), cell(0, 1)], 1)
        # outward direction along +axis if lower node inside
        outward_pos = lo_in[ii, jj, kk]
        # fix orientation per quad against the outward direction
        P4 = V[q]                                         # (m,4,3)
        n = np.cross(P4[:, 2] - P4[:, 0], P4[:, 3] - P4[:, 1])
        s = n[:, axis] * np.where(outward_pos, 1.0, -1.0)
        flip = s < 0
        q[flip] = q[flip][:, ::-1]
        quads.append(q)
    quads = np.concatenate(quads, 0) if quads else np.zeros((0, 4), int)
    return V, quads


def quads_to_tris(V, Q):
    """split quads along the shorter diagonal."""
    d02 = np.linalg.norm(V[Q[:, 0]] - V[Q[:, 2]], axis=1)
    d13 = np.linalg.norm(V[Q[:, 1]] - V[Q[:, 3]], axis=1)
    a = d02 <= d13
    T1 = np.where(a[:, None], Q[:, [0, 1, 2]], Q[:, [1, 2, 3]])
    T2 = np.where(a[:, None], Q[:, [0, 2, 3]], Q[:, [1, 3, 0]])
    return np.concatenate([T1, T2], 0)


# ------------------------------------------------------------------------------------------------ mesh utilities
def edge_list(F):
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 0)
    E.sort(axis=1)
    return np.unique(E, axis=0)


def compact(V, F, *vattrs):
    used = np.unique(F)
    remap = -np.ones(len(V), int)
    remap[used] = np.arange(len(used))
    out = [V[used], remap[F]] + [a[used] for a in vattrs]
    return out


def components(F, nv):
    """connected component label per vertex (labels propagate over triangle edges)."""
    lab = np.arange(nv)
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 0)
    while True:
        m = np.minimum(lab[E[:, 0]], lab[E[:, 1]])
        new = lab.copy()
        np.minimum.at(new, E[:, 0], m)
        np.minimum.at(new, E[:, 1], m)
        # pointer jumping
        new = new[new]
        if np.array_equal(new, lab):
            break
        lab = new
    return lab


def keep_largest(V, F):
    lab = components(F, len(V))
    flab = lab[F[:, 0]]
    ids, cnts = np.unique(flab, return_counts=True)
    keep = ids[np.argmax(cnts)]
    return compact(V, F[flab == keep])


def boundary_edges(F):
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 0)
    key = np.sort(E, axis=1)
    _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    inv = inv.reshape(-1)
    return E[cnt[inv] == 1]       # directed edges as in their triangle


def boundary_loops(F):
    """ordered vertex loops of the open boundary (list of int arrays)."""
    be = boundary_edges(F)
    nxt = {}
    for a, b in be.tolist():
        nxt.setdefault(a, []).append(b)
    loops = []
    seen = set()
    for a in list(nxt):
        if a in seen:
            continue
        loop = [a]
        seen.add(a)
        cur = a
        while True:
            cand = [b for b in nxt.get(cur, []) if b not in seen]
            if not cand:
                break
            cur = cand[0]
            loop.append(cur)
            seen.add(cur)
        loops.append(np.array(loop))
    return loops


def adjacency(V, F):
    """CSR-ish neighbour lists via edge list; returns (E, deg)"""
    E = edge_list(F)
    deg = np.bincount(E.ravel(), minlength=len(V)).astype(float)
    return E, deg


def laplacian_smooth(V, F, iters=10, lam=0.5, fixed=None, E=None):
    if E is None:
        E = edge_list(F)
    deg = np.bincount(E.ravel(), minlength=len(V)).astype(float)
    deg[deg == 0] = 1
    V = V.copy()
    for _ in range(iters):
        acc = np.zeros_like(V)
        np.add.at(acc, E[:, 0], V[E[:, 1]])
        np.add.at(acc, E[:, 1], V[E[:, 0]])
        avg = acc / deg[:, None]
        d = (avg - V) * lam
        if fixed is not None:
            d[fixed] = 0
        V += d
    return V


def taubin(V, F, iters=10, lam=0.5, mu=-0.53, fixed=None):
    E = edge_list(F)
    for _ in range(iters):
        V = laplacian_smooth(V, F, 1, lam, fixed, E)
        V = laplacian_smooth(V, F, 1, mu, fixed, E)
    return V


# ------------------------------------------------------------------------------------------------ implicit clipping
def clip_mesh(V, F, c, vattrs=()):
    """Remove the part of a triangle mesh where c(v) > 0 (c given per vertex), cutting triangles exactly at c == 0 (linear along edges).
    vattrs: tuple of per-vertex arrays interpolated to the new vertices.  Returns (V2, F2, attrs2, new_vertex_mask)."""
    c = np.asarray(c, float)
    out_ = c > 0
    nout = out_[F].sum(1)
    keep_all = nout == 0
    mixed = (nout == 1) | (nout == 2)
    Vn = [V]
    An = [list(vattrs)]
    nv = len(V)
    # edges of mixed tris that cross
    Fm = F[mixed]
    E = np.concatenate([Fm[:, [0, 1]], Fm[:, [1, 2]], Fm[:, [2, 0]]], 0)
    cross = out_[E[:, 0]] != out_[E[:, 1]]
    Ec = E[cross]
    Ec = np.sort(Ec, axis=1)
    uE, inv = np.unique(Ec, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    ca, cb = c[uE[:, 0]], c[uE[:, 1]]
    t = ca / (ca - cb)
    newV = V[uE[:, 0]] + t[:, None] * (V[uE[:, 1]] - V[uE[:, 0]])
    new_attrs = [a[uE[:, 0]] + t.reshape((-1,) + (1,) * (a.ndim - 1)) * (a[uE[:, 1]] - a[uE[:, 0]]) for a in vattrs]
    emap = {}
    for k, (a, b) in enumerate(uE.tolist()):
        emap[(a, b)] = nv + k
    V2 = np.concatenate([V, newV], 0)
    A2 = [np.concatenate([a, na], 0) for a, na in zip(vattrs, new_attrs)]
    tris = [F[keep_all]]
    outs = []
    for tri in Fm.tolist():
        o = [out_[v] for v in tri]
        k = sum(o)
        if k == 1:
            i = o.index(True)
            a, b, cc = tri[i], tri[(i + 1) % 3], tri[(i + 2) % 3]       # a outside; b, cc inside (keeps winding a,b,cc)
            ab = emap[(min(a, b), max(a, b))]
            ac = emap[(min(a, cc), max(a, cc))]
            outs.append((ab, b, cc))
            outs.append((ab, cc, ac))
        else:       # two outside, one inside
            i = o.index(False)
            a, b, cc = tri[i], tri[(i + 1) % 3], tri[(i + 2) % 3]       # a inside
            ab = emap[(min(a, b), max(a, b))]
            ac = emap[(min(a, cc), max(a, cc))]
            outs.append((a, ab, ac))
    if outs:
        tris.append(np.array(outs, int))
    F2 = np.concatenate(tris, 0)
    newmask = np.zeros(len(V2), bool)
    newmask[nv:] = True
    # compact
    used = np.unique(F2)
    remap = -np.ones(len(V2), int)
    remap[used] = np.arange(len(used))
    return V2[used], remap[F2], [a[used] for a in A2], newmask[used]
