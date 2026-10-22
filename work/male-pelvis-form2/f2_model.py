"""MALE PELVIS FORM2 sculpt model (butt + groin).  Positions only; topology untouched.
python3 f2_model.py <params.json|-> <tag>      -> data/V_<tag>.npy, data/P_<tag>.json, stats on stdout
Terms (applied in this order, each is a smooth displacement field evaluated on the CURRENT positions):
  roof   : vertical grab - lowers the crotch roof / lobe inner-underside / cleft bottom near the centre line (|x| small), tilted front->rear
  fill   : masked Taubin smoothing of the rear cleft zone (kills the flat-floored trench and the ring seam)
  cleft  : V-groove carve (y displacement of rear-facing surface), depth schedule D(z), width s(z)
  crease : soft concave band under the lobes (normal displacement) following z_f(|x|)
  mound  : front mound (+forward) and soft inguinal V carve
  seam   : masked Taubin of the leg-top ring band
  pin    : re-pins the extreme rear contour to the plate's sub-pixel side contour (as chat-9 did, but z-limited)
"""
import sys, json
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2')
from common import V0, F, N0, neighbors, vnormals, GROUPS
from sculpt import smoothstep, band, taubin, taubin_scalar, diffuse_scalar, laplacian, gauss

W = __import__('pathlib').Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2')
def pw(x, xs, ys): return np.interp(x, xs, ys)
def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): deep_merge(a[k], v)
        else: a[k] = v
    return a

DEF = dict(
    zone=dict(zlo=0.705, zhi=1.07, xmax=0.22),
    roof=dict(on=True, a0=0.014, a1=0.010, y0=-0.05, y1=0.065, wx0=0.025, wx1=0.062, za=0.715, zb=0.765, zh_front=0.835, zh_rear=0.88, zfade=0.04),
    fill=dict(on=True, iters=40, u0=0.050, u1=0.085, z=[0.765, 0.785, 0.93, 0.96]),
    cleft=dict(on=True, z=[0.74, 0.76, 0.78, 0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.93],
               D=[22.0, 22.0, 22.0, 21.0, 17.0, 11.0, 7.0, 3.5, 1.5, 0.0], s=[0.012, 0.012, 0.013, 0.015, 0.016, 0.018, 0.020, 0.022, 0.024, 0.026], p=1.0),
    crease=dict(on=False, A=5.0, z0=0.757, k=0.17, sz=0.008, u0=0.02, u1=0.15, fade_u=[0.015, 0.03, 0.11, 0.16]),
    mound=dict(on=True, A=7.0, su=0.050, z=0.835, sz=0.038, vA=3.0),
    seam=dict(on=True, iters=12, zc=0.776, hz=0.014, u1=0.215),
    pin=dict(on=True, z0=0.775, z1=0.95, gain=1.0, su=0.045, sm=0.004),
    smooth=dict(iters=3))

def build(P, verbose=True):
    V = V0.copy().astype(np.float64); X, Y, Z = V0[:, 0], V0[:, 1], V0[:, 2]; U = np.abs(X)
    N = vnormals(V0); ny = N[:, 1]; wr = smoothstep(0.10, 0.50, ny); wf = smoothstep(0.10, 0.50, -ny); info = {}
    def rec(name, Vn):
        d = np.linalg.norm(Vn - V, axis=1) * 1000; info[name] = dict(moved=int((d > 1e-4).sum()), max_mm=float(d.max()))
        return Vn
    # ---- roof (vertical grab) ----
    r = P['roof']
    if r['on']:
        Dy = r['a0'] + r['a1'] * smoothstep(r['y0'], r['y1'], Y)
        tt = np.clip((U - r['wx0']) / (r['wx1'] - r['wx0']), 0, 1); Wx = 0.5 * (1 + np.cos(np.pi * tt))
        Wlo = smoothstep(r['za'], r['zb'], Z)
        zh = r['zh_front'] + (r['zh_rear'] - r['zh_front']) * smoothstep(-0.05, 0.05, Y)
        Whi = 1 - smoothstep(zh - r['zfade'], zh, Z)
        Wyr = 1 - smoothstep(r.get('yr0', 0.066), r.get('yr1', 0.088), Y)                 # do not drag the lobe flanks (y > ~66 mm) down
        Wyf = r.get('f0', 0.45) + (1 - r.get('f0', 0.45)) * smoothstep(r.get('yf0', -0.19), r.get('yf1', -0.15), Y)
        dz = -Dy * Wx * Wlo * Whi * Wyr * Wyf
        V2 = V.copy(); V2[:, 2] += dz; V = rec('roof', V2)
    # ---- arch pinch (narrow the keyhole top: pull the inner-thigh walls toward the centre line, strongest near the roof) ----
    ar = P.get('arch', dict(on=False))
    if ar['on']:
        Zc = V[:, 2]; Uc = np.abs(V[:, 0])
        zr = ar['zroof']                                                  # approximate new roof height
        wz = smoothstep(zr - ar['h'], zr, Zc) * (1 - smoothstep(zr, zr + 0.012, Zc))
        wx = 1 - smoothstep(ar['u0'], ar['u1'], Uc); wy = (1 - smoothstep(ar['y1'], ar['y1'] + 0.03, V[:, 1])) * smoothstep(ar['y0'] - 0.03, ar['y0'], V[:, 1])
        V2 = V.copy(); V2[:, 0] = V[:, 0] * (1 - ar['k'] * wz * wx * wy); V = rec('arch', V2)
    # ---- fill (smooth the rear cleft zone) ----
    f = P['fill']
    if f['on']:
        Nc = vnormals(V); wrc = smoothstep(0.10, 0.50, Nc[:, 1]); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        w = (1 - smoothstep(f['u0'], f['u1'], Uc)) * band(Zc, *f['z']) * wrc
        V = rec('fill', taubin(V, w, iters=f['iters']))
    # ---- lateral lobe fullness (headroom below the plate's extreme rear contour) ----
    lt = P.get('lateral', dict(on=False))
    if lt['on']:
        Nc = vnormals(V); wrc = smoothstep(0.10, 0.50, Nc[:, 1]); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        shape = lt['A'] * 1e-3 * np.exp(-0.5 * ((Uc - lt['u0']) / lt['su']) ** 2) * band(Zc, *lt['z'])
        cap = np.maximum(plate_target(Zc) - lt.get('margin', 0.002) - V[:, 1], 0.0)
        dy = np.minimum(shape, cap); V2 = V.copy(); V2[:, 1] += dy * wrc; V = rec('lateral', V2)
    # ---- pin the extreme rear contour (before the carving terms, which live off the apex columns) ----
    pn = P['pin']
    if pn['on']:
        V = rec('pin', pin_contour(V, pn))
    # ---- cleft V carve ----
    c = P['cleft']
    if c['on']:
        Nc = vnormals(V); wrc = smoothstep(0.10, 0.50, Nc[:, 1]); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        D = pw(Zc, c['z'], c['D']) * 1e-3; s = pw(Zc, c['z'], c['s'])
        if 'shape' in c: sh = c['shape']; g = (1 - sh) * np.exp(-0.5 * (Uc / s) ** 2) + sh / (1.0 + (Uc / s) ** 2)
        else: g = 1.0 / (1.0 + (Uc / s) ** 2) ** c['p'] if c['p'] != 0 else np.exp(-0.5 * (Uc / s) ** 2)
        g = g * (1 - smoothstep(c.get('t0', 0.035), c.get('t1', 0.075), Uc))
        V2 = V.copy(); V2[:, 1] -= D * g * wrc; V = rec('cleft', V2)
    # ---- crease ----
    cr = P['crease']
    if cr['on']:
        Nc = vnormals(V); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        zf = cr['z0'] + cr['k'] * Uc; wu = band(Uc, *cr['fade_u']); psi = np.exp(-0.5 * ((Zc - zf) / cr['sz']) ** 2) * wu
        wdir = np.clip(Nc[:, 1] * 0.5 - Nc[:, 2] * 0.8 + 0.2, 0, 1)      # rear or down facing
        V2 = V.copy(); V2 += -(cr['A'] * 1e-3) * (psi * wdir)[:, None] * Nc; V = rec('crease', V2)
    # ---- mound (front) ----
    m = P['mound']
    if m['on']:
        Nc = vnormals(V); wfc = smoothstep(0.10, 0.50, -Nc[:, 1]); Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        bump = np.exp(-0.5 * (Uc / m['su']) ** 2) * np.exp(-0.5 * ((Zc - m['z']) / m['sz']) ** 2)
        V2 = V.copy(); V2[:, 1] -= m['A'] * 1e-3 * bump * wfc; V = rec('mound', V2)
    # ---- seam (leg-top ring band) ----
    sm = P['seam']
    if sm['on']:
        Uc = np.abs(V[:, 0]); Zc = V[:, 2]
        w = np.exp(-0.5 * ((Zc - sm['zc']) / sm['hz']) ** 2) * (1 - smoothstep(sm['u1'] - 0.03, sm['u1'], Uc))
        V = rec('seam', taubin(V, w, iters=sm['iters']))
    # ---- final light smoothing of the displacement (not the surface) ----
    ds = P['smooth']
    if ds['iters'] > 0:
        D = V - V0; idx_, cnt_ = __import__('sculpt')._lap_ops()
        for _ in range(ds['iters']):
            Pm = np.vstack([D, np.zeros((1, 3))]); nb = Pm[idx_].sum(1) / cnt_[:, None]; mv = (np.abs(D).sum(1) > 0) | (np.abs(nb).sum(1) > 1e-12)
            D = np.where(mv[:, None], D + 0.5 * (nb - D), D)
        V = V0 + D
    # ---- zone mask ----
    zn = P['zone']; IN = (Z >= zn['zlo']) & (Z <= zn['zhi']) & (U <= zn['xmax'])
    Dfin = np.where(IN[:, None], V - V0, 0.0); V = V0 + Dfin
    return V, info

_pin_cache = {}
def plate_target(z):
    """plate extreme rear contour (m): mean of left/right sub-pixel contours, lightly smoothed"""
    if 'zP' not in _pin_cache:
        pl = json.load(open(W / 'data/plate_rear_subpx.json')); zP = np.array(pl['z'])
        L = np.array([np.nan if v is None else v for v in pl['left']], float); R = np.array([np.nan if v is None else v for v in pl['right']], float)
        m = np.nanmean(np.stack([L, R]), axis=0); ok = np.isfinite(m); m = np.interp(zP, zP[ok], m[ok])
        k = 9; ker = np.ones(k) / k; ms = np.convolve(np.pad(m, k // 2, mode='edge'), ker, 'valid')
        _pin_cache['zP'], _pin_cache['m'] = zP, ms
    return np.interp(z, _pin_cache['zP'], _pin_cache['m'])

def rear_max_columns(V, zs, umin=0.02, umax=0.15):
    """for each z: max over |x| in [umin, umax] of the rear-most y (using section_x on both sides) and the |x| where it occurs"""
    import common
    saved = common.V0
    out_m = np.zeros(len(zs)); out_u = np.zeros(len(zs))
    # fast estimate from vertices: bin rear-facing vertices by z (+-1.5 mm) and take the max y with |x| in range
    Nc = vnormals(V); wr = Nc[:, 1] > 0.2; U = np.abs(V[:, 0]); sel = wr & (U >= umin) & (U <= umax)
    for i, z in enumerate(zs):
        m = sel & (np.abs(V[:, 2] - z) < 0.0035)
        if m.sum() == 0: out_m[i] = np.nan; continue
        j = np.where(m)[0][np.argmax(V[m, 1])]; out_m[i] = V[j, 1]; out_u[i] = U[j]
    return out_m, out_u

def pin_contour(V, pn):
    zs = np.arange(pn['z0'] - 0.01, pn['z1'] + 0.011, 0.004)
    m1, um = rear_max_columns(V, zs)
    mT = plate_target(zs); ok = np.isfinite(m1)
    F = np.zeros(len(zs)); F[ok] = pn['gain'] * (mT[ok] - m1[ok])
    wz = band(zs, pn['z0'] - 0.01, pn['z0'], pn['z1'] - 0.03, pn['z1']); F = F * wz
    # smooth F and um along z
    def sm(a, k=5):
        a = np.where(np.isfinite(a), a, 0); return np.convolve(np.pad(a, k // 2, mode='edge'), np.ones(k) / k, 'valid')
    F = sm(F, 5); um = sm(np.where(ok, um, 0.055), 5)
    Nc = vnormals(V); wrc = smoothstep(0.10, 0.50, Nc[:, 1]); U = np.abs(V[:, 0]); Z = V[:, 2]
    Fz = np.interp(Z, zs, F); uz = np.interp(Z, zs, um)
    phi = np.exp(-0.5 * ((U - uz) / pn['su']) ** 2)
    V2 = V.copy(); V2[:, 1] += Fz * phi * wrc
    return V2

if __name__ == '__main__':
    P = json.loads(json.dumps(DEF)); tag = sys.argv[2]
    if sys.argv[1] != '-': deep_merge(P, json.load(open(sys.argv[1])))
    V, info = build(P); d = V - V0; mv = np.linalg.norm(d, axis=1)
    print(tag, 'moved', int((mv > 1e-7).sum()), 'max mm', (mv.max() * 1000).round(2), 'max|dx|,|dy|,|dz| mm', [(np.abs(d[:, k]).max() * 1000).round(2) for k in range(3)])
    for k, v in info.items(): print('  ', k, v)
    np.save(f'data/V_{tag}.npy', V); json.dump(P, open(f'data/P_{tag}.json', 'w'), indent=1)
