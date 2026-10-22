"""Mesh helpers for the legs/feet zone (numpy only; runs in Blender's python 3.13)."""
import pickle
import numpy as np
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs'
ZT = 0.765                       # crotch apex: zone is z < ZT (start coordinates), |x| < XMAX
XMAX = 0.27

V0 = np.load(W + '/data/V_start.npy')
F = pickle.load(open(W + '/data/F.pkl', 'rb'))
N = len(V0)
ZONE = (V0[:, 2] < ZT) & (np.abs(V0[:, 0]) < XMAX)
LEFT = ZONE & (V0[:, 0] > 0)      # +x leg
RIGHT = ZONE & (V0[:, 0] < 0)

# edges / adjacency
_E = set()
for p in F:
    for k in range(len(p)):
        a, b = p[k], p[(k + 1) % len(p)]
        _E.add((min(a, b), max(a, b)))
E = np.array(sorted(_E))
Ei, Ej = E[:, 0], E[:, 1]
DEG = np.bincount(np.r_[Ei, Ej], minlength=N).astype(np.float64)
TRI = np.array([[p[0], p[k], p[k + 1]] for p in F for k in range(1, len(p) - 1)])


def umbrella(V):
    """mean of neighbours - v"""
    acc = np.zeros_like(V)
    np.add.at(acc, Ei, V[Ej]); np.add.at(acc, Ej, V[Ei])
    out = acc / np.maximum(DEG, 1)[:, None] - V
    out[DEG == 0] = 0.0
    return out


def normals(V):
    t = TRI
    fn = np.cross(V[t[:, 1]] - V[t[:, 0]], V[t[:, 2]] - V[t[:, 0]])
    vn = np.zeros_like(V)
    for k in range(3): np.add.at(vn, t[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def taubin(V, mask_w, iters=20, lam=0.5, mu=-0.53):
    """volume-preserving smoothing; mask_w (N,) in 0..1 scales the step per vertex"""
    V = V.copy()
    for _ in range(iters):
        V += lam * mask_w[:, None] * umbrella(V)
        V += mu * mask_w[:, None] * umbrella(V)
    return V


def zone_weight(z, top=ZT, ramp=0.06):
    """1 inside, 0 at the zone top (smoothstep over `ramp` below it)"""
    return smoothstep(top, top - ramp, z)


def write_blend(Vnew, out_path, src=None):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=src or (W + '/baseline/artdir_after_torso.blend'))
    me = bpy.data.objects['Body_M'].data
    assert len(me.vertices) == len(Vnew)
    me.vertices.foreach_set('co', np.asarray(Vnew, np.float64).reshape(-1))
    me.update()
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)


def aniso_umbrella(V, axis=(0.0, 0.0, 1.0), p=2.0, eps=0.05):
    """edge-weighted umbrella: weights = |cos(angle between edge and axis)|^p (smooths along `axis` only)"""
    ax = np.asarray(axis, float)
    d = V[Ej] - V[Ei]
    l = np.maximum(np.linalg.norm(d, axis=1), 1e-12)
    a = (np.abs(d @ ax) / l) ** p
    acc = np.zeros_like(V); den = np.full(len(V), eps)
    np.add.at(acc, Ei, a[:, None] * d); np.add.at(acc, Ej, -a[:, None] * d)
    np.add.at(den, Ei, a); np.add.at(den, Ej, a)
    return acc / den[:, None]


def taubin_aniso(V, w, iters=60, lam=0.5, mu=-0.53, **kw):
    V = V.copy()
    for _ in range(iters):
        V += lam * w[:, None] * aniso_umbrella(V, **kw)
        V += mu * w[:, None] * aniso_umbrella(V, **kw)
    return V


# ---------------------------------------------------------------- biharmonic fairing (constrained)
def _lap_ops():
    """sparse uniform Laplacian L = D^-1 A - I as (rows, cols, vals) with a COO matvec"""
    rows = np.r_[Ei, Ej]; cols = np.r_[Ej, Ei]
    deg = np.maximum(DEG, 1)
    vals = 1.0 / deg[rows]
    return rows, cols, vals


_LR, _LC, _LV = _lap_ops()


def Lmul(X):
    out = np.zeros_like(X)
    for a in range(X.shape[1]):
        out[:, a] = np.bincount(_LR, weights=_LV * X[_LC, a], minlength=N) - X[:, a] * (DEG > 0)
    return out


def LTmul(Y):
    out = np.zeros_like(Y)
    for a in range(Y.shape[1]):
        out[:, a] = np.bincount(_LC, weights=_LV * Y[_LR, a], minlength=N) - Y[:, a] * (DEG > 0)
    return out


def fair(V, free, lam=3.0, omega=None, fixed_axes=None, iters=400, tol=1e-9):
    """minimise  sum_free omega|x - x0|^2 + lam |L x|^2  over the `free` vertices (bool mask), others fixed.
    omega: (N,) weights (default 1). fixed_axes: dict {axis: bool mask} - free vertices whose coordinate on that axis stays put."""
    X = V.copy()
    om = np.ones(N) if omega is None else omega
    idx = np.nonzero(free)[0]
    x0 = V.copy()
    # per-axis free masks
    fm = np.zeros((N, 3), bool); fm[idx] = True
    if fixed_axes:
        for a, m in fixed_axes.items(): fm[m, a] = False

    def Aop(Xf):          # (omega I + lam L^T L) restricted to free coordinates
        Y = np.zeros_like(X); Y[fm] = Xf[fm]
        out = om[:, None] * Y + lam * LTmul(Lmul(Y))
        out[~fm] = 0
        return out

    # rhs: omega x0 + lam L^T (-L x_fixed)  where x_fixed = coordinates held constant
    Xc = X.copy(); Xc[fm] = 0.0                      # constants only
    rhs = om[:, None] * x0 - lam * LTmul(Lmul(Xc)); rhs[~fm] = 0
    Xs = X.copy()
    r = rhs - Aop(Xs); p = r.copy(); rs = (r * r).sum()
    for it in range(iters):
        Ap = Aop(p); alpha = rs / max((p * Ap).sum(), 1e-300)
        Xs = Xs + alpha * p; r = r - alpha * Ap; rsn = (r * r).sum()
        if rsn < tol: break
        p = r + (rsn / rs) * p; rs = rsn
    Xs[~fm] = X[~fm]
    return Xs


# ---------------------------------------------------------------- tangential relaxation with re-projection onto a reference surface
def _closest_on_tris(P, A, B, C):
    """closest point on triangles (A,B,C) (m,3) for each point of P (n,3) -> (n,m,3) is too big; returns best point per query (n,3) and distance (n,)"""
    n = len(P); m = len(A)
    ab = B - A; ac = C - A
    out = np.zeros((n, 3)); best = np.full(n, 1e9)
    for s in range(0, n, 64):
        p = P[s:s + 64, None, :]                 # (k,1,3)
        ap = p - A[None]                         # (k,m,3)
        d1 = (ab[None] * ap).sum(-1); d2 = (ac[None] * ap).sum(-1)
        bp = p - B[None]; d3 = (ab[None] * bp).sum(-1); d4 = (ac[None] * bp).sum(-1)
        cp = p - C[None]; d5 = (ab[None] * cp).sum(-1); d6 = (ac[None] * cp).sum(-1)
        vc = d1 * d4 - d3 * d2; vb = d5 * d2 - d1 * d6; va = d3 * d6 - d5 * d4
        denom = va + vb + vc
        denom = np.where(np.abs(denom) < 1e-30, 1e-30, denom)
        v = vb / denom; w = vc / denom
        v = np.clip(v, 0, 1); w = np.clip(w, 0, 1)
        over = v + w > 1
        t = np.where(over, v + w, 1.0); v = np.where(over, v / t, v); w = np.where(over, w / t, w)
        q = A[None] + ab[None] * v[..., None] + ac[None] * w[..., None]
        dd = ((q - p) ** 2).sum(-1)
        j = dd.argmin(1)
        out[s:s + 64] = q[np.arange(len(j)), j]; best[s:s + 64] = np.sqrt(dd[np.arange(len(j)), j])
    return out, best


def relax_project(V, free, weight, iters=20, lam=0.5, reg_tris=None):
    """tangential Laplacian smoothing of the `free` vertices, then re-projection onto the surface of the input mesh (restricted to reg_tris triangles)"""
    ref = V.copy()
    if reg_tris is None:
        tri = TRI
    else:
        tri = reg_tris
    A, B, C = ref[tri[:, 0]], ref[tri[:, 1]], ref[tri[:, 2]]
    idx = np.nonzero(free)[0]
    X = V.copy()
    for it in range(iters):
        U = umbrella(X)[idx]
        nrm = normals(X)[idx]
        Ut = U - (U * nrm).sum(1, keepdims=True) * nrm
        Y = X[idx] + lam * weight[idx, None] * Ut
        Q, d = _closest_on_tris(Y, A, B, C)
        X[idx] = Q
    return X
