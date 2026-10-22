"""Edit e2v: ear rebuilt from scratch on a clean skull base.
  x_skull(y,z): thin-plate RBF through the head-side vertices in a collar outside the ear (the ear-free skull surface)
  H(y,z) = Hc(phi) * rim(d)  +  relief (antihelix, concha, tragus, antitragus, lobe)   (mm, +x outward)
  rim(d): rolled helix = quarter-ellipse wall to a crest at d_c (the carved helix loop), then a soft fall to the scapha level
Vertices keep their (y,z) -> carved loops (attach / helix / concha) stay on their curves; topology untouched."""
import sys; sys.path.insert(0, '.')
from edlib import *
import sculpt as S

mm = 1e-3
XC_KNOTS = [(-125, 88.5), (-100, 89.5), (-75, 91.5), (-50, 94.0), (-25, 96.5), (0, 98.0), (25, 98.8), (50, 98.0), (70, 96.5), (85, 94.8), (100, 93.0), (115, 91.0)]
HC_FRONT = [(135, 11.0), (160, 8.5), (180, 7.0), (205, 6.5), (235, 8.0)]       # relative standoff on the front side (angle deg, mm)
PRM_V = dict(
    knots_deg=[0, 40, 90, 130, 170, 215, 255, 300, 340],
    knots_H=[22.0, 21.0, 18.5, 13.5, 8.5, 8.0, 10.5, 16.5, 20.5],
    d_c=3.4, hold=1.4, foot=2.6, scapha=0.74, ds=3.6, anti=3.4, concha=5.6, tragus=4.2, antitragus=3.2, lobe=1.6,
    skirt=1.2, skirt_w=9.0, fit=(21.0, 31.0), blend=(20.0, 9.0), smooth_iters=2)


def outline_geometry():
    poly = S.ear_poly()                                   # (y,z), m
    c = poly.mean(axis=0)
    return poly, c


def ellipse_angle(y, z, c, ey=0.018, ez=0.028):
    return np.arctan2((z - c[1]) / ez, (y - c[0]) / ey)


def periodic_fit(deg, vals, order=3):
    t = np.radians(np.asarray(deg, float)); v = np.asarray(vals, float)
    A = [np.ones_like(t)]
    for k in range(1, order + 1): A += [np.cos(k * t), np.sin(k * t)]
    A = np.stack(A, axis=1); coef = np.linalg.lstsq(A, v, rcond=None)[0]
    def f(phi):
        B = [np.ones_like(phi)]
        for k in range(1, order + 1): B += [np.cos(k * phi), np.sin(k * phi)]
        return np.stack(B, axis=-1) @ coef
    return f


def tps_fit(P, vals, lam=1e-6):
    """polyharmonic r^3 RBF with a linear polynomial: returns f(Q)"""
    n = len(P)
    D = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
    K_ = D ** 3 + lam * np.eye(n)
    Pm = np.hstack([np.ones((n, 1)), P])
    A = np.zeros((n + 3, n + 3)); A[:n, :n] = K_; A[:n, n:] = Pm; A[n:, :n] = Pm.T
    rhs = np.concatenate([vals, np.zeros(3)])
    sol = np.linalg.solve(A, rhs); w = sol[:n]; a = sol[n:]
    def f(Q):
        Dq = np.linalg.norm(Q[:, None, :] - P[None, :, :], axis=2)
        return (Dq ** 3) @ w + a[0] + Q @ a[1:]
    return f


def helix_profile(d, Hc, p):
    """rim(d)*Hc (mm); d in m, >0 inside.  wall starts `foot` mm OUTSIDE the outline, crest at d_c"""
    dm = d * 1000.0
    w0 = -p['foot']; w1 = p['d_c']
    t = np.clip((dm - w0) / (w1 - w0), 0.0, 1.0)
    qe = np.sqrt(np.maximum(1.0 - (1.0 - t) ** 2, 0.0))                   # quarter ellipse (vertical foot, flat crest)
    foot_blend = sstep(0.0, 0.42, t) ** 0.7                              # soften the vertical foot into a fillet
    wall = qe * foot_blend
    fall = p['scapha'] + (1.0 - p['scapha']) * np.exp(-(np.maximum(dm - w1 - p['hold'], 0.0) / p['ds']) ** 1.6)
    return Hc * wall * fall


def ear_relief(yy, zz, p, Hc):
    dA = np.minimum(S.polyline_dist(yy, zz, S.EAR_ANTI), np.minimum(S.polyline_dist(yy, zz, S.EAR_ANTI_UP1), S.polyline_dist(yy, zz, S.EAR_ANTI_UP2)))
    poly = S.ear_poly(); d_in = -S.poly_dist(yy, zz, poly)
    ins = sstep(5.5 * mm, 11.0 * mm, d_in)
    anti = p['anti'] * np.exp(-(dA / (3.4 * mm)) ** 2) * ins * (Hc / 14.0)
    cy, cz = S._yz(647.5, 189.5)
    r2 = ((yy - cy) / (9.6 * mm)) ** 2 + ((zz - cz) / (13.0 * mm)) ** 2
    concha = -p['concha'] * np.maximum(1 - r2, 0.0) ** 1.0
    ty, tz = S._yz(640.2, 184.5); tragus = p['tragus'] * np.exp(-(((yy - ty) / (3.4 * mm)) ** 2 + ((zz - tz) / (3.8 * mm)) ** 2))
    ay_, az_ = S._yz(642.5, 197.5); antit = p['antitragus'] * np.exp(-(((yy - ay_) / (3.4 * mm)) ** 2 + ((zz - az_) / (3.2 * mm)) ** 2))
    ly, lz = S._yz(646.0, 205.5); lobe = p['lobe'] * np.exp(-(((yy - ly) / (7.0 * mm)) ** 2 + ((zz - lz) / (6.5 * mm)) ** 2))
    return anti + concha + tragus + antit + lobe


def e2v_ear(V, M, loops=None, prm=None, return_parts=False, xc_knots=None):
    p = dict(PRM_V); p.update(prm or {})
    V = V.copy(); sgn = np.where(V[:, 0] < 0, -1.0, 1.0)
    poly, c = outline_geometry()
    y, z = V[:, 1], V[:, 2]; ax = np.abs(V[:, 0])
    d = -S.poly_dist(y, z, poly)                                           # >0 inside the outline (m)
    region = (ax > 0.058) & (y > -0.075) & (y < 0.050) & (z > 1.49) & (z < 1.635)
    fit_ring = region & (d < -p['fit'][0] * mm) & (d > -p['fit'][1] * mm)
    core = region & (d >= -p['blend'][0] * mm)
    xc = XC_KNOTS if xc_knots is None else xc_knots
    out_parts = {}
    Hc_v = np.zeros(len(V))
    for side in (-1.0, 1.0):
        sm = (sgn == side)
        ci = np.where(fit_ring & sm)[0]
        if len(ci) > 700: ci = ci[np.linspace(0, len(ci) - 1, 700).astype(int)]
        skull = tps_fit(np.column_stack([y[ci], z[ci]]), ax[ci])
        ki = np.where(core & sm)[0]
        xs = skull(np.column_stack([y[ki], z[ki]]))
        # crest standoff from the ABSOLUTE crest target: Hc(phi) = Xc(phi) - x_skull at the helix loop (+ relative front knots), periodic Fourier fit
        hl = np.array(loops['LOOP_helix_R' if side > 0 else 'LOOP_helix_L'])
        ph_l = np.degrees(ellipse_angle(y[hl], z[hl], c)); xs_l = skull(np.column_stack([y[hl], z[hl]]))
        kd = np.array([k for k, _ in xc], float); kx = np.array([v for _, v in xc], float)
        xc_l = np.interp(ph_l, kd, kx, left=kx[0], right=kx[-1]) * mm
        hc_l = (xc_l - xs_l) * 1000.0
        deg = np.concatenate([ph_l, [k for k, _ in HC_FRONT]]); val = np.concatenate([hc_l, [v for _, v in HC_FRONT]])
        wts = np.concatenate([np.ones(len(ph_l)), 6.0 * np.ones(len(HC_FRONT))])
        tt = np.radians(deg); A = [np.ones_like(tt)]
        for k in range(1, 6): A += [np.cos(k * tt), np.sin(k * tt)]
        A = np.stack(A, axis=1); coef = np.linalg.lstsq(A * wts[:, None], val * wts, rcond=None)[0]
        phi_all = ellipse_angle(y[ki], z[ki], c)
        B = [np.ones_like(phi_all)]
        for k in range(1, 6): B += [np.cos(k * phi_all), np.sin(k * phi_all)]
        Hc_v[ki] = np.stack(B, axis=1) @ coef
        H = helix_profile(d[ki], Hc_v[ki], p) + ear_relief(y[ki], z[ki], p, Hc_v[ki])
        # skirt: gentle rise around the base (outside the outline), none at the top
        top_fade = 1.0 - sstep(1.566, 1.588, z[ki])
        sk = p['skirt'] * np.exp(-(np.maximum(-d[ki], 0.0) / (p['skirt_w'] * mm)) ** 1.5) * (d[ki] < 0) * top_fade
        # blend at the core edge so the field decays to the unchanged vertices at d = -collar[0]
        edge = sstep(-p['blend'][0] * mm, -p['blend'][1] * mm, d[ki])
        xnew = xs + (H + sk) * mm
        V[ki, 0] = side * (ax[ki] * (1 - edge) + xnew * edge)
        out_parts[side] = (ki, xs, H)
    # light fairing of the rebuilt ear (rim stays: loops are not special-cased, weights moderate)
    w = np.where(core & (d > -2 * mm), 0.55, np.where(core, 0.35 * sstep(-p['blend'][0] * mm, -p['blend'][1] * mm, d), 0.0)).astype(float)
    V = M.taubin(V, w, iters=p['smooth_iters'])
    return (V, out_parts) if return_parts else V


if __name__ == '__main__':
    tag_in, tag_out = sys.argv[1], sys.argv[2]
    V0, F, loops = load(tag_in); M = Mesh(V0, F)
    V1 = e2v_ear(V0, M, loops=loops)
    d = np.linalg.norm(V1 - V0, axis=1); print('moved', int((d > 1e-9).sum()), 'max mm %.2f' % (d.max() * 1000))
    np.save(f'data/V_{tag_out}.npy', V1)
