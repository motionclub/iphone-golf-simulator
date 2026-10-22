"""Shared helpers for the male legs+feet FORM2 job.  numpy only (runs in Blender's python 3.13 or any python with numpy).

Coordinates: metres, Blender world (x = character's left, y = back, z up).  The LEFT foot is x > 0; the right foot is the mirror (x -> -x).
"""
import pickle
from collections import defaultdict
import numpy as np

ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W = ROOT + '/work/male-legs-feet-form2'
ZT = 0.765            # zone: start z < ZT and |x| < XMAX
XMAX = 0.27
Z0 = 0.002472762716934085   # sole plane of the PASS mesh = exact min z of Body_M (float32 value 0.0024727627)
TOE_OUT_DEG = 3.3     # forefoot axis angle measured on the PASS foot (centre line drifts 7 mm over 12 cm)


BASE_TAG = 'b51c'        # data/V_<tag>.npy / F_<tag>.pkl extracted from baseline/start_<sha>.blend (shared ArtDir blend b51cbb05, after the hands FORM3 install)
BASE_BLEND = W + '/baseline/start_b51cbb05.blend'
BASE_SHA = 'b51cbb05d5135325b083462efc1b6e05d444a8a514c6c3b58547dad9564431ee'


def load_base():
    V = np.load(W + f'/data/V_{BASE_TAG}.npy')
    F = pickle.load(open(W + f'/data/F_{BASE_TAG}.pkl', 'rb'))
    return V, F


def _pad(mask, n):
    if n is None or n == len(mask): return mask
    out = np.zeros(n, bool); out[:len(mask)] = mask; return out


def zone_mask_from_orig(n=None):
    Vo = np.load(ROOT + '/work/male-parallel-legs/data/V_start_orig.npy')
    return _pad((Vo[:, 2] < ZT) & (np.abs(Vo[:, 0]) < XMAX), n)


def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def edges_of(F):
    E = set()
    for p in F:
        for k in range(len(p)):
            a, b = p[k], p[(k + 1) % len(p)]
            E.add((min(a, b), max(a, b)))
    return np.array(sorted(E))


def check_manifold(faces):
    """(n_edges, n_boundary, n_nonmanifold, n_same_direction_pairs)"""
    e = defaultdict(list)
    for f in faces:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            e[(min(a, b), max(a, b))].append((a, b))
    bnd = sum(1 for v in e.values() if len(v) == 1)
    nm = sum(1 for v in e.values() if len(v) > 2)
    bad = sum(1 for v in e.values() if len(v) == 2 and v[0] == v[1])
    return len(e), bnd, nm, bad


def boundary_edges(faces):
    e = defaultdict(list)
    for fi, f in enumerate(faces):
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            e[(min(a, b), max(a, b))].append(fi)
    return [k for k, v in e.items() if len(v) == 1]


FRAME_ORIGIN = [0.2212, -0.1835]      # (x on the left foot, y) of the knuckle line on the forefoot axis; set from the toe length by set_origin()
TOE_TIP_Y = -0.2235                    # plate toe tip (big toe front-most point)


def set_origin(L_big, alpha_deg=TOE_OUT_DEG, lc_big=0.0):
    a = np.radians(alpha_deg)
    # big-toe tip pole sits at (f = L_big, l = lc_big): world y = y_O - L cos(a) + l sin(a)
    y = TOE_TIP_Y + L_big * np.cos(a) - lc_big * np.sin(a)
    x = 0.2235 - 0.058 * (y + 0.2235)
    FRAME_ORIGIN[0], FRAME_ORIGIN[1] = float(x), float(y)


def foot_frame(side, alpha_deg=TOE_OUT_DEG, origin=None):
    """Return (O, Fh, Lh, Zh) for the foot frame.  side = +1 left (x>0) / -1 right.  O = point on the forefoot axis at the knuckle line (z = 0).
    Fh forward (toward toes), Lh lateral (outwards), Zh up."""
    a = np.radians(alpha_deg)
    origin = FRAME_ORIGIN if origin is None else origin
    O = np.array([side * origin[0], origin[1], 0.0])
    Fh = np.array([side * np.sin(a), -np.cos(a), 0.0])
    Lh = np.array([side * np.cos(a), np.sin(a), 0.0])
    Zh = np.array([0.0, 0.0, 1.0])
    return O, Fh, Lh, Zh


def to_local(P, side, frame=None):
    O, Fh, Lh, Zh = frame or foot_frame(side)
    R = np.asarray(P, float) - O
    return np.stack([R @ Fh, R @ Lh, R[..., 2] if R.ndim > 1 else R[2]], -1)


def to_world(L, side, frame=None):
    O, Fh, Lh, Zh = frame or foot_frame(side)
    L = np.asarray(L, float)
    return O + L[..., 0:1] * Fh + L[..., 1:2] * Lh + L[..., 2:3] * Zh


def orient_consistently(faces, fixed_faces):
    """faces: list of tuples (new).  fixed_faces: list of tuples with trusted orientation.  Returns the new faces flipped as needed
    so the whole mesh is consistently oriented (BFS from the fixed faces)."""
    from collections import deque
    allf = [tuple(f) for f in fixed_faces] + [tuple(f) for f in faces]
    nfix = len(fixed_faces)
    edges = defaultdict(list)
    for fi, f in enumerate(allf):
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            edges[(min(a, b), max(a, b))].append((fi, a, b))
    flipped = [False] * len(allf)
    visited = [False] * len(allf)
    for fi in range(nfix):
        visited[fi] = True
    seeds = set()
    for e, lst in edges.items():
        if any(fi >= nfix for fi, _, _ in lst):
            for (fi, a, b) in lst:
                if fi < nfix:
                    seeds.add(fi)
    q = deque(sorted(seeds)); seen_q = set(q)
    while q:
        fi = q.popleft()
        f = allf[fi]
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            if flipped[fi]:
                a, b = b, a
            e = (min(a, b), max(a, b))
            for (fj, c, d) in edges[e]:
                if fj == fi or visited[fj]:
                    continue
                cj, dj = (d, c) if flipped[fj] else (c, d)
                if (cj, dj) == (a, b):
                    flipped[fj] = True
                visited[fj] = True
                if fj not in seen_q:
                    seen_q.add(fj); q.append(fj)
    out = []
    for fi in range(nfix, len(allf)):
        f = allf[fi]
        out.append(tuple(reversed(f)) if flipped[fi] else f)
    return out, visited[nfix:]


def vertex_normals(V, F):
    """area-weighted smooth vertex normals of the mesh (polygons fan-triangulated), outward if the mesh is CCW-outward."""
    V = np.asarray(V, float)
    N = np.zeros_like(V)
    for p in F:
        p = list(p)
        for k in range(1, len(p) - 1):
            a, b, c = V[p[0]], V[p[k]], V[p[k + 1]]
            n = np.cross(b - a, c - a)
            N[p[0]] += n; N[p[k]] += n; N[p[k + 1]] += n
    L = np.linalg.norm(N, axis=1, keepdims=True)
    return N / np.maximum(L, 1e-15)


class Mesh:
    """adjacency helper: umbrella operator, taubin smoothing with per-vertex weights"""
    def __init__(self, V, F):
        self.E = edges_of(F)
        self.N = len(V)
        self.Ei, self.Ej = self.E[:, 0], self.E[:, 1]
        self.deg = np.bincount(np.r_[self.Ei, self.Ej], minlength=self.N).astype(np.float64)

    def umbrella(self, V):
        acc = np.zeros_like(V)
        np.add.at(acc, self.Ei, V[self.Ej]); np.add.at(acc, self.Ej, V[self.Ei])
        out = acc / np.maximum(self.deg, 1)[:, None] - V
        out[self.deg == 0] = 0.0
        return out

    def taubin(self, V, w, iters=10, lam=0.45, mu=-0.47):
        V = V.copy()
        for _ in range(iters):
            V += lam * w[:, None] * self.umbrella(V)
            V += mu * w[:, None] * self.umbrella(V)
        return V


def zone_mask_eff(n=None):
    """job zone = literal zone (orig z<0.765 & |x|<0.27) + the 207 foot lateral-wall vertices (orig |x|>=0.27, z<0.15; the only |x|>=0.27 geometry below the crotch,
    left unmoved by the earlier legs chat; lowest arm/hand geometry is z=0.805)."""
    Vo = np.load(ROOT + '/work/male-parallel-legs/data/V_start_orig.npy')
    lit = (Vo[:, 2] < ZT) & (np.abs(Vo[:, 0]) < XMAX)
    strip = (np.abs(Vo[:, 0]) >= XMAX) & (Vo[:, 2] < 0.15)
    return _pad(lit | strip, n)
