"""MALE PELVIS FORM2 sculpt model v2 (butt + groin).  Positions only; topology untouched.
python3 f2_model2.py <params.json|-> <tag>      -> data/V_<tag>.npy, data/P_<tag>.json
Central idea: DESIGN the rear surface of the cleft zone as an explicit target (valley between the lobe ridges, fill-or-carve), lower the crotch roof with a
smooth grab, and smooth the keyhole neighbourhood so no fold-backs appear.  All terms are smooth displacement fields on the start mesh."""
import sys, json
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2')
from common import V0, F, vnormals
from sculpt import smoothstep, band, taubin
import hf
W = __import__('pathlib').Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2')
def pw(x, xs, ys): return np.interp(x, xs, ys)
def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): deep_merge(a[k], v)
        else: a[k] = v
    return a

DEF = dict(
    zone=dict(zlo=0.705, zhi=1.07, xmax=0.22),
    roof=dict(on=True, a0=0.022, a1=0.006, y0=-0.05, y1=0.065, wx0=0.012, wx1=0.080, za=0.700, zb=0.775, zh_front=0.835, zh_rear=0.90, zfade=0.04, yr0=0.058, yr1=0.076, f0=0.45, yf0=-0.19, yf1=-0.15),
    arch=dict(on=True, k=0.3, zroof=0.753, h=0.02, u0=0.012, u1=0.04, y0=-0.12, y1=0.07),
    fpinch=dict(on=True, k=0.5, z=[0.735, 0.755, 0.795, 0.82], y0=-0.19, y1=-0.12, y2=-0.07, y3=-0.04, u0=0.020, u1=0.040, u2=0.085, u3=0.115),
    fseam=dict(on=True, iters=80, zc=0.78, hz=0.02, u1=0.10, u2=0.14, y0=-0.20, y1=-0.08),
    cleft=dict(on=True, z=[0.76, 0.78, 0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92, 0.94, 0.96, 0.98], D=[12, 12, 13, 11, 8.5, 6, 4, 2.5, 1.3, 0.5, 0.1, 0.0], scale=1.6,
               u1=0.055, shape=0.25, zfade0=0.94, zfade1=1.0, zlo0=0.775, zlo1=0.785),
    lateral=dict(on=True, A=14.0, u0=0.15, su=0.035, z=[0.84, 0.875, 0.96, 1.0], margin=0.002),
    lateral_dn=dict(on=True, A=4.0, u0=0.15, su=0.035, z=[0.76, 0.775, 0.82, 0.85]),
    shelf=dict(on=True, iters=40, z=[0.895, 0.915, 0.965, 0.99], u1=0.17, u2=0.21),
    lumbar=dict(on=False, iters=120, z=[0.88, 0.93, 1.03, 1.07], u1=0.17, u2=0.215),
    pin=dict(on=True, z0=0.775, z1=0.98, gain=1.0, su=0.045),
    bias=dict(mm=0.0, z=[0.775, 0.80, 0.855, 0.885]),
    shelf2=dict(on=False, zref=0.90, z=[0.90, 0.918, 1.00, 1.03], u1=0.085, u2=0.125, ucols=[0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13]),
    trim=dict(on=True, z=[0.742, 0.752, 0.772, 0.785], tol=0.002, su=0.030, passes=2),
    crease=dict(on=True, A=10.0, z0=0.752, k=0.2, sz=0.016, fade_u=[0.035, 0.055, 0.12, 0.17]),
    seam=dict(on=True, iters=20, zc=0.776, hz=0.016, u1=0.215),
    gapsmooth=dict(on=True, iters=40, u1=0.05, u2=0.10, z0=0.72, z1=0.80),
    mound=dict(on=True, A=8.0, su=0.050, z=0.835, sz=0.038),
    smooth=dict(iters=3))

_hf = {}
def hf_rear():
    if 'g' not in _hf:
        f = W / 'data/hf_rear_start.npz'
        if f.exists(): d = np.load(f); _hf['g'] = hf.Grid(d['u'], d['z'], d['H'], 'rear')
        else:
            g = hf.build(V0, 'rear'); np.savez(f, u=g.u, z=g.z, H=g.H); _hf['g'] = g
    return _hf['g']

_pin = {}
BIAS = dict(mm=0.0, z=[0.775, 0.80, 0.855, 0.885])
def plate_target(z):
    base = _plate_target_raw(z)
    return base + BIAS['mm'] * 1e-3 * band(np.asarray(z, float), *BIAS['z'])
def _plate_target_raw(z):
    if 'zP' not in _pin:
        pl = json.load(open(W / 'data/plate_rear_subpx.json')); zP = np.array(pl['z'])
        L = np.array([np.nan if v is None else v for v in pl['left']], float); R = np.array([np.nan if v is None else v for v in pl['right']], float)
        m = np.nanmean(np.stack([L, R]), axis=0); ok = np.isfinite(m); m = np.interp(zP, zP[ok], m[ok]); k = 9
        _pin['zP'], _pin['m'] = zP, np.convolve(np.pad(m, k // 2, mode='edge'), np.ones(k) / k, 'valid')
    return np.interp(z, _pin['zP'], _pin['m'])

def ridge_u(z, g, lo=0.035, hi=0.075):
    """position of the lobe ridge (|x| of the max rear y) per z, from the start heightfield, smoothed"""
    us = np.arange(lo, hi + 1e-9, 0.0025); zz = np.asarray(z)
    out = np.zeros(len(zz))
    for i, zv in enumerate(zz):
        h = g.sample(us, np.full(len(us), zv)); out[i] = us[int(np.argmax(h))]
    k = 7; return np.convolve(np.pad(out, k // 2, mode='edge'), np.ones(k) / k, 'valid')

def build(P, verbose=False):
    BIAS['mm'] = float(P.get('bias', {}).get('mm', 0.0)); BIAS['z'] = list(P.get('bias', {}).get('z', [0.775, 0.80, 0.855, 0.885]))
    V = V0.copy().astype(np.float64); X, Y, Z = V0[:, 0], V0[:, 1], V0[:, 2]; U = np.abs(X); info = {}
    def rec(name, Vn):
        d = np.linalg.norm(Vn - V, axis=1) * 1000; info[name] = dict(moved=int((d > 1e-4).sum()), max_mm=float(d.max())); return Vn
    # ---------- roof (vertical grab with cos^2 falloff) ----------
    r = P['roof']
    if r['on']:
        Dy = r['a0'] + r['a1'] * smoothstep(r['y0'], r['y1'], Y)
        tt = np.clip((U - r['wx0']) / (r['wx1'] - r['wx0']), 0, 1); Wx = 0.5 * (1 + np.cos(np.pi * tt))
        Wlo = smoothstep(r['za'], r['zb'], Z)
        zh = r['zh_front'] + (r['zh_rear'] - r['zh_front']) * smoothstep(-0.05, 0.05, Y); Whi = 1 - smoothstep(zh - r['zfade'], zh, Z)
        Wyr = 1 - smoothstep(r['yr0'], r['yr1'], Y); Wyf = r['f0'] + (1 - r['f0']) * smoothstep(r['yf0'], r['yf1'], Y)
        V2 = V.copy(); V2[:, 2] += -Dy * Wx * Wlo * Whi * Wyr * Wyf; V = rec('roof', V2)
    # ---------- arch pinch ----------
    ar = P['arch']
    if ar['on']:
        Zc = V[:, 2]; Uc = np.abs(V[:, 0]); zr = ar['zroof']
        wz = smoothstep(zr - ar['h'], zr, Zc) * (1 - smoothstep(zr, zr + 0.012, Zc)); wx = 1 - smoothstep(ar['u0'], ar['u1'], Uc)
        wy = (1 - smoothstep(ar['y1'], ar['y1'] + 0.03, V[:, 1])) * smoothstep(ar['y0'] - 0.03, ar['y0'], V[:, 1])
        V2 = V.copy(); V2[:, 0] = V[:, 0] * (1 - ar['k'] * wz * wx * wy); V = rec('arch', V2)
    # ---------- front pinch: pull the inner-front thigh walls toward the centre line (narrows the front mouth of the gap) ----------
    fp = P['fpinch']
    if fp['on']:
        Zc = V[:, 2]; Uc = np.abs(V[:, 0]); Yc = V[:, 1]
        wz = band(Zc, *fp['z']); wy = smoothstep(fp['y0'], fp['y1'], Yc) * (1 - smoothstep(fp['y2'], fp['y3'], Yc)); wx = smoothstep(fp['u0'], fp['u1'], Uc) * (1 - smoothstep(fp['u2'], fp['u3'], Uc))
        V2 = V.copy(); V2[:, 0] = V[:, 0] * (1 - fp['k'] * wz * wy * wx); V = rec('fpinch', V2)
    # ---------- cleft: explicit target valley between the lobe ridges ----------
    c = P['cleft']
    if c['on']:
        g = hf_rear(); zs = np.arange(0.74, 1.0001, 0.005); u1z = ridge_u(zs, g) if c.get('u1') is None else np.full(len(zs), c['u1'])
        Nc = vnormals(V); wrc = smoothstep(0.10, 0.50, Nc[:, 1]); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        u1 = np.interp(Zc, zs, u1z)
        Yl = g.sample(np.clip(u1, g.u[0], g.u[-1]), Zc)                       # lobe ridge level of the START surface at this height
        D = pw(Zc, c['z'], c['D']) * 1e-3 * c.get('scale', 1.0)
        rr = np.clip(Uc / np.maximum(u1, 1e-4), 0, 1)
        # valley profile: phi(0)=1, phi(1)=0, phi'(1)=0.  shape blends a smooth bowl (bowl) with a sharper V-ish (vee)
        bowl = (1 - rr ** 2) ** 2; vee = (1 - rr) ** 2 * (1 + rr) ; sh = c.get('shape', 0.5); phi = (1 - sh) * bowl + sh * vee
        yt = Yl - D * phi
        w_u = 1 - smoothstep(0.0, 0.008, Uc - u1)                                           # replace the surface for u < u1, hand over to the old surface right after the ridge
        w_z = smoothstep(c['zlo0'], c['zlo1'], Zc) * (1 - smoothstep(c['zfade0'], c['zfade1'], Zc))
        dy = (yt - V[:, 1]) * w_u * w_z * wrc
        V2 = V.copy(); V2[:, 1] += dy; V = rec('cleft', V2)
    # ---------- upper shelf / M-dip smoothing (z 0.90-1.0): removes the +5 deg pitch hump and the row ripples ----------
    sf = P['shelf']
    if sf['on']:
        Uc = np.abs(V[:, 0]); Zc = V[:, 2]; w = band(Zc, *sf['z']) * (1 - smoothstep(sf['u1'], sf['u2'], Uc))
        V = rec('shelf', taubin(V, w, iters=sf['iters']))
    lb = P['lumbar']
    if lb['on']:
        Uc = np.abs(V[:, 0]); Zc = V[:, 2]; w = band(Zc, *lb['z']) * (1 - smoothstep(lb['u1'], lb['u2'], Uc))
        V = rec('lumbar', taubin(V, w, iters=lb['iters']))
    # ---------- lateral fullness (headroom under the plate contour) ----------
    lt = P['lateral']
    if lt['on']:
        Nc = vnormals(V); wrc = smoothstep(0.10, 0.50, Nc[:, 1]); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        shape = lt['A'] * 1e-3 * np.exp(-0.5 * ((Uc - lt['u0']) / lt['su']) ** 2) * band(Zc, *lt['z'])
        cap = np.maximum(plate_target(Zc) - lt.get('margin', 0.002) - V[:, 1], 0.0)
        V2 = V.copy(); V2[:, 1] += np.minimum(shape, cap) * wrc; V = rec('lateral', V2)
    ld = P['lateral_dn']
    if ld['on']:
        Nc = vnormals(V); wrc = smoothstep(0.10, 0.50, Nc[:, 1]); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        V2 = V.copy(); V2[:, 1] -= ld['A'] * 1e-3 * np.exp(-0.5 * ((Uc - ld['u0']) / ld['su']) ** 2) * band(Zc, *ld['z']) * wrc; V = rec('lateral_dn', V2)
    # ---------- pin the extreme rear contour at the lobe columns ----------
    pn = P['pin']
    if pn['on']: V = rec('pin', pin_contour(V, pn))
    s2 = P['shelf2']
    if s2['on']:
        from common import rear_curve
        uc = np.array(s2['ucols']); yr = np.zeros(len(uc))
        for i, u in enumerate(uc):
            a_ = rear_curve(V, u + 1e-6, np.array([s2['zref']]))[0]; b_ = rear_curve(V, -u - 1e-6, np.array([s2['zref']]))[0]; yr[i] = np.nanmean([a_, b_])
        Nc = vnormals(V); wrc = smoothstep(0.10, 0.50, Nc[:, 1]); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        Pz = plate_target(Zc) - plate_target(s2['zref'])                           # contour drop relative to the reference height (negative above)
        yt = np.interp(Uc, uc, yr) + Pz
        w = (1 - smoothstep(s2['u1'], s2['u2'], Uc)) * band(Zc, *s2['z']) * wrc
        dyt = np.clip(yt - V[:, 1], -s2.get('cap', 0.003), s2.get('cap', 0.003)); V2 = V.copy(); V2[:, 1] += dyt * w; V = rec('shelf2', V2)
    tm = P['trim']
    if tm['on']:
        for _ in range(tm.get('passes', 1)): V = rec('trim', trim_contour(V, tm))
    # ---------- crease ----------
    cr = P['crease']
    if cr['on']:
        Nc = vnormals(V); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        zf = cr['z0'] + cr['k'] * Uc; wu = band(Uc, *cr['fade_u']); psi = np.exp(-0.5 * ((Zc - zf) / cr['sz']) ** 2) * wu
        wdir = np.clip(Nc[:, 1] * 0.5 - Nc[:, 2] * 0.8 + 0.2, 0, 1)
        V2 = V.copy(); V2 += -(cr['A'] * 1e-3) * (psi * wdir)[:, None] * Nc; V = rec('crease', V2)
    # ---------- front mound ----------
    m = P['mound']
    if m['on']:
        Nc = vnormals(V); wfc = smoothstep(0.10, 0.50, -Nc[:, 1]); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        bump = np.exp(-0.5 * (Uc / m['su']) ** 2) * np.exp(-0.5 * ((Zc - m['z']) / m['sz']) ** 2)
        V2 = V.copy(); V2[:, 1] -= m['A'] * 1e-3 * bump * wfc; V = rec('mound', V2)
    # ---------- seam (leg-top ring) + keyhole neighbourhood smoothing ----------
    sm = P['seam']
    if sm['on']:
        Uc = np.abs(V[:, 0]); Zc = V[:, 2]; w = np.exp(-0.5 * ((Zc - sm['zc']) / sm['hz']) ** 2) * (1 - smoothstep(sm['u1'] - 0.03, sm['u1'], Uc))
        V = rec('seam', taubin(V, w, iters=sm['iters']))
    fs = P['fseam']
    if fs['on']:
        Uc = np.abs(V[:, 0]); Zc = V[:, 2]; Yc = V[:, 1]
        w = np.exp(-0.5 * ((Zc - fs['zc']) / fs['hz']) ** 2) * (1 - smoothstep(fs['u1'], fs['u2'], Uc)) * smoothstep(fs['y0'], fs['y0'] + 0.03, Yc) * (1 - smoothstep(fs['y1'], fs['y1'] + 0.04, Yc))
        V = rec('fseam', taubin(V, w, iters=fs['iters']))
    gs = P['gapsmooth']
    if gs['on']:
        Uc = np.abs(V[:, 0]); Zc = V[:, 2]; w = (1 - smoothstep(gs['u1'], gs['u2'], Uc)) * band(Zc, gs['z0'] - 0.01, gs['z0'], gs['z1'], gs['z1'] + 0.02)
        V = rec('gapsmooth', taubin(V, w, iters=gs['iters']))
    # ---------- displacement-field smoothing ----------
    ds = P['smooth']
    if ds['iters'] > 0:
        D_ = V - V0; idx_, cnt_ = __import__('sculpt')._lap_ops()
        for _ in range(ds['iters']):
            Pm = np.vstack([D_, np.zeros((1, 3))]); nb = Pm[idx_].sum(1) / cnt_[:, None]; mv = (np.abs(D_).sum(1) > 0) | (np.abs(nb).sum(1) > 1e-12)
            D_ = np.where(mv[:, None], D_ + 0.5 * (nb - D_), D_)
        V = V0 + D_
    zn = P['zone']; IN = (Z >= zn['zlo']) & (Z <= zn['zhi']) & (U <= zn['xmax'])
    V = V0 + np.where(IN[:, None], V - V0, 0.0)
    return V, info

def rear_max_columns(V, zs, cols=(0.03, 0.04, 0.05, 0.06, 0.07, 0.085, 0.10, 0.12)):
    """continuous (section based) rear contour: for each z the max over a set of |x| columns of the rear-most y (mean of +x / -x), and the column where it occurs"""
    from common import rear_curve
    A = np.full((len(cols), len(zs)), np.nan)
    for i, x in enumerate(cols):
        a_ = rear_curve(V, x + 1e-6, zs); b_ = rear_curve(V, -x - 1e-6, zs); A[i] = np.nanmean(np.stack([a_, b_]), axis=0)
    ok = np.isfinite(A).any(axis=0); m = np.full(len(zs), np.nan); u = np.zeros(len(zs))
    m[ok] = np.nanmax(A[:, ok], axis=0); u[ok] = np.array(cols)[np.nanargmax(np.where(np.isfinite(A[:, ok]), A[:, ok], -9), axis=0)]
    return m, u
def trim_contour(V, tr):
    """one-sided: reduce the extreme rear contour where it overshoots the plate contour (+tol) at the lower lobe / keyhole lip, gaussian around the offending column"""
    zs = np.arange(tr['z'][0], tr['z'][3] + 1e-9, 0.004); m1, um = rear_max_columns(V, zs, cols=(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.085, 0.10)); mT = plate_target(zs); ok = np.isfinite(m1)
    Fz = np.zeros(len(zs)); Fz[ok] = np.minimum(0.0, mT[ok] + tr['tol'] - m1[ok]) * band(zs[ok] if False else zs, *tr['z'])[ok] if ok.any() else 0
    def sm(a, k=3): a = np.where(np.isfinite(a), a, 0); return np.convolve(np.pad(a, k // 2, mode='edge'), np.ones(k) / k, 'valid')
    Fz = sm(Fz, 3); um = sm(np.where(ok, um, 0.03), 3)
    Nc = vnormals(V); wrc = smoothstep(0.10, 0.50, Nc[:, 1]); U = np.abs(V[:, 0]); Z = V[:, 2]
    phi = np.exp(-0.5 * ((U - np.interp(Z, zs, um)) / tr['su']) ** 2); V2 = V.copy(); V2[:, 1] += np.interp(Z, zs, Fz) * phi * wrc; return V2
def pin_contour(V, pn):
    zs = np.arange(pn['z0'] - 0.01, pn['z1'] + 0.016, 0.004); m1, um = rear_max_columns(V, zs); mT = plate_target(zs); ok = np.isfinite(m1)
    Fz = np.zeros(len(zs)); Fz[ok] = pn['gain'] * (mT[ok] - m1[ok]); Fz = Fz * band(zs, pn['z0'] - 0.01, pn['z0'], pn['z1'] - 0.03, pn['z1'] + 0.005)
    def sm(a, k=5): a = np.where(np.isfinite(a), a, 0); return np.convolve(np.pad(a, k // 2, mode='edge'), np.ones(k) / k, 'valid')
    Fz = sm(Fz, 3); um = sm(np.where(ok, um, 0.055), 5)
    Nc = vnormals(V); wrc = smoothstep(0.10, 0.50, Nc[:, 1]); U = np.abs(V[:, 0]); Z = V[:, 2]
    phi = np.exp(-0.5 * ((U - np.interp(Z, zs, um)) / pn['su']) ** 2); V2 = V.copy(); V2[:, 1] += np.interp(Z, zs, Fz) * phi * wrc; return V2

if __name__ == '__main__':
    P = json.loads(json.dumps(DEF)); tag = sys.argv[2]
    if sys.argv[1] != '-': deep_merge(P, json.load(open(sys.argv[1])))
    V, info = build(P); d = V - V0; mv = np.linalg.norm(d, axis=1)
    print(tag, 'moved', int((mv > 1e-7).sum()), 'max mm', (mv.max() * 1000).round(2), 'max|dx|,|dy|,|dz| mm', [float((np.abs(d[:, k]).max() * 1000).round(2)) for k in range(3)])
    for k, v in info.items(): print('  ', k, v)
    np.save(f'data/V_{tag}.npy', V); json.dump(P, open(f'data/P_{tag}.json', 'w'), indent=1)
