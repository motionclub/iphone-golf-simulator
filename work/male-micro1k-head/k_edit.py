"""Micro1k edit library: undo the Micro1j neck-side jaw relief, soften the cheeks, build a real mandible edge on the jaw, flatten the nape strip.
Position-only, topology unchanged.  Run with Blender's python3.13 and PYTHONPATH=pylib.  Work in metres; mm in names where noted."""
import sys, math, pickle, json
from pathlib import Path
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head')
from j_edit import *          # Ctx (K data = installed Micro1j blend), gauss, interp_profile, sstep, rotate_normals, updated_normals, moved_report, mm
from j_neck import fair_disp

DJAW = np.load(W / 'data/Djaw_j1.npy')           # Micro1j jaw-border relief (the thing Adnan rejected), relative to the Micro1j-without-jaw state


class KCtx(Ctx):
    def __init__(self):
        super().__init__()
        L = self.loops
        sets = dict(mouth=L['LOOP_mouth_seam'] + L['LOOP_mouth_lip_upper'] + L['LOOP_mouth_lip_lower'],
                    nose=L['LOOP_ala_L'] + L['LOOP_ala_R'] + L['LOOP_nostril_L'] + L['LOOP_nostril_R'],
                    eye=L['LOOP_lid_margin_L'] + L['LOOP_lid_margin_R'],
                    ear=L['LOOP_ear_attach_L'] + L['LOOP_ear_attach_R'] + L['LOOP_helix_L'] + L['LOOP_helix_R'] + L['LOOP_concha_L'] + L['LOOP_concha_R'])
        self.dist = {}
        for k, ids in sets.items():
            d, _ = self.geodesic(self.V0, sorted(set(ids)), maxd=0.09); self.dist[k] = d


def undo_jaw(ctx, V):
    """remove the Micro1j jaw-border relief (installed blend -> apple + nape only)"""
    return V - DJAW


def feather(ctx, w, n=2):
    w = np.asarray(w, float).copy()
    for _ in range(n): w = np.maximum(w, 0.5 * ctx.M.nbr_mean(w[:, None])[:, 0] * (w == 0))
    return w


def cheek_weight(ctx, V, z_lo=(1.478, 1.498), z_hi=(1.566, 1.582), x_in=(0.012, 0.026), x_out=(0.074, 0.090), y_max=(-0.020, -0.044),
                 d_mouth=(7.0, 18.0), d_nose=(5.0, 15.0), d_eye=(9.0, 22.0), d_ear=(14.0, 30.0)):
    """smooth 0..1 weight of the face-lateral cheek region (mm for distances)"""
    x, y, z = np.abs(V[:, 0]), V[:, 1], V[:, 2]
    w = (sstep(z_lo[0], z_lo[1], z) * (1 - sstep(z_hi[0], z_hi[1], z)) * sstep(x_in[0], x_in[1], x) * (1 - sstep(x_out[0], x_out[1], x)) * sstep(y_max[0], y_max[1], y))
    w *= sstep(d_mouth[0] * mm, d_mouth[1] * mm, ctx.dist['mouth']) * sstep(d_nose[0] * mm, d_nose[1] * mm, ctx.dist['nose'])
    w *= sstep(d_eye[0] * mm, d_eye[1] * mm, ctx.dist['eye']) * sstep(d_ear[0] * mm, d_ear[1] * mm, ctx.dist['ear'])
    w[~ctx.zone] = 0.0
    return w


def soften_cheek(ctx, V, alpha=0.6, iters=30, **wk):
    """blend the cheek region toward its own low-pass surface: reduces ridge + hollow relief, keeps the broad shape and the silhouette"""
    w = cheek_weight(ctx, V, **wk)
    reg = feather(ctx, (w > 1e-3).astype(float), 4)
    reg[~ctx.zone] = 0
    Vlp = ctx.M.taubin(V, reg, iters=iters, lam=0.5, mu=-0.53)
    return V + alpha * w[:, None] * (Vlp - V), w


VH0 = None


def toward_h0(ctx, V, gamma=0.5, **wk):
    """blend the cheek region toward the Micro1h cheek (smooth analytic head, before the Micro1i PMO / hollow / malar relief)"""
    global VH0
    if VH0 is None: VH0 = np.load(I1 / 'data/V_h0.npy')
    w = cheek_weight(ctx, V, **wk)
    return V + gamma * w[:, None] * (VH0 - V), w
