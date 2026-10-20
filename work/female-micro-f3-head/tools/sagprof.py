"""sagittal (x = 0) front profile of mesh npz files vs the plate left/right silhouettes.  python3 sagprof.py name=npz ...  (prints y_front(z) in mm)"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, meshlib as ml, slices as sl, fl

def plate_front(zs):
    sil = json.load(open(fl.W / 'data/sil.json'))
    out = {}
    for side in ('left', 'right'):
        ys, zz = [], []
        for r in range(150, 262):
            v = sil[side].get(str(r))
            if not v: continue
            y = fl.ycolL(v[0]) if side == 'left' else fl.ycolR(v[1])
            ys.append(y); zz.append(float(fl.zrow(r)))
        o = np.argsort(zz); out[side] = np.interp(zs, np.array(zz)[o], np.array(ys)[o])
    return out

def mesh_front(V, F, zs, x0=0.0):
    T = ml.tri_fan(F); segs = sl.slice_axis(V, T, 0, x0)
    polys = sorted(sl.chain(segs), key=len, reverse=True)
    res = np.full(len(zs), np.nan)
    for p in polys[:3]:
        for j in range(len(p) - 1):
            a, b = p[j], p[j + 1]
            lo, hi = min(a[2], b[2]), max(a[2], b[2])
            for i, z in enumerate(zs):
                if lo <= z <= hi and hi > lo:
                    t = (z - a[2]) / (b[2] - a[2]); y = a[1] + t * (b[1] - a[1])
                    if np.isnan(res[i]) or y < res[i]: res[i] = y
    return res

if __name__ == '__main__':
    zs = np.arange(1.430, 1.5201, 0.004)
    pf = plate_front(zs)
    items = [a.split('=', 1) for a in sys.argv[1:]]
    prof = {}
    for n, p in items:
        V, F, d = ml.load(p); prof[n] = mesh_front(V, F, zs)
    print('   z    plateL plateR ' + ' '.join('%8s' % n for n, _ in items))
    for i, z in enumerate(zs):
        print('%.3f %7.1f %6.1f ' % (z, pf['left'][i] * 1000, pf['right'][i] * 1000) + ' '.join('%8.1f' % (prof[n][i] * 1000) for n, _ in items))
