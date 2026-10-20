"""Micro1l lips v2 (reference-driven): fuller, more natural lips measured against the face_lock FRONT + PROFILE plates.
Plate measurements (front plate, |x| in mm; redness R-G > 54 for the vermilion, luminance minimum for the seam; +-0.65 mm = one plate row):
  seam z 1507.7 (|x| <= 6), 1509.0 (8..28);  upper vermilion border z 1515.5 (notch at x=0), 1516.8 (x 2..14), 1515.5 (16..18), 1514.2 (20), merges with the seam at ~22;
  lower border z 1497.3 (x <= 18).   Start mesh: seam 1506.4 .. 1506.5 (x<=12), upper loop 1513.4 .. 1512.4 (a DIP at x=10..12, no cupid's bow), lower loop 1497.2 (ok).
  Profile plates: upper-lip pad 1.0-2.7 mm behind the plate (z 1514-1520), lower lip + chin within +-1.5 mm.
So the upper lip is ~3-4.5 mm too short, its border has no bow (dips at x=10..12) and the pad is flat.  Plan = plate curves, blended by `strength` (default 0.85: 'slightly more full', not a new mouth).
Geometry: vertical piecewise-linear warp keyed on the three carved loops (lower border / seam / upper border), forward pads (-y) for the upper lip + seam row; positions only.
`plan()` also returns the curves the Face_M lip paint is built from, so paint edge == carved loop."""
import sys, json
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from l_edit import *

XS = np.arange(0.0, 41.0, 1.0)          # |x| grid, mm

# ---- plate-derived targets (mm); smooth knots through the measurements above
H_UP = ([0, 3, 6, 10, 14, 18, 22, 26, 30, 34], [7.4, 8.4, 8.6, 8.2, 7.4, 6.0, 4.0, 2.0, 0.6, 0.0])           # upper vermilion height above the seam
H_LO = ([0, 6, 10, 14, 18, 22, 26, 30, 34], [10.4, 10.8, 11.0, 10.8, 9.0, 5.5, 1.5, 0.3, 0.0])                # lower vermilion height below the seam
D_SEAM = ([0, 5, 11, 16, 22, 28, 40], [1.1, 1.1, 1.9, 1.9, 1.0, 0.0, 0.0])                                    # seam raise vs the start loop (mm)


def _smooth(y, n=2):
    y = np.asarray(y, float).copy()
    for _ in range(n): y[1:-1] = 0.25 * y[:-2] + 0.5 * y[1:-1] + 0.25 * y[2:]
    return y


def loop_curve(V, ids, xs=XS):
    """mean z (mm) of a loop vs |x| (mm), light smoothing, linear fill-in; the loop vertices of both sides are folded"""
    P = V[np.array(ids)]; ax = np.abs(P[:, 0]) * 1000.0; z = P[:, 2] * 1000.0
    o = np.argsort(ax); ax, z = ax[o], z[o]
    out = np.full(len(xs), np.nan)
    for i, x in enumerate(xs):
        m = np.abs(ax - x) < 1.6
        if m.any(): out[i] = np.average(z[m], weights=1.0 / (1.0 + (ax[m] - x) ** 2))
    ok = np.isfinite(out)
    if ok.sum() < len(xs): out = np.interp(xs, xs[ok], out[ok])
    return _smooth(out, 3)


def plan(ctx, V, strength=0.85):
    """returns dict of curves (mm) on XS: old/new seam, upper, lower; also heights"""
    L = ctx.loops
    s_old = loop_curve(V, L['LOOP_mouth_seam']); u_old = loop_curve(V, L['LOOP_mouth_lip_upper']); l_old = loop_curve(V, L['LOOP_mouth_lip_lower'])
    s_new = s_old + np.interp(XS, *D_SEAM) * strength
    hu = np.interp(XS, *H_UP); hl = np.interp(XS, *H_LO)
    u_tar = s_new + hu; l_tar = s_new - hl
    # blend old -> plate target by `strength`; keep the borders at or above/below the seam, and merge to the seam where the target height is ~0
    u_new = u_old + strength * (u_tar - u_old); l_new = l_old + strength * (l_tar - l_old)
    u_new = np.maximum(u_new, s_new + 0.05); l_new = np.minimum(l_new, s_new - 0.05)
    # beyond the lip body the carved loops return to the old curves (corners unchanged)
    fade = 1.0 - np.clip((XS - 26.0) / 6.0, 0.0, 1.0)
    u_new = u_old + (u_new - u_old) * fade; l_new = l_old + (l_new - l_old) * fade; s_new = s_old + (s_new - s_old) * fade
    # paint curves: the vermilion tapers to the seam at the mouth corners (the carved loops keep their old, wider ring)
    taper = 1.0 - np.clip((XS - 25.0) / 7.0, 0.0, 1.0) ** 1.5
    up_paint = s_new + (u_new - s_new) * taper; lo_paint = s_new + (l_new - s_new) * taper
    return dict(x=XS, seam_old=s_old, up_old=u_old, lo_old=l_old, seam=s_new, up=u_new, lo=l_new, up_paint=up_paint, lo_paint=lo_paint)


def lips(ctx, V, scale=1.0, strength=0.85, up_pad=1.8, seam_fwd=0.8, low_fwd=0.0, up_margin=9.0, lo_margin=7.0, x_pad=24.0, smooth=2, plan_out=None):
    """returns (V', mask).  vertical warp of the lip band to the plan + forward pads.  forward = -y"""
    V = V.copy(); P = plan(ctx, V, strength * scale)
    if plan_out: json.dump({k: np.asarray(v).tolist() for k, v in P.items()}, open(plan_out, 'w'))
    ax = np.abs(V[:, 0]) * 1000.0; z = V[:, 2] * 1000.0
    zone = ctx.zone & (z > 1486.0) & (z < 1532.0) & (V[:, 1] < -0.118) & (ax < 40.0)
    dnose = ctx.dist['nose']; wn = sstep(4.0 * mm, 11.0 * mm, dnose)
    so = np.interp(ax, XS, P['seam_old']); uo = np.interp(ax, XS, P['up_old']); lo = np.interp(ax, XS, P['lo_old'])
    ds = np.interp(ax, XS, P['seam'] - P['seam_old']); du = np.interp(ax, XS, P['up'] - P['up_old']); dl = np.interp(ax, XS, P['lo'] - P['lo_old'])
    # piecewise-linear vertical displacement keyed on lower border / seam / upper border; fades above the upper border and below the lower border
    dzv = np.where(z >= so, ds + (du - ds) * np.clip((z - so) / np.maximum(uo - so, 0.5), 0, 1), dl + (ds - dl) * np.clip((z - lo) / np.maximum(so - lo, 0.5), 0, 1))
    dzv = np.where(z > uo, du * (1.0 - sstep(0.0, up_margin, z - uo)), dzv)
    dzv = np.where(z < lo, dl * (1.0 - sstep(0.0, lo_margin, lo - z)), dzv)
    D = np.zeros_like(V); D[:, 2] = dzv * mm
    # forward pads relative to the NEW seam
    zs_new = np.interp(ax, XS, P['seam']); dz = z + dzv - zs_new
    def xwin(xm, xlim, p=2.4): return np.clip(1.0 - (xm / xlim) ** p, 0.0, 1.0)
    fy = up_pad * np.exp(-0.5 * ((dz - 8.0) / 3.6) ** 2) * xwin(ax, x_pad) + seam_fwd * np.exp(-0.5 * (dz / 1.8) ** 2) * xwin(ax, 28.0) + low_fwd * np.exp(-0.5 * ((dz + 5.0) / 3.4) ** 2) * xwin(ax, 22.0)
    D[:, 1] = -fy * mm
    D *= (scale * zone * wn)[:, None]
    w = (np.linalg.norm(D, axis=1) > 0).astype(float); w = feather(ctx, w, 2)
    for _ in range(smooth): D = D + 0.5 * w[:, None] * (ctx.M.nbr_mean(D) - D)
    D[~ctx.zone] = 0.0
    m = np.linalg.norm(D, axis=1) > 1e-7
    return V + D, m


# =====================================================================================================================
# r2 (user feedback: "lips too feminine - get the exact lip shape of the reference image"): ABSOLUTE plan from curves traced on the face_lock front plate
# (gridded overlay, `r2_analysis/lip_overlay.py`; right half, mirrored, mm).  Seam = centre of the dark mouth line, up / lo = the visible vermilion borders.
CURVES_R2 = dict(
    seam=[[0, 1506.0], [5, 1506.3], [10, 1506.9], [15, 1507.4], [20, 1508.0], [25, 1508.8], [30, 1509.8], [35, 1511.0], [37, 1511.6]],
    seam_t=[[0, 3.2], [10, 3.1], [20, 2.8], [30, 2.4], [34, 2.4], [37, 1.2]],
    up=[[0, 1513.8], [3, 1514.6], [6, 1515.3], [9, 1515.6], [12, 1515.3], [16, 1514.4], [20, 1513.4], [25, 1512.0], [30, 1510.9], [35, 1510.9], [37, 1511.6]],
    lo=[[0, 1496.8], [5, 1496.9], [10, 1497.3], [15, 1498.2], [20, 1499.8], [25, 1502.2], [28, 1504.5], [30, 1506.5], [32, 1508.6], [37, 1511.6]])


def plan_abs(ctx, V, strength=1.0, curves=None):
    C = curves or CURVES_R2
    f = lambda k: np.interp(XS, [p[0] for p in C[k]], [p[1] for p in C[k]])
    L = ctx.loops
    s_old = loop_curve(V, L['LOOP_mouth_seam']); u_old = loop_curve(V, L['LOOP_mouth_lip_upper']); l_old = loop_curve(V, L['LOOP_mouth_lip_lower'])
    s_new = s_old + strength * (f('seam') - s_old); u_new = u_old + strength * (f('up') - u_old); l_new = l_old + strength * (f('lo') - l_old)
    u_new = np.maximum(u_new, s_new + 0.05); l_new = np.minimum(l_new, s_new - 0.05)
    # beyond the plate corner (|x| > 37) the carved loops keep their old curves
    fade = 1.0 - np.clip((XS - 36.0) / 4.0, 0.0, 1.0)
    u_new = u_old + (u_new - u_old) * fade; l_new = l_old + (l_new - l_old) * fade; s_new = s_old + (s_new - s_old) * fade
    seam_t = np.interp(XS, [p[0] for p in C['seam_t']], [p[1] for p in C['seam_t']])
    return dict(x=XS, seam_old=s_old, up_old=u_old, lo_old=l_old, seam=s_new, up=u_new, lo=l_new, up_paint=f('up'), lo_paint=f('lo'), seam_paint=f('seam'), seam_t=seam_t)


def lips2(ctx, V, scale=1.0, strength=1.0, up_pad=1.2, seam_fwd=0.5, low_fwd=0.0, up_margin=9.0, lo_margin=7.0, x_pad=24.0, smooth=2, plan_out=None, curves=None):
    """absolute-curve variant of lips(): the carved loops go to the traced plate curves (strength 1 = exact)"""
    V = V.copy(); P = plan_abs(ctx, V, strength * scale, curves)
    if plan_out: json.dump({k: np.asarray(v).tolist() for k, v in P.items()}, open(plan_out, 'w'))
    ax = np.abs(V[:, 0]) * 1000.0; z = V[:, 2] * 1000.0
    zone = ctx.zone & (z > 1486.0) & (z < 1532.0) & (V[:, 1] < -0.118) & (ax < 42.0)
    dnose = ctx.dist['nose']; wn = sstep(4.0 * mm, 11.0 * mm, dnose)
    so = np.interp(ax, XS, P['seam_old']); uo = np.interp(ax, XS, P['up_old']); lo = np.interp(ax, XS, P['lo_old'])
    ds = np.interp(ax, XS, P['seam'] - P['seam_old']); du = np.interp(ax, XS, P['up'] - P['up_old']); dl = np.interp(ax, XS, P['lo'] - P['lo_old'])
    dzv = np.where(z >= so, ds + (du - ds) * np.clip((z - so) / np.maximum(uo - so, 0.5), 0, 1), dl + (ds - dl) * np.clip((z - lo) / np.maximum(so - lo, 0.5), 0, 1))
    dzv = np.where(z > uo, du * (1.0 - sstep(0.0, up_margin, z - uo)), dzv)
    dzv = np.where(z < lo, dl * (1.0 - sstep(0.0, lo_margin, lo - z)), dzv)
    D = np.zeros_like(V); D[:, 2] = dzv * mm
    zs_new = np.interp(ax, XS, P['seam']); dz = z + dzv - zs_new
    def xwin(xm, xlim, p=2.4): return np.clip(1.0 - (xm / xlim) ** p, 0.0, 1.0)
    fy = up_pad * np.exp(-0.5 * ((dz - 8.0) / 3.6) ** 2) * xwin(ax, x_pad) + seam_fwd * np.exp(-0.5 * (dz / 1.8) ** 2) * xwin(ax, 28.0) + low_fwd * np.exp(-0.5 * ((dz + 5.0) / 3.4) ** 2) * xwin(ax, 22.0)
    D[:, 1] = -fy * mm
    D *= (scale * zone * wn)[:, None]
    w = (np.linalg.norm(D, axis=1) > 0).astype(float); w = feather(ctx, w, 2)
    for _ in range(smooth): D = D + 0.5 * w[:, None] * (ctx.M.nbr_mean(D) - D)
    D[~ctx.zone] = 0.0
    m = np.linalg.norm(D, axis=1) > 1e-7
    return V + D, m
