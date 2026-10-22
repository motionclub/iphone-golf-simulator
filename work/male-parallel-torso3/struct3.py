"""FORM3 structural feature fields (y-displacements on the torso zone, front/back weighted like the FORM2 basis).
h = outward height change in mm (front: -y, back: +y).  All fields vanish at |x|>=0.20, z<=0.775 (ramped to 0.815), z>=1.35 (taper) -> zone borders untouched.
Features carve BEHIND the silhouette extremes or lift masses up to them, so the side-plate depth is unchanged.
python3.13 struct3.py <tag> [json]  -> data/V_<tag>.npy  (+ data/params_<tag>.json)"""
import sys, json
import numpy as np
sys.path.insert(0, '.')
from pmo3 import *

P_ = dict(
    # ---- front: chest
    pec_lift=dict(A=4.0, x0=0.095, sx=0.034, z0=1.225, sz=0.028),            # pec masses rise toward the silhouette extreme
    sternum=dict(A=3.0, sx=0.012, za=1.185, zb=1.215, zc=1.285, zd=1.318),   # soft sternum valley
    shelf=dict(A=3.5, zc0=1.168, zc_curve=0.050, sz=0.012, xc=0.35, x_in=0.00, x_out=0.19),   # lower-pec crease line (smile), xc = centre strength (fraction)
    # ---- front: mid
    linea=dict(A=1.5, sx=0.007, za=0.93, zb=0.96, zc=1.14, zd=1.165),
    iliac=dict(A=3.0, s=0.010, x1=0.17, z1=0.95, x2=0.02, z2=0.875),         # inguinal / iliac V creases
    oblique=dict(A=2.0, s=0.008, x0=0.12, za=0.955, zb=0.985, zc=1.10, zd=1.13),   # semilunar lines (abdominal plane vs oblique plane)
    # ---- back: glute
    cleft=dict(A=9.0, z_lo=0.775, z_pk0=0.82, z_pk1=0.86, z_hi=0.935, s_lo=0.006, s_hi=0.014),
    lobes=dict(A=4.0, x0=0.070, sx=0.034, z0=0.858, sz=0.034),
    # monotone-deepening intergluteal cleft: depth knots (mm) at zk, width sigma s_top (z>=0.95) .. s_bot (z<=0.82)
    cleft2=dict(a0=0.0, a1=0.0, a2=0.0, a3=0.0, a4=0.0, a5=0.0, a6=0.0, a7=0.0, s_top=0.006, s_bot=0.011),
)
CLEFT2_ZK = [0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92, 0.95]
def gx(d, s): return np.exp(-0.5 * (d / s) ** 2)

def fields(V, P):
    x = V[:, 0]; z = V[:, 2]; ax = np.abs(x); n = len(V); hF = np.zeros(n); hB = np.zeros(n)
    c = P['pec_lift']; hF += c['A'] * gx(ax - c['x0'], c['sx']) * gx(z - c['z0'], c['sz'])
    c = P['sternum']; hF -= c['A'] * gx(ax, c['sx']) * ramp(z, c['za'], c['zb'], c['zc'], c['zd'])
    c = P['shelf']; zc = c['zc0'] + c['zc_curve'] * (ax / 0.17) ** 2; px = (c['xc'] + (1 - c['xc']) * sstep(ax / 0.06)) * (1 - sstep((ax - c['x_out'] + 0.04) / 0.04))
    hF -= c['A'] * gx(z - zc, c['sz']) * px
    c = P['linea']; hF -= c['A'] * gx(ax, c['sx']) * ramp(z, c['za'], c['zb'], c['zc'], c['zd'])
    c = P['iliac']; vx = c['x2'] - c['x1']; vz = c['z2'] - c['z1']; L2 = vx * vx + vz * vz
    t = np.clip(((ax - c['x1']) * vx + (z - c['z1']) * vz) / L2, 0, 1); d = np.hypot(ax - (c['x1'] + t * vx), z - (c['z1'] + t * vz))
    hF -= c['A'] * gx(d, c['s']) * sstep(t / 0.25) * (1 - 0.6 * sstep((t - 0.85) / 0.15))
    c = P['oblique']; hF -= c['A'] * gx(ax - c['x0'], c['s']) * ramp(z, c['za'], c['zb'], c['zc'], c['zd'])
    c = P['cleft']; s = c['s_lo'] + (c['s_hi'] - c['s_lo']) * np.clip((c['z_hi'] - z) / (c['z_hi'] - 0.80), 0, 1)      # narrow at the top, wider toward the crotch (V)
    hB -= c['A'] * gx(ax, s) * ramp(z, c['z_lo'], c['z_pk0'], c['z_pk1'], c['z_hi'])
    c = P['cleft2']; ak = np.array([c['a%d' % i] for i in range(8)]); dep = np.interp(z, CLEFT2_ZK, ak, left=ak[0], right=0.0)
    s2 = c['s_top'] + (c['s_bot'] - c['s_top']) * np.clip((0.95 - z) / 0.13, 0, 1); hB -= dep * gx(ax, s2)
    c = P['lobes']; hB += c['A'] * gx(ax - c['x0'], c['sx']) * gx(z - c['z0'], c['sz'])
    return hF, hB

def apply(V, P, T):
    hF, hB = fields(V, P); dy = (-T.wf * hF + T.wb * hB) * T.taper * 1e-3          # taper already contains Z mask, x-taper, floor ramp, top fade
    Vn = V.copy(); Vn[:, 1] += dy; return Vn, hF, hB

if __name__ == '__main__':
    tag = sys.argv[1]; base = 'base'; zero_others = False
    if len(sys.argv) > 2:
        for k, v in json.loads(sys.argv[2]).items():
            if k == '_base': base = v
            elif k == '_only': zero_others = v          # list of features to keep, all other amplitudes -> 0
            elif isinstance(v, dict): P_[k].update(v)
            else: P_[k] = v
    if zero_others is not False:
        for f in ('pec_lift', 'shelf', 'sternum', 'linea', 'iliac', 'oblique', 'cleft', 'lobes'):
            if f not in zero_others: P_[f]['A'] = 0.0
        if 'cleft2' not in zero_others:
            for i in range(8): P_['cleft2']['a%d' % i] = 0.0
    V0 = np.load('data/V_base.npy'); V = np.load(f'data/V_{base}.npy'); T = Torso3(V0)
    Vn, hF, hB = apply(V, P_, T); Pg, dF, dB = deficit_guard(Vn, V, T, sigma=0.008, n=3)
    np.save(f'data/V_{tag}.npy', Pg); json.dump(P_, open(f'data/params_{tag}.json', 'w'), indent=1)
    d = (Pg[:, 1] - V[:, 1]) * 1000; V = V0
    print(tag, 'dy [%.1f, %.1f] mm  moved %d  extreme drift front %.2f back %.2f mm' % (d.min(), d.max(), int(np.any(Pg != V, axis=1).sum()), np.nanmax(np.abs(dF)) * 1000, np.nanmax(np.abs(dB)) * 1000))
