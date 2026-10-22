"""fit camera (azimuth, scale, shift) of the 3/4 and top plate panels to the model silhouette.
python3.13 calib34.py  -> data/q3.json   (uses data/prev_phi.npz point cloud)"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl
a = fl.load_plate(); fg = fl.fg_mask(a)
d = np.load(fl.W / 'data/prev_phi.npz'); V = d['V']
V = V[V[:, 2] > 1.42]

def raster(pts_uv, w, h, rad=1):
    m = np.zeros((h, w), bool)
    c = np.round(pts_uv[:, 0]).astype(int); r = np.round(pts_uv[:, 1]).astype(int)
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            cc = c + dx; rr = r + dy
            ok = (cc >= 0) & (cc < w) & (rr >= 0) & (rr < h)
            m[rr[ok], cc[ok]] = True
    return m

def fill_rows(m):
    out = m.copy()
    for i in range(m.shape[0]):
        xs = np.where(m[i])[0]
        if len(xs): out[i, xs.min():xs.max() + 1] = True
    return out

def project(P, az, s, ut, zt, cxp, cyp, x0, y0):
    ar = np.radians(az)
    u = P[:, 0] * np.cos(ar) + P[:, 1] * np.sin(ar)
    col = cxp + (u - ut) / s - x0; row = cyp - (P[:, 2] - zt) / s - y0
    return np.stack([col, row], axis=1)

def loss(name, az, s, ut, zt, ignore=None):
    x0, y0, x1, y1 = fl.PANELS[name]['box']; w, h = x1 - x0, y1 - y0; cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
    uv = project(V, az, s, ut, zt, cxp, cyp, x0, y0)
    m = fill_rows(raster(uv, w, h))
    pm = fill_rows(fg[y0:y1, x0:x1].copy())
    pm[int(0.80 * h):, :] = False; m[int(0.80 * h):, :] = False        # ignore neck/collar region below the chin
    if ignore is not None:
        X0, Y0, X1, Y1 = ignore; m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] = False; pm[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] = False
    inter = (m & pm).sum(); union = (m | pm).sum()
    return 1 - inter / max(union, 1), m, pm

def fit(name, az0, s0, ut0, zt0, ignore):
    best = (loss(name, az0, s0, ut0, zt0, ignore)[0], az0, s0, ut0, zt0)
    steps = [3.0, 0.00004, 0.0015, 0.0015]
    for it in range(60):
        improved = False
        for k in range(4):
            for sg in (-1, 1):
                p = list(best[1:]); p[k] += sg * steps[k]
                l = loss(name, *p, ignore)[0]
                if l < best[0] - 1e-5: best = (l, *p); improved = True
        if not improved:
            steps = [t * 0.5 for t in steps]
            if steps[1] < 4e-6: break
    return best

out = {}
# q3R (panel 440..800): face to the image right, near ear on the left; the ear is not in the model -> ignore the ear box
for name, az0, ear in (('q3R', -38.0, (560, 455, 610, 520)), ('q3L', -26.0, (170, 450, 215, 520))):
    x0, y0, x1, y1 = fl.PANELS[name]['box']; cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
    s0 = 0.00155
    # initial: the head centre at the image centre
    r = fit(name, az0, s0, 0.0, 1.55, ear)
    print(name, 'loss %.4f az %.2f s %.6f ut %.4f zt %.4f' % r)
    l, az, s, ut, zt = r
    ar = np.radians(az)
    # camera target in world: u = ut along image right axis (cos az, sin az), height zt;  keep y such that the target lies on the view axis
    out[name] = dict(yaw=az, ortho=s * (x1 - x0), tx=float(ut * np.cos(ar)), ty=float(ut * np.sin(ar)), tz=zt, el=0.0, loss=l)
json.dump(out, open(fl.W / 'data/q3.json', 'w'), indent=1)
