"""Garment finishing + detail primitives: rims, inner return bands, ribbons (seams/piping), buttons, mesh accumulation.

A garment is accumulated as parts (V, F, N, mat) where N are custom per-vertex normals and mat is a per-face material slot
(0 = main fabric, 1 = piping).  Parts keep their own vertices so every sub-surface can carry its own normals.
"""
import numpy as np
from kitlib import *
from sdf import *


# ------------------------------------------------------------------------------------------------ accumulation
class Acc:
    def __init__(self):
        self.V, self.F, self.N, self.M, self.tag = [], [], [], [], []
        self.n = 0
        self.tagnames = []

    def add(self, V, F, N, mat, tag=''):
        V = np.asarray(V, float)
        F = np.asarray(F, int)
        N = np.asarray(N, float)
        ln = np.linalg.norm(N, axis=1, keepdims=True)
        ln[ln == 0] = 1
        N = N / ln
        self.V.append(V)
        self.F.append(F + self.n)
        self.N.append(N)
        m = np.full(len(F), mat, int) if np.isscalar(mat) else np.asarray(mat, int)
        self.M.append(m)
        if tag not in self.tagnames:
            self.tagnames.append(tag)
        self.tag.append(np.full(len(F), self.tagnames.index(tag), int))
        self.n += len(V)

    def merged(self):
        V = np.concatenate(self.V)
        F = np.concatenate(self.F)
        N = np.concatenate(self.N)
        M = np.concatenate(self.M)
        T = np.concatenate(self.tag)
        a = V[F[:, 1]] - V[F[:, 0]]
        b = V[F[:, 2]] - V[F[:, 0]]
        area = 0.5 * np.linalg.norm(np.cross(a, b), axis=1)
        keep = (area > 3e-10) & (F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])
        self.dropped_degenerate = int((~keep).sum())
        F, M, T = F[keep], M[keep], T[keep]
        used = np.unique(F)
        remap = -np.ones(len(V), int)
        remap[used] = np.arange(len(used))
        self._T = T
        return V[used], remap[F], N[used], M

    def tags(self):
        return self._T, list(self.tagnames)


def orient_outward(V, F, N, ref=None):
    """flip triangle windings whose geometric normal opposes the mean of their vertex normals."""
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    nm = N[F].sum(1)
    flip = np.einsum('ij,ij->i', fn, nm) < 0
    F = F.copy()
    F[flip] = F[flip][:, [0, 2, 1]]
    return F


# ------------------------------------------------------------------------------------------------ surface projector
class Surface:
    """projects points onto a garment sheet and gives smooth analytic normals from the shell field."""

    def __init__(self, V, F, grid=None, field=None):
        self.V, self.F = V, F
        self.tree = bvh_from(V, F)
        self.grid, self.field = grid, field
        self._vn = vertex_normals(V, F)

    def nearest(self, P):
        P = np.asarray(P, float)
        loc = np.empty_like(P)
        nrm = np.empty_like(P)
        for i, p in enumerate(P.tolist()):
            l, n, idx, d = self.tree.find_nearest(p)
            loc[i] = l
            nrm[i] = n
        if self.grid is not None:
            g = self.grid.gradient(self.field, loc, eps=self.grid.h * 0.6)
            ln = np.linalg.norm(g, axis=1, keepdims=True)
            ok = ln[:, 0] > 1e-6
            nrm[ok] = g[ok] / ln[ok]
        return loc, nrm

    def normals_at(self, P):
        return self.nearest(P)[1]

    def cast_polar(self, center_xy, thetas, zs, rout=0.6):
        """rays from outside toward the vertical axis through center_xy at polar angles theta (0 = front -y, +pi/2 = +x) and heights zs."""
        thetas = np.asarray(thetas, float)
        zs = np.asarray(zs, float)
        cx, cy = center_xy
        loc = np.empty((len(thetas), 3))
        for i, (th, z) in enumerate(zip(thetas.tolist(), zs.tolist())):
            dxy = np.array([np.sin(th), -np.cos(th)])
            o = [cx + dxy[0] * rout, cy + dxy[1] * rout, z]
            l, n, idx, dist = self.tree.ray_cast(o, [-dxy[0], -dxy[1], 0.0])
            if idx is None:
                l2, _, _, _ = self.tree.find_nearest([cx + dxy[0] * 0.1, cy + dxy[1] * 0.1, z])
                l = l2
            loc[i] = l
        _, nrm = self.nearest(loc)
        return loc, nrm

    def cast(self, P, direction, fallback=True, return_miss=False):
        """first hit of rays from P along `direction`; returns (loc, nrm) (falls back to the nearest point on a miss unless fallback=False;
        return_miss=True also returns the miss mask)."""
        P = np.asarray(P, float)
        d = unit(direction)
        loc = np.empty_like(P)
        miss = np.zeros(len(P), bool)
        for i, p in enumerate(P.tolist()):
            l, n, idx, dist = self.tree.ray_cast(p, d.tolist())
            if idx is None:
                miss[i] = True
                loc[i] = p
            else:
                loc[i] = l
        if miss.any() and fallback:
            l2, _ = self.nearest(P[miss])
            loc[miss] = l2
        # smooth normals from the field at the hit locations
        _, nrm = self.nearest(loc)
        if return_miss:
            return loc, nrm, miss
        return loc, nrm


def ring_points(surf, center_xy, z, n=72, rout=0.6, theta0=0.0):
    """n points on the sheet at height z around the vertical axis (outside-in rays), for closed ring ribbons."""
    th = theta0 + np.linspace(0, 2 * np.pi, n, endpoint=False)
    loc, _ = surf.cast_polar(center_xy, th, np.full(n, z), rout)
    return loc


def vertex_field_normals(grid, field, P):
    g = grid.gradient(field, P, eps=grid.h * 0.6)
    ln = np.linalg.norm(g, axis=1, keepdims=True)
    ln[ln == 0] = 1
    return g / ln


# ------------------------------------------------------------------------------------------------ thickness: rims + inner bands
def graph_distance(V, F, seeds, iters=60):
    E = edge_list(F)
    L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    dist = np.full(len(V), np.inf)
    dist[seeds] = 0
    for _ in range(iters):
        new = dist.copy()
        np.minimum.at(new, E[:, 1], dist[E[:, 0]] + L)
        np.minimum.at(new, E[:, 0], dist[E[:, 1]] + L)
        if np.array_equal(new, dist):
            break
        dist = new
    return dist


def boundary_outdir(V, F, N, loop):
    """unit tangent-plane direction pointing away from the sheet at each vertex of a boundary loop."""
    nb = {}
    for tri in F.tolist():
        for k in range(3):
            nb.setdefault(tri[k], set()).update((tri[(k + 1) % 3], tri[(k + 2) % 3]))
    lp = set(loop.tolist())
    out = np.zeros((len(loop), 3))
    for i, v in enumerate(loop.tolist()):
        inner = [u for u in nb[v] if u not in lp]
        if not inner:
            inner = list(nb[v])
        c = V[inner].mean(0)
        d = V[v] - c
        d = d - N[v] * (d @ N[v])
        ln = np.linalg.norm(d)
        out[i] = d / ln if ln > 0 else N[v]
    # smooth the directions along the loop (removes the scallops of a grid-cut boundary)
    for _ in range(4):
        out = 0.25 * np.roll(out, 1, 0) + 0.5 * out + 0.25 * np.roll(out, -1, 0)
    ln = np.linalg.norm(out, axis=1, keepdims=True)
    ln[ln == 0] = 1
    return out / ln


def add_sheet(acc, V, F, N, mat=0, tag='sheet'):
    acc.add(V, F, N, mat, tag)


def add_rims_and_inner(acc, V, F, N, t=0.002, depth=0.02, piped=None, rim_roll=0.35, mat_main=0, mat_pipe=1, inner=True, skip=None):
    """thickness at every open boundary: rounded rim strip (3 rows) + inner return band `depth` deep.
    piped: dict loop_index -> bool (rim in piping material); default False."""
    loops = boundary_loops(F)
    piped = piped or {}
    infos = []
    keep_idx = [i for i, l in enumerate(loops) if not (skip is not None and skip(V[l]))]
    allb = np.concatenate([loops[i] for i in keep_idx]) if keep_idx else np.zeros(0, int)
    # inner band (faces whose vertices are all within `depth` of any boundary)
    if inner and len(allb):
        dist = graph_distance(V, F, allb)
        fm = (dist[F] <= depth).all(1)
        # include faces touching the band so that the band reaches `depth`
        used = np.unique(F[fm])
        remap = -np.ones(len(V), int)
        remap[used] = np.arange(len(used))
        Vi = V[used] - N[used] * t
        Fi = remap[F[fm]][:, [0, 2, 1]]
        acc.add(Vi, Fi, -N[used], mat_main, 'inner')
    for li, loop in enumerate(loops):
        if li not in keep_idx:
            continue
        u = boundary_outdir(V, F, N, loop)
        Nl = N[loop]
        P0 = V[loop]
        P1 = P0 + u * (rim_roll * t) - Nl * (0.5 * t)
        P2 = P0 - Nl * t
        n = len(loop)
        Vr = np.concatenate([P0, P1, P2])
        Nr = np.concatenate([Nl, u, -Nl])
        quads = []
        for k in range(n):
            k2 = (k + 1) % n
            quads.append((k, k2, n + k2, n + k))
            quads.append((n + k, n + k2, 2 * n + k2, 2 * n + k))
        quads = np.array(quads)
        Fr = np.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]], 0)
        Fr = orient_outward(Vr, Fr, Nr)
        acc.add(Vr, Fr, Nr, mat_pipe if piped.get(li, False) else mat_main, f'rim{li}')
    return loops


# ------------------------------------------------------------------------------------------------ closed double-walled shells
def rim_strip(V, N, Vi, loop, u, tl, bull=1.0, rows=4):
    """bullnose edge between the outer boundary (V[loop]) and the inner boundary (Vi[loop]): half-ellipse in the (N, u) plane,
    semi-axes tl/2 (along N) and bull*tl/2 (along u, outward).  Returns (V, F, N) of the strip (rows x len(loop) vertices)."""
    n = len(loop)
    Nl = N[loop]
    P0 = V[loop]
    P2 = Vi[loop]
    C = 0.5 * (P0 + P2)
    half = 0.5 * (P0 - P2)                        # = N * tl / 2 (exactly along the normal)
    R = []
    RN = []
    for r in range(rows):
        phi = np.pi * r / (rows - 1)
        if r == 0:
            R.append(P0)
            RN.append(Nl)
        elif r == rows - 1:
            R.append(P2)
            RN.append(-Nl)
        else:
            c, s = np.cos(phi), np.sin(phi)
            R.append(C + half * c + u * (bull * 0.5 * tl * s)[:, None])
            d = Nl * c + u * s
            RN.append(d)
    Vr = np.concatenate(R)
    Nr = np.concatenate(RN)
    # winding from the loop direction (boundary_loops follows the sheet's own directed boundary edges a->b): the strip must traverse each shared
    # edge b->a, so the closed shell is consistently oriented by construction (no per-triangle guessing)
    quads = []
    for r in range(rows - 1):
        for k in range(n):
            k2 = (k + 1) % n
            quads.append((r * n + k2, r * n + k, (r + 1) * n + k, (r + 1) * n + k2))
    quads = np.array(quads)
    Fr = np.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]], 0)
    return Vr, Fr, Nr


def ensure_inner_clearance(V, N, tv, trees, c_inner, iters=6):
    """closed shells: the INNER wall (V - N*tv) must stay >= c_inner off the body.  Where it is closer, the outer sheet vertex is pushed out along its
    normal by the deficit (a few convex tips - toes, heels - where the nearest-face direction and the sheet normal disagree)."""
    V = V.copy()
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    tv = np.broadcast_to(np.asarray(tv, float), (len(V),))
    for it in range(iters):
        Vi = V - N * tv[:, None]
        moved = 0
        for i, p in enumerate(Vi.tolist()):
            best = None
            for tr in trees:
                loc, n, idx, d = tr.find_nearest(p)
                if idx is None:
                    continue
                sg = (p[0] - loc[0]) * n[0] + (p[1] - loc[1]) * n[1] + (p[2] - loc[2]) * n[2]
                sd = d if sg >= 0 else -d
                if best is None or sd < best:
                    best = sd
            if best is not None and best < c_inner:
                V[i] += N[i] * (c_inner - best + 5e-5)
                moved += 1
        if moved == 0:
            break
    return V


def fix_inner_overlaps(V, F, N, tv, trees, step=0.0005, iters=14, verbose=False):
    """triangle-level check of the INNER wall (V - N*tv) against the body meshes: a flat triangle can cut across a curved limb or a toe tip even when all
    its vertices are clear.  Vertices of intersecting inner triangles are pushed out along their normals (outer sheet moves with them) until none intersect."""
    V = V.copy()
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    tv = np.broadcast_to(np.asarray(tv, float), (len(V),))
    for it in range(iters):
        Vi = V - N * tv[:, None]
        tin = bvh_from(Vi, F)
        bad = set()
        for tb in trees:
            for pi, pb in tin.overlap(tb):
                bad.add(pi)
        if verbose:
            print(f'    fix_inner_overlaps it{it}: {len(bad)} inner triangles intersect the body')
        if not bad:
            break
        vid = np.unique(F[sorted(bad)])
        V[vid] += N[vid] * step
    return V


def add_closed_shell(acc, V, F, N, tv, mat=0, face_mat=None, tag='shell', bull=1.0, rim_rows=4, mat_rim=None, loops_keep=None):
    """Open sheet (V, F, N) -> closed double-walled shell: outer sheet, inner sheet (V - N*tv, reversed, N flipped) and a bullnose rim strip on
    every boundary loop.  tv: wall thickness (scalar or per-vertex).  The three parts keep their own vertices (own normals); weld_parts() merges
    the coincident rim/sheet vertices into one watertight manifold at the end.  Returns dict(Vi=inner vertices, loops=boundary loops)."""
    V = np.asarray(V, float)
    N = np.asarray(N, float)
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    tv = np.broadcast_to(np.asarray(tv, float), (len(V),)).copy()
    Vi = V - N * tv[:, None]
    fm = mat if face_mat is None else face_mat
    acc.add(V, F, N, fm, tag + '_out')
    acc.add(Vi, F[:, [0, 2, 1]], -N, fm, tag + '_in')
    loops = boundary_loops(F)
    n_be = len(boundary_edges(F))
    if sum(len(l) for l in loops) != n_be:
        print(f'  WARNING add_closed_shell[{tag}]: boundary loops cover {sum(len(l) for l in loops)} of {n_be} boundary edges (pinched loop?)')
    mr = (mat if np.isscalar(mat) else 0) if mat_rim is None else mat_rim
    for li, loop in enumerate(loops):
        if len(loop) < 3:
            continue
        u = boundary_outdir(V, F, N, loop)
        Vr, Fr, Nr = rim_strip(V, N, Vi, loop, u, tv[loop], bull=bull, rows=rim_rows)
        acc.add(Vr, Fr, Nr, mr, f'{tag}_rim{li}')
    return dict(Vi=Vi, loops=loops)


def weld_parts(V, F, N, M, T=None, eps=1e-7):
    """merge vertices that sit at the same position (rim/sheet seams of the closed shells).  The original per-vertex normals are kept as
    per-corner (loop) normals so the smooth shading is unchanged.  Returns (Vw, Fw, LN (3*len(Fw), 3), Mw, Tw)."""
    V = np.asarray(V, float)
    key = np.round(V / eps).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.reshape(-1)
    Vw = V[first]
    Fw = inv[np.asarray(F)]
    ok = (Fw[:, 0] != Fw[:, 1]) & (Fw[:, 1] != Fw[:, 2]) & (Fw[:, 0] != Fw[:, 2])
    LN = np.asarray(N, float)[np.asarray(F)]
    Mw = np.asarray(M)[ok]
    Tw = None if T is None else np.asarray(T)[ok]
    return Vw, Fw[ok], LN[ok].reshape(-1, 3), Mw, Tw


def mesh_topology(V, F):
    """watertightness report of a triangle mesh (after welding): boundary / non-manifold / inconsistent-direction edges and island count."""
    F = np.asarray(F)
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 0)
    Es = np.sort(E, axis=1)
    u, inv, cnt = np.unique(Es, axis=0, return_inverse=True, return_counts=True)
    d, dc = np.unique(E, axis=0, return_counts=True)
    par = np.arange(len(V))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for a, b in u.tolist():
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    used = np.unique(F)
    roots = {}
    for a in used.tolist():
        roots.setdefault(find(a), []).append(a)
    return dict(boundary_edges=int((cnt == 1).sum()), nonmanifold_edges=int((cnt > 2).sum()), same_direction_edges=int((dc > 1).sum()),
                islands=len(roots), island_sizes=sorted((len(v) for v in roots.values()), reverse=True))


def fill_small_holes(V, F, LN, M, T, max_len=8):
    """close boundary loops of <= max_len edges (pinched slivers of the iso-surface meshes) with a flat fan wound against the loop direction;
    new faces take the material/tag of the adjacent face and the geometric face normal.  Returns (F, LN, M, T, n_filled)."""
    loops = boundary_loops(F)
    be = boundary_edges(F)
    if not loops or not len(be):
        return F, LN, M, T, 0
    owner = {}
    for fi, f in enumerate(F.tolist()):
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            owner[(a, b)] = fi
    newF, newLN, newM, newT = [], [], [], []
    nfill = 0
    for loop in loops:
        k = len(loop)
        if k < 3 or k > max_len:
            continue
        ok = all((int(loop[i]), int(loop[(i + 1) % k])) in owner for i in range(k))
        if not ok:
            continue
        fi = owner[(int(loop[0]), int(loop[1]))]
        for i in range(1, k - 1):
            tri = [int(loop[0]), int(loop[i + 1]), int(loop[i])]
            n = np.cross(V[tri[1]] - V[tri[0]], V[tri[2]] - V[tri[0]])
            ln = np.linalg.norm(n)
            n = n / ln if ln > 0 else np.array([0, 0, 1.0])
            newF.append(tri)
            newLN.append(np.tile(n, (3, 1)))
            newM.append(M[fi])
            newT.append(None if T is None else T[fi])
        nfill += 1
    if not newF:
        return F, LN, M, T, 0
    F2 = np.concatenate([F, np.array(newF)])
    LN2 = np.concatenate([LN, np.concatenate(newLN)])
    M2 = np.concatenate([M, np.array(newM)])
    T2 = None if T is None else np.concatenate([T, np.array(newT)])
    return F2, LN2, M2, T2, nfill


def finalize_acc(acc):
    """merged + welded accumulator -> dict(V, F, LN (per-corner normals), M, T, tagnames, topo).  Faces keep their order (LN is 3 normals per face)."""
    Vf, Ff, Nf, Mf = acc.merged()
    T, tn = acc.tags()
    Vw, Fw, LN, Mw, Tw = weld_parts(Vf, Ff, Nf, Mf, T)
    Fw, LN, Mw, Tw, nfill = fill_small_holes(Vw, Fw, LN, Mw, Tw)
    topo = mesh_topology(Vw, Fw)
    topo['small_holes_filled'] = nfill
    return dict(V=Vw, F=Fw, LN=LN, M=Mw, T=Tw, tagnames=np.array(tn), topo=topo)


def mirror_part(res):
    """reflect a finalized part across x = 0: positions and per-corner normals reflected, triangle winding swapped (corner order 1<->2)."""
    out = dict(res)
    out['V'] = res['V'] * np.array([-1, 1, 1])
    out['F'] = res['F'][:, [0, 2, 1]]
    out['LN'] = (res['LN'].reshape(-1, 3, 3)[:, [0, 2, 1], :] * np.array([-1, 1, 1])).reshape(-1, 3)
    return out


def save_part(path, res):
    np.savez(path, V=res['V'], F=res['F'], LN=res['LN'], M=res['M'], T=res['T'], tagnames=res['tagnames'])


# ------------------------------------------------------------------------------------------------ curves
def catmull(P, spacing, closed=False):
    """Catmull-Rom through control points, resampled at ~spacing arc length."""
    P = np.asarray(P, float)
    if closed:
        P = np.concatenate([P[-1:], P, P[:2]])
    else:
        P = np.concatenate([2 * P[:1] - P[1:2], P, 2 * P[-1:] - P[-2:-1]])
    pts = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        seg = np.linalg.norm(p2 - p1)
        m = max(2, int(np.ceil(seg / spacing * 1.5)))
        for s in np.linspace(0, 1, m, endpoint=False):
            s2, s3 = s * s, s ** 3
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s2 + (-p0 + 3 * p1 - 3 * p2 + p3) * s3))
    if not closed:
        pts.append(P[-2])
    pts = np.array(pts)
    return resample(pts, spacing, closed)


def resample(pts, spacing, closed=False):
    pts = np.asarray(pts, float)
    if closed:
        pts = np.concatenate([pts, pts[:1]])
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    total = s[-1]
    n = max(2, int(round(total / spacing)))
    t = np.linspace(0, total, n + (0 if closed else 1), endpoint=not closed)
    out = np.stack([np.interp(t, s, pts[:, a]) for a in range(3)], 1)
    return out


def smooth_path(P, iters=3, closed=False):
    P = P.copy()
    for _ in range(iters):
        if closed:
            P = 0.25 * np.roll(P, 1, 0) + 0.5 * P + 0.25 * np.roll(P, -1, 0)
        else:
            Q = P.copy()
            Q[1:-1] = 0.25 * P[:-2] + 0.5 * P[1:-1] + 0.25 * P[2:]
            P = Q
    return P


# ------------------------------------------------------------------------------------------------ ribbons / buttons
RIBBON_MIN_SPACING = 0.0075
RIBBON_BIAS = 0.0007
RIBBON_BASE = 0.0008          # depth the closed ribbon base is buried into the shell wall (m)


def ribbon(acc, surf, ctrl, width, lift, mat=0, spacing=0.003, closed=False, taper_end=0.0, tag='ribbon', profile=None, ray=None, polar=None, base=None):
    """raised ribbon following `ctrl` (control points) projected onto the sheet.  Returns the projected centre line.
    base: depth of the buried closing base (m); the ribbon is then a closed island (default RIBBON_BASE, 0 = old open strip)."""
    # closure: base=None -> 'flat' (closed profile, flat underside; cheapest watertight island), base=0 -> 'open' (old strip), base>0 -> 'buried' base rows
    closure = 'flat' if base is None else ('open' if base == 0 else 'buried')
    base = 0.0 if closure != 'buried' else base
    spacing = max(spacing, RIBBON_MIN_SPACING)
    if profile is None and width <= 0.0045:
        profile = [(-0.5, 0.2, -55), (0.0, 1.0, 0), (0.5, 0.2, 55)]
    if polar is not None:
        # ctrl are (theta, z) pairs; densify in (theta, z) space, cast outside-in rays about the vertical axis polar=(cx, cy)
        pr = 0.17
        c2 = np.array([[t * pr, z, 0.0] for t, z in ctrl])
        dense = catmull(c2, spacing * 1.0, closed)
        loc, nrm = surf.cast_polar(polar, dense[:, 0] / pr, dense[:, 1])
    else:
        pts = catmull(ctrl, spacing, closed)
        if ray is not None:
            loc, nrm, miss = surf.cast(pts, ray, fallback=False, return_miss=True)
            if miss.any():                                  # rays that leave the sheet (sleeve opening, hem) are dropped, never snapped to some far 'nearest' point
                loc, nrm = loc[~miss], nrm[~miss]
                if len(loc) < 3:
                    return loc
        else:
            loc, nrm = surf.nearest(pts)
    for _ in range(2):                       # project again after smoothing for a clean path
        loc = smooth_path(loc, 3, closed)
        loc, nrm = surf.nearest(loc)
    loc = smooth_path(loc, 2, closed)
    loc, nrm = surf.nearest(loc)
    loc = loc + nrm * RIBBON_BIAS          # facets of the coarse shell sag below the smooth surface: keep thin ribbons from dipping in and out (dashes)
    n = len(loc)
    tg = np.zeros_like(loc)
    if closed:
        tg = np.roll(loc, -1, 0) - np.roll(loc, 1, 0)
    else:
        tg[1:-1] = loc[2:] - loc[:-2]
        tg[0] = loc[1] - loc[0]
        tg[-1] = loc[-1] - loc[-2]
    ln = np.linalg.norm(tg, axis=1, keepdims=True)
    bad = ln[:, 0] < 1e-9
    if bad.any():
        good = np.nonzero(~bad)[0]
        for k in np.nonzero(bad)[0]:
            tg[k] = tg[good[np.argmin(np.abs(good - k))]]
        ln = np.linalg.norm(tg, axis=1, keepdims=True)
    tg /= ln
    side = np.cross(nrm, tg)
    side /= np.linalg.norm(side, axis=1, keepdims=True)
    # cross-section (offset across, height, slope angle for the normal)
    prof = profile or [(-0.5, 0.15, -60), (-0.3, 0.85, -25), (0.0, 1.0, 0), (0.3, 0.85, 25), (0.5, 0.15, 60)]
    # taper the ends (width scale)
    ws = np.ones(n)
    if taper_end > 0 and not closed:
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(loc, axis=0), axis=1))])
        ws = np.clip(np.minimum(L, L[-1] - L) / taper_end, 0.25, 1.0)
    rows, rn = [], []
    for off, hh, ang in prof:
        a = np.radians(ang)
        rows.append(loc + side * (off * width * ws)[:, None] + nrm * (hh * lift * ws)[:, None] * 1.0)
        rn.append(nrm * np.cos(a) + side * np.sin(a))
    if closure == 'buried':
        # closed section: buried base row on each side (inside the wall of the shell it sits on) + flat underside -> every ribbon is its own closed island
        lo_off, hi_off = prof[0][0], prof[-1][0]
        bl = loc + side * (lo_off * width * ws)[:, None] - nrm * base
        br = loc + side * (hi_off * width * ws)[:, None] - nrm * base
        rows = [bl] + rows + [br]
        rn = [-side] + rn + [side]
    nr = len(rows)
    V = np.concatenate(rows)
    Nn = np.concatenate(rn)
    quads = []
    last = n if closed else n - 1
    closed_prof = closure != 'open'
    ncross = nr if closed_prof else nr - 1                  # closed profile wraps from the last row back to the first
    for j in range(ncross):
        j2 = (j + 1) % nr
        for k in range(last):
            k2 = (k + 1) % n
            quads.append((j * n + k, j * n + k2, j2 * n + k2, j2 * n + k))
    quads = np.array(quads)
    Fq = np.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]], 0)
    if closed_prof:
        # the (profile x path) grid has one uniform winding by construction: a single outward test (section centroid) decides the flip for ALL faces
        secc = np.stack(rows, 1).mean(1)                    # (n, 3) section centroids
        kk = np.minimum(Fq[:, 0] % n, n - 1)
        fn = np.cross(V[Fq[:, 1]] - V[Fq[:, 0]], V[Fq[:, 2]] - V[Fq[:, 0]])
        fc = V[Fq].mean(1)
        if np.einsum('ij,ij->i', fn, fc - secc[kk]).sum() < 0:
            Fq = Fq[:, [0, 2, 1]]
    else:
        Fq = orient_outward(V, Fq, Nn)
    if not closed:       # end caps
        caps = []
        for base_k, rev in ((0, False), (n - 1, True)):
            ring = [j * n + base_k for j in range(nr)]
            for j in range(1, nr - 1):
                tri = (ring[0], ring[j], ring[j + 1])
                caps.append(tri[::-1] if rev else tri)
        caps = np.array(caps)
        if closed_prof:
            ec = np.stack(rows, 1).mean(1)
            tg_e = np.array([tg[0], tg[-1]])
            which = (caps[:, 0] % n) == (n - 1)
            fn = np.cross(V[caps[:, 1]] - V[caps[:, 0]], V[caps[:, 2]] - V[caps[:, 0]])
            want = np.where(which[:, None], tg[-1][None, :], -tg[0][None, :])      # end caps face along / against the path
            score = np.einsum('ij,ij->i', fn, want)
            for end in (False, True):                       # each end cap is one planar polygon: its winding is decided once (area-weighted)
                m = which == end
                if m.any() and score[m].sum() < 0:
                    caps[m] = caps[m][:, [0, 2, 1]]
        else:
            caps = orient_outward(V, caps, Nn)
        Fq = np.concatenate([Fq, caps])
    acc.add(V, Fq, Nn, mat, tag)
    return loc


def dome(acc, center, normal, radius, height, mat=0, seg=12, rings=3, tag='button'):
    """button / eyelet: low dome disc on a surface point (rings of decreasing radius + a single apex vertex; no degenerate triangles)."""
    n = unit(normal)
    a = np.cross(n, [0, 0, 1.0])
    if np.linalg.norm(a) < 1e-3:
        a = np.cross(n, [0, 1.0, 0])
    a = unit(a)
    b = np.cross(n, a)
    V, N = [], []
    for r in range(rings):                       # rings 0 .. rings-1 (the apex is added separately)
        f = r / rings
        rr = radius * np.cos(f * np.pi / 2)
        hh = height * (0.3 + 0.7 * np.sin(f * np.pi / 2))
        sl = f * np.pi / 2
        for s in range(seg):
            ang = 2 * np.pi * s / seg
            d = a * np.cos(ang) + b * np.sin(ang)
            V.append(center + d * rr + n * hh)
            N.append(n * np.sin(sl + 0.4) + d * np.cos(sl + 0.4))
    apex = len(V)
    V.append(center + n * height)
    N.append(n)
    base0 = len(V)
    for s in range(seg):
        ang = 2 * np.pi * s / seg
        d = a * np.cos(ang) + b * np.sin(ang)
        V.append(center + d * radius - n * 0.0005)
        N.append(d)
    cb = len(V)                                  # base cap centre (closes the dome so it is its own watertight island)
    V.append(center - n * 0.0005)
    N.append(-n)
    V = np.array(V)
    N = np.array(N)
    F = []
    for r in range(rings - 1):
        for s in range(seg):
            s2 = (s + 1) % seg
            F.append((r * seg + s, r * seg + s2, (r + 1) * seg + s2))
            F.append((r * seg + s, (r + 1) * seg + s2, (r + 1) * seg + s))
    last = (rings - 1) * seg
    for s in range(seg):
        s2 = (s + 1) % seg
        F.append((last + s, last + s2, apex))
    for s in range(seg):
        s2 = (s + 1) % seg
        F.append((base0 + s, base0 + s2, s2))
        F.append((base0 + s, s2, s))
        F.append((cb, base0 + s2, base0 + s))
    F = orient_outward(V, np.array(F), N)
    acc.add(V, F, N, mat, tag)


def tube(acc, pts, radius, mat=0, sides=6, tag='tube', cap=True):
    """round tube along a polyline (for laces etc.)."""
    pts = np.asarray(pts, float)
    n = len(pts)
    tg = np.zeros_like(pts)
    tg[1:-1] = pts[2:] - pts[:-2]
    tg[0] = pts[1] - pts[0]
    tg[-1] = pts[-1] - pts[-2]
    tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    ref = np.array([0, 0, 1.0])
    V, N = [], []
    for i in range(n):
        a = np.cross(tg[i], ref)
        if np.linalg.norm(a) < 1e-3:
            a = np.cross(tg[i], [0, 1.0, 0])
        a = unit(a)
        b = np.cross(tg[i], a)
        rad = radius[i] if hasattr(radius, '__len__') else radius
        for s in range(sides):
            ang = 2 * np.pi * s / sides
            d = a * np.cos(ang) + b * np.sin(ang)
            V.append(pts[i] + d * rad)
            N.append(d)
    V = np.array(V)
    N = np.array(N)
    F = []
    for i in range(n - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            F.append((i * sides + s, (i + 1) * sides + s, (i + 1) * sides + s2))
            F.append((i * sides + s, (i + 1) * sides + s2, i * sides + s2))
    F = np.array(F)
    if cap:
        c0 = len(V)
        V = np.vstack([V, pts[0] - tg[0] * 0.0, pts[-1]])
        N = np.vstack([N, -tg[0], tg[-1]])
        extra = []
        for s in range(sides):
            s2 = (s + 1) % sides
            extra.append((c0, s2, s))
            extra.append((c0 + 1, (n - 1) * sides + s, (n - 1) * sides + s2))
        F = np.vstack([F, np.array(extra)])
    F = orient_outward(V, F, N)
    acc.add(V, F, N, mat, tag)


# ------------------------------------------------------------------------------------------------ clearance enforcement
def enforce_clearance(V, F, trees, c_min, iters=4, smooth=0, fixed=None, verbose=True):
    """push shell vertices out of every body (list of BVHTree) until signed clearance >= c_min; light Taubin between rounds.
    Returns the new vertices (the shell stays a single sheet; no topology change)."""
    V = V.copy()
    E = edge_list(F)
    worst0 = None
    for it in range(iters):
        moved = 0
        worst = 1e9
        for i, p in enumerate(V.tolist()):
            best = None
            for tr in trees:
                loc, n, idx, d = tr.find_nearest(p)
                if idx is None:
                    continue
                s = (p[0] - loc[0]) * n[0] + (p[1] - loc[1]) * n[1] + (p[2] - loc[2]) * n[2]
                sd = d if s >= 0 else -d
                if best is None or sd < best[0]:
                    best = (sd, loc, n)
            if best is None:
                continue
            sd, loc, n = best
            cm = c_min(p) if callable(c_min) else c_min
            worst = min(worst, sd - cm + (c_min if not callable(c_min) else 0.0))
            if sd < cm:
                tgt = (loc[0] + n[0] * cm, loc[1] + n[1] * cm, loc[2] + n[2] * cm)
                V[i] = tgt
                moved += 1
        if worst0 is None:
            worst0 = worst
        if verbose:
            print(f'    enforce_clearance it{it}: worst {worst*1000:+.2f} mm, moved {moved}')
        if moved == 0:
            break
        # spread the correction a little (Laplacian on the whole sheet is too aggressive -> only 2 light passes)
        for _ in range(smooth):
            V = laplacian_smooth(V, F, 1, 0.25, fixed=None, E=E)
    return V


def enforce_clearance_zone(V, F, tree, c_min, zlo, zhi, axis=None, iters=12, verbose=False):
    """keep shell vertices with zlo <= z <= zhi at signed distance >= c_min from ONE closed obstacle (the waistband).  Vertices are moved
    HORIZONTALLY away from the obstacle's vertical axis `axis` (cx, cy) - never up/down - so the lap of a hem over a band edge keeps its height.
    Without `axis` the push follows the nearest-face normal."""
    V = V.copy()
    zone = np.nonzero((V[:, 2] >= zlo) & (V[:, 2] <= zhi))[0]
    for it in range(iters):
        moved = 0
        worst = 1e9
        for i in zone.tolist():
            p = V[i]
            loc, n, idx, d = tree.find_nearest(p.tolist())
            if idx is None:
                continue
            sg = (p[0] - loc[0]) * n[0] + (p[1] - loc[1]) * n[1] + (p[2] - loc[2]) * n[2]
            sd = d if sg >= 0 else -d
            worst = min(worst, sd)
            if sd < c_min:
                if axis is None:
                    V[i] = (loc[0] + n[0] * c_min, loc[1] + n[1] * c_min, loc[2] + n[2] * c_min)
                else:
                    h = np.array([p[0] - axis[0], p[1] - axis[1], 0.0])
                    ln = np.linalg.norm(h)
                    if ln < 1e-9:
                        continue
                    h /= ln
                    V[i] = p + h * max(0.0004, 0.8 * (c_min - sd))        # small horizontal steps converge without overshoot
                moved += 1
        if verbose:
            print(f'    enforce_zone it{it}: worst {worst*1000:+.2f} mm, moved {moved}')
        if moved == 0:
            break
    return V


def resolve_overlaps(V, F, meshes, step=0.0015, iters=8, verbose=True):
    """meshes: list of (Vb, Fb).  Garment triangles that intersect a body triangle (vertices may still be clear) are pushed outward
    along their smooth vertex normals until the BVH overlap test is empty."""
    V = V.copy()
    btrees = [bvh_from(Vb, Fb) for Vb, Fb in meshes]
    for it in range(iters):
        tg = bvh_from(V, F)
        bad = set()
        for tb in btrees:
            for pg, pb in tg.overlap(tb):
                bad.add(pg)
        if verbose:
            print(f'    resolve_overlaps it{it}: {len(bad)} garment tris overlapping')
        if not bad:
            break
        vid = np.unique(F[sorted(bad)])
        N = vertex_normals(V, F)
        V[vid] += N[vid] * step
        # spread to the 1-ring a little so that no tiny spikes appear
        E = edge_list(F)
        m = np.zeros(len(V), bool)
        m[vid] = True
        ring = np.unique(np.concatenate([E[m[E[:, 0]], 1], E[m[E[:, 1]], 0]]))
        ring = np.setdiff1d(ring, vid)
        V[ring] += N[ring] * (0.5 * step)
    return V


def smooth_boundaries(V, F, iters=4, snap=True):
    """smooth every open boundary loop along itself (removes grid-cut zigzag) and snap the moved vertices back onto the sheet."""
    V = V.copy()
    loops = boundary_loops(F)
    tree = bvh_from(V, F) if snap else None
    for l in loops:
        P = V[l].copy()
        for _ in range(iters):
            P = 0.25 * np.roll(P, 1, 0) + 0.5 * P + 0.25 * np.roll(P, -1, 0)
        if snap:
            for i, p in enumerate(P.tolist()):
                loc, n, idx, d = tree.find_nearest(p)
                P[i] = loc
        V[l] = P
    return V


def add_rim_segments(acc, V, F, N, t=0.002, vmask=None, piped=False, rim_roll=0.35, mat_main=0, mat_pipe=1, tag='rimseg', inner_depth=0.0):
    """rim strips only along boundary edges whose both vertices satisfy vmask (bool per vertex); other boundary segments are left open."""
    loops = boundary_loops(F)
    for li, loop in enumerate(loops):
        u = boundary_outdir(V, F, N, loop)
        Nl = N[loop]
        P0 = V[loop]
        P1 = P0 + u * (rim_roll * t) - Nl * (0.5 * t)
        P2 = P0 - Nl * t
        n = len(loop)
        Vr = np.concatenate([P0, P1, P2])
        Nr = np.concatenate([Nl, u, -Nl])
        ok = vmask[loop]
        quads = []
        for kk in range(n):
            k2 = (kk + 1) % n
            if not (ok[kk] and ok[k2]):
                continue
            quads.append((kk, k2, n + k2, n + kk))
            quads.append((n + kk, n + k2, 2 * n + k2, 2 * n + kk))
        if not quads:
            continue
        quads = np.array(quads)
        Fr = np.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]], 0)
        Fr = orient_outward(Vr, Fr, Nr)
        acc.add(Vr, Fr, Nr, mat_pipe if piped else mat_main, tag)


def ring_at_z(V, F, z, n=72, which='longest'):
    """ordered closed ring of points on a sheet at height z (slice of the mesh), resampled to n points; None if the slice is empty."""
    loops = [P for P in slice_plane(V, F, 2, float(z)) if len(P) >= 8]
    if not loops:
        return None
    seglen = lambda a: float(np.sum(np.linalg.norm(np.diff(np.vstack([a, a[:1]]), axis=0), axis=1)))
    P = max(loops, key=seglen) if which == 'longest' else loops[which]
    Pc = np.concatenate([P, P[:1]])
    seg = np.linalg.norm(np.diff(Pc, axis=0), axis=1)
    c = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, c[-1], n, endpoint=False)
    return np.stack([np.interp(t, c, Pc[:, a]) for a in range(3)], 1)


def resolve_overlaps_body(V, F, bodies_meshes, step=0.0015, iters=14, verbose=True, extra=0.0):
    """like resolve_overlaps but the push direction comes from the BODY: each vertex of an overlapping garment triangle moves along the outward
    normal of the nearest body surface point (works for double-sided strips whose own normals face the skin).  bodies_meshes: list of (Vb, Fb)."""
    V = V.copy()
    btrees = [bvh_from(Vb, Fb) for Vb, Fb in bodies_meshes]
    for it in range(iters):
        tg = bvh_from(V, F)
        bad = set()
        for tb in btrees:
            for pg, pb in tg.overlap(tb):
                bad.add(pg)
        if verbose:
            print(f'    resolve_overlaps_body it{it}: {len(bad)} garment tris overlapping')
        if not bad:
            break
        vid = np.unique(F[sorted(bad)])
        for i in vid.tolist():
            best = None
            for tb in btrees:
                loc, n, idx, d = tb.find_nearest(V[i].tolist())
                if idx is not None and (best is None or d < best[0]):
                    best = (d, n)
            if best is not None:
                V[i] += np.array(best[1]) * step
        E = edge_list(F)
        m = np.zeros(len(V), bool)
        m[vid] = True
        ring = np.unique(np.concatenate([E[m[E[:, 0]], 1], E[m[E[:, 1]], 0]]))
        ring = np.setdiff1d(ring, vid)
        for i in ring.tolist():
            best = None
            for tb in btrees:
                loc, n, idx, d = tb.find_nearest(V[i].tolist())
                if idx is not None and (best is None or d < best[0]):
                    best = (d, n)
            if best is not None:
                V[i] += np.array(best[1]) * (0.5 * step)
    return V
