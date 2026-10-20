"""Nape + pelvis model v4: heightfield terms + side-silhouette pinning (rear), front groin terms, nape hump removal.
python3.13 np_model4.py <params.json|-> <tag>   -> data/V_<tag>.npy, data/P_<tag>.json
Displacement is along world Y only (x,z bit-identical -> front/back silhouettes unchanged by construction)."""
import sys, json
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin')
from sculpt import *
import hf
from hf import Grid

def pw(x, xs, ys): return np.interp(x, xs, ys)
def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): deep_merge(a[k], v)
        else: a[k] = v
    return a

DEF = dict(
    nape=dict(on=True, z=[1.34, 1.36, 1.37, 1.38, 1.39, 1.40, 1.41, 1.42, 1.43, 1.44, 1.45, 1.46, 1.47],
              d=[0.0, -1.0, -3.0, -7.0, -12.0, -16.0, -16.0, -13.0, -9.0, -5.0, -2.0, -0.5, 0.0], sx=0.075, xcut=0.14),
    rear=dict(on=True, zlo0=0.762, zlo1=0.776, zhi0=1.00, zhi1=1.05, xe0=0.155, xe1=0.205,
              blur=dict(sig=0.010, w=[0.765, 0.78, 0.83, 0.90], zc_u=[0.0, 0.05, 0.07, 0.09], zc_v=[0.776, 0.776, 0.765, 0.70]),
              s_u=[0.0, 0.03, 0.06, 0.09, 0.12, 0.15, 0.21], s_v=[0.0, 0.0, 0.0, 0.006, 0.014, 0.022, 0.022], B=[0.745, 0.775, 0.84, 0.93],
              cleft=dict(z=[0.776, 0.79, 0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92, 0.96], C=[8.0, 13.0, 16.0, 17.0, 15.0, 12.0, 8.0, 4.0, 1.0, 0.0], s0=0.020, s1=0.013),
              pin=dict(on=True, gain=1.0, zw=[0.770, 0.782, 1.02, 1.05], su=0.05, zfill=0.81, file='data/D_sil_start.json', ushape=[0.035, 0.065, 0.14, 0.17])),
    front=dict(on=True, zlo0=0.768, zlo1=0.778, zhi0=0.92, zhi1=0.98, xe0=0.17, xe1=0.21,
               blur=dict(sig=0.010, w=[0.768, 0.78, 0.82, 0.88], zc_u=[0.0, 0.035, 0.06, 0.09], zc_v=[0.777, 0.777, 0.765, 0.70]),
               mound=dict(A=5.0, su=0.045, z=0.822, sz=0.032),
               groove=dict(A=4.0, sig=0.011, p0=[0.175, 0.885], p1=[0.045, 0.797])),
    smooth=dict(iters=4, zlo=0.76, zhi=1.07, zlo_n=1.30, zhi_n=1.50, iters_n=3))

_grids = {}
def grids():
    if 'rear' not in _grids:
        _grids['rear'] = hf.build(V0, 'rear'); _grids['front'] = hf.build(V0, 'front')
    return _grids

def masked_blur_z(grid, sigma, zceil_fn):
    H = grid.H; z = grid.z; dz = z[1] - z[0]; out = H.copy(); k = int(np.ceil(3 * sigma / dz)); t = np.arange(-k, k + 1) * dz; w = np.exp(-0.5 * (t / sigma) ** 2)
    for i, u in enumerate(grid.u):
        m = (z >= zceil_fn(u)).astype(float); f = H[i] * m
        num = np.convolve(np.pad(f, k, mode='edge'), w, mode='valid'); den = np.convolve(np.pad(m, k, mode='constant'), w, mode='valid')
        ok = den > 1e-6; out[i, ok] = num[ok] / den[ok]
    return Grid(grid.u, grid.z, out, grid.name + '_blur')

def bump(z, B): return smoothstep(B[0], B[1], z) * (1 - smoothstep(B[2], B[3], z))
def seg_dist(U, Zc, p0, p1):
    p0 = np.array(p0); p1 = np.array(p1); d = p1 - p0; L2 = d @ d
    t = np.clip(((U - p0[0]) * d[0] + (Zc - p0[1]) * d[1]) / L2, 0, 1)
    return np.hypot(U - (p0[0] + t * d[0]), Zc - (p0[1] + t * d[1])), t

class Rear:
    """terms(U,Z) -> displacement (metres) of the rear surface before zone/normal weights; pin() adds the silhouette-pinning correction"""
    def __init__(self, P, G):
        self.P = P; self.Hr = G['rear']; r = P['rear']; bl = r['blur']
        self.Hs = masked_blur_z(self.Hr, bl['sig'], lambda u: np.interp(u, bl['zc_u'], bl['zc_v'])) if bl['sig'] > 0 else self.Hr
        self.pin_F = None
    def zone(self, U, Z):
        r = self.P['rear']; return band(Z, r['zlo0'], r['zlo1'], r['zhi0'], r['zhi1']) * (1 - smoothstep(r['xe0'], r['xe1'], U))
    def terms(self, U, Z):
        r = self.P['rear']; bl = r['blur']; H0 = self.Hr.sample(U, Z); Hs = self.Hs.sample(U, Z)
        wb = band(Z, bl['w'][0], bl['w'][1], bl['w'][2], bl['w'][3]); T = wb * (Hs - H0)
        s = pw(U, r['s_u'], r['s_v']); Bz = bump(Z, r['B'])
        T = T + (self.Hs.sample(U, Z - s * Bz) - Hs)
        c = r['cleft']; Cd = pw(Z, c['z'], c['C']) * 1e-3; sc = c['s0'] + (c['s1'] - c['s0']) * smoothstep(0.82, 0.92, Z)
        T = T - Cd * np.exp(-0.5 * (U / sc) ** 2)
        return T
    def prepare_pin(self):
        r = self.P['rear']; pn = r['pin']
        if not pn['on']: return
        D = json.load(open(W / pn['file'])); zD = np.array(D['z']); DD = np.array(D['D'])
        g = self.Hr; Ug, Zg = np.meshgrid(g.u, g.z, indexing='ij')
        H1 = g.H + self.zone(Ug, Zg) * self.terms(Ug, Zg)
        sel = (g.u >= 0.02) & (g.u <= 0.15)                   # lobe / thigh columns (cleft columns excluded from the max search)
        Hm = H1[sel]; um = g.u[sel][np.argmax(Hm, axis=0)]; m1 = Hm.max(axis=0)
        m0 = g.H[sel].max(axis=0); mT = m0 + pn['gain'] * np.interp(g.z, zD, DD)
        wz = band(g.z, *pn['zw']); F = wz * (mT - m1)
        self.pin = dict(z=g.z, F=F, um=np.convolve(np.pad(um, 6, mode='edge'), np.ones(13) / 13, mode='valid'), m1=m1, mT=mT, m0=m0)
    def pin_term(self, U, Z):
        if self.pin is None if hasattr(self, 'pin') else True: return 0.0 * U
        r = self.P['rear']['pin']; p = self.pin; F = np.interp(Z, p['z'], p['F']); um = np.interp(Z, p['z'], p['um'])
        phi_g = np.exp(-0.5 * ((U - um) / r['su']) ** 2); phi_b = band(U, *r['ushape'])
        a = 1 - smoothstep(r['zfill'] - 0.008, r['zfill'] + 0.008, Z)      # underside (fill) uses the broad window; the upper part follows the max column
        return F * (a * phi_b + (1 - a) * phi_g)

W = __import__('pathlib').Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin')

def build(P):
    V = V0.copy(); X, Y, Z = V0[:, 0], V0[:, 1], V0[:, 2]; U = np.abs(X)
    N = vnormals(V0); ny = N[:, 1]; wr = smoothstep(0.10, 0.50, ny); wf = smoothstep(0.10, 0.50, -ny)
    dY = np.zeros(N0); G = grids(); info = {}
    n = P['nape']
    if n['on']:
        inz = (Z >= n['z'][0]) & (Z <= n['z'][-1]) & (U <= n['xcut']); d = pw(Z, n['z'], n['d']) * 1e-3
        dY += np.where(inz, wr * np.exp(-0.5 * (U / n['sx']) ** 2) * (1 - smoothstep(n['xcut'] - 0.04, n['xcut'], U)) * d, 0.0)
    r = P['rear']
    if r['on']:
        R = Rear(P, G); R.pin = None; R.prepare_pin()
        Tv = R.terms(U, Z) + R.pin_term(U, Z); dY += wr * R.zone(U, Z) * Tv
        info['pin'] = {k: np.asarray(v).tolist() for k, v in (R.pin or {}).items()} if R.pin else None
    f = P['front']
    if f['on']:
        Hf = G['front']; bl = f['blur']; Hs = masked_blur_z(Hf, bl['sig'], lambda u: np.interp(u, bl['zc_u'], bl['zc_v'])) if bl['sig'] > 0 else Hf
        H0 = Hf.sample(U, Z); wb = band(Z, bl['w'][0], bl['w'][1], bl['w'][2], bl['w'][3]); T = wb * (Hs.sample(U, Z) - H0)
        m = f['mound']; T = T - m['A'] * 1e-3 * np.exp(-0.5 * (U / m['su']) ** 2) * np.exp(-0.5 * ((Z - m['z']) / m['sz']) ** 2)
        g = f['groove']; dist, t = seg_dist(U, Z, g['p0'], g['p1']); T = T + g['A'] * 1e-3 * np.exp(-0.5 * (dist / g['sig']) ** 2) * smoothstep(0.0, 0.15, t) * (1 - smoothstep(0.85, 1.0, t))
        Mz = band(Z, f['zlo0'], f['zlo1'], f['zhi0'], f['zhi1']); Mx = 1 - smoothstep(f['xe0'], f['xe1'], U); dY += wf * Mz * Mx * T
    V[:, 1] = V0[:, 1] + dY
    s = P['smooth']
    if s['iters'] > 0:
        moved = (np.abs(dY) > 1e-6).astype(float); w = np.clip(diffuse_scalar(moved, np.ones(N0), iters=3, lam=0.5) * 1.2, 0, 1)
        w_p = w * band(Z, s['zlo'] - 0.006, s['zlo'], s['zhi'], s['zhi'] + 0.02); w_n = w * band(Z, s['zlo_n'] - 0.01, s['zlo_n'], s['zhi_n'], s['zhi_n'] + 0.02)
        V[:, 1] = taubin_scalar(V[:, 1], w_p, iters=s['iters']); V[:, 1] = taubin_scalar(V[:, 1], w_n, iters=s['iters_n'])
    return V, info

if __name__ == '__main__':
    P = json.loads(json.dumps(DEF)); tag = sys.argv[2]
    if sys.argv[1] != '-': deep_merge(P, json.load(open(sys.argv[1])))
    V, info = build(P); d = V - V0; mv = np.linalg.norm(d, axis=1)
    print(tag, 'moved', int((mv > 1e-7).sum()), 'max mm', (mv.max() * 1000).round(2), 'dy range mm', (d[:, 1].min() * 1000).round(2), (d[:, 1].max() * 1000).round(2),
          'max|dx|,|dz| mm', (np.abs(d[:, 0]).max() * 1000).round(3), (np.abs(d[:, 2]).max() * 1000).round(3))
    np.save(f'data/V_{tag}.npy', V); json.dump(P, open(f'data/P_{tag}.json', 'w'), indent=1)
    if info.get('pin'):
        p = info['pin']; z = np.array(p['z']);
        print('pin: z  m0  m1(before pin)  mT(target)  F(mm)')
        for zz in np.arange(0.76, 1.06, 0.02):
            i = int(np.argmin(np.abs(z - zz))); print(f'  {z[i]:.3f} {p["m0"][i]*1000:6.1f} {p["m1"][i]*1000:6.1f} {p["mT"][i]*1000:6.1f} {p["F"][i]*1000:6.1f}')
