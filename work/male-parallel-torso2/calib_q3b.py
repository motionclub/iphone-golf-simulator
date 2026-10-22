"""Calibrate the sheet's 3/4 panels (yaw, column offset) by how well camera-frame SH lighting fitted on the limbs explains the panel. Writes data/q3_calib2.json"""
import sys, json
sys.path.insert(0, '.')
from plateview import *
from zone import zone_mask
V = np.load('data/V_base.npy'); N = vertex_normals(V); Z = zone_mask(V)
ini = json.load(open('data/q3_calib.json'))
RANGE = {'q3FL': range(22, 58, 2), 'q3FR': range(-58, -20, 2), 'q3BL': range(122, 160, 2), 'q3BR': range(-160, -120, 2)}
SHB = gblur(SHEET, 1.1)
body = (V[:, 2] < 1.40) & (np.abs(V[:, 0]) < 0.62)
res = {}
for name in RANGE:
    c0 = ini[name]; best = None
    for az in RANGE[name]:
        for dc in range(-14, 15, 2):
            vw = ViewYaw(name, az, c0['col_off'] + dc, 0.00580, c0['sole_row'])
            vis = visible_gen(vw, V, N, sel=V[:, 2] < 1.40, res=1.0, rad=1) & body
            col, row = vw.project(V); I = bilinear(SHB, col, row)
            fit = vis & ~Z; A = sh2c(N, vw)
            c, *_ = np.linalg.lstsq(A[fit], I[fit], rcond=None); r = I[fit] - A[fit] @ c
            r2 = 1 - (r ** 2).sum() / ((I[fit] - I[fit].mean()) ** 2).sum()
            if best is None or r2 > best[0]: best = (r2, az, dc)
    # refine around best with mpp and fine steps
    r2, az, dc = best; best2 = best + (0.00580,)
    for az2 in np.arange(az - 2, az + 2.01, 0.5):
        for dc2 in np.arange(dc - 2, dc + 2.01, 1.0):
            for mpp in (0.00572, 0.00576, 0.00580, 0.00584, 0.00588):
                vw = ViewYaw(name, az2, c0['col_off'] + dc2, mpp, c0['sole_row'])
                vis = visible_gen(vw, V, N, sel=V[:, 2] < 1.40, res=1.0, rad=1) & body
                col, row = vw.project(V); I = bilinear(SHB, col, row); fit = vis & ~Z; A = sh2c(N, vw)
                c, *_ = np.linalg.lstsq(A[fit], I[fit], rcond=None); r = I[fit] - A[fit] @ c; r2b = 1 - (r ** 2).sum() / ((I[fit] - I[fit].mean()) ** 2).sum()
                if r2b > best2[0]: best2 = (r2b, az2, dc2, mpp)
    res[name] = dict(r2=float(best2[0]), yaw=float(best2[1]), col0=float(c0['col_off'] + best2[2]), mpp=float(best2[3]), sole_row=c0['sole_row'])
    print(name, res[name])
json.dump(res, open('data/q3_calib2.json', 'w'), indent=1)
