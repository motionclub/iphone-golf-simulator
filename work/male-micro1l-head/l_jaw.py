"""Micro1l jaw: continuous soft-plastic mandible edge from the chin midline -> body -> gonial angle -> ramus fade, plus a modest V->U lowering of the
jaw underside at the chin sides (the plate's visible jaw line sits 3-5 mm lower than ours at |x| 20-40 mm).  Position-only, along smoothed normals / -z.
Built on Micro1k's arc machinery (arc over the mesh's natural border = n_z -0.5 iso-line) but extended around the chin and with its own surface-distance field."""
import sys, heapq
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from l_edit import *

# natural jaw border (right side), (x, y, z) metres: chin corner (45 deg normal) -> body -> angle -> ramus.  Chin part from sagittal sections of the CURRENT mesh,
# body/angle/ramus = Micro1k's ARC_NAT (same surface; chat-9's nape tail moved <= 1.5 mm there)
ARC_L = np.array([(0.000, -0.1445, 1.4620), (0.010, -0.1435, 1.4628), (0.020, -0.1385, 1.4645), (0.027, -0.1310, 1.4665),
                  (0.034, -0.128, 1.4685), (0.046, -0.112, 1.4725), (0.056, -0.098, 1.4790), (0.061, -0.085, 1.4815), (0.064, -0.066, 1.4825),
                  (0.068, -0.0425, 1.4850), (0.0715, -0.0345, 1.497), (0.0735, -0.031, 1.511), (0.0765, -0.029, 1.5247)])


# r2 (user feedback: chin + jawline must connect): chin part of the arc moved DOWN to the chin's inferior border (front edge of the under-chin plane, support points of the sagittal
# contours at 70/60 deg) and blended into the natural border by x ~ 46 mm; everything beyond x 46 is unchanged
ARC_R2 = np.array([(0.000, -0.1325, 1.4543), (0.010, -0.1330, 1.4551), (0.020, -0.1300, 1.4575), (0.027, -0.1260, 1.4612), (0.034, -0.1225, 1.4665), (0.046, -0.1090, 1.4720),
                   (0.056, -0.098, 1.479), (0.061, -0.085, 1.4815), (0.064, -0.066, 1.4825), (0.068, -0.0425, 1.4850), (0.0715, -0.0345, 1.497), (0.0735, -0.031, 1.511), (0.0765, -0.029, 1.5247)])


def snap_arc3(ctx, V, side, ctrl, step=0.002, passes=2, rad=0.006):
    """control points (x,y,z; right side, mirrored by `side`) -> nearest mesh surface vertex in 3D (within `rad`, mean of the 3 nearest) -> smooth polyline resampled every `step`"""
    pts = []
    zone = np.where(ctx.zone & (V[:, 2] > 1.43) & (V[:, 2] < 1.56) & (V[:, 1] < 0.02) & (V[:, 0] * side > -0.012))[0]
    for c in ctrl:
        q = np.array([c[0] * side, c[1], c[2]])
        d = np.linalg.norm(V[zone] - q, axis=1); i = zone[np.argsort(d)[:3]]
        w = 1.0 / np.maximum(np.sort(d)[:3], 1e-4); p = (V[i] * w[:, None]).sum(0) / w.sum()
        pts.append(p)
    pts = np.array(pts)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    tt = np.arange(0, cum[-1], step)
    out = np.stack([np.interp(tt, cum, pts[:, k]) for k in range(3)], axis=1)
    for _ in range(passes): out[1:-1] = 0.25 * out[:-2] + 0.5 * out[1:-1] + 0.25 * out[2:]
    return out


def arc_field3(ctx, V, N, side, maxd=0.06, ctrl=None, passes=3, xmin=-0.006):
    """signed surface distance s (m; + = jaw/cheek side, - = under-jaw/neck side) and arc parameter t in [0,1] for every vertex with x*side > xmin"""
    arc = snap_arc3(ctx, V, side, ARC_L if ctrl is None else ctrl, passes=passes)
    idx = np.where((V[:, 0] * side > xmin) & ctx.zone)[0]
    src = []
    for p in arc:
        dd = np.linalg.norm(V[idx] - p, axis=1); src.append(int(idx[np.argmin(dd)]))
    src = sorted(set(src))
    dist, who = ctx.geodesic(V, src, maxd=maxd)
    tan = np.gradient(arc, axis=0); tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-12)
    L = len(arc); sidx = {}
    for s_ in src: sidx[s_] = int(np.argmin(np.linalg.norm(arc - V[s_], axis=1)))
    s_signed = np.full(ctx.n, np.inf); t_par = np.zeros(ctx.n); ref = np.array([0.0, -0.4, 1.0])
    for v in np.where(np.isfinite(dist) & (V[:, 0] * side > xmin))[0]:
        q = who[v]; j = sidx[q]; n = N[q]; tau = tan[j]; b = np.cross(n, tau); b /= max(np.linalg.norm(b), 1e-12)
        if b @ ref < 0: b = -b
        sgn = 1.0 if ((V[v] - V[q]) @ b) >= 0 else -1.0
        s_signed[v] = sgn * dist[v]; t_par[v] = j / max(L - 1, 1)
    return s_signed, t_par, arc


def chord_spline(pts, step=0.0006):
    """C1 chordal Catmull-Rom through the points, resampled every `step` m; returns (P, T) positions and unit tangents"""
    pts = np.asarray(pts, float); n = len(pts)
    t = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    m = np.zeros_like(pts)
    m[1:-1] = (pts[2:] - pts[:-2]) / (t[2:] - t[:-2])[:, None]
    m[0] = (pts[1] - pts[0]) / (t[1] - t[0]); m[-1] = (pts[-1] - pts[-2]) / (t[-1] - t[-2])
    tt = np.arange(0, t[-1] + 1e-9, step); idx = np.clip(np.searchsorted(t, tt, side='right') - 1, 0, n - 2)
    h = (t[idx + 1] - t[idx])[:, None]; u = ((tt - t[idx])[:, None]) / h
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
    P = h00 * pts[idx] + h10 * h * m[idx] + h01 * pts[idx + 1] + h11 * h * m[idx + 1]
    T = np.gradient(P, axis=0); T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    return P, T


def snap_ctrl(ctx, V, side, ctrl, k=3):
    """control points -> inverse-distance mean of the k nearest zone vertices (3D)"""
    zone = np.where(ctx.zone & (V[:, 2] > 1.43) & (V[:, 2] < 1.56) & (V[:, 1] < 0.02) & (V[:, 0] * side > -0.012))[0]
    out = []
    for c in ctrl:
        q = np.array([c[0] * side, c[1], c[2]]); d = np.linalg.norm(V[zone] - q, axis=1); i = zone[np.argsort(d)[:k]]
        w = 1.0 / np.maximum(np.sort(d)[:k], 1e-4); out.append((V[i] * w[:, None]).sum(0) / w.sum())
    return np.array(out)


def euclid_field(ctx, V, Nd, side, ctrl=None, step=0.0006, xmin=-0.006, band=0.034, smooth_ctrl=1):
    """signed Euclidean distance s (m; + above/outside the border, - below) to the smooth spline arc, arc parameter t in [0,1], for vertices near the arc"""
    P0 = snap_ctrl(ctx, V, side, ARC_L if ctrl is None else ctrl)
    for _ in range(smooth_ctrl): P0[1:-1] = 0.25 * P0[:-2] + 0.5 * P0[1:-1] + 0.25 * P0[2:]
    P, T = chord_spline(P0, step)
    idx = np.where(ctx.zone & (V[:, 0] * side > xmin) & (V[:, 2] > 1.40) & (V[:, 2] < 1.57))[0]
    s = np.full(ctx.n, np.inf); tpar = np.zeros(ctx.n); L = len(P); jn = np.zeros(ctx.n, np.int64)
    # surface normal along the arc: smoothed vertex normal of the nearest vertex to each arc sample (via the near-arc vertices)
    near = idx[np.where(np.min(np.linalg.norm(V[idx][:, None, :] - P[None, ::10, :], axis=2), axis=1) < 0.012)[0]]
    Na = np.zeros_like(P)
    for j in range(L):
        d = np.linalg.norm(V[near] - P[j], axis=1); i = near[np.argsort(d)[:3]]; n = Nd[i].mean(0); Na[j] = n / np.linalg.norm(n)
    Na = np.stack([np.convolve(np.pad(Na[:, k], 20, mode='edge'), np.ones(41) / 41, mode='valid') for k in range(3)], axis=1); Na /= np.linalg.norm(Na, axis=1, keepdims=True)
    ref = np.array([0.0, -0.4, 1.0]); Bj = np.cross(Na, T); Bj /= np.maximum(np.linalg.norm(Bj, axis=1, keepdims=True), 1e-12); Bj[(Bj @ ref) < 0] *= -1
    for i0 in range(0, len(idx), 1500):
        ii = idx[i0:i0 + 1500]; d = np.linalg.norm(V[ii][:, None, :] - P[None, :, :], axis=2); j = np.argmin(d, axis=1); dm = d[np.arange(len(ii)), j]
        for q in range(len(ii)):
            if dm[q] > band: continue
            b = np.cross(Na[j[q]], T[j[q]]); b /= max(np.linalg.norm(b), 1e-12)
            if b @ ref < 0: b = -b
            s[ii[q]] = (1.0 if (V[ii[q]] - P[j[q]]) @ b >= 0 else -1.0) * dm[q]; tpar[ii[q]] = j[q] / (L - 1); jn[ii[q]] = j[q]
    return s, tpar, (P, jn, Bj)


def smooth_normals(ctx, N, iters=8):
    Nd = N.copy()
    for _ in range(iters):
        Nd = 0.5 * Nd + 0.5 * ctx.M.nbr_mean(Nd); Nd /= np.maximum(np.linalg.norm(Nd, axis=1, keepdims=True), 1e-12)
    return Nd


def u_drop_profile(x_mm, base=0.0, amp=5.0, cen=33.0, wid=15.0, x_fade=(54.0, 68.0), scale=1.0, mid=(6.0, 16.0)):
    """mm of downward shift of the jaw underside vs |x| (mm): ~0.8 x the measured plate-vs-mesh jaw-line delta (2 / 3.9 / 5.6 / 3.2 / 1.6 / 0 at x 0 / 20 / 30 / 40 / 50 / 60)"""
    ax = np.abs(x_mm)
    p = base + amp * np.exp(-(((ax - cen) / wid) ** 2))
    p *= (1.0 - sstep(x_fade[0], x_fade[1], ax)) * sstep(mid[0], mid[1], ax)           # no lowering of the chin midline (profile silhouette matches the plate there)
    return scale * p


def jaw(ctx, V, B=3.0, s0=1.0, sig_up=4.5, sig_lo=8.0, drop=1.0, drop_kw=None, drop_win=(18.0, 34.0, 12.0), ear_clear=(8.0, 24.0), zlim=(1.43, 1.545), nsm=8, dsm=3,
        B_ang=2.0, ang_t=(0.62, 0.82), t_fade_end=(0.9, 1.0), midline_blend=0.006, euclid=True, chin_scale=1.0, chin_t=(0.12, 0.40), sig_up_ang=None, arc='l', sig_up_chin=None, sig_lo_chin=None, chin_sig_t=(0.18, 0.45)):
    """returns (V', mask).  crest d(s) = B*crest(s) along smoothed normals (asymmetric: sig_up on the jaw side, sig_lo below), plus the U-drop (-z) with a window g(s) around the border"""
    V = V.copy(); Ng = vertex_normals(V, ctx.F); Nd = smooth_normals(ctx, Ng, nsm)
    D = np.zeros_like(V); NB = np.zeros_like(V); NBF = np.zeros_like(V)
    for side in (1, -1):
        s, t, arc_ = euclid_field(ctx, V, Nd, side, ctrl=(ARC_R2 if arc == 'r2' else None)) if euclid else arc_field3(ctx, V, Ng, side)
        sel = np.where(np.isfinite(s) & (V[:, 0] * side > -midline_blend) & (V[:, 2] > zlim[0]) & (V[:, 2] < zlim[1]) & ctx.zone)[0]
        smm = s[sel] * 1000.0
        sup = sig_up + (sig_up_ang - sig_up) * sstep(ang_t[0] - 0.12, ang_t[1], t[sel]) if sig_up_ang is not None else sig_up        # gentler upper flank at the angle / ramus (no pocket between cheek and crest)
        chin_w = 1.0 - sstep(chin_sig_t[0], chin_sig_t[1], t[sel])
        if sig_up_chin is not None: sup = sup + (sig_up_chin - sup) * chin_w                     # the chin mesh is sparse (valence 3-5, 6-9 mm): a wider crest there is sampled smoothly, a narrow one makes triangular spikes
        slo = sig_lo + ((sig_lo_chin - sig_lo) * chin_w if sig_lo_chin is not None else 0.0)
        crest = np.where(smm >= s0, np.exp(-0.5 * ((smm - s0) / sup) ** 2), np.exp(-0.5 * ((smm - s0) / slo) ** 2))
        we = sstep(ear_clear[0] * mm, ear_clear[1] * mm, ctx.dist['ear'][sel])
        Bfull = B + (B_ang - B) * sstep(ang_t[0], ang_t[1], t[sel])
        Bt = Bfull * (chin_scale + (1.0 - chin_scale) * sstep(chin_t[0], chin_t[1], t[sel]))
        wt = 1.0 - sstep(t_fade_end[0], t_fade_end[1], t[sel])
        dn = Bt * crest * we * wt * mm
        sg = np.where(smm >= s0, sup, slo); dcr = (-(smm - s0) / sg ** 2) * crest * we * wt; slope = Bt * dcr; slope_full = Bfull * dcr            # dimensionless d(height)/ds of the crest (geometry / full-height crest)
        if euclid:
            Parc, jn, Bj = arc_; bb = Bj[jn[sel]]; tp = bb - (bb * Nd[sel]).sum(1, keepdims=True) * Nd[sel]; tp /= np.maximum(np.linalg.norm(tp, axis=1, keepdims=True), 1e-9)
            gdir = tp                                      # smooth across-arc direction (arc binormal): continuous through s = 0, no sign flip
            wov = np.where(np.abs(V[sel, 0]) < midline_blend, 0.5, 1.0)
            NB[sel] += (-slope[:, None] * gdir) * wov[:, None]; NBF[sel] += (-slope_full[:, None] * gdir) * wov[:, None]
        # U-drop: window around the border (asymmetric Gaussian in s: more below, less above)
        g = np.where(smm >= 0.0, 1.0 - sstep(0.0, drop_win[2], smm), 1.0 - sstep(drop_win[0], drop_win[1], -smm))
        wzz = sstep(1.446, 1.458, V[sel, 2])                                   # keep the neck column below the under-jaw plane untouched
        dz = -drop * u_drop_profile(V[sel, 0] * 1000.0, **(drop_kw or {})) * g * wzz * we * wt * mm
        # midline: both sides' fields overlap for |x| < midline_blend -> average (weight 0.5 each there)
        w_ov = np.where(np.abs(V[sel, 0]) < midline_blend, 0.5, 1.0)
        D[sel, :] += (Nd[sel] * dn[:, None] + np.stack([np.zeros_like(dz), np.zeros_like(dz), dz], axis=1)) * w_ov[:, None]
    if dsm:
        w = (np.linalg.norm(D, axis=1) > 0).astype(float); w = feather(ctx, w, 2)
        for _ in range(dsm): D = D + 0.5 * w[:, None] * (ctx.M.nbr_mean(D) - D)
    D[~ctx.zone] = 0.0
    m = np.linalg.norm(D, axis=1) > 1e-7
    jaw.last_nb = NB; jaw.last_nb_full = NBF
    return V + D, m
