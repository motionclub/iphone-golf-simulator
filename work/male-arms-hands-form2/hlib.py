"""Shared helpers for the male arms+hands form pass (frames, mesh IO, topology)."""
import numpy as np, pickle
from pathlib import Path
from collections import defaultdict
W = Path(__file__).resolve().parent
R = W.parents[1]

# ---- right-hand local frame (same constants as work/male-micro1e/hand_sdf.py): local = (a', n, w)
#  w along the hand (wrist -> fingertips), n = palm normal (+n = palm side), a' = across, +a' = front / thumb side
O = np.array([0.554, -0.0775, 0.925])
D = np.array([0.63709983, -0.11248794, -0.76252886]); D /= np.linalg.norm(D)
A = np.array([0.0, -1.0, 0.0]); A = A - A.dot(D) * D; A /= np.linalg.norm(A)
N = np.cross(D, A); N /= np.linalg.norm(N)
A_SHIFT = 0.0175
O2 = O + A_SHIFT * A

def to_local(P, side=+1):
    Q = np.array(P, float).copy()
    if side < 0: Q[:, 0] = -Q[:, 0]
    Rr = Q - O2
    return np.stack([Rr @ A, Rr @ N, Rr @ D], 1)

def to_global(L, side=+1):
    L = np.asarray(L, float)
    P = O2 + L[:, 0:1] * A + L[:, 1:2] * N + L[:, 2:3] * D
    if side < 0:
        P = P.copy(); P[:, 0] = -P[:, 0]
    return P

def smooth01(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

# ---- mesh container
class Mesh:
    """V (n,3) float32, polys: list of tuples (CCW as stored in Blender)."""
    def __init__(self, V, polys):
        self.V = np.asarray(V); self.polys = [tuple(int(i) for i in p) for p in polys]
    @staticmethod
    def from_npz(path):
        D_ = np.load(path)
        cv, ls, lt = D_['corner_verts'], D_['loop_start'], D_['loop_total']
        polys = [tuple(cv[s:s + t]) for s, t in zip(ls, lt)]
        return Mesh(D_['V'], polys)
    def tris(self):
        T = []
        for p in self.polys:
            for k in range(1, len(p) - 1):
                T.append((p[0], p[k], p[k + 1]))
        return np.array(T, np.int64)
    def arrays(self):
        sizes = np.array([len(p) for p in self.polys], np.int32)
        ls = np.r_[0, np.cumsum(sizes)[:-1]].astype(np.int32)
        cv = np.array([i for p in self.polys for i in p], np.int32)
        return cv, ls, sizes

def edges_of(polys):
    E = set()
    for f in polys:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            E.add((min(a, b), max(a, b)))
    return np.array(sorted(E))

def edge_faces(polys):
    ef = {}
    for fi, f in enumerate(polys):
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            ef.setdefault((min(a, b), max(a, b)), []).append(fi)
    return ef

def face_normals(V, polys):
    Nn = np.zeros((len(polys), 3))
    for i, f in enumerate(polys):
        p = V[list(f)].astype(np.float64); q = np.roll(p, -1, 0)
        Nn[i] = [((p[:, 1] - q[:, 1]) * (p[:, 2] + q[:, 2])).sum(), ((p[:, 2] - q[:, 2]) * (p[:, 0] + q[:, 0])).sum(), ((p[:, 0] - q[:, 0]) * (p[:, 1] + q[:, 1])).sum()]
    l = np.linalg.norm(Nn, axis=1, keepdims=True); return Nn / np.maximum(l, 1e-15)

def taubin(V, E, w, iters, lam=0.5, mu=-0.53):
    n = len(V); deg = np.bincount(E.ravel(), minlength=n).astype(float)
    p = V.astype(np.float64).copy(); ww = np.asarray(w, float)[:, None]
    def lap(q):
        s = np.zeros_like(q); np.add.at(s, E[:, 0], q[E[:, 1]]); np.add.at(s, E[:, 1], q[E[:, 0]])
        return s / np.maximum(deg, 1)[:, None] - q
    for _ in range(iters):
        p = p + lam * ww * lap(p); p = p + mu * ww * lap(p)
    return p

# ---- hand cut (works on any polygon list)
def boundary_info(polys, kept):
    ec = defaultdict(list)
    for fi in np.nonzero(kept)[0]:
        f = polys[fi]
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            ec[(min(a, b), max(a, b))].append(fi)
    bedges = [e for e, v in ec.items() if len(v) == 1]
    verts = set(v for e in bedges for v in e)
    cnt = defaultdict(int)
    for fi in np.nonzero(kept)[0]:
        for v in polys[fi]:
            if v in verts: cnt[v] += 1
    adj = defaultdict(list)
    for a, b in bedges:
        adj[a].append(b); adj[b].append(a)
    return bedges, verts, cnt, adj

def extract_cut(V, polys, side, w0=-0.055, peel=8):
    """Cut the hand off at w>=w0, peel boundary corner faces until the wrist boundary is a simple loop.
    returns dict(L, free (vertex mask used only by removed faces), removed (face mask), kept (face mask), ring (ordered vertex ids))"""
    L = to_local(V, side); gx = side * V[:, 0]
    Hs = (gx > 0.30) & (V[:, 2] < 1.10) & (L[:, 2] >= w0)
    rem = np.array([Hs[list(p)].any() for p in polys]); kept = ~rem
    for it in range(peel):
        bedges, verts, cnt, adj = boundary_info(polys, kept)
        corners = set(v for v in verts if cnt[v] == 1)
        if not corners: break
        trial = kept.copy()
        for fi in np.nonzero(kept)[0]:
            if any(v in corners for v in polys[fi]): trial[fi] = False
        b2, v2, c2, a2 = boundary_info(polys, trial)
        if not all(len(v) == 2 for v in a2.values()): break
        kept = trial
    bedges, verts, cnt, adj = boundary_info(polys, kept)
    # the loop near this hand only
    near = {v for v in adj if gx[v] > 0.2}
    adj2 = {v: [u for u in adj[v] if u in near] for v in near}
    assert all(len(v) == 2 for v in adj2.values()), 'boundary is not a simple loop'
    start = next(iter(adj2)); ring = [start]; prev = None; cur = start
    while True:
        nxt = [v for v in adj2[cur] if v != prev]
        nxt = nxt[0] if prev is not None else adj2[cur][0]
        if nxt == start: break
        ring.append(nxt); prev, cur = cur, nxt
    assert len(ring) == len(adj2), (len(ring), len(adj2))
    used = np.zeros(len(V), bool)
    for fi in np.nonzero(kept)[0]: used[list(polys[fi])] = True
    allused = np.zeros(len(V), bool)
    for p in polys: allused[list(p)] = True
    free = (~used) & allused & (gx > 0.2)
    return dict(L=L, free=free, removed=~kept, kept=kept, ring=ring, Hs=Hs)

def order_ring(ring, L):
    """keep the boundary loop's connectivity order; choose direction (dorsal-first) and start vertex (nearest the +a' equator).
    returns ordered vertex id list, monotonic t in [0,1) per vertex"""
    ring = list(ring)
    P = L[ring]
    c = P.mean(axis=0)
    A_ = 0.5 * (P[:, 0].max() - P[:, 0].min()); B_ = 0.5 * (P[:, 1].max() - P[:, 1].min())
    ang = np.arctan2((P[:, 1] - c[1]) / B_, (P[:, 0] - c[0]) / A_)
    d = np.diff(np.r_[ang, ang[0]]); d = (d + np.pi) % (2 * np.pi) - np.pi
    if d.sum() > 0:
        ring = ring[::-1]; ang = ang[::-1]
    t = (-ang / (2 * np.pi)) % 1.0
    k0 = int(np.argmin(t))
    ring = ring[k0:] + ring[:k0]; t = np.r_[t[k0:], t[:k0]]
    t = (t - t[0]) % 1.0
    t = np.maximum.accumulate(t)
    return ring, t, c, (A_, B_)

def orient_consistently(faces, fixed_faces):
    """faces: list of tuples (new). fixed_faces: list of tuples with trusted orientation. Returns oriented list (flips as needed)."""
    from collections import deque
    allf = [tuple(f) for f in fixed_faces] + [tuple(f) for f in faces]
    nfix = len(fixed_faces)
    edges = defaultdict(list)
    for fi, f in enumerate(allf):
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            edges[(min(a, b), max(a, b))].append((fi, a, b))
    flipped = [False] * len(allf); visited = [False] * len(allf)
    for fi in range(nfix): visited[fi] = True
    seeds = set()
    for e, lst in edges.items():
        if any(fi >= nfix for fi, _, _ in lst):
            for (fi, a, b) in lst:
                if fi < nfix: seeds.add(fi)
    q = deque(sorted(seeds)); seen_q = set(q)
    while q:
        fi = q.popleft(); f = allf[fi]
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            if flipped[fi]: a, b = b, a
            e = (min(a, b), max(a, b))
            for (fj, c, d) in edges[e]:
                if fj == fi or visited[fj]: continue
                cj, dj = (d, c) if flipped[fj] else (c, d)
                if (cj, dj) == (a, b): flipped[fj] = True
                visited[fj] = True
                if fj not in seen_q: seen_q.add(fj); q.append(fj)
    out = []
    for fi in range(nfix, len(allf)):
        f = allf[fi]; out.append(tuple(reversed(f)) if flipped[fi] else f)
    return out, visited

def check_manifold(polys):
    e = defaultdict(list)
    for f in polys:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            e[(min(a, b), max(a, b))].append((a, b))
    bnd = sum(1 for v in e.values() if len(v) == 1)
    nm = sum(1 for v in e.values() if len(v) > 2)
    bad = sum(1 for v in e.values() if len(v) == 2 and v[0] == v[1])
    return dict(edges=len(e), boundary=bnd, nonmanifold=nm, bad_orient=bad)
