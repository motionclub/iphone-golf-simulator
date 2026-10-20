"""Micro1l edit library: jaw definition all around + cheek de-fat + fuller lips on the CURRENT male HeroBase head (blend 9bfd788a).
Position-only, topology unchanged.  Run with Blender's python3.13 and PYTHONPATH=pylib.  Metres; `mm` for conversions.
Builds on Micro1k's Ctx / geodesic machinery (j_edit.py); data (V_start, F_start, loops_start, vn_stored) is the CURRENT 33,196-vertex Body_M."""
import sys, math, pickle, json
from pathlib import Path
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_edit import *          # Ctx, gauss, interp_profile, sstep, vertex_normals, rotate_normals, updated_normals, moved_report, mm, W, I1, plane_section ...


class LCtx(Ctx):
    """Ctx + geodesic distance to the protected loops (mouth, nose, eye, ear)."""
    def __init__(self, with_dist=True):
        super().__init__()
        self.iso = self.M.deg == 0                 # unreferenced (isolated) vertices (eye-hole leftovers) must never move
        self.zone = self.zone & ~self.iso
        L = self.loops
        self.sets = dict(mouth=L['LOOP_mouth_seam'] + L['LOOP_mouth_lip_upper'] + L['LOOP_mouth_lip_lower'],
                         nose=L['LOOP_ala_L'] + L['LOOP_ala_R'] + L['LOOP_nostril_L'] + L['LOOP_nostril_R'],
                         eye=L['LOOP_lid_margin_L'] + L['LOOP_lid_margin_R'],
                         ear=L['LOOP_ear_attach_L'] + L['LOOP_ear_attach_R'] + L['LOOP_helix_L'] + L['LOOP_helix_R'] + L['LOOP_concha_L'] + L['LOOP_concha_R'])
        self.dist = {}
        if with_dist:
            for k, ids in self.sets.items():
                d, _ = self.geodesic(self.V0, sorted(set(ids)), maxd=0.09); self.dist[k] = d


def feather(ctx, w, n=2):
    w = np.asarray(w, float).copy()
    for _ in range(n): w = np.maximum(w, 0.5 * ctx.M.nbr_mean(w[:, None])[:, 0] * (w == 0))
    return w


def smooth_normals(ctx, N, iters=8):
    Nd = N.copy()
    for _ in range(iters):
        Nd = 0.5 * Nd + 0.5 * ctx.M.nbr_mean(Nd); Nd /= np.maximum(np.linalg.norm(Nd, axis=1, keepdims=True), 1e-12)
    return Nd


def smooth_field(ctx, D, w, iters=3):
    """umbrella-smooth a displacement field D (n,3) only where w>0 (w: 0..1)"""
    w = np.asarray(w, float)[:, None]
    for _ in range(iters): D = D + 0.5 * w * (ctx.M.nbr_mean(D) - D)
    return D


_VH0 = None
def vh0(ctx):
    """Micro1h smooth analytic head (old 30,296-vertex indexing, head indices are stable), padded with the current positions"""
    global _VH0
    if _VH0 is None:
        a = np.load(I1 / 'data/V_h0.npy'); out = ctx.V0.copy(); out[:len(a)] = a; _VH0 = out
    return _VH0


def moved(ctx, V1, thr=1e-9):
    d = np.linalg.norm(V1 - ctx.V0, axis=1)
    return d > thr


def sharpen_normals(ctx, N, w, k=1.0, iters=6):
    """shading-only 'normal unsharp mask': n' = n + k (n - smooth(n)) blended by the per-vertex weight w (0..1) -- boosts the shading edge of a soft crest without moving geometry"""
    Ns = N.copy()
    for _ in range(iters):
        Ns = 0.5 * Ns + 0.5 * ctx.M.nbr_mean(Ns); Ns /= np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
    out = N + k * (N - Ns); out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)
    w = np.asarray(w, float)[:, None]
    res = N * (1 - w) + out * w; res /= np.maximum(np.linalg.norm(res, axis=1, keepdims=True), 1e-12)
    return res
