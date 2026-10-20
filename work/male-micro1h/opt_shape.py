"""Fit smooth-volume sculpt parameters (cheeks, nose block, muzzle, nasolabial, brows, orbit) by analysis-by-synthesis:
plate-lit Lambert shading of the sculpted head vs plate luminance (front + both 3/4), plus profile and 3/4 contour constraints.  Numpy only."""
import sys, math, json, time, copy
sys.path.insert(0, '.')
import numpy as np
import shade2 as SH
import sculpt as S
import proxy as PX
import fit_nf3q as FN
import h1lib as H

VIEWS = ('front', 'q3L', 'q3R')
LUM = {n: np.asarray(SH.plate.crop(SH.VIEWS[n]['box'])).astype(float) for n in VIEWS}
PE = H.plate_extents()
PROF_ROWS = [r for r in range(140, 264, 4)]
PROF_Y = {int(r): float(PE['yf'][np.where(PE['rows'] == r)[0][0]]) for r in PROF_ROWS if len(np.where(PE['rows'] == r)[0])}
PROF_Z = {r: float(H.zrow(r)) for r in PROF_Y}

# parameters: name -> (initial, lo, hi, step)
PARAMS = {
    'malar_h': (6.4, 3.0, 13.0, 1.0), 'malar_x': (45.0, 36.0, 54.0, 3.0), 'malar_z': (1.542, 1.528, 1.558, 0.004), 'malar_rx': (25.0, 15.0, 33.0, 3.0), 'malar_rz': (17.0, 9.0, 25.0, 2.5),
    'buccal_h': (3.0, 0.0, 8.0, 1.0), 'buccal_z': (1.503, 1.488, 1.522, 0.004),
    'nose_Fs': (1.0, 0.80, 1.30, 0.06),
    'ala_h': (12.5, 4.0, 17.0, 1.5), 'ala_rx': (9.5, 5.0, 15.0, 1.2), 'ala_rz': (7.5, 4.0, 12.0, 1.0), 'ala_cx': (19.5, 14.0, 25.0, 1.5),
    'mouth_wexp': (2.4, 1.3, 3.2, 0.3), 'mouth_ws': (1.0, 0.65, 1.25, 0.08),
    'naso_depth': (2.7, 0.3, 5.5, 0.6), 'naso_width': (3.8, 2.0, 8.0, 0.8),
    'brow_s': (1.0, 0.5, 1.6, 0.12), 'orbit_depth': (5.0, 1.0, 9.0, 1.0), 'glab_h': (1.4, 0.0, 3.5, 0.5),
}
THETA0 = {k: v[0] for k, v in PARAMS.items()}


def make_prm(th):
    prm = copy.deepcopy(S.PRM)
    prm['malar'] = dict(x=th['malar_x'], z=th['malar_z'], rx=th['malar_rx'], rz=th['malar_rz'], h=th['malar_h'])
    b = prm['buccal']; b['h'] = th['buccal_h']; b['z'] = th['buccal_z']
    prm['nose_F'] = [f * th['nose_Fs'] for f in S.PRM['nose_F']]
    a = prm['ala']; a['h'] = th['ala_h']; a['rx'] = th['ala_rx']; a['rz'] = th['ala_rz']; a['cx'] = th['ala_cx']
    prm['mouth'] = dict(prm['mouth'], wexp=th['mouth_wexp'], wscale=th['mouth_ws'])
    prm['nasolabial'] = dict(prm['nasolabial'], depth=th['naso_depth'], width=th['naso_width'])
    prm['brow'] = [(x, z, rx, rz, h * th['brow_s']) for (x, z, rx, rz, h) in S.PRM['brow']]
    prm['orbit'] = dict(prm['orbit'], depth=th['orbit_depth'])
    prm['glabella'] = dict(prm['glabella'], h=th['glab_h'])
    return prm


# light per view fitted once on the baseline sculpt
_P0 = SH.stage1(SH.V0)
_N0 = PX.vertex_normals(_P0, SH.F0)
LIGHT = {}
for n in VIEWS:
    Nimg, m, _ = SH.splat(_P0, _N0, n)
    LIGHT[n] = SH.fit_light(Nimg, m, LUM[n], n)


def roi_mask(P1, idx, m):
    pts = np.zeros(idx.shape + (3,)); pts[m] = P1[idx[m]]
    x = np.abs(pts[..., 0]); y = pts[..., 1]; z = pts[..., 2]
    roi = m & (z > 1.500) & (z < 1.640) & (x < 0.068) & (y < -0.035)
    roi &= ~((x > 0.012) & (x < 0.062) & (z > 1.570) & (z < 1.626))            # eyes + brows (paint/albedo)
    return roi


def objective(th, detail=False, wp=40.0, wc=8.0, reg=1.0):
    prm = make_prm(th)
    P1 = SH.stage1(SH.V0, prm)
    N1 = PX.vertex_normals(P1, SH.F0)
    shade = 0.0; parts = {}
    for n in VIEWS:
        Nimg, m, idx = SH.splat(P1, N1, n)
        roi = roi_mask(P1, idx, m)
        l, a, b = LIGHT[n][0], LIGHT[n][1], LIGHT[n][2]
        pred = a + b * np.clip(Nimg @ l, 0, None)
        r = (LUM[n] - pred)[roi]
        d = 22.0
        rho = np.where(np.abs(r) < d, 0.5 * r * r, d * (np.abs(r) - 0.5 * d))
        parts['shade_' + n] = float(np.sqrt(2 * rho.mean())) if len(r) else 0.0
        shade += float(rho.mean()) * 2.0
    # profile constraint (mm)
    pr = []
    c = np.abs(P1[:, 0]) < 0.004
    for r_, y_ in PROF_Y.items():
        sel = c & (np.abs(P1[:, 2] - PROF_Z[r_]) < 0.0007)
        if sel.any(): pr.append((P1[sel, 1].min() - y_) * 1000)
    pr = np.array(pr); prof = float(np.mean(pr ** 2))
    parts['prof_rms_mm'] = math.sqrt(prof)
    res = FN.residuals(P1=P1)
    cont = float(np.mean(res ** 2)); parts['contour_rms_mm'] = math.sqrt(cont)
    rg = 0.0
    for k, (v0, lo, hi, st) in PARAMS.items():
        rg += ((th[k] - v0) / ((hi - lo) * 0.35)) ** 2
    total = shade / len(VIEWS) + wp * prof + wc * cont + reg * rg * 4.0
    parts['reg'] = rg
    return (total, parts) if detail else total


def descend(th, sweeps=3, log=print):
    best = objective(th); log('start total %.2f' % best)
    for sw in range(sweeps):
        improved = False
        for k, (v0, lo, hi, st) in PARAMS.items():
            for sgn in (+1, -1):
                for mult in (1.0, 2.0):
                    t = dict(th); t[k] = float(np.clip(th[k] + sgn * st * mult, lo, hi))
                    if t[k] == th[k]: continue
                    e = objective(t)
                    if e < best - 1e-3:
                        best = e; th = t; improved = True; log('  sweep %d %-11s -> %8.3f  total %.2f' % (sw, k, th[k], best)); break
                else:
                    continue
                break
        _, parts = objective(th, detail=True)
        log('sweep %d done total %.2f  %s' % (sw, best, {k: round(v, 2) for k, v in parts.items()}))
        json.dump(th, open('data/opt_theta.json', 'w'))
        if not improved: break
    return th, best


if __name__ == '__main__':
    t0 = time.time()
    tot, parts = objective(THETA0, detail=True)
    print('baseline total %.2f' % tot, {k: round(v, 2) for k, v in parts.items()}, 'secs/eval %.1f' % (time.time() - t0))
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        th, best = descend(dict(THETA0), sweeps=int(sys.argv[2]) if len(sys.argv) > 2 else 3, log=lambda s: print(s, flush=True))
        print('FINAL', json.dumps(th))
