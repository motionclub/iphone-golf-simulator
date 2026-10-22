"""Nape + pelvis displacement model (positions only, topology identical).
python3.13 np_model.py <params.json> <tag>   -> data/V_<tag>.npy, data/D_<tag>.npz (indices + delta)
All displacement is along world Y (depth) so front/back silhouettes (x extents) are exactly unchanged by construction.
Mirror-symmetric in x (u = |x|); weights restrict to rear-facing (nape/glute) or front-facing (groin) vertices."""
import sys, json
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin')
from sculpt import *

DEF = dict(
    # ---- nape (rear neck base) ----
    nape=dict(on=True, z=[1.34, 1.36, 1.37, 1.38, 1.39, 1.40, 1.41, 1.42, 1.43, 1.44, 1.45, 1.46, 1.47],
              d=[0.0, -1.0, -3.0, -7.0, -12.0, -16.0, -16.0, -13.0, -9.0, -5.0, -2.0, -0.5, 0.0], sx=0.075, xcut=0.14),
    # ---- glute (rear pelvis) ----
    glute=dict(on=True, zlo0=0.755, zlo1=0.785, zhi0=1.00, zhi1=1.06, xe0=0.15, xe1=0.20,
               cleft=dict(C0=13.0, z0=0.783, z1=0.805, zu0=0.86, zu1=0.96, s0=0.022, s1=0.014),
               fill=dict(A=14.0, u=0.085, su=0.035, z=0.780, sz=0.012),
               trim=dict(A=6.0, u=0.04, su=0.035, z=0.845, sz=0.03),
               lat=dict(A=0.0, u=0.125, su=0.03, z=0.87, sz=0.05)),
    # ---- groin (front pelvis) ----
    groin=dict(on=False),
    smooth=dict(iters=4, zlo=0.75, zhi=1.08))

def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): deep_merge(a[k], v)
        else: a[k] = v
    return a

def interp(z, zs, ds):
    return np.interp(z, zs, ds)

def build(P, V=None):
    V = V0.copy() if V is None else V.copy()
    X, Y, Z = V0[:, 0], V0[:, 1], V0[:, 2]; U = np.abs(X)
    N = vnormals(V0); ny = N[:, 1]
    wr = smoothstep(0.10, 0.50, ny)           # rear-facing weight
    wf = smoothstep(0.10, 0.50, -ny)          # front-facing weight
    dY = np.zeros(N0)
    # ---------------- nape ----------------
    n = P['nape']
    if n['on']:
        inz = (Z >= n['z'][0]) & (Z <= n['z'][-1]) & (U <= n['xcut'])
        d = interp(Z, n['z'], n['d']) * 1e-3
        gx = np.exp(-0.5 * (U / n['sx']) ** 2)
        wx = 1 - smoothstep(n['xcut'] - 0.04, n['xcut'], U)
        dY += np.where(inz, wr * gx * wx * d, 0.0)
    # ---------------- glute ----------------
    g = P['glute']
    if g['on']:
        Mz = band(Z, g['zlo0'], g['zlo1'], g['zhi0'], g['zhi1']); Mx = 1 - smoothstep(g['xe0'], g['xe1'], U); M = Mz * Mx * wr
        c = g['cleft']; sc = c['s0'] + (c['s1'] - c['s0']) * smoothstep(c['z1'], 0.92, Z)
        Cd = c['C0'] * smoothstep(c['z0'], c['z1'], Z) * (1 - smoothstep(c['zu0'], c['zu1'], Z))
        T = -Cd * np.exp(-0.5 * (U / sc) ** 2)
        f = g['fill']; T = T + f['A'] * np.exp(-0.5 * ((U - f['u']) / f['su']) ** 2) * np.exp(-0.5 * ((Z - f['z']) / f['sz']) ** 2)
        t = g['trim']; T = T - t['A'] * np.exp(-0.5 * ((U - t['u']) / t['su']) ** 2) * np.exp(-0.5 * ((Z - t['z']) / t['sz']) ** 2)
        l = g['lat']; T = T + l['A'] * np.exp(-0.5 * ((U - l['u']) / l['su']) ** 2) * np.exp(-0.5 * ((Z - l['z']) / l['sz']) ** 2)
        dY += M * T * 1e-3
    V[:, 1] = V0[:, 1] + dY
    # ---------------- cleanup smoothing (only where we moved) ----------------
    s = P['smooth']
    if s['iters'] > 0:
        moved = np.abs(dY) > 1e-6
        w = smoothstep(0, 1.5e-3, np.abs(dY)) * 0.0 + moved.astype(float)
        # grow the mask a little so the smoothing also blends the border
        w = diffuse_scalar(w, np.ones(N0), iters=3, lam=0.5)
        w = np.clip(w * 1.2, 0, 1) * band(Z, s['zlo'] - 0.01, s['zlo'], s['zhi'], s['zhi'] + 0.02)
        V[:, 1] = taubin_scalar(V[:, 1], w, iters=s['iters'])      # y only: x,z (hence the front/back silhouettes) stay bit-identical
    return V

if __name__ == '__main__':
    P = json.loads(json.dumps(DEF)); tag = sys.argv[2]
    if len(sys.argv) > 1 and sys.argv[1] != '-': deep_merge(P, json.load(open(sys.argv[1])))
    V = build(P); d = (V - V0)
    mv = np.linalg.norm(d, axis=1)
    print(tag, 'moved', int((mv > 1e-7).sum()), 'max mm', (mv.max() * 1000).round(2), 'dy range mm', (d[:, 1].min() * 1000).round(2), (d[:, 1].max() * 1000).round(2),
          'max |dx|,|dz| mm', (np.abs(d[:, 0]).max() * 1000).round(3), (np.abs(d[:, 2]).max() * 1000).round(3))
    np.save(f'data/V_{tag}.npy', V); json.dump(P, open(f'data/P_{tag}.json', 'w'), indent=1)
