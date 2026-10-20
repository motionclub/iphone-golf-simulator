"""Fit the front-half section exponent n_f(z) from the far-cheek contour (left edge) of the two 3/4 plates.
/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 fit_nf.py"""
import sys, json
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, loft as L
K = H.K; TOP = H.TOP
E = json.load(open(H.W / 'plates/q3_edges.json'))
PAN = {'q3L': dict(psi=32.5, cx=219.0), 'q3R': dict(psi=30.0, cx=(433 + 834) / 2)}
APEX = 397.0
lf = L.Loft()


def section_left_u(z, nf, psi, a=None):
    """leftmost screen coordinate (m, relative to the target u0) of the loft section at z with front exponent nf"""
    p = lf.at(np.array([z])); a_ = p['a'][0]; f = p['f'][0]; b = p['b'][0]; yw = p['yw'][0]; nb = p['nb'][0]
    t = np.linspace(0, 2 * np.pi, 1441)
    c, s = np.cos(t), np.sin(t)
    front = s < 0
    n = np.where(front, nf, nb); sd = np.where(front, f, b)
    x = a_ * np.sign(c) * np.abs(c) ** (2.0 / n)
    y = yw + sd * np.sign(s) * np.abs(s) ** (2.0 / n)
    ps = np.radians(psi)
    u = x * np.cos(ps) + y * np.sin(ps)
    u0 = -0.040 * np.sin(ps)           # target (0,-0.04)
    return u.min() - u0, u.max() - u0


res = {}
for name, pr in PAN.items():
    print(name)
    for row in range(420, 590, 10):
        z = TOP - (row - APEX) * K
        e = E[name].get(str(row))
        if not e: continue
        ul_plate = (e[0] - pr['cx']) * K          # screen-left edge (m) from panel centre
        ur_plate = (e[1] + 1 - pr['cx']) * K
        best = None
        for nf in np.arange(1.6, 4.01, 0.1):
            ul, ur = section_left_u(z, nf, pr['psi'])
            err = abs(ul - ul_plate)
            if best is None or err < best[0]: best = (err, nf, ul, ur)
        _, nf, ul, ur = best
        print(f'  row {row} z={z:.4f}  plate L {ul_plate*1000:7.1f} R {ur_plate*1000:7.1f} | best nf={nf:.1f} mesh L {ul*1000:7.1f} R {ur*1000:7.1f} (R err {1000*(ur-ur_plate):+5.1f})')
