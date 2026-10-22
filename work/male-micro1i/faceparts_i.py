"""Micro1i Face_M builder: same parts as Micro1h plus softer/thicker brows, lash + lid-crease lines, taller lips, softer nostril crescents.
Runs inside Blender; imports the Micro1h modules for the shared pieces (eyeballs, ray-cast strip helper)."""
import math, sys
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
H1 = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h'
for p in (H1, H1.replace('micro1h', 'micro1e')):
    if p not in sys.path: sys.path.insert(0, p)
import h1lib as H
import sculpt as S
import finalize as FZ
import faceparts as FP
from h1lib import K, zrow, xcol

mm = 0.001
FP.SLOTS[:] = ['Brow', 'Sclera', 'Iris', 'Pupil', 'Limbal', 'Catch', 'LidLine', 'Lip', 'LipUp', 'Seam', 'Nostril', 'BrowSoft', 'LidCrease']
FP.SLOT_COL.update({'BrowSoft': ((0.22, 0.175, 0.14), 0.55), 'LidCrease': ((0.34, 0.20, 0.14), 0.55)})
PRM = dict(brow_scale=1.0, brow_soft=1.0, lash_w=2.5, crease_w=1.0, crease_gap=6.2, lip_up_h=4.8, lip_lo_h=10.4, lip_up_w=35.0, lip_lo_w=31.0, seam_w=2.6,
           nostril_rx=5.2, nostril_rz=2.3)


def make_brow_i(side, bvh, nu=48, nv=9, lift_h=1.25, scale=1.0, soft=None):
    """brow ribbon from the plate centre-line.  scale widens the ribbon; soft=(factor) builds the outer soft layer (wider, lower lift)"""
    cl = np.array(FP.BROW_CL); th = np.array(FP.BROW_TH) * scale
    seg = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(cl, axis=0).T))]); seg /= seg[-1]
    sg = np.linspace(0, 1, nu)
    colc = np.interp(sg, seg, cl[:, 0]); rowc = np.interp(sg, seg, cl[:, 1]); thc = np.interp(sg, seg, th)
    cap0 = 0.09
    thc = thc * np.sqrt(np.clip(1.0 - (1.0 - np.minimum(sg / cap0, 1.0)) ** 2, 0.0, 1.0)).clip(0.18, 1.0)
    if soft:
        thc = thc * soft + 1.1                            # px: a thin soft rim (~1.4 mm) around the core
    dcol = np.gradient(colc); drow = np.gradient(rowc); L = np.hypot(dcol, drow); nc = -drow / L; nr = dcol / L
    V = []; Fc = []
    for i in range(nu):
        for k in range(nv):
            v = (k / (nv - 1)) * 2 - 1
            c = colc[i] + nc[i] * v * thc[i] / 2; r = rowc[i] + nr[i] * v * thc[i] / 2
            x = float(xcol(c)); z = float(zrow(r))
            if side > 0: x = -x
            hit = bvh.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)), 3.0)
            if hit[0] is None: raise RuntimeError('brow ray missed')
            p, n = hit[0], hit[1]
            lh = (lift_h * (0.55 if soft else 1.0) * mm) * max(0.0, 1 - abs(v) ** 2.4) * (0.35 + 0.65 * min(1.0, thc[i] / 6.0)) + (0.12 if soft else 0.25) * mm
            V.append((p.x + n.x * lh, p.y + n.y * lh, p.z + n.z * lh))
    for i in range(nu - 1):
        for k in range(nv - 1):
            a = i * nv + k; b = (i + 1) * nv + k; c = (i + 1) * nv + k + 1; d = i * nv + k + 1
            Fc.append((a, b, c, d))
    return np.array(V), Fc


def crease_strip(bvh, margin_pts, side, nu=40, gap=6.2 * mm, width=1.0 * mm, lift=0.18 * mm):
    """thin dark line following the upper-lid crease: the upper margin chain offset upward by `gap` (tapering at both ends)"""
    pts = np.asarray(margin_pts)
    u = np.abs(pts[:, 0]); z = pts[:, 2]
    xc, zc = 0.5 * (u.max() + u.min()), 0.5 * (z.max() + z.min())
    th = np.arctan2(z - zc, u - xc); sel = th > -0.12
    chain = pts[sel][np.argsort(th[sel])]
    seg = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(chain, axis=0), axis=1))]); t = np.linspace(0, seg[-1], nu)
    X = np.stack([np.interp(t, seg, chain[:, k]) for k in range(3)], axis=1)
    ax = np.abs(X[:, 0]); az = X[:, 2]
    taper = np.sin(np.linspace(0, math.pi, nu)) ** 0.6
    V = []
    for i in range(nu):
        for o in (-0.5, 0.5):
            xx = (ax[i] + 0.0) * (1 if side > 0 else -1); zz = az[i] + gap * taper[i] * (0.55 + 0.45 * taper[i]) + o * width * taper[i]
            hit = bvh.ray_cast(Vector((float(xx), -1.0, float(zz))), Vector((0, 1, 0)), 3.0)
            if hit[0] is None: p = Vector((xx, -0.15, zz))
            else: p = hit[0] + hit[1] * lift
            V.append((p.x, p.y, p.z))
    Fc = []
    for i in range(nu - 1):
        a = i * 2; b = (i + 1) * 2; Fc.append([a, b, b + 1, a + 1])
    return V, Fc


def lower_lid_strip(bvh, margin_pts, side, nu=28, gap=1.2 * mm, width=0.8 * mm, lift=0.16 * mm):
    pts = np.asarray(margin_pts)
    u = np.abs(pts[:, 0]); z = pts[:, 2]
    xc, zc = 0.5 * (u.max() + u.min()), 0.5 * (z.max() + z.min())
    th = np.arctan2(z - zc, u - xc); sel = th < -0.35
    chain = pts[sel][np.argsort(-th[sel])]
    seg = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(chain, axis=0), axis=1))]); t = np.linspace(0, seg[-1], nu)
    X = np.stack([np.interp(t, seg, chain[:, k]) for k in range(3)], axis=1)
    taper = np.sin(np.linspace(0, math.pi, nu)) ** 0.8
    V = []
    for i in range(nu):
        for o in (-0.5, 0.5):
            xx = np.abs(X[i, 0]) * (1 if side > 0 else -1); zz = X[i, 2] - gap * taper[i] + o * width * taper[i]
            hit = bvh.ray_cast(Vector((float(xx), -1.0, float(zz))), Vector((0, 1, 0)), 3.0)
            p = hit[0] + hit[1] * lift if hit[0] is not None else Vector((xx, -0.15, zz))
            V.append((p.x, p.y, p.z))
    Fc = []
    for i in range(nu - 1):
        a = i * 2; b = (i + 1) * 2; Fc.append([a, b, b + 1, a + 1])
    return V, Fc


def smooth_strip(V, nu, nv, passes=3, w=0.5):
    """moving average of a strip's vertices along its length (index i) -- removes the vertex-spacing sawtooth of the ray-cast skin"""
    A = np.array(V, float).reshape(nu, nv, 3)
    for _ in range(passes):
        B = A.copy(); B[1:-1] = (1 - w) * A[1:-1] + w * 0.5 * (A[:-2] + A[2:]); A = B
    return [tuple(p) for p in A.reshape(-1, 3)]


def lip_patch_i(bvh, which, nu=44, nv=5, lift=0.30 * mm, hu=6.6, hl=10.4, wu=35.0, wl=31.0):
    xs = np.linspace(-1, 1, nu)
    if which == 'up': W, Hh, p_ = wu * mm, hu * mm, 1.55
    else: W, Hh, p_ = wl * mm, hl * mm, 1.9
    pts = np.zeros((nu, nv, 2))
    for i, u in enumerate(xs):
        x = u * W
        z0 = float(S.seam_z(np.array([abs(x)]))[0])
        h = Hh * max(0.0, 1.0 - abs(u) ** p_) ** (1.0 / p_)
        for k in range(nv):
            v = k / (nv - 1); sgn = 1.0 if which == 'up' else -1.0
            pts[i, k] = (x, z0 + sgn * v * h)
    V, F = FP.grid_strip(bvh, pts, nu, nv, lift, flip=(which != 'up'))
    return smooth_strip(V, nu, nv), F


def seam_ribbon_i(bvh, nu=56, width=2.6 * mm, lift=0.55 * mm):
    xs = np.linspace(-38.5 * mm, 38.5 * mm, nu)
    pts = np.zeros((nu, 3, 2))
    for i, x in enumerate(xs):
        z0 = float(S.seam_z(np.array([abs(x)]))[0])
        wv = width * math.sqrt(max(0.0, 1.0 - (abs(x) / (38.5 * mm)) ** 2.4))
        for k, o in enumerate((-0.5, 0.0, 0.5)): pts[i, k] = (x, z0 + o * wv)
    V, F = FP.grid_strip(bvh, pts, nu, 3, lift)
    return smooth_strip(V, nu, 3, passes=4), F


def nostril_liner_i(bvh, side, nu=16, lift=0.12 * mm, rx=5.2 * mm, rz=2.3 * mm, ring=None, P=None):
    if ring is not None:
        q = np.asarray(P)[list(ring)]; cx = float(q[:, 0].mean()); cz = float(q[:, 2].mean()) - 0.2 * mm
        rx = 0.5 * (q[:, 0].max() - q[:, 0].min()) * 0.92; rz = min(0.5 * (q[:, 2].max() - q[:, 2].min()) * 0.8, rz)
    else:
        n = S.PRM['nostril']; cx = side * n['cx'] * mm; cz = float(zrow(n['row']))
    pts = np.zeros((nu, 3, 2))
    for i, u in enumerate(np.linspace(-1, 1, nu)):
        h = rz * max(0.0, 1.0 - abs(u) ** 2.0) ** 0.8
        x = cx + u * rx
        tilt = -0.9 * mm * u * side * 0 - 0.9 * mm * (u * side * (1 if side > 0 else 1)) * 0 + 0.8 * mm * (-u) * 0
        for k, v in enumerate((-1.0, 0.0, 1.0)): pts[i, k] = (x, cz + v * h + 0.9 * mm * (1.0 - u) * 0.5 - 0.45 * mm)
    return FP.grid_strip(bvh, pts, nu, 3, lift)


def build_face_m_i(P_skin, F_skin, margin=None, prm=None, nostrils=None):
    p = dict(PRM); p.update(prm or {})
    verts = [tuple(v) for v in P_skin]; tris = []
    for f in F_skin:
        tris.append((int(f[0]), int(f[1]), int(f[2])))
        if len(f) > 3: tris.append((int(f[0]), int(f[2]), int(f[3])))
    bvh = BVHTree.FromPolygons(verts, tris)
    parts = FP.Parts()
    cmap = {0: 'Sclera', 1: 'Iris', 2: 'Pupil', 3: 'Limbal', 4: 'Catch'}
    for side in (-1, 1):
        V, F, mat = FZ.eyeball_mesh(side)
        parts.add(V, F, [cmap[m] for m in mat], orient=('radial', [side * S.EYEBALL['cx'], S.EYEBALL['cy'], H.LM['eye_z']]))
    for side in (-1, +1):
        try:
            V, F = make_brow_i(side, bvh, nu=32, nv=5, scale=p['brow_soft'] * 1.0, soft=p['brow_soft']); parts.add(V, F, 'BrowSoft', orient='front')
            V, F = make_brow_i(side, bvh, nu=40, nv=7, scale=p['brow_scale']); parts.add(V, F, 'Brow', orient='front')
        except RuntimeError:
            pass
        mp = np.asarray(P_skin)[list(margin[side])]
        V, F = FP.lid_line_strip_loop(bvh, P_skin, margin[side], side, off=(0.0, 0.7 * mm, 1.4 * mm, 2.1 * mm, p['lash_w'] * mm), lift=0.30 * mm); parts.add(V, F, 'LidLine', orient='front')
        V, F = crease_strip(bvh, mp, side, gap=p['crease_gap'] * mm, width=p['crease_w'] * mm); parts.add(V, F, 'LidCrease', orient='front')
        V, F = lower_lid_strip(bvh, mp, side); parts.add(V, F, 'LidLine', orient='front')
    for which in ('up', 'lo'):
        V, F = lip_patch_i(bvh, which, hu=p['lip_up_h'], hl=p['lip_lo_h'], wu=p['lip_up_w'], wl=p['lip_lo_w'])
        parts.add(V, F, 'LipUp' if which == 'up' else 'Lip', orient='front')
    V, F = seam_ribbon_i(bvh, width=p['seam_w'] * mm); parts.add(V, F, 'Seam', orient='front')
    for side in (-1, +1):
        if nostrils is not None:
            V, F = nostril_liner_i(bvh, side, rx=p['nostril_rx'] * mm, rz=p['nostril_rz'] * mm, ring=nostrils[side], P=P_skin)
            q = np.asarray(P_skin)[list(nostrils[side])]; ctr = [float(q[:, 0].mean()), -0.06, float(q[:, 2].mean())]
        else:
            V, F = nostril_liner_i(bvh, side, rx=p['nostril_rx'] * mm, rz=p['nostril_rz'] * mm); ctr = [side * 0.0145, -0.06, 1.5368]
        parts.add(V, F, 'Nostril', orient=('radial', ctr))
    return parts.object('Face_M'), parts
