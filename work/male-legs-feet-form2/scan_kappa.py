import sys, json
sys.path.insert(0, '.')
import numpy as np
from ff_common import *
from ff_build import DEFAULT, ToeRow
import ff_assemble as A
from ff_slopes import slopes_fn
import relief as R
d = json.load(open('design_v9.json')); relief_cfg = d.pop('relief'); d.pop('straighten', None)
P = dict(DEFAULT); P.update(d)
set_origin(P['L'][0], lc_big=float(ToeRow(P).lc[0]))
f_cut = float(to_local(np.array([[FRAME_ORIGIN[0], -0.095, 0.0]]), +1)[0, 0])
V1 = np.load('tmp/V1_b13.npy'); V0, F = load_base()
def angles(poly):
    out = []
    n = len(poly)
    for q in range(n):
        u = poly[(q - 1) % n] - poly[q]; v = poly[(q + 1) % n] - poly[q]
        c = (u @ v) / max(np.linalg.norm(u) * np.linalg.norm(v), 1e-18); out.append(np.degrees(np.arccos(np.clip(c, -1, 1))))
    return out
for kappa, beta in ((0.0, 0.5), (0.0, 1.0), (0.05, 1.0), (0.1, 1.0)):
    P['straighten'] = kappa; P['respace'] = beta
    Vn, Fn, meta, cuts, builds = A.assemble(V1, F, P=P, f_cut=f_cut, slopes_fn=slopes_fn, verbose=False)
    kept = set(tuple(sorted(f)) for f in F)
    new = [f for f in Fn if tuple(sorted(f)) not in kept]
    mins = []; bad = 0; emin = 1e9; nbad_edge = 0
    for f in new:
        a = angles([Vn[i] for i in f]); mins.append(min(a))
        if min(a) < 12 or max(a) > 168: bad += 1
        for k in range(len(f)):
            e = np.linalg.norm(Vn[f[k]] - Vn[f[(k + 1) % len(f)]]) * 1000; emin = min(emin, e); nbad_edge += e < 1.0
    # flipped faces among OLD kept faces (compared with the base): count faces whose normal disagrees with the neighbour mean
    from collections import defaultdict
    def flips(V, FF):
        ef = defaultdict(list)
        for i, p in enumerate(FF):
            for k in range(len(p)):
                a, b = p[k], p[(k + 1) % len(p)]; ef[(min(a, b), max(a, b))].append(i)
        def nrm(p):
            p = list(p); n = np.cross(V[p[2]] - V[p[0]], V[p[3]] - V[p[1]]) if len(p) == 4 else np.cross(V[p[1]] - V[p[0]], V[p[2]] - V[p[0]]); return n / max(np.linalg.norm(n), 1e-18)
        N_ = np.array([nrm(p) for p in FF]); out = 0
        for i, p in enumerate(FF):
            nb = []
            for k in range(len(p)):
                a, b = p[k], p[(k + 1) % len(p)]; nb += [j for j in ef[(min(a, b), max(a, b))] if j != i]
            if nb and N_[i] @ N_[nb].mean(0) < 0: out += 1
        return out
    nflip = flips(Vn, Fn)
    print(f'kappa {kappa:4.2f} beta {beta:3.1f}: flipped faces total {nflip} | new faces {len(new)} worst min-angle {min(mins):5.1f} deg, faces with angle<12 or >168: {bad}, shortest edge {emin:5.2f} mm, edges<1mm {nbad_edge}')
