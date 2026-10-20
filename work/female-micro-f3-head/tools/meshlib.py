"""numpy mesh helpers for the F2 lower-face work (pure numpy, system python3 or Blender python).
load(npz) -> V, F (list of arrays) ; adjacency ; vertex normals ; principal curvatures by quadric fit ; dihedral angles."""
import numpy as np


def load(path):
    d = np.load(path, allow_pickle=True)
    V = d['V'].astype(np.float64); off = d['Foff']; flat = d['F']
    F = [flat[off[i]:off[i + 1]] for i in range(len(off) - 1)]
    return V, F, d


def tri_fan(F):
    T = []
    for fi, f in enumerate(F):
        for i in range(1, len(f) - 1): T.append((int(f[0]), int(f[i]), int(f[i + 1]), fi))
    return np.array(T, np.int64)


def vertex_adj(F, n):
    adj = [set() for _ in range(n)]
    for f in F:
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m]); adj[a].add(b); adj[b].add(a)
    return adj


def vertex_normals(V, F):
    T = tri_fan(F)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    fn = np.cross(b - a, c - a)                      # area-weighted
    N = np.zeros_like(V)
    for k in range(3): np.add.at(N, T[:, k], fn)
    nn = np.linalg.norm(N, axis=1, keepdims=True)
    return N / np.maximum(nn, 1e-30), T, fn


def face_normals(V, F):
    out = np.zeros((len(F), 3))
    for i, f in enumerate(F):
        p = V[f]; n = np.zeros(3)
        for j in range(1, len(f) - 1): n += np.cross(p[j] - p[0], p[j + 1] - p[0])
        out[i] = n / max(np.linalg.norm(n), 1e-30)
    return out


def rings(adj, v, k):
    S = {v}; fr = {v}
    for _ in range(k):
        nx = set()
        for u in fr: nx |= adj[u]
        nx -= S; S |= nx; fr = nx
    S.discard(v)
    return list(S)


def curvature(V, F, N=None, ring=2, rad=None, idx=None):
    """principal curvatures (convex positive, 1/m) by a weighted quadric fit in the tangent plane. returns k1 >= k2 (n,), and the principal direction of k1 (n,3).
    ring: neighbourhood rings; rad: optional max neighbour distance (m)."""
    n = len(V)
    adj = vertex_adj(F, n)
    if N is None: N, _, _ = vertex_normals(V, F)
    k1 = np.zeros(n); k2 = np.zeros(n); d1 = np.zeros((n, 3))
    ids = range(n) if idx is None else idx
    for v in ids:
        nb = rings(adj, v, ring)
        if len(nb) < 5: continue
        d = V[nb] - V[v]
        if rad is not None:
            m = np.linalg.norm(d, axis=1) < rad; d = d[m]
            if len(d) < 5: continue
        nv = N[v]
        t1 = np.cross(nv, [0.0, 0.0, 1.0] if abs(nv[2]) < 0.9 else [1.0, 0.0, 0.0]); t1 /= np.linalg.norm(t1); t2 = np.cross(nv, t1)
        u = d @ t1; w = d @ t2; h = d @ nv
        A = np.stack([u * u, u * w, w * w, u, w], 1)
        r = np.linalg.norm(d, axis=1); wt = 1.0 / (r + 1e-4)
        sol = np.linalg.lstsq(A * wt[:, None], h * wt, rcond=None)[0]
        a, b, c = sol[0], sol[1], sol[2]
        Hs = np.array([[2 * a, b], [b, 2 * c]])           # hessian of the height field along the outward normal
        ev, evec = np.linalg.eigh(-Hs)                    # convex -> positive
        k2[v], k1[v] = ev[0], ev[1]
        e = evec[:, 1]; d1[v] = e[0] * t1 + e[1] * t2
    return k1, k2, d1


def dihedral(V, F):
    """per undirected edge: angle (deg) between the two adjacent face normals; returns dict (a,b)->deg"""
    fn = face_normals(V, F)
    em = {}
    for fi, f in enumerate(F):
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m]); key = (min(a, b), max(a, b)); em.setdefault(key, []).append(fi)
    out = {}
    for k, fs in em.items():
        if len(fs) == 2:
            c = float(np.clip(np.dot(fn[fs[0]], fn[fs[1]]), -1, 1)); out[k] = np.degrees(np.arccos(c))
    return out


def edge_stats(V, F):
    e = set()
    for f in F:
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m]); e.add((min(a, b), max(a, b)))
    e = np.array(sorted(e)); L = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1)
    return e, L
