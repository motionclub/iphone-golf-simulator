import sys, json
sys.path.insert(0, '.')
from plateview import *
from zone import zone_mask
V = np.load('data/V_base.npy'); N = vertex_normals(V); Z = zone_mask(V)
cal = json.load(open('data/q3_calib2.json')); SHB = gblur(SHEET, 1.1)
body = (V[:, 2] < 1.40) & (np.abs(V[:, 0]) < 0.62)
for name, c in cal.items():
    vw = ViewYaw(name, c['yaw'], c['col0'], c['mpp'], c['sole_row']); vis = visible_gen(vw, V, N, sel=V[:, 2] < 1.40, res=1.0, rad=1) & body
    col, row = vw.project(V); I = bilinear(SHB, col, row); A = sh2c(N, vw)
    fit = vis & ~Z; cc, *_ = np.linalg.lstsq(A[fit], I[fit], rcond=None); p = A @ cc
    test = vis & Z & (np.abs(V[:, 0]) < 0.15) & (V[:, 2] > 0.80) & (V[:, 2] < 1.36)
    print(f'{name}: yaw {c["yaw"]:6.1f} fit-set corr {np.corrcoef(I[fit], p[fit])[0,1]:.3f} (n {fit.sum()}) | TORSO held-out corr {np.corrcoef(I[test], p[test])[0,1]:.3f} (n {test.sum()}), lum std {I[test].std():.1f}, SH coeffs {np.round(cc,1)}')
