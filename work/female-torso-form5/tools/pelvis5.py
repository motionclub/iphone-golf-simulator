"""FEMALE TORSO FORM5 underbutt: continuous lobe underside + recessed thigh back + LEG-TOP extension (documented mask).  numpy only.

Problem (FORM4): the thigh back (original, +92.5 mm at z .76-.81, x .065) sits ~10 mm deeper than the plate's (+83) and the lobe has nowhere to curve into: the lobe starts at
z .82 and climbs ~15 mm in 2 cm right above the pinned zone-floor ring (z .795), full width -> one horizontal groove ("mechanical cut").
FORM5: y-only field on the BACK half of the zone interior + the thigh tops below the old floor (flood-filled thigh tubes, floor ring pinned):
  * thigh back recessed by R(z) <= R0 over z .62-.84 (0 at the floor ring, smooth),
  * each lobe's lower flank extended by its own dome  y_d = Y0(x) - k (z - za(x))^2  (k ~ 7400 mm/m^2 = FORM4's measured lobe curvature, plate silhouette S-curve is the same parabola),
  * surface = smooth-max(recessed thigh, dome)  -> the fold is the (curved, lateral-rising) intersection, softened by the smooth-max radius; blended into FORM4 above z ~.87.
"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
import numpy as np
from torso2 import PS, CO0, T, BORDER, ED, EA, EB, sstep, sstep5, gauss1d, smax
from footprint import grid_surface

N = len(CO0)
ZV = CO0[:, 2]


def flood_ext(zf, zone=T, border=BORDER):
    """thigh-tube vertices below the old zone floor, z >= zf, connected to the old leg-top border (hands excluded: they are not connected through the legs).
    returns (ext mask, floor-ring mask)"""
    nbr = [[] for _ in range(N)]
    for a, b in zip(EA, EB):
        nbr[a].append(b); nbr[b].append(a)
    seed = np.where(border & (ZV < 0.83))[0]
    ok = np.zeros(N, bool); ok[seed] = True
    st = list(seed)
    while st:
        v = st.pop()
        for w in nbr[v]:
            if not ok[w] and (not zone[w]) and ZV[w] >= zf:
                ok[w] = True; st.append(w)
    ext = ok & ~border
    ring = np.zeros(N, bool)
    for v in np.where(ext)[0]:
        for w in nbr[v]:
            if (not ok[w]) and (not zone[w]):
                ring[v] = True; break
    return ext, ring


PD = dict(
    zf=0.62,                       # floor of the LEG-TOP extension (ring pinned)
    R0=0.0095, rz0=0.62, rz1=0.76, rz2=0.79, rz3=0.84,        # thigh recess: 0 at rz0 -> R0 at rz1 (sstep5), flat to rz2, -> 0 at rz3
    wx0=0.012, wx1=0.047,          # centre-line weight: 0 for |x|<wx0 (gap / cleft untouched) -> 1 at wx1
    wxo0=0.125, wxo1=0.172,        # lateral fade of the recess (thigh sides)
    wy0=0.012, wy1=0.052,          # back-half weight on the ORIGINAL y: 0 at y<=wy0 -> 1 at y>=wy1
    rmode='scale', rpow=1.0, wg0=0.006, wg1=0.045,   # recess mode: 'scale' = depth-proportional (y/y_peak)^rpow (no x window), gap guard |x| wg0->wg1
    kd=7400.0,                     # dome curvature mm/m^2 (FORM4 lobe flank ~7000-8100)
    kd_lat=6200.0, kd_x0=0.085, kd_x1=0.125,     # laterally flatter lobes
    dz_dome=0.0,                   # shift of the dome apex height (m): + raises the dome (fold higher), - lowers
    ku=0.016,                      # smooth-max radius (m) of the thigh/dome union
    zw0=0.855, zw1=0.885,          # blend back to FORM4 above this z (sstep)
    za_blend=0.015,                # dome joins FORM4 over this height below the apex
    fold_lift=0.0, fold_x0=0.06, fold_x1=0.12,   # extra rise of the fold laterally (m at x1): shifts the extension up with |x|
    gdep=0.0, gz0=0.802, gz_rise=0.02, gx0=0.03, gx1=0.13, gw=0.009, gxo0=0.125,   # thin curved fold crease (off by default)
    cdip=0.0, cd_x0=0.025, cd_x1=0.06, cd_z0=0.80, cd_z1=0.855, cd_zw=0.02,   # central lower-lobe relief (off by default)
    rm0=0.01, rm1=0.0,                            # medial fade window of the recess (rm1 = 0: off)
    tm_x0=0.10, tm_x1=0.0,                        # lateral fade of the smooth thigh model (tm_x1 = 0: off)
    rl0=0.12, rl1=0.0,                            # lateral fade window of the recess (rl1 = 0: off)
    dshift=0.0, ds_x0=0.07, ds_x1=0.12,          # lateral rise (m) of the recess taper + thigh->lobe hand-over (z-shift): the fold starts higher at the lateral columns (curved smile)
    zanc=0.845, qa=0.015, qw=0.02,  # anchor height of the lobe extension; hand-over to FORM4 between zanc-qa and zanc-qa+qw
    # ---- 'ramp' mode (FORM5 v2): the lobe underside is a smooth sigmoid ramp from the recessed thigh to FORM4's lobe (tangent-line continuation): y = YT + R(z) (Y_lobe - YT)
    ramp=0, ra=2.0, rc=3.0, rzf=0.775, rza=0.86, rzf_x=0.0, rza_x=0.0, rx0=0.06, rx1=0.13, rsig=3, rq2w=0.012, rkap=0.0,
)


def column_apex(co4, P):
    """per-column apex of the FORM4 lobes: Y0(|x|) (m), za(|x|) (m): sub-grid parabola refinement of the argmax, then a smooth polynomial in |x| (no staircase noise)"""
    xs = np.arange(0.0, 0.1801, 0.004); zs = np.arange(0.82, 0.93, 0.002)
    G = grid_surface(co4, 'back', xs, zs, sig=0.006)
    Y0 = np.zeros(len(xs)); za = np.zeros(len(xs))
    for j in range(len(xs)):
        i = int(G[:, j].argmax())
        i0, i1 = max(i - 12, 0), min(i + 13, len(zs))
        pz = np.polyfit(zs[i0:i1], G[i0:i1, j], 2)
        if pz[0] < -1e-6:
            za[j] = -pz[1] / (2 * pz[0]); Y0[j] = np.polyval(pz, za[j])
        else:
            za[j] = zs[i]; Y0[j] = G[i, j]
    xs_ok = (xs >= 0.0) & (xs <= 0.150)
    cy = np.polyfit(xs[xs_ok], Y0[xs_ok], 6); cz = np.polyfit(xs[xs_ok], za[xs_ok], 4)
    xe = np.minimum(xs, 0.150)
    return xs, np.polyval(cy, xe), np.polyval(cz, xe)


def lobe_ext_table(co4, P):
    """FORM4's smooth lobe surface continued DOWN from the anchor height za0: C2 with FORM4 at za0 (value, slope, curvature from the Gaussian-averaged back surface), curvature then relaxing to
    kappa_b over `ext_len`.  returns (xs, zs, Y[zs, xs]) tables (x = |x|)."""
    za0 = P.get('zanc', 0.845)
    xs = np.arange(0.0, 0.1801, 0.002)
    zq = np.array([za0 - 0.010, za0, za0 + 0.010])
    G = grid_surface(co4, 'back', xs, zq, sig=0.007)
    def sm(a, s=0.008):
        k = np.arange(-int(3 * s / 0.002), int(3 * s / 0.002) + 1) * 0.002
        w = np.exp(-0.5 * (k / s) ** 2); w /= w.sum(); pad = len(k) // 2
        return np.convolve(np.pad(a, pad, mode='edge'), w, mode='valid')
    G0 = sm(G[1]); g1 = sm((G[2] - G[0]) / 0.02)
    kap_a = sm(-(G[2] - 2 * G[1] + G[0]) / 0.01 ** 2, 0.010)               # convex curvature (1/m) at the anchor
    kap_a = np.clip(kap_a, P.get('kap_lo', 8.0), P.get('kap_hi', 22.0))
    ax = xs
    kap_b = 2.0 * (P['kd'] + (P['kd_lat'] - P['kd']) * sstep((ax - P['kd_x0']) / (P['kd_x1'] - P['kd_x0']))) / 1000.0
    zs = np.arange(0.60, za0 + 1e-9, 0.0005)[::-1]                            # from the anchor downward
    h = 0.0005
    dist = za0 - zs
    sblend = sstep(dist / P.get('ext_len', 0.03))                             # 0 at the anchor -> 1 far below
    Y = np.zeros((len(zs), len(xs)))
    for j in range(len(xs)):
        kap = kap_a[j] + (kap_b[j] - kap_a[j]) * sblend
        slope = g1[j] + np.concatenate([[0.0], np.cumsum(0.5 * (kap[1:] + kap[:-1]) * h)])
        Y[:, j] = G0[j] - np.concatenate([[0.0], np.cumsum(0.5 * (slope[1:] + slope[:-1]) * h)])
    return xs, zs[::-1], Y[::-1]


def ext_eval(table, axv, zv):
    xs, zs, Y = table
    iz = np.clip((zv - zs[0]) / (zs[1] - zs[0]), 0, len(zs) - 1.001)
    ix = np.clip(axv / (xs[1] - xs[0]), 0, len(xs) - 1.001)
    i0 = iz.astype(int); j0 = ix.astype(int); fz = iz - i0; fx = ix - j0
    return (Y[i0, j0] * (1 - fz) * (1 - fx) + Y[i0 + 1, j0] * fz * (1 - fx) + Y[i0, j0 + 1] * (1 - fz) * fx + Y[i0 + 1, j0 + 1] * fz * fx)


def thigh_model(P):
    """smooth thigh back surface Y(x,z) = a(x) + b(x) (z-z0) + c(x) (z-z0)^2, per-column fit of the DENOISED original over z .64-.78 (both legs folded onto |x|),
    coefficients smoothed over x; extrapolated up through the fold so the thigh/dome intersection is clean (the raw denoised original keeps lattice terraces)."""
    xs = np.arange(0.0, 0.1801, 0.004); zs = np.arange(0.64, 0.781, 0.004)
    sel = (PS[:, 1] > 0.0) & (PS[:, 2] > 0.60) & (PS[:, 2] < 0.82) & (np.abs(PS[:, 0]) < 0.20)
    Pt = PS[sel]
    ax_ = np.abs(Pt[:, 0])
    G = np.zeros((len(zs), len(xs)))
    for j, x in enumerate(xs):
        for i, z in enumerate(zs):
            d2 = (ax_ - x) ** 2 + (Pt[:, 2] - z) ** 2
            w = np.exp(-d2 / (2 * 0.008 ** 2))
            G[i, j] = (w * Pt[:, 1]).sum() / max(w.sum(), 1e-12)
    z0 = 0.72
    co = np.array([np.polyfit(zs - z0, G[:, j], 2)[::-1] for j in range(len(xs))])        # columns: a, b, c
    def sm(v, s=0.008):
        k = np.arange(-int(3 * s / 0.004), int(3 * s / 0.004) + 1) * 0.004
        ww = np.exp(-0.5 * (k / s) ** 2); ww /= ww.sum(); pad = len(k) // 2
        return np.convolve(np.pad(v, pad, mode='edge'), ww, mode='valid')
    co = np.stack([sm(co[:, 0]), sm(co[:, 1]), sm(co[:, 2])], 1)
    return xs, co, z0


def rfun(z, P, ds=0.0):
    """thigh recess profile R(z): 0 at rz0 -> R0 at rz1, flat to rz2, -> 0 at rz3.  `ds` (m, array or scalar) shifts the DESCENDING part up (lateral columns: the fold starts higher)"""
    up = sstep5((z - P['rz0']) / (P['rz1'] - P['rz0']))
    dn = 1.0 - sstep5((z - ds - P['rz2']) / (P['rz3'] - P['rz2']))
    return P['R0'] * up * dn


def region_geodesic(src, reg_all):
    """graph geodesic distance (m) from the vertex set `src` through edges with both ends in `reg_all`"""
    m = reg_all[EA] & reg_all[EB]
    ea, eb = EA[m], EB[m]
    el = np.linalg.norm(CO0[ea] - CO0[eb], axis=1)
    d = np.where(src, 0.0, 9.0)
    for _ in range(400):
        nd = d.copy()
        np.minimum.at(nd, eb, d[ea] + el)
        np.minimum.at(nd, ea, d[eb] + el)
        if np.allclose(nd, d):
            break
        d = nd
    return d


def build_pelvis(co4, P=None, ext=None, ring=None, return_parts=False):
    P = {**PD, **(P or {})}
    if ext is None:
        ext, ring = flood_ext(P['zf'])
    co = co4.copy()
    reg = (T | ext) & ~ring                      # movable vertices; the floor ring (and the old arm / neck borders, far above) stay bit-identical
    # ---- smooth base: the extension verts and the old leg-top border ring (previously pinned to the raw original) take the DENOISED original (Taubin) with a
    #      geodesic ramp from the floor ring, exactly like torso4.build3 does inside the zone (Bw); old zone interior keeps FORM4's positions
    oldint = T & ~BORDER
    dfl = region_geodesic(ring, (T | ext))
    Bw5 = sstep(dfl / P.get('bw_r', 0.05)) * sstep5((np.abs(CO0[:, 0]) - 0.012) / 0.02)      # denoise ramp from the floor ring; the thigh-gap walls keep their original positions
    base = co4.copy()
    sel = (ext | (T & BORDER & (ZV < 0.83))) & reg
    if P.get('dn_z0') is not None:
        # keep the ORIGINAL vertex detail (lattice jitter that the authored custom normals were baked against) on the thigh below dn_z0; denoise only the fold band above (stripe-test straightness of the thigh)
        Bw5 = Bw5 * sstep((CO0[:, 2] - P['dn_z0']) / P.get('dn_w', 0.04))
    base[sel] = CO0[sel] + Bw5[sel, None] * (PS[sel] - CO0[sel])
    x = base[:, 0]; z = base[:, 2]; ax = np.abs(x)
    yo = PS[:, 1].copy(); yb = base[:, 1]        # denoised original y, current base y
    if P.get('dn_z0') is not None:
        yo = CO0[:, 1] + sstep((CO0[:, 2] - P['dn_z0']) / P.get('dn_w', 0.04)) * (PS[:, 1] - CO0[:, 1])      # raw original y on the thigh, denoised in the fold band
    wb = sstep((yo - P['wy0']) / (P['wy1'] - P['wy0']))                              # back half only
    wc = sstep5((ax - P['wx0']) / (P['wx1'] - P['wx0']))                              # keep the gap / cleft
    # ---- thigh surface = denoised original y, depth-proportionally recessed (no x window -> no vertical bands); gap/cleft protected above z .76
    zg = np.arange(0.60, 0.90, 0.004)
    ypk = np.array([PS[(np.abs(PS[:, 2] - zz) < 0.006) & (np.abs(PS[:, 0]) < 0.19), 1].max() for zz in zg])
    ypk_v = np.interp(z, zg, gauss1d(ypk, 0.012, step=0.004))
    if P.get('thigh_smooth', 1):
        txs, tco, tz0 = thigh_model(P)
        ca = np.interp(ax, txs, tco[:, 0]); cb = np.interp(ax, txs, tco[:, 1]); cc = np.interp(ax, txs, tco[:, 2])
        zc_ = np.clip(z, 0.62, 0.86) - tz0
        yo_s = ca + cb * zc_ + cc * zc_ ** 2
        wm_ = 1.0 - sstep((ax - P['tm_x0']) / (P['tm_x1'] - P['tm_x0'])) if P.get('tm_x1', 0.0) > 0 else 1.0     # the smooth thigh model is only trusted on the thigh back (|x| < tm_x0); it is fitted per column and poor on the sparse lateral flank
        yo = yo + sstep((z - P.get('ts0', 0.74)) / P.get('tsw', 0.04)) * wm_ * (yo_s - yo)         # raw denoised original below .74, smooth extrapolated thigh above (clean fold intersection)
    dsh = P['dshift'] * sstep((ax - P['ds_x0']) / (P['ds_x1'] - P['ds_x0'])) if P['dshift'] != 0.0 else 0.0
    wr = 1.0 - sstep((ax - P['rl0']) / (P['rl1'] - P['rl0'])) if P.get('rl1', 0.0) > 0 else 1.0            # lateral fade of the thigh recess (hip flank keeps its own surface: no fold there)
    wmed = sstep((ax - P['rm0']) / (P['rm1'] - P['rm0'])) if P.get('rm1', 0.0) > 0 else 1.0       # medial fade of the recess (leg-gap edges keep their own shape)
    YT = yo - rfun(z, P, dsh) * np.clip(yo / ypk_v, 0.0, 1.0) ** P['rpow'] * wr * wmed   # rpow 1: depth-proportional; rpow 0: uniform in x (keeps the thigh's n_x pattern = straight stripes)
    # ---- lobe underside extension anchored to FORM4's own smooth lobe surface at za0 (value + slope), curvature K below (C1 with FORM4, no apex fit / blend dents)
    za0 = P.get('zanc', 0.845)
    tab = lobe_ext_table(co4, P)
    lift = P['fold_lift'] * sstep((ax - P['fold_x0']) / (P['fold_x1'] - P['fold_x0'])) if P['fold_lift'] != 0.0 else 0.0
    y_ext = ext_eval(tab, ax, np.minimum(z - lift, za0))                       # raising the fold laterally = evaluating the extension lower down (shifted up)
    ku = P['ku'] + P.get('ku_lat', 0.0) * sstep((ax - 0.09) / 0.04)
    YUm = smax(YT, y_ext, np.maximum(ku, 1e-4))                                # lobe mode: smooth union of the recessed thigh and the anchored lobe underside
    u = sstep((z - dsh - P.get('um0', 0.80)) / P.get('umw', 0.02))              # 0: thigh mode (recess only), 1: lobe mode (union, centre-line protected)
    wz = 1.0 - sstep((z - P['zw0']) / (P['zw1'] - P['zw0']))
    w = wb * wz
    q = sstep((z - (za0 - P.get('qa', 0.015))) / P.get('qw', 0.02))              # hand over to FORM4's own surface around the anchor height
    wlat = 1.0 - sstep5((ax - P.get('wl0', 0.118)) / P.get('wlw', 0.04))        # lobe-mode (union) does not reach the lateral hip flank
    ynew = yb + w * ((1.0 - u) * (YT - yb) + u * wc * wlat * (1.0 - q) * (YUm - yb))
    YU = np.where(u > 0.5, YUm, YT); YD = y_ext
    if P.get('ramp', 0):
        sx = sstep((ax - P['rx0']) / (P['rx1'] - P['rx0']))
        zf_x = P['rzf'] + P['rzf_x'] * sx + dsh                       # ramp start (smile: lowest at the centre, higher laterally)
        if P.get('cdz', 0.0):
            zf_x = zf_x - P['cdz'] * (1.0 - sstep((ax - P.get('c_x0', 0.03)) / (P.get('c_x1', 0.07) - P.get('c_x0', 0.03))))      # centre dip: the fold hugs the leg-gap top (plate: dark fold line lowest next to the gap)
        za_x = P['rza'] + P['rza_x'] * sx                              # ramp end (lobe plateau height)
        t = np.clip((z - zf_x) / np.maximum(za_x - zf_x, 1e-3), 0.0, 1.0)
        if P['rsig'] == 'beta':                                        # Beta-CDF ramp: R' ~ t^a (1-t)^c  (peak slope at t* = a/(a+c); a>=2 -> C2 start)
            tg = np.linspace(0.0, 1.0, 2001); bb = tg ** P['ra'] * (1.0 - tg) ** P['rc']; cc = np.cumsum(bb); cc = (cc - cc[0]) / (cc[-1] - cc[0])
            Rr = np.interp(t, tg, cc)
        else:
            Rr = sstep(t) if P['rsig'] == 3 else sstep5(t)
        y_lin = ext_eval(tab, ax, np.minimum(z, P.get('zanc', 0.845)))                 # FORM4 lobe tangent-line continuation (rkap = 0)
        if P.get('cdip', 0.0):
            # central lower-lobe relief: pull the lobe underside back by up to cdip (m) near the cleft (|x| < cd_x0 full -> 0 at cd_x1), inside z cd_z0..cd_z1 - lightens the dark blob above the leg gap (no silhouette column is touched)
            wcx = 1.0 - sstep((ax - P['cd_x0']) / (P['cd_x1'] - P['cd_x0']))
            wcz = sstep((z - P['cd_z0']) / P.get('cd_zw', 0.02)) * (1.0 - sstep((z - P['cd_z1']) / P.get('cd_zw', 0.02)))
            y_lin = y_lin - P['cdip'] * wcx * wcz
        q2 = sstep((z - za_x) / P['rq2w'])
        ynew = yb + w * ((1.0 - Rr) * (YT - yb) + Rr * wc * wlat * (1.0 - q2) * (y_lin - yb))
        YU = YT + Rr * (y_lin - YT)
        if P.get('gdep', 0.0):
            # thin curved fold crease (the plate's dark fold line is a narrow crease that a no-AO matcap cannot show): a shallow gaussian groove in y following the smile z_c(x)
            zc_ = P['gz0'] + P['gz_rise'] * sstep((ax - P['gx0']) / (P['gx1'] - P['gx0']))
            wxg = sstep((ax - 0.012) / 0.02) * (1.0 - sstep((ax - P.get('gxo0', 0.125)) / 0.035))
            ynew = ynew - w * wxg * P['gdep'] * np.exp(-(((z - zc_) / P['gw']) ** 2))
    out = base.copy()
    out[:, 1] = ynew
    # ---- light fairing of y in the fold band (graph diffusion, weighted window): removes the last vertex-scale noise inherited from FORM4's partially denoised rows
    kf = int(P.get('fair_k', 0))
    if kf > 0:
        wf = sstep((z - P.get('fz0', 0.765)) / P.get('fz_w0', 0.02)) * (1.0 - sstep((z - P.get('fz1', 0.875)) / P.get('fz_w1', 0.02))) * np.where(reg, 1.0, 0.0)
        yy = out[:, 1].copy()
        m_e = reg[EA] & reg[EB]
        ea, eb = EA[m_e], EB[m_e]
        deg = np.bincount(np.r_[ea, eb], minlength=N).astype(float)
        for _ in range(kf):
            for lam in (P.get('fair_l', 0.5), P.get('fair_mu', -0.53)):          # Taubin pair: removes vertex-scale noise without shrinking the convex lobe flank
                sm = np.zeros(N); np.add.at(sm, ea, yy[eb]); np.add.at(sm, eb, yy[ea])
                nb = np.where(deg > 0, sm / np.maximum(deg, 1), yy)
                yy = yy + lam * wf * (nb - yy)
        out[:, 1] = yy
    co = np.where(reg[:, None], out, co4)
    if return_parts:
        return co, dict(YT=YT, YD=YD, YU=YU, wb=wb, wc=wc, Y0=Y0, za=za, ext=ext, ring=ring, reg=reg, Bw5=Bw5, base=base)
    return co


if __name__ == '__main__':
    co4 = np.load('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/data/co_FORM4_final.npy').astype(np.float64)
    co, parts = build_pelvis(co4, return_parts=True)
    d = np.linalg.norm(co - co4, axis=1)
    print('moved verts', int((d > 1e-9).sum()), ' max move mm', round(1000 * d.max(), 2), ' ext verts', int(parts['ext'].sum()), ' ring', int(parts['ring'].sum()))
    np.save('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/data/co5p_test.npy', co)
