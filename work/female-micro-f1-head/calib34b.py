"""landmark-based fit of the 3/4 panel cameras (yaw, scale, shift) using model surface points at the front-plate landmark (x,z).
python3.13 calib34b.py"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, geo
H = geo.Head()
def surf(x, z, iters=6):
    y = -0.12
    for _ in range(iters):
        d = np.array([[x, y, z]]) - geo.C[None, :]; u = d / np.linalg.norm(d, axis=1, keepdims=True)
        P = H.phi(u)[0]; y = P[1]
    return np.array([x, y, z])
# plate landmarks: name -> (3D front-plate (x,z) or full 3D), q3L (col,row), q3R (col,row);  near side = x<0 (camera at -x)
LM = {
 'iris_near': ((-0.0461, None, 1.5556), (245.0, 478.3), (645.8, 478.3)),
 'iris_far':  ((+0.0461, None, 1.5556), (300.8, 478.3), (694.7, 479.7)),
 'mouth_near': ((-0.0354, None, 1.4842), (250.8, 524.2), (650.2, 524.7)),
 'mouth_far':  ((+0.0354, None, 1.4842), (291.3, 525.3), (687.0, 526.7)),
 'nose_tip': ((0.0, -0.1462, 1.5164), (278.3, 508.3), (674.2, 509.2)),
 'brow_in_near': ((-0.0223, None, 1.5911), (None, None), (663.3, 455.8)),
 'brow_in_far': ((+0.0223, None, 1.5911), (None, None), (686.7, 457.0)),
 'chin': ((0.0, -0.097, 1.4269), (265.0, 560.8), (665.0, 560.5)),
}
P3 = {}
for k, (p, a, b) in LM.items():
    P3[k] = surf(p[0], p[2]) if p[1] is None else np.array([p[0], p[1], p[2]])
out = {}
for name, idx in (('q3L', 1), ('q3R', 2)):
    x0, y0, x1, y1 = fl.PANELS[name]['box']; cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
    keys = [k for k in LM if LM[k][idx][0] is not None]
    pix = np.array([LM[k][idx] for k in keys]); P = np.array([P3[k] for k in keys])
    def res(p):
        az, s, ut, zt = p; ar = np.radians(az)
        u = P[:, 0] * np.cos(ar) + P[:, 1] * np.sin(ar)
        col = cxp + (u - ut) / s; row = cyp - (P[:, 2] - zt) / s
        return np.concatenate([col - pix[:, 0], row - pix[:, 1]])
    best = None
    for az0 in range(-60, 5, 5):
        p = np.array([az0, 0.00154, 0.0, 1.55]); st = np.array([4.0, 0.00006, 0.002, 0.002])
        l = (res(p) ** 2).sum()
        for it in range(200):
            imp = False
            for k in range(4):
                for sg in (-1, 1):
                    q = p.copy(); q[k] += sg * st[k]; lq = (res(q) ** 2).sum()
                    if lq < l - 1e-9: p, l, imp = q, lq, True
            if not imp:
                st *= 0.5
                if st[1] < 1e-7: break
        if best is None or l < best[0]: best = (l, p)
    l, p = best
    r = res(p); print(name, 'rms px %.2f' % np.sqrt((r ** 2).mean()), 'yaw %.2f scale %.6f ut %.4f zt %.4f' % tuple(p))
    for k, e in zip(keys, np.stack([r[:len(keys)], r[len(keys):]], 1)): print('   ', k, np.round(e, 1))
    az, s, ut, zt = p; ar = np.radians(az)
    out[name] = dict(yaw=float(az), ortho=float(s * (x1 - x0)), tx=float(ut * np.cos(ar)), ty=float(ut * np.sin(ar)), tz=float(zt), el=0.0)
out['top'] = dict(yaw=0.0, ortho=0.518, tx=0.0, ty=-0.0277, tz=1.6, el=90.0)
json.dump(out, open(fl.W / 'data/q3.json', 'w'), indent=1)
