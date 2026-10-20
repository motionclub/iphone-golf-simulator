"""Nape + pelvis model v3 (derived from v2): heightfield remap (rear glute fold smile, cleft, lobes; front groin mound + inguinal V) + nape hump removal.
python3.13 np_model2.py <params.json|-> <tag>   -> data/V_<tag>.npy, data/P_<tag>.json
Displacement is along world Y only (x,z bit-identical -> front/back silhouettes unchanged by construction)."""
import sys, json
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin')
from sculpt import *
import hf

def pw(x, xs, ys): return np.interp(x, xs, ys)

DEF = dict(
    nape=dict(on=True, z=[1.34, 1.36, 1.37, 1.38, 1.39, 1.40, 1.41, 1.42, 1.43, 1.44, 1.45, 1.46, 1.47],
              d=[0.0, -1.0, -3.0, -7.0, -12.0, -16.0, -16.0, -13.0, -9.0, -5.0, -2.0, -0.5, 0.0], sx=0.075, xcut=0.14),
    rear=dict(on=True, zlo0=0.755, zlo1=0.775, zhi0=1.00, zhi1=1.06, xe0=0.155, xe1=0.205,
              # fold shift s(u) in metres (+ = ramp moves up): smile = low at the centre, rising laterally
              blur=dict(sig=0.017, w=[0.755, 0.775, 0.835, 0.90], zc_u=[0.0, 0.05, 0.07, 0.09], zc_v=[0.776, 0.776, 0.765, 0.70]),
              s_u=[0.0, 0.03, 0.06, 0.09, 0.12, 0.15, 0.21], s_v=[-0.004, -0.004, 0.0, 0.010, 0.022, 0.030, 0.030],
              B=[0.745, 0.775, 0.84, 0.93],             # remap bump: 0 -> 1 over [0],[1]; 1 -> 0 over [2],[3]
              cleft=dict(C0=16.0, z0=0.778, z1=0.800, zu0=0.86, zu1=0.97, s0=0.020, s1=0.012),
              trim=dict(A=3.0, u=0.04, su=0.035, z=0.845, sz=0.03),
              lat=dict(A=0.0, u=0.125, su=0.03, z=0.87, sz=0.05)),
    front=dict(on=True, zlo0=0.76, zlo1=0.775, zhi0=0.92, zhi1=0.98, xe0=0.17, xe1=0.21,
               s_u=[0.0, 0.03, 0.06, 0.10, 0.21], s_v=[-0.008, -0.008, -0.004, 0.0, 0.0], B=[0.745, 0.775, 0.80, 0.86],
               mound=dict(A=6.0, su=0.05, z=0.825, sz=0.035),
               groove=dict(A=4.5, sig=0.011, p0=[0.175, 0.885], p1=[0.045, 0.797])),
    smooth=dict(iters=4, zlo=0.74, zhi=1.08, zlo_n=1.30, zhi_n=1.50, iters_n=3))

def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): deep_merge(a[k], v)
        else: a[k] = v
    return a

def masked_blur_z(grid, sigma, zceil_fn):
    """Gaussian blur of H(u,z) along z using only samples at/above the gap ceiling z_ceil(u) (normalised convolution); returns a new Grid"""
    H = grid.H; z = grid.z; dz = z[1] - z[0]; out = H.copy(); k = int(np.ceil(3 * sigma / dz)); t = np.arange(-k, k + 1) * dz; w = np.exp(-0.5 * (t / sigma) ** 2)
    for i, u in enumerate(grid.u):
        m = (z >= zceil_fn(u)).astype(float); f = H[i] * m
        num = np.convolve(np.pad(f, k, mode='edge'), w, mode='valid'); den = np.convolve(np.pad(m, k, mode='constant'), w, mode='valid')
        ok = den > 1e-6; out[i, ok] = num[ok] / den[ok]
    from hf import Grid
    return Grid(grid.u, grid.z, out, grid.name + '_blur')

def bump(z, B):
    return smoothstep(B[0], B[1], z) * (1 - smoothstep(B[2], B[3], z))

def seg_dist(U, Zc, p0, p1):
    p0 = np.array(p0); p1 = np.array(p1); d = p1 - p0; L2 = d @ d
    t = np.clip(((U - p0[0]) * d[0] + (Zc - p0[1]) * d[1]) / L2, 0, 1)
    return np.hypot(U - (p0[0] + t * d[0]), Zc - (p0[1] + t * d[1])), t

_grids = {}
def grids():
    if 'rear' not in _grids:
        _grids['rear'] = hf.build(V0, 'rear'); _grids['front'] = hf.build(V0, 'front')
    return _grids

def build(P):
    V = V0.copy(); X, Y, Z = V0[:, 0], V0[:, 1], V0[:, 2]; U = np.abs(X)
    N = vnormals(V0); ny = N[:, 1]
    wr = smoothstep(0.10, 0.50, ny); wf = smoothstep(0.10, 0.50, -ny)
    dY = np.zeros(N0); G = grids()
    # ---------------- nape ----------------
    n = P['nape']
    if n['on']:
        inz = (Z >= n['z'][0]) & (Z <= n['z'][-1]) & (U <= n['xcut'])
        d = pw(Z, n['z'], n['d']) * 1e-3; gx = np.exp(-0.5 * (U / n['sx']) ** 2); wx = 1 - smoothstep(n['xcut'] - 0.04, n['xcut'], U)
        dY += np.where(inz, wr * gx * wx * d, 0.0)
    # ---------------- rear (glute) ----------------
    r = P['rear']
    if r['on']:
        Hr = G['rear']; Mz = band(Z, r['zlo0'], r['zlo1'], r['zhi0'], r['zhi1']); Mx = 1 - smoothstep(r['xe0'], r['xe1'], U); M = Mz * Mx * wr
        s = pw(U, r['s_u'], r['s_v']); Bz = bump(Z, r['B'])
        H0 = Hr.sample(U, Z)
        bl = r['blur']
        if bl['sig'] > 0:
            Hs = masked_blur_z(Hr, bl['sig'], lambda u: np.interp(u, bl['zc_u'], bl['zc_v']))
            wb = band(Z, bl['w'][0], bl['w'][1], bl['w'][2], bl['w'][3]); H1 = H0 + wb * (Hs.sample(U, Z) - H0)
            Hr1 = Hs; Hn = Hs.sample(U, Z - s * Bz); Hn = H0 + wb * 0 + (Hn - Hs.sample(U, Z)) * 1.0 + wb * (Hs.sample(U, Z) - H0)
        else: Hn = Hr.sample(U, Z - s * Bz)
        T = Hn - H0
        c = r['cleft']; sc = c['s0'] + (c['s1'] - c['s0']) * smoothstep(c['z1'], 0.92, Z)
        Cd = c['C0'] * 1e-3 * smoothstep(c['z0'], c['z1'], Z) * (1 - smoothstep(c['zu0'], c['zu1'], Z)); T = T - Cd * np.exp(-0.5 * (U / sc) ** 2)
        t = r['trim']; T = T - t['A'] * 1e-3 * np.exp(-0.5 * ((U - t['u']) / t['su']) ** 2) * np.exp(-0.5 * ((Z - t['z']) / t['sz']) ** 2)
        l = r['lat']; T = T + l['A'] * 1e-3 * np.exp(-0.5 * ((U - l['u']) / l['su']) ** 2) * np.exp(-0.5 * ((Z - l['z']) / l['sz']) ** 2)
        dY += M * T
    # ---------------- front (groin) ----------------
    f = P['front']
    if f['on']:
        Hf = G['front']; Mz = band(Z, f['zlo0'], f['zlo1'], f['zhi0'], f['zhi1']); Mx = 1 - smoothstep(f['xe0'], f['xe1'], U); M = Mz * Mx * wf
        s = pw(U, f['s_u'], f['s_v']); Bz = bump(Z, f['B'])
        T = Hf.sample(U, Z - s * Bz) - Hf.sample(U, Z)
        m = f['mound']; T = T - m['A'] * 1e-3 * np.exp(-0.5 * (U / m['su']) ** 2) * np.exp(-0.5 * ((Z - m['z']) / m['sz']) ** 2)     # forward (more negative y)
        g = f['groove']; dist, t = seg_dist(U, Z, g['p0'], g['p1']); T = T + g['A'] * 1e-3 * np.exp(-0.5 * (dist / g['sig']) ** 2) * smoothstep(0.0, 0.15, t) * (1 - smoothstep(0.85, 1.0, t))
        dY += M * T
    V[:, 1] = V0[:, 1] + dY
    # ---------------- cleanup smoothing (y only) ----------------
    s = P['smooth']
    if s['iters'] > 0:
        moved = (np.abs(dY) > 1e-6).astype(float); w = diffuse_scalar(moved, np.ones(N0), iters=3, lam=0.5); w = np.clip(w * 1.2, 0, 1)
        w_p = w * band(Z, s['zlo'] - 0.01, s['zlo'], s['zhi'], s['zhi'] + 0.02); w_n = w * band(Z, s['zlo_n'] - 0.01, s['zlo_n'], s['zhi_n'], s['zhi_n'] + 0.02)
        V[:, 1] = taubin_scalar(V[:, 1], np.maximum(w_p * (s['iters'] > 0), 0), iters=s['iters'])
        V[:, 1] = taubin_scalar(V[:, 1], w_n, iters=s['iters_n'])
    return V

if __name__ == '__main__':
    P = json.loads(json.dumps(DEF)); tag = sys.argv[2]
    if sys.argv[1] != '-': deep_merge(P, json.load(open(sys.argv[1])))
    V = build(P); d = V - V0; mv = np.linalg.norm(d, axis=1)
    print(tag, 'moved', int((mv > 1e-7).sum()), 'max mm', (mv.max() * 1000).round(2), 'dy range mm', (d[:, 1].min() * 1000).round(2), (d[:, 1].max() * 1000).round(2),
          'max|dx|,|dz| mm', (np.abs(d[:, 0]).max() * 1000).round(3), (np.abs(d[:, 2]).max() * 1000).round(3))
    np.save(f'data/V_{tag}.npy', V); json.dump(P, open(f'data/P_{tag}.json', 'w'), indent=1)
