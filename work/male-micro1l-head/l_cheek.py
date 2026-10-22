"""Micro1l cheek de-fat.  The cheek region = face-lateral skin between eye / nose / mouth / ear loops (smooth 0..1 weight, never touches the loops).
Variants: toward the Micro1h smooth analytic cheek (gamma), normal-deflation of the pad (mm), and a zygomatic-plane hint."""
import sys
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from l_edit import *


def cheek_weight(ctx, V, z_lo=(1.470, 1.492), z_hi=(1.566, 1.584), x_in=(0.012, 0.026), x_out=(0.074, 0.090), y_max=(-0.020, -0.044),
                 d_mouth=(7.0, 18.0), d_nose=(5.0, 15.0), d_eye=(9.0, 22.0), d_ear=(14.0, 30.0)):
    """smooth 0..1 weight of the face-lateral cheek region (mm for distances); the same footprint family as Micro1k's, slightly lower at the bottom"""
    x, y, z = np.abs(V[:, 0]), V[:, 1], V[:, 2]
    w = (sstep(z_lo[0], z_lo[1], z) * (1 - sstep(z_hi[0], z_hi[1], z)) * sstep(x_in[0], x_in[1], x) * (1 - sstep(x_out[0], x_out[1], x)) * sstep(y_max[0], y_max[1], y))
    w *= sstep(d_mouth[0] * mm, d_mouth[1] * mm, ctx.dist['mouth']) * sstep(d_nose[0] * mm, d_nose[1] * mm, ctx.dist['nose'])
    w *= sstep(d_eye[0] * mm, d_eye[1] * mm, ctx.dist['eye']) * sstep(d_ear[0] * mm, d_ear[1] * mm, ctx.dist['ear'])
    w[~ctx.zone] = 0.0
    return w


def toward_h0(ctx, V, gamma=0.5, **wk):
    w = cheek_weight(ctx, V, **wk)
    return V + gamma * w[:, None] * (vh0(ctx) - V), w


def laplace_membrane(ctx, V, region, pinned, iters=400, lam=0.6):
    """harmonic membrane: Jacobi/Laplacian relaxation of the free vertices (region & ~pinned), pinned vertices stay -> V_m"""
    P = V.copy(); free = (region > 0) & (~pinned)
    w = free.astype(float)[:, None]
    for _ in range(iters):
        P = P + w * lam * (ctx.M.nbr_mean(P) - P)
    return P


def dome_field(ctx, V, wsrc, collar=3, iters=400):
    """signed height (m) of V above its own membrane along the vertex normal, on the region wsrc>0 (collar rings of pinned boundary)"""
    reg = (wsrc > 1e-3).astype(float)
    ext = feather(ctx, reg, collar)                 # region + collar
    pinned = (ext > 0) & (reg == 0)
    Vm = laplace_membrane(ctx, V, ext, pinned, iters=iters)
    N = vertex_normals(V, ctx.F)
    h = ((V - Vm) * N).sum(1)
    return h, Vm, N, ext


def silhouette_guard(N, views=((0, -1, 0), (-0.656, -0.755, 0), (0.588, -0.809, 0)), lo=0.10, hi=0.55):
    """0..1 weight that goes to 0 where the surface normal is perpendicular to any of the camera view directions (front, q3 yaw 41/36)
    (camera looks along +y for the front plate; for yaw a the camera sits at (sin a, -cos a)); n.c = cosine to the direction toward the camera"""
    g = np.ones(len(N))
    for c in views:
        c = np.array(c, float); c /= np.linalg.norm(c)
        g *= sstep(lo, hi, N @ c)
    return g


def jaw_protect(ctx, V, band=(2.0, 12.0)):
    """0..1: zero on/below the mandible border arc and within `band[0]` mm above it, 1 beyond `band[1]` mm above (keeps the cheek filter off the jaw edge)"""
    import l_jaw as J
    Ng = vertex_normals(V, ctx.F); Nd = J.smooth_normals(ctx, Ng, 8); prot = np.ones(ctx.n)
    for side in (1, -1):
        s, t, _ = J.euclid_field(ctx, V, Nd, side, band=0.06)
        ok = np.isfinite(s) & (V[:, 0] * side > -0.006)
        smm = np.where(ok, s * 1000.0, 99.0)
        prot = np.minimum(prot, np.where(ok, sstep(band[0], band[1], smm), 1.0))
    return prot


def lowpass(ctx, V, alpha=1.0, iters=120, protect=True, wk=None):
    """frequency-selective de-fat: blend the cheek region toward its own heavy low-pass (Taubin) surface -- removes the 5-25 mm blobs/bags that read as fat pads,
    keeps the broad volume and the silhouette; weight fades gradually towards mouth / nose / eye / ear loops and the mandible arc"""
    wk = dict(wk or {})
    w = cheek_weight(ctx, V, **wk)
    if protect: w = w * jaw_protect(ctx, V)
    reg = feather(ctx, (w > 1e-3).astype(float), 8); reg[~ctx.zone] = 0
    Vlp = ctx.M.taubin(V, reg, iters=iters, lam=0.5, mu=-0.53)
    return V + alpha * w[:, None] * (Vlp - V), w


def deflate(ctx, V, amount=2.0, wk=None, guard=True, protect=True, guard_lo=0.0, guard_hi=0.30, iters=3):
    """silhouette-guarded normal deflation of the cheek pad: amount (mm) at the pad centre, 0 where the surface is tangent to the front / 3/4 cameras (silhouette tangents; both cheeks, all five views)
    and at the loops.  guard = prod over views of smoothstep(lo, hi, n.c): n.c = cosine between the (smoothed) normal and the direction towards the camera"""
    wk = dict(wk or {}); w = cheek_weight(ctx, V, **wk)
    if protect: w = w * jaw_protect(ctx, V)
    N = vertex_normals(V, ctx.F); Nd = N.copy()
    for _ in range(8): Nd = 0.5 * Nd + 0.5 * ctx.M.nbr_mean(Nd); Nd /= np.maximum(np.linalg.norm(Nd, axis=1, keepdims=True), 1e-12)
    g = np.ones(ctx.n)
    if guard:
        for yaw in (0.0, 41.0, 36.0):
            a = np.radians(yaw)
            for sgn in ((1.0,) if yaw == 0.0 else (1.0, -1.0)):
                c = np.array([sgn * np.sin(a), -np.cos(a), 0.0]); g *= sstep(guard_lo, guard_hi, Nd @ c)
        # the front camera: the cheek silhouette tangent is where |n_x| -> 1
        g *= sstep(guard_lo, guard_hi, Nd @ np.array([0.0, -1.0, 0.0]))
    D = -(amount * mm) * (w * g)[:, None] * Nd
    if iters:
        ww = feather(ctx, ((w * g) > 1e-3).astype(float), 2)
        for _ in range(iters): D = D + 0.5 * ww[:, None] * (ctx.M.nbr_mean(D) - D)
    return V + D, w * g


def hollow_weight(ctx, V, xc=48.0, zc=1.518, rx=17.0, rz=12.0, p=2.2):
    """smooth elliptic bump (0..1) over the buccal region below the cheekbone, in (|x|, z) mm"""
    ax = np.abs(V[:, 0]) * 1000.0; z = V[:, 2] * 1000.0
    q = (((ax - xc) / rx) ** 2 + ((z - zc * 1000.0) / (rz)) ** 2)
    return np.exp(-0.5 * q ** (p / 2.0) * 2.0 / 2.0) if False else np.exp(-q ** (p / 2.0) * 0.9)


def deflate2(ctx, V, base=2.0, hollow=2.0, wk=None, hk=None, guard_lo=0.0, guard_hi=0.18, protect=True, iters=3):
    """cheek de-fat: broad pad deflation `base` (mm) + extra buccal hollow `hollow` (mm) below the cheekbone, along smoothed normals, silhouette-guarded (soft)"""
    wk = dict(wk or {}); w = cheek_weight(ctx, V, **wk)
    if protect: w = w * jaw_protect(ctx, V)
    Hh = hollow_weight(ctx, V, **dict(hk or {}))
    N = vertex_normals(V, ctx.F); Nd = N.copy()
    for _ in range(8): Nd = 0.5 * Nd + 0.5 * ctx.M.nbr_mean(Nd); Nd /= np.maximum(np.linalg.norm(Nd, axis=1, keepdims=True), 1e-12)
    g = np.ones(ctx.n)
    for yaw in (0.0, 41.0, 36.0):
        a = np.radians(yaw)
        for sgn in ((1.0,) if yaw == 0.0 else (1.0, -1.0)):
            c = np.array([sgn * np.sin(a), -np.cos(a), 0.0]); g *= sstep(guard_lo, guard_hi, Nd @ c)
    amt = (base + hollow * Hh) * mm
    D = -(amt * w * g)[:, None] * Nd
    if iters:
        ww = feather(ctx, ((w * g) > 1e-3).astype(float), 2)
        for _ in range(iters): D = D + 0.5 * ww[:, None] * (ctx.M.nbr_mean(D) - D)
    return V + D, w * g


def deflate3(ctx, V, base=3.0, hollow=2.0, wk=None, hk=None, gmin=0.35, guard_hi=0.35, protect=True, smooth=6):
    """cheek de-fat v3: broad smooth pad deflation `base` (mm) + buccal hollow `hollow` (mm) along smoothed normals.  The silhouette guard never goes to zero (gmin) so the amplitude has no steep gradient
    at the lateral face (that made creases); wide protection ramps at mouth / nose / eye / ear / mandible arc; the displacement field is Laplacian-smoothed over its whole support."""
    kw = dict(d_mouth=(8.0, 34.0), d_nose=(6.0, 30.0), d_eye=(10.0, 30.0), d_ear=(14.0, 36.0), x_in=(0.016, 0.040), z_lo=(1.482, 1.500))
    kw.update(wk or {})
    w = cheek_weight(ctx, V, **kw)
    if protect: w = w * jaw_protect(ctx, V, band=(3.0, 16.0))
    Hh = hollow_weight(ctx, V, **dict(hk or {}))
    N = vertex_normals(V, ctx.F); Nd = N.copy()
    for _ in range(8): Nd = 0.5 * Nd + 0.5 * ctx.M.nbr_mean(Nd); Nd /= np.maximum(np.linalg.norm(Nd, axis=1, keepdims=True), 1e-12)
    g = np.ones(ctx.n)
    for yaw in (0.0, 41.0, 36.0):
        a = np.radians(yaw)
        for sgn in ((1.0,) if yaw == 0.0 else (1.0, -1.0)):
            c = np.array([sgn * np.sin(a), -np.cos(a), 0.0]); g *= sstep(0.0, guard_hi, Nd @ c)
    g = gmin + (1.0 - gmin) * g
    amt = (base + hollow * Hh) * mm
    D = -(amt * w * g)[:, None] * Nd
    ww = feather(ctx, (w > 1e-3).astype(float), 3)
    for _ in range(smooth): D = D + 0.5 * ww[:, None] * (ctx.M.nbr_mean(D) - D)
    return V + D, w * g
