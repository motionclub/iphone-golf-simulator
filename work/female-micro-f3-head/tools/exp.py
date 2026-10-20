"""experiment helpers: build Head2 variants, write assembled-order npz meshes (zone-blended), sagittal plots."""
import sys, json, copy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, geo, geo2, loftf, fl, phi2, meshlib as ml
from fl import sstep as _sstep3, sstep5 as _sstep5
SMOOTH5 = {'on': False}


def sstep(a, b, x):
    return _sstep5(a, b, x) if SMOOTH5['on'] else _sstep3(a, b, x)

FB0 = list(phi2.FRONT_BASE0)
FB_VERT = [(r, c) for (r, c) in FB0 if r < 244] + [(244, 573.0), (246, 573.0), (248, 573.0), (250, 573.0)]
Z0 = np.array(phi2.PROF0['z']); DY0 = np.array(phi2.PROF0['dy'])


def prof_nochin(zcut=1.452, taper=0.004):
    w = sstep(zcut - taper, zcut + taper, Z0)
    return dict(z=list(Z0), dy=list(DY0 * w))


def build(under=None, fb=FB_VERT, prof=None, prm_extra=None, zmin_loft=1.395, neck_blend=None):
    prm = copy.deepcopy(geo.DEFAULT_PRM)
    if under: prm['under'].update(under)
    if prm_extra:
        for k, v in prm_extra.items():
            if isinstance(v, dict): prm[k].update(v)
            else: prm[k] = v
    loftf.FRONT_BASE = list(fb) if fb else list(FB0)
    H = geo2.Head2(prm, zmin_loft=zmin_loft, neck_blend=neck_blend)
    if prof is not None: H.prof_corr = prof
    loftf.FRONT_BASE = list(FB0)
    return H


PROTECT_GROUPS = ('LOOP_seam', 'LOOP_lip_up', 'LOOP_lip_lo', 'LOOP_ala_L', 'LOOP_ala_R', 'LOOP_nostril_L', 'LOOP_nostril_R')


class Ctx:
    def __init__(self):
        self.V, self.F, self.d = ml.load(fl.W / 'data/F1.npz')
        vm = json.load(open(fl.W / 'data/work_assembled_vmap.json')); self.pmap = {int(k): int(v) for k, v in vm['pmap'].items()}
        st = np.load(fl.W / 'data/b17_state.npz'); self.U = st['U']; self.Pp = st['P'][:len(self.U)]
        self.ids = np.array([self.pmap[i] for i in range(len(self.U))])
        self.Pold = self.V[self.ids].copy()          # the staged blend's own float32 positions (patch P differs by float32 rounding only)
        import collections
        self.groups = json.load(open(fl.W / 'data/F1_groups.json'))
        # chain-protect fade: exactly 0 on the mouth / nose chain vertices, rising to 1 over 8 mm around them
        prot_ids = []
        for nm in PROTECT_GROUPS:
            prot_ids += self.groups[nm]
        prot_ids = np.array(sorted(set(prot_ids)))
        Q = self.V[prot_ids]; Pm = self.Pold
        dmin = np.full(len(Pm), 1e9)
        for q in Q:
            dmin = np.minimum(dmin, np.linalg.norm(Pm - q[None, :], axis=1))
        self.chain_fade = sstep(0.0, 0.008, dmin)


def zone_w(P, p=None):
    """smooth zone weight on OLD positions: 1 in the lower face (chin, jaw body, lower cheek), 0 outside / in the protected mouth-nose-eye-ear zones"""
    p = p or {}
    x = np.abs(P[:, 0]); y = P[:, 1]; z = P[:, 2]
    zt = p.get('ztop', 1.505); zt1 = p.get('ztop1', 1.545)
    w = 1.0 - sstep(zt, zt1, z)                                            # fade out toward the cheekbone
    # protected mouth/nose core: |x| < 0.043 above the sulcus
    prot = (1.0 - sstep(0.040, 0.052, x)) * sstep(1.446, 1.4545, z)
    w *= 1.0 - prot
    # ear zone
    ear = sstep(0.058, 0.070, x) * sstep(-0.012, -0.030, -y) * 0 
    earz = sstep(0.060, 0.072, x) * sstep(-0.035, -0.020, y) * sstep(1.452, 1.462, z) * (1.0 - sstep(0.075, 0.095, y))
    w *= 1.0 - earz
    # back limit: jaw angle / neck: fade with y
    yb0 = p.get('yb0', -0.040); yb1 = p.get('yb1', 0.030)
    wy = 1.0 - sstep(yb0, yb1, y)
    wy = np.where(x < 0.040, 1.0 - sstep(-0.050, -0.032, y), wy)         # under-chin: stop in front of the neck wall
    w *= wy
    w *= sstep(1.410, 1.418, z)
    return w


def mesh_variant(H, ctx, name, wfun=zone_w, wp=None, exact_only=False, save=True):
    Pn = H.phi(ctx.U)
    w = wfun(ctx.Pold, wp)[:, None]
    Pb = ctx.Pold * (1 - w) + Pn * w
    if exact_only:
        Pb = np.where(np.linalg.norm(np.load(fl.W / 'data/phi_resid_b17.npz')['res'], axis=1)[:, None] < 1e-6, Pb, ctx.Pold)
    Vn = ctx.V.copy(); Vn[ctx.ids] = Pb
    if save: np.savez(fl.W / f'data/var_{name}.npz', V=Vn, F=ctx.d['F'], Foff=ctx.d['Foff'])
    return Vn, w[:, 0]


# ------------------------------------------------------------------------------------------------ lower-face loft rows without the a_corr compensation
ACORR = json.load(open(fl.W / 'data/a_corr.json'))


def smooth_rows(zk, v, sig):
    out = np.empty_like(v)
    for i, zi in enumerate(zk):
        w = np.exp(-0.5 * ((zk - zi) / sig) ** 2); out[i] = (w * v).sum() / w.sum()
    return out


def apply_lower_rows(H, z0=1.490, z1=1.505, sig=0.0045, da_extra=None):
    """loft half width below ~1.495: plate rows WITHOUT the F1 a_corr compensation (it was clamped at +12 mm to make up for the plane trimming), Gaussian-smoothed;
    blends back to the F1 rows above z1."""
    L = H.L; zk = L.zk
    corr = np.interp(zk, ACORR['z'], ACORR['da'])
    base = L.a - corr
    bs = smooth_rows(zk, base, sig)
    if da_extra is not None: bs = bs + np.interp(zk, da_extra[0], da_extra[1])
    w = sstep(z0, z1, zk)
    L.a = (1 - w) * bs + w * L.a
    return H


# ------------------------------------------------------------------------------------------------ delta integration
_H_OLD = None


def phi_old(ctx):
    global _H_OLD
    if _H_OLD is None:
        _H_OLD = geo.Head()
        _H_OLD._cache = _H_OLD.phi(ctx.U)
    return _H_OLD._cache


def fair_sets(ctx):
    """vertices that F1 moved by implicit fairing (chin / jaw angle / neck top): their residual vs Phi is a hack-fix of the old construction and is dropped in the lower face"""
    P = ctx.Pold
    chin = (np.abs(P[:, 0]) < 0.050) & (P[:, 1] > -0.140) & (P[:, 1] < -0.050) & (P[:, 2] > 1.412) & (P[:, 2] < 1.455)
    ear_zone = (np.abs(P[:, 0]) > 0.065) & (P[:, 1] > -0.03) & (P[:, 1] < 0.07) & (P[:, 2] > 1.455)
    jaw = (P[:, 2] > 1.4125) & (P[:, 2] < 1.52) & (P[:, 1] > -0.075) & (~ear_zone)
    return chin | jaw


ZONE = {}
NF_SIGMA = 0.010


def lower_zone(P, zt0=1.500, zt1=1.525, xc0=0.020, xc1=0.060, zc0=1.449, zc1=1.4575):
    if 'zt' in ZONE: zt0, zt1 = ZONE['zt']
    """1 in the lower face (chin, jaw, lower cheek); 0 in the mouth/nose core (|x| < ~0.045 above the sulcus), the ear zone and above the lower cheek"""
    x = np.abs(P[:, 0]); y = P[:, 1]; z = P[:, 2]
    w = 1.0 - sstep(zt0, zt1, z)
    prot = (1.0 - sstep(xc0, xc1, x)) * sstep(zc0, zc1, z)
    earz = sstep(0.056, 0.068, x) * (1.0 - sstep(-0.045, -0.030, -y) * 0) * sstep(-0.040, -0.026, y) * sstep(1.448, 1.458, z)
    back = 1.0 - sstep(0.000, 0.035, y)                       # nothing behind the jaw angle (nape / back of the head) moves
    return w * (1.0 - prot) * (1.0 - earz) * back


def mesh_delta(H, ctx, name, drop_resid=True, ymax=None, save=True, scale=1.0, nb=(-0.058, -0.046)):
    """P_new = P_old + wm*[(Phi_new - Phi_old)(U) - [chin set]*(P_old - Phi_old)(U)],  wm = 1 - sstep(nb, y of the OLD MESH vertex): exactly zero near the neck"""
    Po = phi_old(ctx); Pn = H.phi(ctx.U)
    R = ctx.Pold - Po
    m = fair_sets(ctx) & (np.linalg.norm(R, axis=1) > 1e-6)
    P0 = ctx.Pold
    g = 1.0 - sstep(1.447, 1.462, P0[:, 2])                                                            # below the jaw: everything behind the chin underside is neck (all x)
    wm = (1.0 - sstep(nb[0], nb[1], P0[:, 1]) * g) * sstep(1.4225, 1.4265, P0[:, 2]) * lower_zone(P0) * scale
    wm = wm[:, None]
    Pnew = ctx.Pold + wm * (Pn - Po)
    if drop_resid: Pnew = Pnew - wm * m[:, None] * R
    dP = Pnew - ctx.Pold
    dP[np.linalg.norm(dP, axis=1) < 2e-7] = 0.0                      # float noise below one float32 ulp -> exactly zero
    Pnew = ctx.Pold + dP
    Vn = ctx.V.copy(); Vn[ctx.ids] = Pnew
    if save: np.savez(fl.W / f'data/var_{name}.npz', V=Vn, F=ctx.d['F'], Foff=ctx.d['Foff'])
    return Vn, dP, m


def apply_a_smooth(H, sig=0.005, z0=1.525, z1=1.545, rows=('a',), tf=0.545):
    """remove the curvature spikes / ripple of the loft rows (a: corners of F1's clamped +12 mm a_corr plateau at z 1.444/1.458/1.462/1.478; yf, yb: plate quantisation):
    Gaussian smoothing in z, faded out above z0..z1; f, b, yw are re-derived from yf/yb when those are smoothed"""
    L = H.L; zk = L.zk
    w = 1.0 - sstep(z0, z1, zk)
    if 'a' in rows:
        L.a = L.a + w * (smooth_rows(zk, L.a, sig) - L.a)
    if 'nf' in rows:        # F1's front-section exponent is piecewise linear with slope jumps at z 1.47 and 1.53 -> horizontal creases across the cheek; smooth it (sigma 10 mm, |change| <= 0.05)
        L.nf = L.nf + (smooth_rows(zk, L.nf, NF_SIGMA) - L.nf)
    if 'yf' in rows or 'yb' in rows:
        if 'yf' in rows: L.yf = L.yf + w * (smooth_rows(zk, L.yf, sig) - L.yf)
        if 'yb' in rows: L.yb = L.yb + w * (smooth_rows(zk, L.yb, sig) - L.yb)
        top = np.where(zk > 1.7039 - 0.0018, 0, 1)    # (closure factor only acts at the very top; not touched here)
        D = L.yb - L.yf; f_new = tf * D; b_new = D - f_new
        keep = zk > 1.56                                   # leave the rows above the smoothing zone exactly as they were
        L.f = np.where(keep, L.f, f_new); L.b = np.where(keep, L.b, b_new); L.yw = np.where(keep, L.yw, L.yf + f_new)
    return H


# ------------------------------------------------------------------------------------------------ normal-direction delta (no tangential slip)
def mesh_normal_delta(H, ctx, name, iters=26, save=True, nb=(-0.058, -0.046), scale=1.0, T=0.020):
    """each moved vertex slides ONLY along its old surface normal onto the new analytic surface: bisection on t in [-T, T] of the signed radial gap
    g(t) = |Phi_new(u_t) - C| - |P_old + t n - C|   (> 0 inside the head).  F1's vertex spacing is kept (ray-chart deltas drag vertices tangentially where the
    normal differs from the ray, which squashed thin triangles under the chin).     P_new = P_old + wm * t * n"""
    P0 = ctx.Pold
    N0, _, _ = ml.vertex_normals(ctx.V, ctx.F)
    n = N0[ctx.ids]
    g = 1.0 - sstep(1.447, 1.462, P0[:, 2])
    wm = (1.0 - sstep(nb[0], nb[1], P0[:, 1]) * g) * sstep(1.4225, 1.4265, P0[:, 2]) * lower_zone(P0) * ctx.chain_fade * scale
    idx = np.where(wm > 0)[0]
    C = geo.C
    def gap(tv):
        Q = P0[idx] + tv[:, None] * n[idx]
        u = Q - C[None, :]; r = np.linalg.norm(u, axis=1); u = u / r[:, None]
        return np.linalg.norm(H.phi(u) - C[None, :], axis=1) - r
    lo = np.full(len(idx), -T); hi = np.full(len(idx), T)
    glo = gap(lo); ghi = gap(hi)
    ok = (glo > 0) & (ghi < 0)
    for _ in range(iters):
        mid = 0.5 * (lo + hi); gm = gap(mid)
        inside = gm > 0
        lo = np.where(inside, mid, lo); hi = np.where(inside, hi, mid)
    t = 0.5 * (lo + hi); t = np.where(ok, t, 0.0)
    tfull = np.zeros(len(P0)); tfull[idx] = t
    dP = (wm * tfull)[:, None] * n
    dP[np.linalg.norm(dP, axis=1) < 2e-7] = 0.0
    Pnew = P0 + dP
    Vn = ctx.V.copy(); Vn[ctx.ids] = Pnew
    if save: np.savez(fl.W / f'data/var_{name}.npz', V=Vn, F=ctx.d['F'], Foff=ctx.d['Foff'])
    return Vn, dP, int((~ok).sum())


# ------------------------------------------------------------------------------------------------ tangential regularisation (F3)
def csr_adj(F, n):
    """directed edge arrays (a -> b) for the umbrella operator"""
    ea, eb = [], []
    for f in F:
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m]); ea += [a, b]; eb += [b, a]
    ea = np.array(ea); eb = np.array(eb)
    key = ea.astype(np.int64) * n + eb; _, u = np.unique(key, return_index=True)
    return ea[u], eb[u]


def project_to_surface(H, P, n, idx, T=0.012, iters=22):
    """slide P[idx] along n[idx] onto the analytic surface of H (bisection on the radial gap); returns new positions for idx"""
    C = geo.C
    def gap(tv):
        Q = P[idx] + tv[:, None] * n[idx]
        u = Q - C[None, :]; r = np.linalg.norm(u, axis=1); u = u / r[:, None]
        return np.linalg.norm(H.phi(u) - C[None, :], axis=1) - r
    lo = np.full(len(idx), -T); hi = np.full(len(idx), T)
    ok = (gap(lo) > 0) & (gap(hi) < 0)
    for _ in range(iters):
        mid = 0.5 * (lo + hi); gm = gap(mid); ins = gm > 0
        lo = np.where(ins, mid, lo); hi = np.where(ins, hi, mid)
    t = np.where(ok, 0.5 * (lo + hi), 0.0)
    return P[idx] + t[:, None] * n[idx], int((~ok).sum())


def relax_zone(H, ctx, V0, w, iters=20, lam=0.5, snap_every=1, verbose=True):
    """tangential Laplacian relaxation of the weighted zone (w in [0,1] per assembled vertex) with re-projection onto the analytic surface.
    Only the tangential part of the umbrella displacement is applied, so the shape (silhouettes, sections) is unchanged; spacing becomes even -> vertex normals get cleaner."""
    V = V0.copy(); n = len(V)
    ea, eb = csr_adj(ctx.F, n)
    deg = np.bincount(ea, minlength=n).astype(float)
    act = np.where(w > 0)[0]
    nbad_tot = 0
    for it in range(iters):
        N, _, _ = ml.vertex_normals(V, ctx.F)
        s = np.zeros_like(V); np.add.at(s, ea, V[eb])
        c = s / np.maximum(deg, 1)[:, None]
        d = c - V
        d = d - (d * N).sum(1, keepdims=True) * N          # tangential part only
        step = (lam * w)[:, None] * d
        V[act] = V[act] + step[act]
        if (it + 1) % snap_every == 0:
            N2, _, _ = ml.vertex_normals(V, ctx.F)
            newp, nbad = project_to_surface(H, V, N2, act)
            V[act] = newp; nbad_tot += nbad
    if verbose: print('relax: iters', iters, 'lam', lam, 'verts', len(act), 'projection bracket failures', nbad_tot)
    return V
