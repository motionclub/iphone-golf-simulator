"""Photometric optimiser (CMA-ES lite) for the FORM3 bust / glute parameters.

loss = (1 - NCC_bandpass) + 0.6*(log amp_ratio)^2 + penalties(silhouette envelope, seam steps, dihedral creases, parameter bounds)
Plate lighting: data/plate_light_fit.json, gain 2.5 (front) / 2.0 (back) calibrated on the unedited regions.

usage (python):  from opt3 import *;  prob = Problem('bust', 'data/P_final.json', SPECS['bust']);  best = prob.run(gens=25, pop=18, seed=1)
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from torso3 import *
import torso2 as t2
import seam
from photo3 import *

HERE = str(WD)
GAIN = {'front': 2.5, 'back': 2.0}
_ZG10 = np.arange(0.82, 1.341, 0.01)

# (name, lo, hi) ; names 'B0.x' address bm_list[0][x]
SPECS = {
    'bust': dict(view='front', box=(-0.115, 0.115, 1.14, 1.30), env=(1.17, 1.29),
                 params=[('B0.xc', 0.070, 0.115), ('B0.zc', 1.195, 1.245), ('B0.sxm', 0.028, 0.065), ('B0.sxl', 0.022, 0.050), ('B0.szd', 0.022, 0.055),
                         ('B0.szu', 0.040, 0.095), ('B0.H', 0.008, 0.050), ('B0.p', 1.0, 2.4), ('B0.gd', 0.0, 0.014), ('B0.gr', 0.85, 1.35), ('B0.gw', 0.10, 0.34),
                         ('b_rec', 0.0, 0.026), ('b_zc', 1.190, 1.240), ('b_rec_wd', 0.04, 0.095), ('b_rec_wu', 0.03, 0.075),
                         ('st_R3', 0.0, 0.016), ('st_sx', 0.020, 0.055), ('st_zc', 1.19, 1.24), ('fl_k', 0.0, 0.5), ('bp_H', 0.0, 0.010), ('bp_zc', 1.235, 1.31), ('bp_xc', 0.03, 0.11)]),
    'bust6': dict(view='front', box=(-0.115, 0.115, 1.15, 1.275), env=(1.17, 1.25), min_H=0.0135, scales=[(1.6, 9.0), (4.0, 20.0)], dih_region='bust', dih_lim=(22.0, 28.5), relief_w=1.0,
                  params=[('B0.xc', 0.080, 0.115), ('B0.zc', 1.205, 1.230), ('B0.sxm', 0.035, 0.065), ('B0.sxl', 0.028, 0.055), ('B0.szd', 0.028, 0.050),
                          ('B0.szu', 0.050, 0.085), ('B0.H', 0.0135, 0.026), ('B0.p', 1.0, 2.0), ('B0.gd', 0.003, 0.010), ('B0.gr', 0.95, 1.30), ('B0.gw', 0.15, 0.40), ('B0.tilt', -0.45, 0.20),
                          ('b_rec', 0.0, 0.020), ('mo_R', 0.0, 0.016), ('mo_xc', 0.07, 0.11), ('mo_sx', 0.05, 0.10), ('mo_szd', 0.03, 0.07)]),
    'bust5': dict(view='front', box=(-0.115, 0.115, 1.15, 1.275), env=(1.17, 1.25), min_H=0.0135, scales=[(1.6, 9.0), (4.0, 20.0)], dih_region='bust', dih_lim=(21.0, 27.0),
                  params=[('B0.xc', 0.085, 0.105), ('B0.zc', 1.205, 1.225), ('B0.sxm', 0.040, 0.056), ('B0.sxl', 0.028, 0.040), ('B0.szd', 0.030, 0.050),
                          ('B0.szu', 0.055, 0.085), ('B0.H', 0.0135, 0.024), ('B0.p', 1.2, 2.0), ('B0.gd', 0.003, 0.010), ('B0.gr', 1.0, 1.3), ('B0.gw', 0.24, 0.40), ('B0.tilt', -0.45, 0.1)]),
    'bust4': dict(view='front', box=(-0.115, 0.115, 1.15, 1.275), env=(1.17, 1.25), min_H=0.0135, scales=[(1.6, 9.0), (4.0, 20.0)],
                  params=[('B0.xc', 0.085, 0.105), ('B0.zc', 1.205, 1.225), ('B0.sxm', 0.040, 0.056), ('B0.sxl', 0.028, 0.040), ('B0.szd', 0.030, 0.050),
                          ('B0.szu', 0.055, 0.085), ('B0.H', 0.0135, 0.024), ('B0.p', 1.2, 2.0), ('B0.gd', 0.004, 0.012), ('B0.gr', 1.0, 1.3), ('B0.gw', 0.15, 0.30), ('B0.tilt', -0.45, 0.1)]),
    'bust3': dict(view='front', box=(-0.115, 0.115, 1.15, 1.275), env=(1.17, 1.29), min_H=0.016, scales=[(1.6, 9.0), (4.0, 20.0)],
                  params=[('B0.xc', 0.075, 0.105), ('B0.zc', 1.200, 1.235), ('B0.sxm', 0.032, 0.060), ('B0.sxl', 0.026, 0.046), ('B0.szd', 0.026, 0.050),
                          ('B0.szu', 0.045, 0.085), ('B0.H', 0.016, 0.045), ('B0.p', 1.0, 2.2), ('B0.gd', 0.0, 0.008), ('B0.gr', 0.95, 1.30), ('B0.gw', 0.10, 0.26), ('B0.tilt', -0.5, 0.5),
                          ('b_rec', 0.0, 0.022), ('b_zc', 1.195, 1.235), ('b_rec_wd', 0.04, 0.085), ('b_rec_wu', 0.03, 0.065),
                          ('st_R3', 0.0, 0.014), ('st_sx', 0.022, 0.050), ('st_zc', 1.195, 1.235), ('fl_k', 0.0, 0.45)]),
    'bust2': dict(view='front', box=(-0.115, 0.115, 1.15, 1.275), env=(1.17, 1.29), min_H=0.013, min_valley=0.004,
                  params=[('B0.xc', 0.072, 0.100), ('B0.zc', 1.200, 1.235), ('B0.sxm', 0.032, 0.060), ('B0.sxl', 0.026, 0.046), ('B0.szd', 0.026, 0.050),
                          ('B0.szu', 0.045, 0.085), ('B0.H', 0.013, 0.045), ('B0.p', 1.0, 2.2), ('B0.gd', 0.0, 0.010), ('B0.gr', 0.95, 1.30), ('B0.gw', 0.10, 0.26),
                          ('b_rec', 0.0, 0.022), ('b_zc', 1.195, 1.235), ('b_rec_wd', 0.04, 0.085), ('b_rec_wu', 0.03, 0.065),
                          ('st_R3', 0.0, 0.014), ('st_sx', 0.022, 0.050), ('st_zc', 1.195, 1.235), ('fl_k', 0.0, 0.45)]),
    'glute4': dict(view='back', box=(-0.14, 0.14, 0.80, 0.97), env=(0.84, 1.0), dih_region='glute', dih_lim=(22.0, 28.5), relief_b_w=1.0,
                   cleft={0.84: (14, 28), 0.86: (12, 26), 0.88: (9, 20), 0.90: (6, 16), 0.92: (3, 12), 0.94: (0, 7)}, vness=(0.86, 0.88, 0.90),
                   params=[('gl_H', 0.0, 0.07), ('gl_xc', 0.050, 0.100), ('gl_zc', 0.84, 0.90), ('gl_sxm', 0.035, 0.075), ('gl_sxl', 0.040, 0.085), ('gl_szd', 0.030, 0.085), ('gl_szu', 0.040, 0.100),
                           ('gm_R', 0.0, 0.040), ('gm_xc', 0.050, 0.100), ('gm_zc', 0.85, 0.91), ('gm_sxm', 0.035, 0.080), ('gm_sxl', 0.025, 0.070), ('gm_szd', 0.030, 0.070), ('gm_szu', 0.015, 0.060),
                           ('cl_c', 0.012, 0.034), ('cl_w0', 0.020, 0.050), ('cl_wup', -0.8, 1.6), ('cl_z0', 0.82, 0.90), ('cl_z1', 0.90, 0.97), ('cl_q', 1.5, 2.6)]),
    'glute3': dict(view='back', box=(-0.14, 0.14, 0.80, 0.97), env=(0.84, 1.0), dih_region='glute', dih_lim=(21.0, 27.0),
                   cleft={0.84: (14, 26), 0.86: (12, 24), 0.88: (9, 20), 0.90: (6, 16), 0.92: (3, 12), 0.94: (0, 7)}, vness=(0.86, 0.88, 0.90),
                   params=[('gl_H', 0.0, 0.07), ('gl_xc', 0.050, 0.100), ('gl_zc', 0.84, 0.90), ('gl_sxm', 0.035, 0.075), ('gl_sxl', 0.040, 0.085), ('gl_szd', 0.030, 0.085), ('gl_szu', 0.040, 0.100),
                           ('gm_R', 0.0, 0.040), ('gm_xc', 0.050, 0.100), ('gm_zc', 0.85, 0.91), ('gm_sxm', 0.035, 0.080), ('gm_sxl', 0.025, 0.070), ('gm_szd', 0.030, 0.070), ('gm_szu', 0.015, 0.060),
                           ('cl_c', 0.012, 0.034), ('cl_w0', 0.020, 0.050), ('cl_wup', -0.8, 1.6), ('cl_z0', 0.82, 0.90), ('cl_z1', 0.90, 0.97), ('cl_q', 1.7, 2.6)]),
    'glute2': dict(view='back', box=(-0.14, 0.14, 0.80, 0.97), env=(0.84, 1.0),
                   cleft={0.84: (14, 26), 0.86: (12, 24), 0.88: (9, 20), 0.90: (6, 16), 0.92: (3, 12), 0.94: (0, 7)}, vness=(0.86, 0.88, 0.90),
                   params=[('gl_H', 0.0, 0.07), ('gl_xc', 0.050, 0.100), ('gl_zc', 0.84, 0.90), ('gl_sxm', 0.035, 0.075), ('gl_sxl', 0.040, 0.085), ('gl_szd', 0.030, 0.085), ('gl_szu', 0.040, 0.100),
                           ('gm_R', 0.0, 0.040), ('gm_xc', 0.050, 0.100), ('gm_zc', 0.85, 0.91), ('gm_sxm', 0.035, 0.080), ('gm_sxl', 0.025, 0.070), ('gm_szd', 0.030, 0.070), ('gm_szu', 0.015, 0.060),
                           ('cl_c', 0.012, 0.034), ('cl_w0', 0.014, 0.045), ('cl_wup', -0.8, 1.6), ('cl_z0', 0.82, 0.90), ('cl_z1', 0.90, 0.99), ('cl_q', 1.25, 2.2)]),
    'glute': dict(view='back', box=(-0.14, 0.14, 0.80, 0.97), env=(0.84, 1.0),
                  params=[('gl_H', 0.0, 0.07), ('gl_xc', 0.050, 0.100), ('gl_zc', 0.84, 0.90), ('gl_sxm', 0.035, 0.075), ('gl_sxl', 0.040, 0.085), ('gl_szd', 0.030, 0.085), ('gl_szu', 0.040, 0.100),
                          ('gm_R', 0.0, 0.040), ('gm_xc', 0.050, 0.100), ('gm_zc', 0.85, 0.91), ('gm_sxm', 0.035, 0.080), ('gm_sxl', 0.025, 0.070), ('gm_szd', 0.030, 0.070), ('gm_szu', 0.015, 0.060),
                          ('cl_c', 0.0, 0.034), ('cl_w0', 0.014, 0.045), ('cl_wup', -0.8, 1.6), ('cl_z0', 0.82, 0.90), ('cl_z1', 0.90, 0.99), ('cl_q', 1.0, 2.2)]),
}


import section as _sec


def cleft_profile(co, z):
    x, y = _sec.crossing(co, z)
    sel = y > 0
    x, y = x[sel], y[sel]
    o = np.argsort(x)
    return x[o], y[o]


def cleft_depth_ratio(co, z):
    """cleft depth (mm) relative to the two lobe apexes at height z, and V-ness = W50/W10 of the depth profile BETWEEN the apexes
    (V or gaussian dip ~0.55, vertical-walled pit -> 1)"""
    x, y = cleft_profile(co, z)
    if len(x) < 6:
        return 0.0, 0.5
    xi = np.arange(-0.12, 0.1201, 0.001)
    yi = np.interp(xi, x, y)
    right = np.where((xi > 0.015) & (xi < 0.11))[0]; left = np.where((xi < -0.015) & (xi > -0.11))[0]
    ir = right[np.argmax(yi[right])]; il = left[np.argmax(yi[left])]
    base = min(yi[ir], yi[il])
    xs = xi[il:ir + 1]
    dd = np.clip(base - yi[il:ir + 1], 0, None)
    d = dd[np.abs(xs) < 0.004].max()
    if d < 0.004:
        return 1000 * d, 0.5
    w50 = xs[dd >= 0.5 * d]; w10 = xs[dd >= 0.1 * d]
    return 1000 * d, float((w50.max() - w50.min()) / max(w10.max() - w10.min(), 1e-6))


def get_param(P, name):
    if name.startswith('B0.'):
        return P['bm_list'][0][name[3:]]
    return P[name]


def set_param(P, name, v):
    if name.startswith('B0.'):
        P['bm_list'][0][name[3:]] = float(v)
    else:
        P[name] = float(v)


class Problem:
    def __init__(self, part, base_json, spec=None, walls=None):
        self.part = part
        self.spec = spec or SPECS[part]
        P = json.load(open(base_json if base_json.startswith('/') else f'{HERE}/{base_json}'))
        # fold bm_scale into the mound heights (optimiser works with explicit H)
        sc = P.get('bm_scale', 1.0)
        P['bm_list'] = [dict(c) for c in P['bm_list']]
        for c in P['bm_list']:
            c['H'] = c['H'] * sc
        P['bm_scale'] = 1.0
        self.base = {**DEFAULT3, **P}
        self.names = [p[0] for p in self.spec['params']]
        self.lo = np.array([p[1] for p in self.spec['params']])
        self.hi = np.array([p[2] for p in self.spec['params']])
        self.x0 = np.array([get_param(self.base, n) for n in self.names])
        self.view = self.spec['view']
        self.box = roi_box(self.view, *self.spec['box'])
        self.light = np.array(LIGHT); self.light[1:] *= GAIN[self.view]
        self.relief_w = self.spec.get('relief_w', 0.0)
        if self.relief_w:
            import relief3 as _r3
            self._r3 = _r3
        self.relief_b_w = self.spec.get('relief_b_w', 0.0)
        if self.relief_b_w:
            import relief3b as _r3b
            self._r3b = _r3b
        self.scales = self.spec.get('scales', [(1.6, 9.0)])
        self.pbs = [plate_bp(self.view, self.box, a, b) for a, b in self.scales]
        self.pb = self.pbs[0]
        self.dF = self.dB = None
        if walls is not None:
            self.dF, self.dB = walls
        else:
            dF, dB = fit_walls(self.base, iters=4, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
            self.dF, self.dB = dF, dB
        self.n_eval = 0
        self.cache = {}
        a0 = seam.dihedral(CO0)
        self.dih_orig = int((seam.ZPAIR & (a0 > 40)).sum())
        self.a0 = a0
        mid0 = 0.5 * (CO0[seam.PAIR_E[:, 0]] + CO0[seam.PAIR_E[:, 1]])
        nb = ~(BORDER[seam.PAIR_E[:, 0]] | BORDER[seam.PAIR_E[:, 1]])           # interior edges only (border-adjacent edges are governed by the seam-step gate)
        self.reg = None
        smooth0 = a0 <= 15.0                                                   # only edges that were smooth in the original count (inherited creases excluded)
        dr = self.spec.get('dih_region')
        if dr == 'bust':
            self.reg = seam.ZPAIR & nb & smooth0 & (mid0[:, 2] >= 1.14) & (mid0[:, 2] <= 1.32) & (np.abs(mid0[:, 0]) <= 0.115) & (mid0[:, 1] < 0)
        elif dr == 'glute':
            self.reg = seam.ZPAIR & nb & smooth0 & (mid0[:, 2] >= 0.80) & (mid0[:, 2] <= 1.02) & (np.abs(mid0[:, 0]) <= 0.15) & (mid0[:, 1] > 0)
        self.dih_lim = self.spec.get('dih_lim', (22.0, 28.0))

    # -------------------------------------------------------------------------------- model
    def params(self, x):
        P = {**self.base, 'bm_list': [dict(c) for c in self.base['bm_list']]}
        for n, v in zip(self.names, x):
            set_param(P, n, v)
        return P

    def build(self, x):
        return build3(self.params(x), self.dF, self.dB)

    def loss(self, x, detail=False):
        x = np.asarray(x, float)
        pen = 0.0
        # bounds (soft reflection into the box + penalty for the excursion)
        xc = np.clip(x, self.lo, self.hi)
        pen += 50.0 * float((((x - xc) / (self.hi - self.lo)) ** 2).sum())
        co = self.build(xc)
        # photometric term
        mbs, mask = model_multi_bp(co, self.view, self.box, self.scales, light=self.light)
        from scipy_free import erode
        m = erode(mask, 6)
        nccs = []; amps = []
        for pbk, mbk in zip(self.pbs, mbs):
            a, b = pbk[m], mbk[m]
            a0, b0 = a - a.mean(), b - b.mean()
            nccs.append(float((a0 * b0).sum() / np.sqrt((a0 ** 2).sum() * (b0 ** 2).sum() + 1e-12)))
            amps.append(float(b0.std() / (a0.std() + 1e-12)))
        ncc = float(np.mean(nccs)); amp = float(np.mean(amps))
        L = (1 - ncc) + 0.6 * float(np.log(max(amp, 1e-3)) ** 2)
        rl = 0.0
        if self.relief_w:
            rl, _t = self._r3.score(co)
            L += self.relief_w * rl
        if self.relief_b_w:
            rl, _t = self._r3b.score(co)
            L += self.relief_b_w * rl
        # silhouette envelope vs plate table over the part's z range
        fe, be = section_extents(co, zg=_ZG10)
        fe, be = fillnan(fe), fillnan(be)
        z0, z1 = self.spec['env']
        mm = (_ZG10 >= z0) & (_ZG10 <= z1)
        if self.view == 'front':
            ref = np.array([plate_front(z) for z in _ZG10]); err = fe - ref
        else:
            ref = np.array([plate_back(z) for z in _ZG10]); err = be - ref
        env_rms = float(np.sqrt((err[mm] ** 2).mean()) * 1000)
        pen += 0.05 * max(0.0, env_rms - 2.0) ** 2
        # seam steps
        bs, _ = seam.border_steps(co)
        arm, legs = bs['arm']['max_mm'], bs['legs']['max_mm']
        pen += 0.4 * max(0.0, arm - 9.3) ** 2 + 0.4 * max(0.0, legs - 7.6) ** 2
        # dihedral creases
        a1 = seam.dihedral(co)
        n40 = int((seam.ZPAIR & (a1 > 40)).sum())
        pen += 0.3 * max(0, n40 - self.dih_orig)
        if self.reg is not None:
            inc = float((a1 - self.a0)[self.reg].max()); ab = float(a1[self.reg].max())
            pen += 0.02 * max(0.0, inc - self.dih_lim[0]) ** 2 + 0.02 * max(0.0, ab - self.dih_lim[1]) ** 2
        if 'cleft' in self.spec:
            for z, (lo, hi) in self.spec['cleft'].items():
                d, r = cleft_depth_ratio(co, z)
                pen += 0.03 * max(0.0, lo - d) ** 2 + 0.03 * max(0.0, d - hi) ** 2
                if z in self.spec.get('vness', ()):
                    pen += 20.0 * max(0.0, r - 0.78) ** 2
        if 'min_H' in self.spec:
            Pn = self.params(xc)
            H_eff = Pn['bm_list'][0]['H']
            pen += 400.0 * max(0.0, self.spec['min_H'] - H_eff) ** 2 / 1e-3 * 1e3 * 1e-3
        self.n_eval += 1
        tot = L + pen
        if detail:
            return dict(loss=tot, ncc=ncc, amp=amp, env_rms=env_rms, arm=arm, legs=legs, n40=n40, pen=pen, relief=rl)
        return tot

    # -------------------------------------------------------------------------------- CMA-ES lite
    def run(self, gens=20, pop=16, seed=0, sigma0=0.18, x_start=None, verbose=True):
        rng = np.random.default_rng(seed)
        n = len(self.x0)
        span = self.hi - self.lo
        m = ((self.x0 if x_start is None else np.asarray(x_start)) - self.lo) / span          # normalised [0,1]
        sig = sigma0
        C = np.eye(n)
        mu = pop // 2
        w = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1)); w /= w.sum()
        mueff = 1 / (w ** 2).sum()
        cs = (mueff + 2) / (n + mueff + 5); ds = 1 + cs + 2 * max(0, np.sqrt((mueff - 1) / (n + 1)) - 1)
        cc = (4 + mueff / n) / (n + 4 + 2 * mueff / n); c1 = 2 / ((n + 1.3) ** 2 + mueff); cmu = min(1 - c1, 2 * (mueff - 2 + 1 / mueff) / ((n + 2) ** 2 + mueff))
        pc = np.zeros(n); ps = np.zeros(n); chiN = np.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n))
        best = (1e9, None)
        f0 = self.loss(self.lo + np.clip(m, 0, 1) * span)
        best = (f0, m.copy())
        if verbose:
            print(f'start loss {f0:.4f}', self.loss(self.lo + np.clip(m, 0, 1) * span, detail=True))
        for g in range(gens):
            eigval, B = np.linalg.eigh(C); eigval = np.maximum(eigval, 1e-12); D = np.sqrt(eigval)
            Z = rng.standard_normal((pop, n))
            Y = Z @ (B * D).T
            X = m + sig * Y
            F = np.array([self.loss(self.lo + np.clip(x, 0, 1) * span) for x in X])
            idx = np.argsort(F)
            if F[idx[0]] < best[0]:
                best = (float(F[idx[0]]), np.clip(X[idx[0]], 0, 1).copy())
            yw = (w[:, None] * Y[idx[:mu]]).sum(0)
            m = m + sig * yw
            invsqrtC = B @ np.diag(1 / D) @ B.T
            ps = (1 - cs) * ps + np.sqrt(cs * (2 - cs) * mueff) * (invsqrtC @ yw)
            hs = (np.linalg.norm(ps) / np.sqrt(1 - (1 - cs) ** (2 * (g + 1))) / chiN) < (1.4 + 2 / (n + 1))
            pc = (1 - cc) * pc + hs * np.sqrt(cc * (2 - cc) * mueff) * yw
            C = (1 - c1 - cmu) * C + c1 * (np.outer(pc, pc) + (1 - hs) * cc * (2 - cc) * C) + cmu * sum(w[i] * np.outer(Y[idx[i]], Y[idx[i]]) for i in range(mu))
            sig *= np.exp((cs / ds) * (np.linalg.norm(ps) / chiN - 1))
            sig = float(np.clip(sig, 0.01, 0.5))
            if verbose and (g % 3 == 0 or g == gens - 1):
                print(f'gen {g:3d} best {best[0]:.4f} gen-best {F[idx[0]]:.4f} sigma {sig:.3f} evals {self.n_eval}', flush=True)
        xb = self.lo + np.clip(best[1], 0, 1) * span
        return xb, self.loss(xb, detail=True)

    def params_dict(self, x):
        return {n: float(v) for n, v in zip(self.names, x)}


if __name__ == '__main__':
    part = sys.argv[1]; gens = int(sys.argv[2]); pop = int(sys.argv[3]); seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    base = sys.argv[5] if len(sys.argv) > 5 else 'data/P_final.json'
    out = sys.argv[6] if len(sys.argv) > 6 else f'data/opt_{part}_s{seed}.json'
    t0 = time.time()
    pr = Problem(part, base)
    print('problem ready', round(time.time() - t0, 1), 's; x0 loss', pr.loss(pr.x0, detail=True))
    xb, det = pr.run(gens=gens, pop=pop, seed=seed)
    print('BEST', det)
    P = pr.params(xb)
    json.dump(P, open(f'{HERE}/{out}', 'w'), default=float, indent=1)
    np.save(f'{HERE}/data/co_opt_{part}_s{seed}.npy', pr.build(xb))
    print('saved', out, 'time', round(time.time() - t0, 1), 's')
