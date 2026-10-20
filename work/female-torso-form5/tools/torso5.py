"""FEMALE TORSO FORM5 core (numpy only; builds on torso4.py).

FORM4's chest = two closed bell domes -> read as circles / targets (closed rim shadow all the way round).
FORM5 bust language (from the plate, see notes in FEMALE_TORSO_FORM5_RESULTS.md):
  * only the LOWER half of each mound is delineated (a smile-shaped under-bust crescent); the upper half merges into the tilted upper-chest plane
  * the mound is a tilted, strongly asymmetric teardrop: short steep-ish lower flank, long gentle upper/lateral tail (side fill, no closed rim)
  * the two mounds meet at a soft sternal valley made by a medial wall window (the mound grows from zero at the centre line), not by tail overlap
  * an open under-bust crease arc (not a ring): groove along the lower arc only, fading out at both ends
Everything is a positions-only height field added through torso4.build3 (its ring remap / wall tables / geodesic weights / border pinning are reused).
"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
import numpy as np
import torso4 as t4
from torso4 import *          # PS, CO0, T, BORDER, ZG, sstep, sstep5, bell, asym, gauss1d, ...
from torso4 import asym, ssign

B5_DEFAULT = dict(
    xc=0.072, zc=1.222,                    # mound centre (|x| mirrored)
    sxm=0.040, sxl=0.052, szd=0.030, szu=0.075,   # sigma-like radii: medial, lateral, down, up
    q=2.0,                                 # profile exponent  exp(-(r/R)^q)
    rot=0.0,                               # footprint rotation (rad); + : lateral end swings DOWN
    H=0.020,                               # peak growth (m)
    xw=0.035,                              # medial wall window: growth ramps 0 -> 1 over |x| in [x0, x0+xw]
    x0=0.0,
    # open under-bust crease (groove): circle arc centre (cxx, czz) radius Rc, lower sector only
    gv=0.0, gw=0.012, cxx=0.075, czz=1.245, Rc=0.067, a0=-165.0, a1=-15.0, aw=18.0,
    # sternal valley groove (vertical, soft): depth sv, half-width ssx, z window
    sv=0.0, ssx=0.016, sz0=1.17, sz1=1.27, szw=0.03,
    # pec swell (upper chest fill that makes the mounds' upper halves merge into the chest plane)
    pH=0.0, pxc=0.065, pzc=1.275, psx=0.075, psz=0.045,
    # lower-mass bias: an extra smaller bump below the centre (fuller lower pole)
    lH=0.0, lxc=0.075, lzc=1.205, lsx=0.040, lsz=0.022,
)


def _rot(u, v, rot):
    if not rot:
        return u, v
    c_, s_ = np.cos(rot), np.sin(rot)
    return c_ * u + s_ * v, -s_ * u + c_ * v


def mound5(x, z, B):
    """forward growth (m) of the signed (|x|-mirrored, summed) FORM5 mounds + pec swell + under-bust crease + sternal valley"""
    tot = 0.0
    for sg in (1.0, -1.0):
        xs = sg * x                               # >0 on this mound's side
        u = xs - B['xc']
        v = z - B['zc']
        u, v = _rot(u, v, B.get('rot', 0.0))
        rx = asym(u, B['sxm'], B['sxl'], 0.012)
        rz = asym(v, B['szd'], B['szu'], 0.010)
        s = np.sqrt((u / rx) ** 2 + (v / rz) ** 2 + 1e-12)
        prof = np.exp(-np.power(s, B['q']))
        wm = sstep5((xs - B['x0']) / B['xw'])    # medial wall: zero at the centre line -> sternal valley, no tail overlap
        m = B['H'] * prof * wm
        if B.get('lH', 0.0):
            u2, v2 = xs - B['lxc'], z - B['lzc']
            m = m + B['lH'] * np.exp(-((u2 / B['lsx']) ** 2 + (v2 / B['lsz']) ** 2)) * wm
        if B.get('pH', 0.0):
            u3, v3 = xs - B['pxc'], z - B['pzc']
            m = m + B['pH'] * np.exp(-((u3 / B['psx']) ** 2 + (v3 / B['psz']) ** 2)) * wm
        if B.get('gv', 0.0):
            # open under-bust crease along the lower sector of a circle
            dx, dz = xs - B['cxx'], z - B['czz']
            r = np.sqrt(dx * dx + dz * dz + 1e-12)
            ang = np.degrees(np.arctan2(dz, dx))
            wa = sstep((ang - B['a0']) / B['aw']) * (1 - sstep((ang - B['a1']) / B['aw']))
            d = r - B['Rc']
            # groove just OUTSIDE the mound edge (below the arc), narrow gaussian
            m = m - B['gv'] * np.exp(-((d - 0.0) / B['gw']) ** 2) * wa * wm
        tot = tot + m
    if B.get('svb', 0.0):
        # sternal valley as a z-BUMP (peak svb at svc, gaussian width svw): the centre column recedes then comes forward again going up -> its upper-chest slope is GENTLER than the pec columns'
        sb = B['svb'] * np.exp(-((z - B.get('svc', 1.235)) / B.get('svw', 0.04)) ** 2)
        tot = tot - sb * np.exp(-(x / B.get('svx', 0.03)) ** 2)
    if B.get('sv', 0.0) or B.get('sv1', 0.0):
        hz = sstep5((z - B['sz0']) / B['szw']) * (1 - sstep5((z - B['sz1']) / B.get('szw1', B['szw'])))
        sdep = B.get('sv', 0.0) + (B.get('sv1', 0.0) - B.get('sv', 0.0)) * sstep((z - B.get('svz0', 1.22)) / B.get('svzw', 0.05))     # deeper (pec valley) above the cleavage
        wsx = B['ssx'] + (B.get('ssx1', B['ssx']) - B['ssx']) * sstep((z - B.get('svz0', 1.22)) / B.get('svzw', 0.05))
        tot = tot - sdep * np.exp(-(x / wsx) ** 2) * hz
    return tot


def softplus_w(t, w):
    return w * np.logaddexp(0.0, t / w)


def mound_arc(x, z, B):
    """FORM5 arc-foot mound (|x| mirrored, signed): lower contour = shallow smile arc (the under-bust crescent) lowest at xarc / zlow,
    flank rises with a soft concave foot to a crest Ll above the foot, long soft decline above (merges into the tilted chest plane);
    lateral weight is a (medial, lateral)-asymmetric generalised gaussian about xcr; medial wall window kills the part beyond the centre line."""
    tot = 0.0
    for sg in (1.0, -1.0):
        xs = sg * x
        d = xs - B['xarc']
        Ra = np.where(d > 0, B.get('Rarc_l', B['Rarc']), B['Rarc'])          # lateral side may curl up faster (smaller radius): hammock
        dd = np.clip(d, -0.85 * Ra, 0.85 * Ra)
        sag = Ra - np.sqrt(Ra * Ra - dd * dd) + (np.abs(d) - np.abs(dd)) * 0.9 * np.sign(d) * np.sign(d)   # beyond 0.85 Ra continue linearly (no blow-up)
        zf = B['zlow'] + sag
        u = (z - zf) / B['Ll']                       # 0 at the foot, 1 at the crest
        us = softplus_w(u, B.get('fw', 0.12))        # soft concave foot
        a = B.get('a', 1.6)
        low = 1.0 - np.power(np.clip(1.0 - us, 0.0, 1.0), a)
        up = np.exp(-np.power(np.clip(u - 1.0, 0.0, None) * B['Ll'] / B['Lu'], B.get('pu', 2.0)))
        prof = np.where(u < 1.0, low, up)
        dx = xs - B['xcr']
        sx = asym(dx, B['sxm'], B['sxl'], 0.012)
        lam = np.exp(-np.power(np.abs(dx / sx), B.get('qx', 2.0)))
        wm = sstep5((xs - B['x0']) / B['xw'])
        m = B['H'] * prof * lam * wm
        if B.get('tr', 0.0):
            # upper-lateral chest tilts back (the plate's lateral upper chest faces UP more: rounded shoulder-front): recess growing with z above tz0 and with |x| beyond tx0
            m = m - B['tr'] * sstep((z - B.get('tz0', 1.21)) / (B.get('tz1', 1.29) - B.get('tz0', 1.21))) * (1.0 - sstep((z - B.get('tzt', 1.30)) / B.get('tzw', 0.035))) * sstep((xs - B.get('tx0', 0.055)) / (B.get('tx1', 0.095) - B.get('tx0', 0.055)))
        if B.get('lf_A', 0.0):
            # lateral upper-chest fill (side fill): forward growth on the lateral chest flank (|x| lf_x0..lf_x1 full -> lf_x2..lf_x3 fade) inside a z window; sits behind the central silhouette column
            wxl = sstep((xs - B['lf_x0']) / (B['lf_x1'] - B['lf_x0'])) * (1.0 - sstep((xs - B['lf_x2']) / (B['lf_x3'] - B['lf_x2'])))
            wzl = sstep((z - B['lf_z0']) / B.get('lf_zw', 0.025)) * (1.0 - sstep((z - B['lf_z1']) / B.get('lf_zw', 0.025)))
            m = m + B['lf_A'] * wxl * wzl
        if B.get('gv', 0.0):
            # shallow groove just below the foot (adds contact darkness without a slit): gaussian about the arc, lower side only
            dz = (z - zf)
            m = m - B['gv'] * np.exp(-((dz + B.get('gz', 0.012)) / B.get('gw', 0.014)) ** 2) * lam * wm
        tot = tot + m
    if B.get('svb', 0.0):
        # sternal valley as a z-BUMP (peak svb at svc, gaussian width svw): the centre column recedes then comes forward again going up -> its upper-chest slope is GENTLER than the pec columns'
        sb = B['svb'] * np.exp(-((z - B.get('svc', 1.235)) / B.get('svw', 0.04)) ** 2)
        tot = tot - sb * np.exp(-(x / B.get('svx', 0.03)) ** 2)
    if B.get('sv', 0.0) or B.get('sv1', 0.0):
        hz = sstep5((z - B['sz0']) / B['szw']) * (1 - sstep5((z - B['sz1']) / B.get('szw1', B['szw'])))
        sdep = B.get('sv', 0.0) + (B.get('sv1', 0.0) - B.get('sv', 0.0)) * sstep((z - B.get('svz0', 1.22)) / B.get('svzw', 0.05))     # deeper (pec valley) above the cleavage
        wsx = B['ssx'] + (B.get('ssx1', B['ssx']) - B['ssx']) * sstep((z - B.get('svz0', 1.22)) / B.get('svzw', 0.05))
        tot = tot - sdep * np.exp(-(x / wsx) ** 2) * hz
    return tot


def bust_amp5(x, z, P):
    B = {**B5_DEFAULT, **P.get('b5', {})}
    if B.get('mode') == 'arc':
        return mound_arc(x, z, B)
    return mound5(x, z, B)


# override the FORM4 dome amplitude (build3 resolves bust_amp from torso4's globals at call time)
t4.bust_amp = bust_amp5


# ------------------------------------------------------------------------------------------------ soft wall corner (FORM5)
_wall3_orig = t4.wall3


def wall3_5(P, dFw=None, dBb=None):
    """FORM4 wall3 with an optional SOFT CORNER for the front wall: P['wc_s'] > 0 replaces the max(table, wl_y) corner (vertical wall -> tilted chest plane,
    slope jump 0 -> .8 within ~4 mm) by the integral of a smoothstep5 slope ramp: slope = wc_s * sstep5((z - wc_z0)/(wc_z1 - wc_z0)), starting on the vertical wall level wl_y
    at wc_z0 and valid up to wc_zend; above wc_zend the original wall (plate table / ramp) is blended back over wc_zb.  Radius of the corner ~ (wc_z1-wc_z0)/atan(wc_s)."""
    if not P.get('wc_s', 0.0):
        return _wall3_orig(P, dFw, dBb)
    P2 = dict(P)
    P2['wl_y'] = None                                        # corner handled here
    Fw0, Bb0 = _wall3_orig(P2, None, None)                   # table (+ramp) wall without wl_y clamp, without corrections
    z = ZG
    z0, z1, sm = P['wc_z0'], P['wc_z1'], P['wc_s']
    y0 = P['wl_y']
    dz = 0.002
    sl = np.where(z >= z0, sm * sstep5((z - z0) / (z1 - z0)), 0.0)
    corner = y0 + np.concatenate([[0.0], np.cumsum(0.5 * (sl[1:] + sl[:-1]) * dz)])      # = y0 up to z0, then recedes with the smooth slope ramp
    zend, zb = P.get('wc_zend', 1.30), P.get('wc_zb', 0.02)
    zj = P.get('wc_zj', 1.17)
    jn = sstep((z - zj) / 0.02)                                                          # table (vertical wall) below zj -> corner curve above zj+.02
    wback = sstep((z - zend) / zb)                                                       # corner curve -> table/ramp wall above zend
    Fw = Fw0 + jn * (1 - wback) * (corner - Fw0)
    if dFw is not None:
        Fw = Fw + dFw
    Bb = Bb0
    if dBb is not None:
        Bb = Bb + dBb
    return Fw, Bb


t4.wall3 = wall3_5


def fit_front5(P, iters=5, zr=(1.12, 1.31), damp=0.9, sm=0.006):
    """FORM5 wall fit: back wall + front wall below 1.12 as in FORM4, then the FRONT wall in the bust band / upper chest is iterated so that the
    front envelope (min y over the zone per z) tracks the sub-pixel plate contour (t4.front_table) over zr; correction tapers to 0 above zr[1]+.02."""
    dF, dB = t4.fit_walls(P, iters=4, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
    tgt = np.array([t4.front_table(zz, P) for zz in ZG])
    w = sstep((ZG - zr[0]) / 0.02) * (1 - sstep((ZG - zr[1]) / 0.02))
    for it in range(iters):
        co = t4.build3(P, dF, dB)
        fe, be = section_extents(co)
        fe = fillnan(fe)
        dF = dF + damp * gauss1d((tgt - fe) * w, sm)
    fc = P.get('fit_conc')
    if fc:
        # second stage: the upper-chest envelope is turned into a CONCAVE profile (monotone slope, no stall-then-steepen groove) and the wall is iterated to it
        zc0, zc1 = fc['z0'], fc['z1']
        co = t4.build3(P, dF, dB)
        fe, be = section_extents(co); fe = fillnan(fe)
        tgt2 = fe + concave_project(ZG, fe, zc0, zc1, fc.get('smooth', 0.008))
        w2 = sstep((ZG - (zc0 - 0.012)) / 0.012) * (1.0 - sstep((ZG - zc1) / 0.012))
        for it in range(int(fc.get('iters', 4))):
            co = t4.build3(P, dF, dB)
            fe, be = section_extents(co); fe = fillnan(fe)
            dF = dF + damp * gauss1d((tgt2 - fe) * w2, sm)
    return dF, dB



def pav_dec(s):
    """L2 isotonic regression: closest NON-INCREASING sequence (pool adjacent violators); preserves the sum"""
    a = -np.asarray(s, float)
    blocks = []
    for v in a:
        blocks.append([v, 1])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
            s2, c2 = blocks.pop(); blocks[-1][0] += s2; blocks[-1][1] += c2
    out = []
    for sm_, c_ in blocks:
        out += [sm_ / c_] * c_
    return -np.array(out)


def concave_project(zg, y, z0, z1, smooth=0.008):
    """front wall/envelope profile y(z) (y increases with z = recedes): replace it on [z0, z1] by the closest profile with NON-INCREASING slope (no stall-then-steepen groove),
    endpoints fixed (isotonic regression of the slope preserves the total rise); the correction is smoothed (gaussian, sigma=smooth) and tapered to 0 at both ends"""
    dz = zg[1] - zg[0]
    i0, i1 = int(round((z0 - zg[0]) / dz)), int(round((z1 - zg[0]) / dz))
    sl = np.diff(y[i0:i1 + 1]) / dz
    si = pav_dec(sl)
    yp = y[i0] + np.concatenate([[0.0], np.cumsum(si) * dz])
    d = np.zeros_like(y); d[i0:i1 + 1] = yp - y[i0:i1 + 1]
    if smooth > 0:
        d = gauss1d(d, smooth)
    wt = sstep((zg - z0) / 0.012) * (1.0 - sstep((zg - (z1 - 0.012)) / 0.012))
    return d * wt


_TT_ORIG = t4.TT.copy()


def make_TT(P):
    """flatter plan-view front in the bust band: TT5 = TT * (1 - amp * wx(|x|) * wz(z)) for front vertices.  The original ring (13.5 mm surface-nets remap) falls away laterally
    ~33 mm between x .054 and .09 at z 1.22, so crest + base give a ~2.4 cm radius ridge at |x|~.055 (the clay 'slash').  amp 0 -> original ring."""
    tf = P.get('tt_flat')
    if not tf:
        return _TT_ORIG.copy()
    x = np.abs(PS[:, 0]); z = PS[:, 2]
    wx = sstep5((tf['x1'] - x) / max(tf['x1'] - tf['x0'], 1e-6))
    wz = sstep((z - tf['z0']) / tf.get('zw', 0.03) + 1.0) * (1.0 - sstep((z - tf['z1']) / tf.get('zw', 0.03)))
    f = tf['amp'] * wx * wz * (_TT_ORIG < 0.5)
    return _TT_ORIG * (1.0 - f)


def build_chest(P, iters=4):
    """chest/upper-zone build for one parameter dict.  P['fit_front'] = 1 -> iterate the front wall to the sub-pixel plate contour over the bust band"""
    t4.TT = make_TT(P)
    if P.get('fit_front', 0):
        dF, dB = fit_front5(P, iters=int(P.get('fit_front_iters', 5)), zr=tuple(P.get('fit_front_zr', (1.12, 1.31))))
    else:
        dF, dB = t4.fit_walls(P, iters=iters, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
    co = t4.build3(P, dF, dB)
    cp = P.get('conc_post')
    if cp:
        co = conc_post(co, cp)
    return co, dF, dB


def conc_post(co, cp):
    """post-process: remove the bend/stall of the upper-chest front profile.  mode 'land' (default): from zs the front envelope e(z) is replaced by a SMOOTH profile whose slope eases
    (smoothstep) from the current slope at zs to a final slope m_e, with m_e solved so that it lands exactly on e(ze) (the pinned neck-base ring side) -> one concave sweep, no crease line;
    mode 'iso': closest non-increasing-slope profile (isotonic regression).  The (<= few mm) correction d(z) is applied as a y-offset to all front zone vertices (weight 1 for |x| < xf0 -> 0 at xf1),
    border vertices untouched."""
    co = co.copy()
    fe, be = section_extents(co); fe = fillnan(fe)
    zs, ze = cp.get('zs', cp.get('z0', 1.26)), cp.get('ze', cp.get('z1', 1.355))
    if cp.get('mode', 'land') == 'iso':
        d = cp.get('gain', 1.0) * concave_project(ZG, fe, zs, ze, cp.get('smooth', 0.008))
    else:
        i0, i1 = int(round((zs - ZG[0]) / 0.002)), int(round((ze - ZG[0]) / 0.002))
        y0, y1 = fe[i0], fe[i1]
        m0 = (fe[i0 + 3] - fe[i0 - 3]) / (6 * 0.002)
        zz = ZG[i0:i1 + 1]; pw = cp.get('pw', 1.0)
        def curve(me):
            sl = m0 + (me - m0) * sstep((zz - zs) / (ze - zs)) ** pw
            return y0 + np.concatenate([[0.0], np.cumsum(0.5 * (sl[1:] + sl[:-1]) * 0.002)])
        lo, hi = -1.5, 2.5
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if curve(mid)[-1] < y1: lo = mid
            else: hi = mid
        d = np.zeros_like(fe); d[i0:i1 + 1] = cp.get('gain', 1.0) * (curve(0.5 * (lo + hi)) - fe[i0:i1 + 1])
        d = gauss1d(d, cp.get('smooth', 0.004))
        d = d * sstep((ZG - zs) / 0.006) * (1.0 - sstep((ZG - (ze - 0.006)) / 0.006))
    zv = co[:, 2]; xv = np.abs(co[:, 0])
    dv = np.interp(zv, ZG, d)
    wx = 1.0 - sstep((xv - cp.get('xf0', 0.10)) / (cp.get('xf1', 0.13) - cp.get('xf0', 0.10)))
    sel = T & ~BORDER & (co[:, 1] < 0.0)
    co[sel, 1] += (dv * wx)[sel]
    return co


def apply_ov(P, ov):
    """override keys: 'b5.H': .02 -> P['b5']['H'];  plain keys go to the top level"""
    import copy
    P = copy.deepcopy(P)
    for k, v in ov.items():
        if k.startswith('b5.'):
            P.setdefault('b5', {})[k[3:]] = v
        else:
            P[k] = v
    return P
