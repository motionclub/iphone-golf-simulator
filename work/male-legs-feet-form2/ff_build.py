"""Forefoot builder: body rings (planar slice of the old surface -> lobed ball ring) + five slit-model toe tubes, in the foot-local frame (f forward, l lateral, z up).

Topology (all quads except the weld strip's few triangles and the pole fans):
  loop    : the cut loop (existing vertices, M of them)
  ring 0  : planar slice of the ORIGINAL surface just ahead of the loop; columns = a subset of the loop vertices (aligned), N = 2 + Kd + Kp columns
  rings   : Hermite morph (slope matched at the weld) from ring 0 into the ball ring; lobes (toe grooves) fade in over `span_g`
  ball    : 'lobed ring' [S_lat, dorsal x Kd (lateral->medial), S_med, plantar x Kp (medial->lateral)] -- toe dorsal arcs separated by valley columns
  toes    : T1 (big, medial) .. T5 (little, lateral); each toe ring = [WL, D_1..D_m, WR, P_m'..P_1']; caps close in a pole.
"""
import numpy as np
from ff_common import *

# near-foot (sagittal) contour read from both profile plates (y, z), metres -- same table as metrics_ff.C_NEW
C_PLATE = np.array([(-0.2235, 0.030), (-0.2215, 0.045), (-0.2150, 0.054), (-0.2000, 0.061), (-0.1800, 0.067), (-0.1600, 0.0705), (-0.1400, 0.079),
                    (-0.1200, 0.0905), (-0.1000, 0.099), (-0.0850, 0.110), (-0.0720, 0.124), (-0.0640, 0.140)])


def plate_z(y):
    return np.interp(y, C_PLATE[:, 0], C_PLATE[:, 1])


# ----------------------------------------------------------------------------------------------------------------------------------
DEFAULT = dict(
    # toes, index 0 = T1 (big toe, medial) ... 4 = T5 (little toe, lateral); all lengths in metres
    W=[0.0270, 0.0200, 0.0180, 0.0160, 0.0145],           # full width at the knuckle line
    L=[0.0480, 0.0450, 0.0385, 0.0320, 0.0260],           # knuckle line -> tip
    H0=[0.0500, 0.0420, 0.0380, 0.0345, 0.0310],          # crown height (above the sole plane) at the knuckle line
    m=[8, 7, 6, 5, 4],                                    # dorsal vertices per toe ring
    mp=[4, 4, 3, 3, 2],                                   # plantar vertices per toe ring (the sole is hidden: fewer)
    splay_deg=[-1.5, 0.0, 2.0, 4.0, 6.0],                 # toe axis yaw, + = lateral
    gap=0.0022,                                           # slit width at the knuckle line
    row_shift=0.0,                                        # lateral shift of the toe row centre vs the foot axis
    shaft_rows=[5, 5, 4, 3, 3],
    s_cap=[0.70, 0.70, 0.70, 0.70, 0.68],
    tip_ratio=0.70,                                       # height at the end of the shaft / H0
    tip_wratio=0.86,                                      # width at the end of the shaft / W
    wf=0.42,                                              # widest-point height fraction of the toe
    n_top=2.4, n_bot=3.0, n_bot_outer=2.1, rb=1.0, cap_angles=[24.0, 48.0, 70.0], psi_end=28.0,
    knuckle_bump=0.06, neck=0.035, pad=0.045,
    valley_drop=0.007,                                    # dorsal valley depth below the lower neighbouring shoulder
    # body
    n_body_rows=11, ball_f1=0.0035, ring_pow=1.4, f1_gap=0.006,
    lift=[0.002, 0.0, 0.0, 0.002, 0.006], vp_up=0.0005,
    prof_w0=0.032, prof_w1=0.006, prof_gain=1.0,          # instep height correction toward the plate contour: full weight behind f=-prof_w0, zero at f=-prof_w1
    span_g=0.042,                                         # lobe fade length behind the ball ring (toe crowns)
    span_v=0.020,                                         # valley (groove) depth fade length behind the ball ring
    straighten=0.0, respace=0.5,                          # weld loop: planarise (kappa) and re-space along the contour (beta)
)


def sgnpow(x, p):
    return np.sign(x) * np.abs(x) ** p


class ToeRow:
    """Geometry of the five toes in the local frame."""

    def __init__(self, P):
        self.P = P
        W = np.array(P['W']); g = P['gap']
        tot = W.sum() + 4 * g
        # lateral coordinate l increases toward the lateral side; T1 (big toe) is medial => most negative l
        edge = -tot / 2 + P['row_shift']
        self.lc = np.zeros(5); self.a0 = W / 2
        x = edge
        for t in range(5):
            self.lc[t] = x + W[t] / 2
            x += W[t] + g
        self.m = list(P['m']); self.mp = list(P['mp'])
        self.Kd = sum(self.m) + 4
        self.Kp = sum(self.mp) + 4
        self.N = 2 + self.Kd + self.Kp

    def pt(self, key, t):
        v = self.P[key]
        return v[t] if isinstance(v, (list, tuple, np.ndarray)) else v

    def env(self, t, s):
        P = self.P
        s = np.atleast_1d(np.asarray(s, float))
        sc = P['s_cap'][t]
        u = np.clip(s / sc, 0, 1)
        a = self.a0[t] * (1 - (1 - self.pt('tip_wratio', t)) * u ** 1.3)
        a = a * (1 - self.pt('neck', t) * np.exp(-((u - 0.55) / 0.22) ** 2) + self.pt('pad', t) * np.exp(-((u - 0.95) / 0.16) ** 2))
        h = P['H0'][t] * (1 - (1 - self.pt('tip_ratio', t)) * u)
        h = h * (1 + self.pt('knuckle_bump', t) * np.exp(-((u - 0.10) / 0.12) ** 2))
        return a, h

    def center_l(self, t, f):
        return self.lc[t] + np.tan(np.radians(self.P['splay_deg'][t])) * f

    def ring_size(self, t):
        return self.m[t] + self.mp[t] + 2

    def p_index(self, t, q):
        """index of plantar vertex P_q (q = 1 lateral-most .. mp medial-most) in a toe ring"""
        return self.m[t] + self.mp[t] + 2 - q

    def ring(self, t, f, scale=1.0, s_for_env=None):
        """Ring [WL, D_1..D_m, WR, P_m'..P_1'] of toe t at forward position f, scaled about its centre."""
        P = self.P; m = self.m[t]; mp = self.mp[t]; L = P['L'][t]
        s = (f / L) if s_for_env is None else s_for_env
        a, h = self.env(t, np.array([s])); a = float(a[0]); h = float(h[0])
        lcn = float(self.center_l(t, f))
        zw = Z0 + P['wf'] * h
        hw = P['wf'] * h
        a0_, a1_ = np.radians(P['psi_end']), np.radians(180.0 - P['psi_end'])
        psi = np.linspace(a0_, a1_, m) if m > 1 else np.array([np.pi / 2])
        psp = np.pi * np.arange(1, mp + 1) / (mp + 1)
        e = 2.0 / P['n_top']
        WL = (lcn + a, zw); WR = (lcn - a, zw)
        D = [(lcn + a * sgnpow(np.cos(p), e), zw + (h - hw) * np.abs(np.sin(p)) ** e) for p in psi]
        nb_lat = P['n_bot_outer'] if t == 4 else P['n_bot']          # lateral-lower corner of the little toe rounder
        nb_med = P['n_bot_outer'] if t == 0 else P['n_bot']          # medial-lower corner of the big toe rounder
        Pl = []
        for p in psp:
            eb = 2.0 / (nb_lat if np.cos(p) >= 0 else nb_med)
            Pl.append((lcn + a * P['rb'] * sgnpow(np.cos(p), eb), zw - hw * np.abs(np.sin(p)) ** eb))
        ring = np.array([WL] + D + [WR] + Pl[::-1])      # (m+mp+2, 2)  (l, z)
        lift = float(self.pt('lift', t))
        if lift > 0:                        # whole toe rides up a little (outer toes barely touch the ground): shape-preserving vertical compression
            ring[:, 1] = Z0 + lift + (ring[:, 1] - Z0) * (1.0 - lift / max(h, 1e-6))
        ring[:, 1] = np.maximum(ring[:, 1], Z0)
        zc = Z0 + 0.5 * h
        c = np.array([lcn, zc])
        ring = c + scale * (ring - c)
        return np.column_stack([np.full(len(ring), f), ring[:, 0], ring[:, 1]])

    def toe_rows(self, t):
        """All rings of toe t (shaft rows + cap rows) and the pole."""
        P = self.P; L = P['L'][t]; sc = P['s_cap'][t]
        nsh = P['shaft_rows'][t]
        f1 = P['ball_f1']
        fs = list(f1 + (sc * L - f1) * (np.arange(nsh) / max(nsh - 1, 1)) ** 0.95) if nsh > 1 else [sc * L]
        rows = [self.ring(t, f) for f in fs]
        for c_ in np.radians(P['cap_angles']):
            f = sc * L + (1 - sc) * L * np.sin(c_)
            rows.append(self.ring(t, f, scale=np.cos(c_), s_for_env=sc))
        _, h = self.env(t, np.array([sc])); h = float(h[0])
        pole = np.array([L, self.center_l(t, L), Z0 + 0.5 * h])
        return rows, pole

    # ---- ball ring (lobed ring at f = 0) ----------------------------------------------------------------------------------------------
    def dorsal_layout(self):
        """columns lateral->medial: ('T', t, q) q=1..m  or ('V', g) with g = gap between toe g (medial) and g+1 (lateral)."""
        cols = []
        for t in range(4, -1, -1):
            for q in range(1, self.m[t] + 1):
                cols.append(('T', t, q))
            if t > 0:
                cols.append(('V', t - 1))
        assert len(cols) == self.Kd
        return cols

    def plantar_layout(self):
        """columns medial->lateral: ('T', t, q') q'=mp..1  or ('V', g)."""
        cols = []
        for t in range(5):
            for q in range(self.mp[t], 0, -1):
                cols.append(('T', t, q))
            if t < 4:
                cols.append(('V', t))
        assert len(cols) == self.Kp
        return cols

    def ball_ring(self):
        """positions (N,3) in the order [S_lat, dorsal x Kd, S_med, plantar x Kp] and the two column tables."""
        P = self.P
        colsD = self.dorsal_layout(); colsP = self.plantar_layout()
        rc = {t: self.ring(t, 0.0) for t in range(5)}
        pos_d = []
        for c in colsD:
            if c[0] == 'T':
                _, t, q = c
                pos_d.append(rc[t][q])
            else:
                g = c[1]
                lm = self.lc[g] + self.a0[g]; ll = self.lc[g + 1] - self.a0[g + 1]
                zsh = min(rc[g][1, 2], rc[g + 1][self.m[g + 1], 2])                 # lower of the two shoulders next to the gap (toe g lateral shoulder, toe g+1 medial shoulder)
                zweb = max(rc[g][0, 2], rc[g + 1][self.m[g + 1] + 1, 2])           # side-wall (web) height
                pos_d.append(np.array([0.0, 0.5 * (lm + ll), max(zsh - P['valley_drop'], zweb + 0.002)]))
        pos_p = []
        for c in colsP:
            if c[0] == 'T':
                _, t, q = c
                pos_p.append(rc[t][self.p_index(t, q)])
            else:
                g = c[1]
                lm = self.lc[g] + self.a0[g]; ll = self.lc[g + 1] - self.a0[g + 1]
                za = rc[g][self.p_index(g, 1), 2]                 # toe g (medial): its lateral-most plantar vertex
                zb = rc[g + 1][self.p_index(g + 1, self.mp[g + 1]), 2]   # toe g+1 (lateral): its medial-most plantar vertex
                pos_p.append(np.array([0.0, 0.5 * (lm + ll), max(za, zb) + P['vp_up']]))
        S_lat = rc[4][0].copy(); S_med = rc[0][self.m[0] + 1].copy()
        out = np.vstack([S_lat[None], np.array(pos_d), S_med[None], np.array(pos_p)])
        return out, colsD, colsP


# ==================================================================================================================================
#  loop handling
# ==================================================================================================================================
def poly_len(Pl):
    d = np.linalg.norm(np.diff(Pl, axis=0), axis=1)
    return np.r_[0, np.cumsum(d)]


def aligned_columns(Lloop, Kd, Kp):
    """Choose the N = 2 + Kd + Kp columns of ring 0 as a subset of the loop vertices (so the weld strip is clean quads plus a few triangles).
    Column 0 = lateral equator, column Kd+1 = medial equator (the split is chosen from the loop so both halves keep enough vertices and the
    equators sit near the true lateral / medial extremes).  Twin vertices (same (l,z) position) are always dropped.
    Returns dict(order, P (reordered loop (M,3)), cols (N loop indices, increasing), dropped, i_med)."""
    P = np.asarray(Lloop, float); M = len(P); N = 2 + Kd + Kp
    assert M >= N, f'loop has {M} vertices < ring size {N}'
    l, z = P[:, 1], P[:, 2]
    area = 0.5 * np.sum(l * np.roll(z, -1) - np.roll(l, -1) * z)
    base_order = list(range(M)) if area >= 0 else list(range(M))[::-1]
    Pb = P[base_order]
    lmax, lmin = Pb[:, 1].max(), Pb[:, 1].min()
    projb = np.linalg.norm((np.roll(Pb, -1, axis=0) - Pb)[:, 1:3], axis=1)          # projected edge i -> i+1 (section plane)
    best = None
    for twin_thr in (0.0026, 0.0022, 0.0018, 0.0015, 0.0012, 0.0008, 0.0004):
        forced_b = np.roll(projb, 1) < twin_thr                                        # vertex j is the second of a twin pair (same l,z as j-1)
        for a in range(M):
            rot = np.array([(a + k) % M for k in range(M)])
            fd = forced_b[rot]
            for d in range(Kd + 1, M - Kp):
                nfd = int(fd[1:d].sum()); nfp = int(fd[d + 1:].sum())
                if (d - 1) - nfd < Kd or (M - d - 1) - nfp < Kp or fd[d] or fd[0]:
                    continue
                b = (a + d) % M
                cost = abs(Pb[a, 1] - lmax) + abs(Pb[b, 1] - lmin)
                if best is None or cost < best[0]: best = (cost, a, d)
        if best is not None: break
    assert best is not None, 'no feasible equator split'
    _, a, d = best
    order_idx = [(a + k) % M for k in range(M)]
    order = [base_order[i] for i in order_idx]
    P2 = P[order]
    nd = d - 1; npl = M - d - 1                       # interior vertex counts of the dorsal / plantar halves
    edge = np.linalg.norm((np.roll(P2, -1, axis=0) - P2)[:, 1:3], axis=1)        # projected (l, z) lengths
    forced = [i for i in range(1, M) if edge[i - 1] < twin_thr]
    def pick_drop(lo, hi, k):
        """drop k interior vertices (indices lo..hi inclusive): twins first, then those with the shortest neighbouring edge; never adjacent"""
        out = [i for i in forced if lo <= i <= hi]
        cand = sorted(range(lo, hi + 1), key=lambda i: (min(edge[i - 1], edge[i]), edge[i - 1] + edge[i]))
        for i in cand:
            if len(out) >= k: break
            if i not in out and all(abs(i - j) > 1 for j in out): out.append(i)
        return out
    drop = pick_drop(1, d - 1, nd - Kd) + pick_drop(d + 1, M - 1, npl - Kp)
    cols = [i for i in range(M) if i not in drop]
    assert len(cols) == N, (len(cols), N, nd, npl)
    return dict(order=order, P=P2, cols=cols, dropped=sorted(drop), i_med=d)


def hermite(p0, m0, p1, m1, tau, D):
    t = tau
    h00 = 2 * t ** 3 - 3 * t ** 2 + 1; h10 = t ** 3 - 2 * t ** 2 + t
    h01 = -2 * t ** 3 + 3 * t ** 2;    h11 = t ** 3 - t ** 2
    return h00 * p0 + h10 * D * m0 + h01 * p1 + h11 * D * m1


def smooth_profile(xs, ys, x, sigma):
    """piecewise-linear through (xs, ys) smoothed with a gaussian of width sigma, evaluated at x."""
    g = np.linspace(xs.min() - 0.05, xs.max() + 0.05, 1200)
    base = np.interp(g, xs, ys)
    k = np.exp(-0.5 * ((g[:, None] - g[None, :]) / sigma) ** 2); k /= k.sum(1, keepdims=True)
    return np.interp(x, g, k @ base)


def minang(poly):
    m_ = 180.0
    n_ = len(poly)
    for q in range(n_):
        u = poly[(q - 1) % n_] - poly[q]; v = poly[(q + 1) % n_] - poly[q]
        c = (u @ v) / max(np.linalg.norm(u) * np.linalg.norm(v), 1e-12)
        m_ = min(m_, np.degrees(np.arccos(np.clip(c, -1, 1))))
    return m_


def poly_normal(poly):
    poly = [np.asarray(q) for q in poly]
    return np.cross(poly[2] - poly[0], poly[-1] - poly[1]) if len(poly) == 4 else np.cross(poly[1] - poly[0], poly[2] - poly[0])


# ==================================================================================================================================
#  the builder
# ==================================================================================================================================
class Builder:
    def __init__(self, n_existing):
        self.N0 = n_existing
        self.pos = []
        self.faces = []
        self.tag = []

    def add(self, p, tag=None):
        self.pos.append(np.asarray(p, float)); self.tag.append(tag); return self.N0 + len(self.pos) - 1

    def face(self, *ids):
        self.faces.append(tuple(int(i) for i in ids))


def build_forefoot(P, loop_ids, Lloop, n_existing, slopes=None, verbose=False):
    """P: params, loop_ids: ids of the cut loop vertices (connectivity order), Lloop their local coords (M,3).
    slopes: dict(ring0 (N,3), slopes (N,2)) from ff_slopes.  Returns Builder (new vertex local positions + faces over [existing ids | new ids]) and diagnostics."""
    ring0 = slopes['ring0']; m0 = np.asarray(slopes['slopes'], float)
    TR = ToeRow(P)
    Kd, Kp, N = TR.Kd, TR.Kp, TR.N
    B = Builder(n_existing)
    info = aligned_columns(Lloop, Kd, Kp)
    ids_o = [loop_ids[i] for i in info['order']]
    P0 = ring0
    fw = float(ring0[0, 0])
    ball, colsD, colsP = TR.ball_ring()
    # smooth ball dome (crown envelope) and the lobe deviations of the dorsal columns
    crown_z = np.array([TR.ring(t, 0.0)[1:TR.m[t] + 1, 2].max() for t in range(5)])
    side_l = np.array([ball[0, 1], ball[Kd + 1, 1]]); side_z = np.array([ball[0, 2], ball[Kd + 1, 2]])
    xs = np.r_[side_l[1], TR.lc, side_l[0]]; ys = np.r_[side_z[1], crown_z, side_z[0]]
    o = np.argsort(xs); xs, ys = xs[o], ys[o]
    ball_s = ball.copy()
    zs_dome = smooth_profile(xs, ys, ball[1:Kd + 1, 1], sigma=0.007)
    ball_s[1:Kd + 1, 2] = np.minimum(zs_dome, ys.max())
    delta = np.zeros(N); delta[1:Kd + 1] = ball[1:Kd + 1, 2] - ball_s[1:Kd + 1, 2]
    valley_mask = np.zeros(N, bool)
    for k, c in enumerate(colsD):
        if c[0] == 'V': valley_mask[1 + k] = True
    m1 = np.zeros((N, 2))
    R = P['n_body_rows']
    Dd = 0.0 - fw
    rings = [P0.copy()]
    for r in range(1, R + 1):
        sr = r / R
        tau = 1.0 - (1.0 - sr) ** P['ring_pow']
        fr = fw + tau * Dd
        lz = hermite(P0[:, 1:3], m0, ball_s[:, 1:3], m1, tau, Dd)
        pos = np.column_stack([np.full(N, fr), lz])
        if r == R:
            pos = ball.copy()
        else:
            gz = smooth01((fr + P['span_g']) / P['span_g'])
            gv = smooth01((fr + P['span_v']) / P['span_v'])
            pos[:, 2] += gz * delta                           # one common fade for crowns and valleys (a faster valley fade leaves a raised fin between the toe shoulders)
            # instep height correction: scale the dorsal heights so the ring apex follows the plate sagittal contour
            wprof = P['prof_gain'] * (1 - smooth01((fr + P['prof_w0']) / (P['prof_w0'] - P['prof_w1'])))
            if wprof > 1e-3:
                dz = pos[1:Kd + 1, 2]
                k_ap = int(np.argmax(dz)) + 1
                y_ap = FRAME_ORIGIN[1] - pos[k_ap, 0] * np.cos(np.radians(TOE_OUT_DEG)) + pos[k_ap, 1] * np.sin(np.radians(TOE_OUT_DEG))
                zt = float(plate_z(y_ap)); zm = float(dz.max())
                kfac = 1.0 + wprof * ((zt - Z0) / max(zm - Z0, 1e-4) - 1.0)
                pos[1:Kd + 1, 2] = Z0 + kfac * (dz - Z0)
        pos[:, 2] = np.maximum(pos[:, 2], Z0)
        rings.append(pos)
    ring_ids = [[B.add(p, ('body', r_ + 1, i_)) for i_, p in enumerate(pos)] for r_, pos in enumerate(rings)]
    # --- weld strip: loop -> ring 0 (columns are kept loop vertices; dropped ones get fans)
    scols = info['cols']; Mloop = len(ids_o); PL = info['P']
    A_ = lambda t: ids_o[t % Mloop]
    for jj in range(N):
        a0 = scols[jj]; a1 = scols[jj + 1] if jj + 1 < N else Mloop
        b0 = ring_ids[0][jj]; b1 = ring_ids[0][(jj + 1) % N]
        k_ = a1 - a0
        if k_ == 1:
            B.face(A_(a0), A_(a1), b1, b0)
        elif k_ == 2:                                  # one dropped vertex d: pick the triangulation with the best minimum angle (and no inversion)
            d_ = A_(a0 + 1)
            pa0, pd, pa1 = PL[a0 % Mloop], PL[(a0 + 1) % Mloop], PL[a1 % Mloop]
            pb0, pb1 = np.asarray(rings[0][jj]), np.asarray(rings[0][(jj + 1) % N])
            n_ref = poly_normal([pa0, pa1, pb1, pb0])
            def score(polys):
                if any(poly_normal(q) @ n_ref <= 0 for q in polys): return -1.0
                return min(minang(q) for q in polys)
            optA = score([[pa0, pd, pb0], [pd, pb1, pb0], [pd, pa1, pb1]])
            optB = score([[pa0, pd, pb0], [pd, pa1, pb1, pb0]])
            optC = score([[pa0, pd, pb1, pb0], [pd, pa1, pb1]])
            best_ = max((optA, 'A'), (optB, 'B'), (optC, 'C'))[1]
            if best_ == 'A':
                B.face(A_(a0), d_, b0); B.face(d_, b1, b0); B.face(d_, A_(a1), b1)
            elif best_ == 'B':
                B.face(A_(a0), d_, b0); B.face(d_, A_(a1), b1, b0)
            else:
                B.face(A_(a0), d_, b1, b0); B.face(d_, A_(a1), b1)
        else:                                          # two or more dropped vertices in a row: triangulate the run polygon [a0 .. a1, b1, b0] as two fans
            h_ = (k_) // 2
            for t in range(a0, a0 + h_):
                B.face(A_(t), A_(t + 1), b0)
            B.face(A_(a0 + h_), b1, b0)
            for t in range(a0 + h_, a1):
                B.face(A_(t), A_(t + 1), b1)
    # --- body quads
    for r in range(len(ring_ids) - 1):
        for i in range(N):
            i2 = (i + 1) % N
            B.face(ring_ids[r][i], ring_ids[r][i2], ring_ids[r + 1][i2], ring_ids[r + 1][i])
    ballids = ring_ids[-1]
    # --- toes
    idxD = {}; idxV = {}
    for k, c in enumerate(colsD):
        if c[0] == 'T': idxD[(c[1], c[2])] = 1 + k
        else: idxV[c[1]] = 1 + k
    idxP = {}; idxVP = {}
    for k, c in enumerate(colsP):
        if c[0] == 'T': idxP[(c[1], c[2])] = Kd + 2 + k
        else: idxVP[c[1]] = Kd + 2 + k
    S_lat, S_med = 0, Kd + 1
    tubes = {}
    for t in range(5):
        m = TR.m[t]; mp = TR.mp[t]
        rows, pole = TR.toe_rows(t)
        ids = [[B.add(p, ('toe', t, a_, i_)) for i_, p in enumerate(row)] for a_, row in enumerate(rows)]
        C = B.add(pole, ('pole', t))
        tubes[t] = (ids, C)
        # dorsal strip: ball ring -> first toe ring
        lat_d = S_lat if t == 4 else idxV[t]
        med_d = S_med if t == 0 else idxV[t - 1]
        top = [ids[0][0]] + [ids[0][q] for q in range(1, m + 1)] + [ids[0][m + 1]]
        ball_top = [ballids[lat_d]] + [ballids[idxD[(t, q)]] for q in range(1, m + 1)] + [ballids[med_d]]
        for j in range(m + 1):
            B.face(ball_top[j], ball_top[j + 1], top[j + 1], top[j])
        # plantar strip (medial -> lateral)
        lat_p = S_lat if t == 4 else idxVP[t]
        med_p = S_med if t == 0 else idxVP[t - 1]
        ball_bot = [ballids[med_p]] + [ballids[idxP[(t, q)]] for q in range(mp, 0, -1)] + [ballids[lat_p]]
        bot = [ids[0][m + 1]] + [ids[0][TR.p_index(t, q)] for q in range(mp, 0, -1)] + [ids[0][0]]
        for j in range(mp + 1):
            B.face(ball_bot[j], ball_bot[j + 1], bot[j + 1], bot[j])
        # tube rows
        nr = TR.ring_size(t)
        for a in range(len(ids) - 1):
            for i in range(nr):
                i2 = (i + 1) % nr
                B.face(ids[a][i], ids[a][i2], ids[a + 1][i2], ids[a + 1][i])
        # cap: triangle fan around the pole (a quad fan on a ring of 8-14 vertices has ~170 degree corners; same final triangle count)
        last = ids[-1]
        for i in range(nr):
            B.face(last[i], last[(i + 1) % nr], C)
    # webs between toe g (medial) and g+1 (lateral):  V_d, WR_{g+1}, V_p, WL_g
    for g in range(4):
        Vd = ballids[idxV[g]]; Vp = ballids[idxVP[g]]
        WLt = tubes[g][0][0][0]; WRn = tubes[g + 1][0][0][TR.m[g + 1] + 1]
        B.face(Vd, WRn, Vp, WLt)
    diag = dict(N=N, Kd=Kd, Kp=Kp, fw=fw, rings=len(rings), loop_M=len(ids_o), dropped=info['dropped'], tr=TR)
    return B, diag
