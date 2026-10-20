"""Micro1j jaw definition: border groove / cheek flattening along the plate-measured jaw border (profile plates 02/03, contrast-enhanced).
Displacements are along the (stored/geometric) vertex normal, inward-biased so the front/3-4 silhouettes do not widen."""
from j_edit import *

# jaw border in the profile plane: (y, z) metres, chin -> angle -> ramus -> ear lobe  (read from plates 02/03, see r/plate_border_poly.png)
POLY = np.array([(-0.140, 1.455), (-0.118, 1.4545), (-0.097, 1.454), (-0.078, 1.4605), (-0.060, 1.469), (-0.048, 1.4765),
                 (-0.040, 1.484), (-0.035, 1.493), (-0.032, 1.505), (-0.030, 1.516), (-0.029, 1.5247)])


def poly_signed_dist(pts_yz, poly=POLY):
    """signed 2D distance (+ toward the cheek: front/up) from points (n,2) to the polyline, and arc-length parameter t in [0, 1] of the foot point"""
    seg = poly[1:] - poly[:-1]; slen = np.linalg.norm(seg, axis=1); cum = np.concatenate([[0], np.cumsum(slen)]); L = cum[-1]
    best = np.full(len(pts_yz), np.inf); sgn = np.zeros(len(pts_yz)); tpar = np.zeros(len(pts_yz))
    for k in range(len(seg)):
        a = poly[k]; d = seg[k]; l2 = float(d @ d)
        t = np.clip(((pts_yz - a) @ d) / l2, 0, 1); foot = a + t[:, None] * d
        r = pts_yz - foot; dist = np.linalg.norm(r, axis=1)
        nrm = np.array([-d[1], d[0]]) / np.sqrt(l2)          # left normal (cheek side)
        better = dist < best
        best = np.where(better, dist, best); sgn = np.where(better, np.sign(r @ nrm + 1e-15), sgn); tpar = np.where(better, (cum[k] + t * slen[k]) / L, tpar)
    return sgn * best, tpar


def edit_jaw(ctx, V, scale=1.0, groove=2.6, sg=5.0, sigg=3.6, flat=0.7, sf=7.0, sigf=5.0, ridge=0.0, sigr=3.0,
             t_in=(0.10, 0.30), t_out=(0.93, 1.0), ear_clear=(0.006, 0.016), xmin=(0.012, 0.030), zlim=(1.43, 1.545)):
    """returns (V', mask).  s in mm.  groove: depth of the channel at s=-sg (neck/behind side), flat: cheek-side inward flattening at s=+sf"""
    V = V.copy(); x, y, z = V[:, 0], V[:, 1], V[:, 2]
    N = ctx.N0.copy()
    cand = (np.abs(x) > 0.010) & (z > zlim[0]) & (z < zlim[1]) & (y > -0.16) & (y < 0.03)
    idx = np.where(cand)[0]
    s, t = poly_signed_dist(np.stack([y[idx], z[idx]], 1)); s_mm = s * 1000.0
    # along-the-curve weight: fade in after the chin, fade out at the ear end
    wt = sstep(t_in[0], t_in[1], t) * (1.0 - sstep(t_out[0], t_out[1], t))
    # lateral weight: keep the chin-centre/submental region untouched
    wx = sstep(xmin[0], xmin[1], np.abs(x[idx]))
    # ear clearance: 3D distance to the ear attach loops
    ear = np.array(sorted(set(ctx.loops['LOOP_ear_attach_L']) | set(ctx.loops['LOOP_ear_attach_R']) | set(ctx.loops['LOOP_helix_L']) | set(ctx.loops['LOOP_helix_R'])))
    de = np.full(len(idx), np.inf)
    for c in range(0, len(ear), 64):
        e = V[ear[c:c + 64]]
        de = np.minimum(de, np.linalg.norm(V[idx][:, None, :] - e[None, :, :], axis=2).min(axis=1))
    we = sstep(ear_clear[0], ear_clear[1], de)
    prof = -groove * gauss(s_mm, -sg, sigg) - flat * gauss(s_mm, sf, sigf) + ridge * gauss(s_mm, 0.0, sigr)
    d = scale * prof * wt * wx * we * mm
    V[idx] += N[idx] * d[:, None]
    m = np.zeros(ctx.n, bool); m[idx[np.abs(d) > 1e-7]] = True
    return V, m


def edit_jaw2(ctx, V, scale=1.0, H=3.4, w=2.6, Lb=17.0, body_amt=0.65, flat=0.0, sf=7.0, sigf=5.0, ridge=0.35, sigr=2.2,
              t_in=(0.12, 0.38), t_out=(0.93, 1.0), t_ramus=0.72, ear_clear=(0.006, 0.016), xmin=(0.012, 0.030), zlim=(1.43, 1.545)):
    """terrace version: the surface below/behind the plate-measured jaw border is recessed by H (wall width 2w, ends at s = -Lb), optional hairline ridge on the border"""
    V = V.copy(); x, y, z = V[:, 0], V[:, 1], V[:, 2]
    N = ctx.N0
    cand = (np.abs(x) > 0.010) & (z > zlim[0]) & (z < zlim[1]) & (y > -0.16) & (y < 0.03)
    idx = np.where(cand)[0]
    s, t = poly_signed_dist(np.stack([y[idx], z[idx]], 1)); s_mm = s * 1000.0
    amp = np.where(t < t_ramus, body_amt + (1 - body_amt) * sstep(0.35, t_ramus, t), 1.0)
    wt = sstep(t_in[0], t_in[1], t) * (1.0 - sstep(t_out[0], t_out[1], t)) * amp
    wx = sstep(xmin[0], xmin[1], np.abs(x[idx]))
    ear = np.array(sorted(set(ctx.loops['LOOP_ear_attach_L']) | set(ctx.loops['LOOP_ear_attach_R']) | set(ctx.loops['LOOP_helix_L']) | set(ctx.loops['LOOP_helix_R'])))
    de = np.full(len(idx), np.inf)
    for c in range(0, len(ear), 64):
        e = V[ear[c:c + 64]]; de = np.minimum(de, np.linalg.norm(V[idx][:, None, :] - e[None, :, :], axis=2).min(axis=1))
    we = sstep(ear_clear[0], ear_clear[1], de)
    wall = sstep(w, -w, s_mm)                                   # 0 above the border, 1 below it
    ret = 1.0 - sstep(-(Lb - 7.0), -Lb, s_mm)                   # return to 0 further below/behind
    prof = -H * wall * ret - flat * gauss(s_mm, sf, sigf) + ridge * gauss(s_mm, 0.0, sigr)
    d = scale * prof * wt * wx * we * mm
    V[idx] += N[idx] * d[:, None]
    m = np.zeros(ctx.n, bool); m[idx[np.abs(d) > 1e-7]] = True
    return V, m


def edit_jaw3(ctx, V, scale=1.0, H=6.0, s0=1.5, Lr=18.0, Lret=14.0, ridge=1.1, sr=0.5, sigr=2.4, flat=0.0, sf=8.0, sigf=5.0,
              body_amt=0.7, t_in=(0.12, 0.38), t_out=(0.93, 1.0), t_ramus=0.72, ear_clear=(0.006, 0.016), xmin=(0.012, 0.030), zlim=(1.43, 1.545), nsm=0, dsm=0, prot=(1.468, 1.486, 12.0, 18.0)):
    """roof-edge version: inclined recess (slope H over Lr) behind a small ridge on the plate border; returns to 0 after Lret more mm"""
    V = V.copy(); x, y, z = V[:, 0], V[:, 1], V[:, 2]
    N = ctx.N0
    cand = (np.abs(x) > 0.010) & (z > zlim[0]) & (z < zlim[1]) & (y > -0.16) & (y < 0.03)
    idx = np.where(cand)[0]
    s, t = poly_signed_dist(np.stack([y[idx], z[idx]], 1)); s_mm = s * 1000.0
    amp = np.where(t < t_ramus, body_amt + (1 - body_amt) * sstep(0.35, t_ramus, t), 1.0)
    wt = sstep(t_in[0], t_in[1], t) * (1.0 - sstep(t_out[0], t_out[1], t)) * amp
    wx = sstep(xmin[0], xmin[1], np.abs(x[idx]))
    ear = np.array(sorted(set(ctx.loops['LOOP_ear_attach_L']) | set(ctx.loops['LOOP_ear_attach_R']) | set(ctx.loops['LOOP_helix_L']) | set(ctx.loops['LOOP_helix_R'])))
    de = np.full(len(idx), np.inf)
    for c in range(0, len(ear), 64):
        e = V[ear[c:c + 64]]; de = np.minimum(de, np.linalg.norm(V[idx][:, None, :] - e[None, :, :], axis=2).min(axis=1))
    we = sstep(ear_clear[0], ear_clear[1], de)
    ramp = sstep(s0, -Lr, s_mm)                                  # 0 on the cheek side, 1 once Lr mm behind the border
    ret = 1.0 - sstep(-Lr, -(Lr + Lret), s_mm)                   # then fade back out
    prof = -H * ramp * ret - flat * gauss(s_mm, sf, sigf) + ridge * gauss(s_mm, sr, sigr)
    d = scale * prof * wt * wx * we * mm
    Nd = N
    if nsm:                                           # coherent displacement directions: umbrella-smoothed normals (renormalised)
        Nd = N.copy()
        for _ in range(nsm):
            Nd = 0.5 * Nd + 0.5 * ctx.M.nbr_mean(Nd); Nd /= np.maximum(np.linalg.norm(Nd, axis=1, keepdims=True), 1e-12)
    D = np.zeros((ctx.n, 3)); D[idx] = Nd[idx] * d[:, None]
    if dsm:                                           # smooth the displacement FIELD (vertices outside the candidate set stay at 0 so it tapers)
        w = np.zeros(ctx.n); w[idx] = 1.0
        for _ in range(dsm):
            D = D + 0.5 * w[:, None] * (ctx.M.nbr_mean(D) - D)
    if prot:                                          # protect the silhouette-defining mastoid/neck-side bulge behind the angle (z < ~1.48)
        pa = np.where(np.abs(x) > 0.010, 1.0, 0.0)
        sa, ta = poly_signed_dist(np.stack([y, z], 1)); sa = sa * 1000.0
        keep = 1.0 - (1.0 - sstep(prot[0], prot[1], z)) * sstep(-prot[2], -prot[3], sa)
        D = D * keep[:, None]
    V = V + D
    m = np.linalg.norm(D, axis=1) > 1e-7
    return V, m
