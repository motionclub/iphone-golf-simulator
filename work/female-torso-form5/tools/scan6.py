"""scan6.py: quick underbutt parameter scans in the numpy plate-lit domain.  python3 tools/scan6.py '{"cdz":[.013,.02,.03]}' ['{"fixed":"overrides"}']
For every combination prints: argmin z of the fold (cm) at |x| .03 .045 .06 .075 .09 .105 .12 vs plate, fwhm (cm), depth, envelope dev max, worst dihedral in the fold region."""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import foldx5 as fx
import pelvis5 as pv
from torso2 import EA, EB
import photo3 as ph

XS = (0.03, 0.045, 0.06, 0.075, 0.09, 0.105, 0.12)
GAIN = 2.0

def stats(co, gain=GAIN):
    img, _ = fx.render(co, gain)
    out = []
    for x in XS:
        v = fx.profile_model(img, x); out.append(fx.fold_stats(v))
    return out

PL = [fx.fold_stats(fx.profile_plate(x)) for x in XS]

_adj = None
def dihedral_worst(co, zlo=0.70, zhi=0.90, x0=0.035, x1=0.17):
    """worst dihedral angle (deg) over edges whose both triangles lie in the region"""
    global _adj
    TRI = ph.TRI
    if _adj is None:
        e = {}
        for ti, t in enumerate(TRI):
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                k = (min(a, b), max(a, b)); e.setdefault(k, []).append(ti)
        _adj = [(k, v) for k, v in e.items() if len(v) == 2]
    P = co
    tn = np.cross(P[TRI[:, 1]] - P[TRI[:, 0]], P[TRI[:, 2]] - P[TRI[:, 0]]); tn /= np.maximum(np.linalg.norm(tn, axis=1, keepdims=True), 1e-12)
    cen = P[TRI].mean(axis=1)
    w = 0.0
    for (a, b), (t0, t1) in _adj:
        c = cen[t0]
        if zlo <= c[2] <= zhi and x0 <= abs(c[0]) <= x1 and c[1] > 0:
            d = np.degrees(np.arccos(np.clip(np.dot(tn[t0], tn[t1]), -1, 1)))
            if d > w: w = d
    return w

if __name__ == '__main__':
    grid = json.loads(sys.argv[1]); fixed = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    keys = list(grid.keys())
    print('plate zmin ' + ' '.join(f'{100*p["zmin"]:5.1f}' for p in PL) + ' | fwhm ' + ' '.join(f'{100*p["fwhm"]:4.1f}' for p in PL) + ' | depth ' + ' '.join(f'{p["depth"]:3.0f}' for p in PL))
    for combo in itertools.product(*[grid[k] for k in keys]):
        over = dict(fixed); over.update(dict(zip(keys, combo)))
        co, PP = fx.build(over)
        st = stats(co)
        zu = np.arange(0.70, 0.881, 0.02)
        dev = 1000 * (fx.benv5.env(co, zu) - np.interp(zu, fx.FB[0], fx.FB[1]))
        dh = dihedral_worst(co)
        tag = ' '.join(f'{k}={v}' for k, v in zip(keys, combo))
        print(f'{tag:44s} zmin ' + ' '.join(f'{100*s["zmin"]:5.1f}' for s in st) + ' | fwhm ' + ' '.join(f'{100*s["fwhm"]:4.1f}' for s in st) + ' | depth ' + ' '.join(f'{s["depth"]:3.0f}' for s in st) + f' | env {np.abs(dev).max():4.1f} dih {dh:4.1f}')
