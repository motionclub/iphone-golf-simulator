"""explore.py : build many variants as overrides on a base param json and show them as one contact sheet.
usage (python): from explore import *; sheet('chest', 'name', {'v1': {...overrides...}, ...}, base='data/P_final.json', enh=1.8)
overrides may contain a special key 'B0' = dict of overrides for bm_list[0] (first mound component) and 'refit' = True to refit bm_scale."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from torso3 import *
import quickgate
from big3 import big
HERE = str(WD)

def build_variant(base, ov, refit=True, fixdz=True):
    Q = {**json.load(open(base))}
    ov = dict(ov)
    B0 = ov.pop('B0', None); refit_ = ov.pop('refit', refit)
    Q.update(ov)
    if B0:
        Q['bm_list'] = [dict(Q['bm_list'][0], **B0)] + list(Q['bm_list'][1:])
    Q = {**DEFAULT3, **Q}
    if refit_:
        sc, _ = fit_bust(Q, scales=np.arange(0.2, 3.01, 0.05), dzs=np.array([Q.get('bm_dz', 0.0)]), zr=(1.16, 1.28), verbose=False)
        Q['bm_scale'] = sc
    dF, dB = fit_walls(Q, iters=4, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
    co = build3(Q, dF, dB)
    return Q, co

def sheet(part, name, variants, base='data/P_final.json', enh=1.8, px=480, look='matcap:soft'):
    items = []
    for k, ov in variants.items():
        Q, co = build_variant(os.path.join(HERE, base) if not base.startswith('/') else base, ov)
        np.save(f'{HERE}/data/co_x_{name}_{k}.npy', co)
        json.dump(Q, open(f'{HERE}/data/P_x_{name}_{k}.json', 'w'), default=float)
        r = quickgate.quick(co, verbose=False)
        H = 1000 * Q.get('bm_scale', 1) * Q['bm_list'][0]['H']
        print(f"{k}: H={H:.1f}mm quick={r['QUICK_PASS']} arm={r['step_arm_mm']} legs={r['step_legs_mm']} dih40={r['dih_gt40']} contour F/B mean {r['contour_front_mean_mm']}/{r['contour_back_mean_mm']} max {r['contour_front_max_mm']}/{r['contour_back_max_mm']}")
        items.append((k, f'data/co_x_{name}_{k}.npy'))
    big(part, f'{HERE}/scratch/r/x_{name}_{part}.png', items, enh=enh, px=px, look=look)


def apex_info(co):
    """most forward point of each mound (|x| 0.04..0.115, z 1.15..1.30) of the absolute front surface + valley depth at the sternum at apex height"""
    from footprint import grid_surface
    xs = np.arange(-0.13, 0.1301, 0.002); zs = np.arange(1.10, 1.34, 0.002)
    G = grid_surface(co, 'front', xs, zs)
    out = {}
    for side, sg in (('R', 1), ('L', -1)):
        cols = np.where((sg * xs >= 0.04) & (sg * xs <= 0.115))[0]
        rows = np.where((zs >= 1.15) & (zs <= 1.30))[0]
        sub = G[np.ix_(rows, cols)]
        i, j = np.unravel_index(np.argmin(sub), sub.shape)
        out[side] = (float(xs[cols[j]]), float(zs[rows[i]]), float(sub[i, j]))
    za = 0.5 * (out['R'][1] + out['L'][1]); iz = int(round((za - 1.10) / 0.002))
    cen = G[iz][np.abs(xs) < 0.006].mean()
    out['valley_mm'] = float(1000 * (cen - 0.5 * (out['R'][2] + out['L'][2])))
    return out


def glute_info(co):
    from footprint import grid_surface
    xs = np.arange(-0.17, 0.1701, 0.002); zs = np.arange(0.78, 1.06, 0.002)
    G = grid_surface(co, 'back', xs, zs)
    out = {}
    for side, sg in (('R', 1), ('L', -1)):
        cols = np.where((sg * xs >= 0.02) & (sg * xs <= 0.15))[0]
        rows = np.where((zs >= 0.84) & (zs <= 0.96))[0]
        sub = G[np.ix_(rows, cols)]
        i, j = np.unravel_index(np.argmax(sub), sub.shape)
        out[side] = (float(xs[cols[j]]), float(zs[rows[i]]), float(sub[i, j]))
    cl = {}
    for z in (0.84, 0.86, 0.88, 0.90, 0.92, 0.94, 0.96):
        iz = int(round((z - 0.78) / 0.002)); line = G[iz]
        cen = line[np.abs(xs) < 0.006].mean(); lob = line[(np.abs(xs) > 0.02) & (np.abs(xs) < 0.15)].max()
        cl[z] = round(1000 * (lob - cen), 1)
    out['cleft_mm'] = cl
    return out
