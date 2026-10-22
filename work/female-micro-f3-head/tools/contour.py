"""front-view jaw contour of the analytic head and the plate's smooth target.  contour_x(H, zs) -> half width (m) of the analytic surface at heights zs;  target_hw(zs) -> cubic fit of the plate silhouette (z 1.447..1.4925)"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, fl

def _plate():
    sil = json.load(open(fl.W / 'data/sil.json'))['front']
    rr = np.array([r for r in sorted(int(r) for r in sil) if 150 <= r <= 262])
    x0 = np.array([sil[str(r)][0] for r in rr]); x1 = np.array([sil[str(r)][1] for r in rr])
    zz = fl.zrow(rr.astype(float)); hw = 0.5 * (x1 - x0 + 1) * fl.K
    o = np.argsort(zz); return zz[o], hw[o]

def target_coef(z0=1.447, z1=1.4925):
    zz, hw = _plate(); m = (zz >= z0) & (zz <= z1)
    return np.polyfit(zz[m] - 1.47, hw[m], 3)

def target_hw(zs):
    return np.polyval(target_coef(), np.asarray(zs) - 1.47)

def contour_x(H, zs, nth=301, nph=360, th=(62, 118), ph=(-72, -18), dz=0.00025, ear=False):
    """upper envelope of x over the analytic surface at heights zs (ear field switched off unless ear=True)"""
    prm_parts = H.prm.get('parts', None)
    if not ear: H.prm['parts'] = ('none',)
    try:
        return _contour_x(H, zs, nth, nph, th, ph, dz)
    finally:
        if prm_parts is None: H.prm.pop('parts', None)
        else: H.prm['parts'] = prm_parts


def _contour_x(H, zs, nth, nph, th, ph, dz):
    T = np.radians(np.linspace(th[0], th[1], nth)); Pp = np.radians(np.linspace(ph[0], ph[1], nph))
    TT, PP = np.meshgrid(T, Pp)
    u = np.stack([np.cos(PP) * np.sin(TT), -np.cos(PP) * np.cos(TT), np.sin(PP)], -1).reshape(-1, 3)
    P = H.phi(u)
    zb = np.round((P[:, 2] - 1.40) / dz).astype(int)
    nb = zb.max() + 1
    xm = np.full(nb, -1.0)
    np.maximum.at(xm, zb, P[:, 0])
    zc = 1.40 + np.arange(nb) * dz
    ok = xm > 0
    return np.interp(zs, zc[ok], xm[ok])

if __name__ == '__main__':
    import trial
    zs = np.arange(1.446, 1.4951, 0.004)
    tg = target_hw(zs)
    for name, kw in (('quad', dict(nf_smooth=1)), ('exp', dict(nf_smooth=1, smin=2))):
        H, P = trial.make_H(**kw); c = contour_x(H, zs)
        print(name, ' '.join('%.3f:%+.1f' % (z, (a - b) * 1000) for z, a, b in zip(zs, c, tg)))
