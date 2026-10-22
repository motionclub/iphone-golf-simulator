"""Micro1k mandible edge + nape strip.
mandible(): a soft-plastic bone edge ON the jaw -- convex crest along the plate mandible arc (ear lobe -> gonial angle -> chin) snapped to the mesh surface,
crisp on the jaw side, long gentle flank under the jaw (no recess, nothing carved into the neck).  3D surface (geodesic) distance, arc frame for the side sign."""
import sys, heapq
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head')
from k_edit import *

# plate mandible arc in 3D (right side): x from the front-plate jaw outline, (y, z) from the profile-plate border (see MALE_HEAD_RESULTS Micro1k)
ARC_CTRL = np.array([(0.030, -0.100, 1.4592), (0.046, -0.0696, 1.464), (0.060, -0.056, 1.472), (0.068, -0.0415, 1.483),
                     (0.0715, -0.0345, 1.497), (0.0735, -0.031, 1.511), (0.0765, -0.029, 1.5247)])


def snap_arc(ctx, V, side=1, step=0.002, ctrl=None, passes=2):
    """control points -> nearest mesh surface points (same side) -> smooth polyline resampled every `step` m"""
    ctrl = ARC_CTRL if ctrl is None else ctrl
    pts = []
    cand = np.where((V[:, 0] * side > 0.015) & (V[:, 2] > 1.43) & (V[:, 2] < 1.56) & (V[:, 1] < 0.02))[0]
    for c in ctrl:
        q = np.array([c[0] * side, c[1], c[2]])
        # surface point: nearest vertex, then lateral (x) value of the surface at that (y, z) from the vertices within 3 mm in (y, z)
        d2 = ((V[cand, 1] - q[1]) ** 2 + (V[cand, 2] - q[2]) ** 2)
        near = cand[d2 < (0.0035 ** 2)]
        if len(near) == 0: near = cand[np.argsort(d2)[:6]]
        x = (V[near, 0] * side).max()                    # outermost sheet at (y, z)
        pts.append([x * side, q[1], q[2]])
    pts = np.array(pts)
    # chord-length cubic (Catmull-Rom) resampling
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    tt = np.arange(0, cum[-1], step)
    out = np.stack([np.interp(tt, cum, pts[:, k]) for k in range(3)], axis=1)
    for _ in range(passes):                              # smoothing of the resampled polyline
        out[1:-1] = 0.25 * out[:-2] + 0.5 * out[1:-1] + 0.25 * out[2:]
    return out


def arc_field(ctx, V, N, side, maxd=0.06, ctrl=None, passes=2):
    """signed surface distance s (m; + = jaw/cheek side, - = under-jaw/neck side) and arc parameter t in [0,1] for every vertex of `side`"""
    arc = snap_arc(ctx, V, side, ctrl=ctrl, passes=passes)
    idx = np.where(V[:, 0] * side > 0.004)[0]
    # nearest mesh vertex to every arc sample -> geodesic sources
    src = []
    for p in arc:
        dd = np.linalg.norm(V[idx] - p, axis=1); src.append(int(idx[np.argmin(dd)]))
    src = sorted(set(src))
    dist, who = ctx.geodesic(V, src, maxd=maxd)
    # tangent / parameter of each source along the arc (project arc samples onto the source list)
    tan = np.gradient(arc, axis=0); tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-12)
    L = len(arc)
    sidx = {}
    for s_ in src:
        j = int(np.argmin(np.linalg.norm(arc - V[s_], axis=1))); sidx[s_] = j
    s_signed = np.full(ctx.n, np.inf); t_par = np.zeros(ctx.n)
    ref = np.array([0.0, -0.4, 1.0])
    for v in np.where(np.isfinite(dist))[0]:
        q = who[v]; j = sidx[q]
        n = N[q]; tau = tan[j]; b = np.cross(n, tau); b /= max(np.linalg.norm(b), 1e-12)
        if b @ ref < 0: b = -b
        r = V[v] - V[q]
        sgn = 1.0 if (r @ b) >= 0 else -1.0
        s_signed[v] = sgn * dist[v]; t_par[v] = j / max(L - 1, 1)
    return s_signed, t_par, arc


def smooth_normals(ctx, N, iters=8):
    Nd = N.copy()
    for _ in range(iters):
        Nd = 0.5 * Nd + 0.5 * ctx.M.nbr_mean(Nd); Nd /= np.maximum(np.linalg.norm(Nd, axis=1, keepdims=True), 1e-12)
    return Nd


ARC_NAT = np.array([(0.034, -0.128, 1.4685), (0.046, -0.112, 1.4725), (0.056, -0.098, 1.4790), (0.061, -0.085, 1.4815), (0.064, -0.066, 1.4825),
                    (0.068, -0.0425, 1.4850), (0.0715, -0.0345, 1.497), (0.0735, -0.031, 1.511), (0.0765, -0.029, 1.5247)])


def mandible(ctx, V, scale=1.0, arc='nat', B=2.4, s0=1.5, sig_up=5.0, sig_lo=12.0, fade_chin=(0.06, 0.28), ear_clear=(8.0, 24.0), xmin=(0.016, 0.034), zlim=(1.43, 1.545), nsm=8, dsm=3, mirror_check=False, arc_passes=2, B_ang=None, ang_t=(0.58, 0.78)):
    """returns (V', mask).  d(s) = B * crest(s) along smoothed normals; asymmetric crest: sig_up on the jaw side (crisp edge), sig_lo on the under-jaw side (gentle)"""
    V = V.copy(); Ng = vertex_normals(V, ctx.F); Nd = smooth_normals(ctx, Ng, nsm)
    D = np.zeros_like(V); ear = sorted(set(ctx.loops['LOOP_ear_attach_L']) | set(ctx.loops['LOOP_ear_attach_R']) | set(ctx.loops['LOOP_helix_L']) | set(ctx.loops['LOOP_helix_R']))
    for side in (1, -1):
        s, t, arc_ = arc_field(ctx, V, Ng, side, ctrl=(ARC_NAT if arc == 'nat' else ARC_CTRL), passes=arc_passes)
        sel = np.where(np.isfinite(s) & (V[:, 0] * side > 0.004) & (V[:, 2] > zlim[0]) & (V[:, 2] < zlim[1]))[0]
        smm = s[sel] * 1000.0
        crest = np.where(smm >= s0, np.exp(-0.5 * ((smm - s0) / sig_up) ** 2), np.exp(-0.5 * ((smm - s0) / sig_lo) ** 2))
        wt = sstep(fade_chin[0], fade_chin[1], t[sel])                                   # fade in after the chin
        wx = sstep(xmin[0], xmin[1], np.abs(V[sel, 0]))
        we = sstep(ear_clear[0] * mm, ear_clear[1] * mm, ctx.dist['ear'][sel])
        Bt = B if B_ang is None else B + (B_ang - B) * sstep(ang_t[0], ang_t[1], t[sel])      # softer at the gonial angle / ramus (it faces sideways: any ridge there is lateral growth)
        d = scale * Bt * crest * wt * wx * we * mm
        D[sel] += Nd[sel] * d[:, None]
    if dsm:
        w = (np.linalg.norm(D, axis=1) > 0).astype(float); w = feather(ctx, w, 2)
        for _ in range(dsm): D = D + 0.5 * w[:, None] * (ctx.M.nbr_mean(D) - D)
    m = np.linalg.norm(D, axis=1) > 1e-7
    return V + D, m


# ---- nape strip (Adnan OK): flatten the C7 bump + crease, z 1.365-1.398, |x| < 20 mm, <= 2 mm
STRIP_Z = [1358.5, 1361.9, 1370.6, 1378.1, 1385.5, 1394.0, 1399.5, 1400.0]
STRIP_DY = [0.0, 0.0, 0.64, -1.76, -2.94, -2.18, -0.4, 0.0]


def nape_strip(ctx, V, sigma=0.0085, xmax=0.021, zlo=1.358, zhi=1.3999, scale=1.0):
    """straight-line target between the lower anchor (z 1.362) and the first zone row: removes the +2.5 mm bump and the -1.8 mm crease; metres, back side only"""
    V = V.copy(); x, y, z = V[:, 0], V[:, 1], V[:, 2]
    m = (y > 0.0) & (np.abs(x) < xmax) & (z >= zlo) & (z < zhi)
    w = np.exp(-0.5 * (x[m] / sigma) ** 2) * (1 - sstep(xmax - 0.006, xmax, np.abs(x[m])))
    V[m, 1] += scale * interp_profile(STRIP_Z, STRIP_DY, z[m] * 1000) * w * 1e-3
    return V, m


# ---- silhouette-neutral trim: the crest grows the jaw angle laterally by ~2 mm; take that width back with a broad, gentle inward shift of the lateral jaw/ramus region
def width_trim(ctx, V, Vref, target=0.0, zr=(1.440, 1.552), dz=0.0025, sig_z=0.003, band_z=((1.445, 1.462), (1.522, 1.540)), band_x=(0.036, 0.052), band_y=((-0.100, -0.070), (0.000, 0.028)), iters=2):
    """per-z excess of the max|x| silhouette over Vref (+ target, mm) -> inward x shift on the lateral region.  returns V', shift(z) table"""
    from j_lib import plane_section
    V = V.copy(); E = ctx.E; head = (Vref[:, 2] > 1.30) & (np.abs(Vref[:, 0]) < 0.12)
    zs = np.arange(zr[0], zr[1], dz); tot = np.zeros(len(zs))
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    for it in range(iters):
        ex = np.zeros(len(zs))
        for i, zz in enumerate(zs):
            a = plane_section(Vref, E, 2, zz, head); b = plane_section(V, E, 2, zz, head)
            if len(a) < 2 or len(b) < 2: continue
            ex[i] = max(0.0, np.abs(b[:, 0]).max() - np.abs(a[:, 0]).max() - target * mm)
        k = np.exp(-0.5 * (np.arange(-4, 5) * dz / sig_z) ** 2); k /= k.sum(); exs = np.convolve(np.pad(ex, 4, mode='edge'), k, mode='valid')
        exs = np.minimum(exs, 1.15 * ex.max() if ex.max() > 0 else 0)
        sh = np.interp(V[:, 2], zs, exs)
        g = (sstep(band_z[0][0], band_z[0][1], V[:, 2]) * (1 - sstep(band_z[1][0], band_z[1][1], V[:, 2])) * sstep(band_x[0], band_x[1], np.abs(V[:, 0]))
             * sstep(band_y[0][0], band_y[0][1], V[:, 1]) * (1 - sstep(band_y[1][0], band_y[1][1], V[:, 1])))
        g[~ctx.zone] = 0.0
        V[:, 0] -= np.sign(V[:, 0]) * sh * g; tot += ex
    return V, dict(z=zs.tolist(), excess_mm=(ex * 1000).tolist())


def width_trim_blob(ctx, V, Vref, sigma_g=0.016, t0=0.6, target=0.0, zr=(1.440, 1.552), dz=0.0025, sig_z=0.003, iters=3, zlim=(1.445, 1.545)):
    """silhouette-neutral trim with a smooth Gaussian footprint around the angle/ramus part (t >= t0) of the crest arc: inward x shift = per-z excess of max|x| over Vref"""
    from j_lib import plane_section
    V = V.copy(); E = ctx.E; head = (Vref[:, 2] > 1.30) & (np.abs(Vref[:, 0]) < 0.12)
    Ng = vertex_normals(V, ctx.F); G = np.zeros(ctx.n)
    for side in (1, -1):
        arc = snap_arc(ctx, V, side, ctrl=ARC_NAT, passes=12); a = arc[int(t0 * (len(arc) - 1)):]
        idx = np.where(V[:, 0] * side > 0.0)[0]
        dmin = np.full(ctx.n, np.inf)
        for i in range(0, len(idx), 4000):
            ii = idx[i:i + 4000]; dd = np.linalg.norm(V[ii][:, None, :] - a[None, :, :], axis=2).min(axis=1); dmin[ii] = dd
        G = np.maximum(G, np.where(np.isfinite(dmin), np.exp(-0.5 * (dmin / sigma_g) ** 2), 0.0))
    G *= sstep(zlim[0], zlim[0] + 0.012, V[:, 2]) * (1 - sstep(zlim[1] - 0.012, zlim[1], V[:, 2])); G[~ctx.zone] = 0.0
    zs = np.arange(zr[0], zr[1], dz); info = []
    for it in range(iters):
        ex = np.zeros(len(zs))
        for i, zz in enumerate(zs):
            a_ = plane_section(Vref, E, 2, zz, head); b_ = plane_section(V, E, 2, zz, head)
            if len(a_) < 2 or len(b_) < 2: continue
            ex[i] = max(0.0, np.abs(b_[:, 0]).max() - np.abs(a_[:, 0]).max() - target * mm)
        k = np.exp(-0.5 * (np.arange(-4, 5) * dz / sig_z) ** 2); k /= k.sum(); exs = np.convolve(np.pad(ex, 4, mode='edge'), k, mode='valid')
        info.append(float(ex.max() * 1000))
        V[:, 0] -= np.sign(V[:, 0]) * np.interp(V[:, 2], zs, exs) * G
    return V, dict(excess_mm_per_iter=info, G=G)
