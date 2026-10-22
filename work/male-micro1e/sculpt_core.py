"""Coordinate-only sculpt toolkit (numpy). Runs inside Blender (live MCP or headless).

Everything is a deterministic function of the BASELINE coordinates (ArtDir Hand_4 lock, SHA d39c6c5e...).
Connectivity is never touched: only vertex positions of Body_M are rewritten.
"""
import numpy as np
from pathlib import Path

W = Path(__file__).resolve().parent
_D = np.load(W / 'baseline/mesh.npz')
BASE = _D['co'].astype(np.float64)
EDGES = _D['edges'].astype(np.int64)
N = len(BASE)
_deg = np.bincount(EDGES.ravel(), minlength=N).astype(np.float64)

FACES = None   # (F,4) filled by load_faces()


def load_faces(me):
    global FACES
    cv = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get('vertex_index', cv)
    FACES = cv.reshape(-1, 4)
    return FACES


def sm(a, b, x):
    """smoothstep 0 at a, 1 at b (a<b or a>b both ok)"""
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def neighbor_mean(p):
    s = np.zeros_like(p)
    np.add.at(s, EDGES[:, 0], p[EDGES[:, 1]])
    np.add.at(s, EDGES[:, 1], p[EDGES[:, 0]])
    return s / np.maximum(_deg, 1)[:, None]


def smooth(p, w, iters=10, lam=0.5, mu=None):
    """Weighted Laplacian smoothing, optional Taubin (mu<0) to avoid shrinkage. w: (N,) 0..1"""
    p = p.copy()
    for _ in range(iters):
        p += lam * w[:, None] * (neighbor_mean(p) - p)
        if mu is not None:
            p += mu * w[:, None] * (neighbor_mean(p) - p)
    return p


def face_normals(p):
    f = FACES
    n = np.cross(p[f[:, 2]] - p[f[:, 0]], p[f[:, 3]] - p[f[:, 1]])
    return n


def vertex_normals(p):
    fn = face_normals(p)
    vn = np.zeros_like(p)
    for k in range(4):
        np.add.at(vn, FACES[:, k], fn)
    l = np.linalg.norm(vn, axis=1, keepdims=True)
    return vn / np.maximum(l, 1e-12)


def flips(p, ref=None):
    """number of faces whose normal reversed relative to ref (default BASE)"""
    ref = BASE if ref is None else ref
    a = face_normals(ref)
    b = face_normals(p)
    d = np.einsum('ij,ij->i', a, b) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-18)
    return int((d < 0).sum()), float(d.min())


def apply_to_blender(p, name='Body_M'):
    import bpy
    me = bpy.data.objects[name].data
    me.vertices.foreach_set('co', p.astype(np.float32).ravel())
    me.update()


def edge_stats(p, mask=None):
    L = np.linalg.norm(p[EDGES[:, 0]] - p[EDGES[:, 1]], axis=1)
    if mask is not None:
        L = L[mask[EDGES[:, 0]] & mask[EDGES[:, 1]]]
    return float(L.min()), float(L.mean()), float(L.max())


# ---------------- SDF helpers -----------------
def sd_ellipsoid(P, c, r):
    q = (P - c) / r
    k0 = np.linalg.norm(q, axis=1)
    k1 = np.linalg.norm(q / r, axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def project(sdf, p, iters=12, h=1e-4):
    p = p.copy()
    for _ in range(iters):
        f = sdf(p)
        g = np.stack([(sdf(p + np.array([h, 0, 0])) - sdf(p - np.array([h, 0, 0]))),
                      (sdf(p + np.array([0, h, 0])) - sdf(p - np.array([0, h, 0]))),
                      (sdf(p + np.array([0, 0, h])) - sdf(p - np.array([0, 0, h])))], 1) / (2 * h)
        gg = np.maximum((g * g).sum(1), 1e-12)
        p -= (f / gg)[:, None] * g
    return p
