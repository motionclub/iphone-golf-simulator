"""MicroF3 data plots -> proof/F3_jaw_contour_vs_plate.png, proof/F3_jaw_wall_normal_elevation.png"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np
import fl, meshlib as ml, slices as sl, contour as ct, trial, make_f3
from analytic_normals import surf_normals
from analytic_grid import grid
from plot2d import plot2d
D = fl.W / 'data/dump'
def load(tag):
    z = np.load(D / f'{tag}.npz'); V = z['Body_F_V']; F = [z['Body_F_F'][z['Body_F_Foff'][i]:z['Body_F_Foff'][i + 1]] for i in range(len(z['Body_F_Foff']) - 1)]
    return V, F
# ---------------------------------------------------------------- contour: half width (mm, u) vs height (mm, v), mesh slices vs plate
zs = np.arange(1.446, 1.4951, 0.001); tg = ct.target_hw(zs)
cur = [(np.stack([tg * 1000, zs * 1000], 1), (240, 240, 240), 3, 'PLATE silhouette (cubic fit of the plate rows)')]
zz, hw = ct._plate(); m = (zz > 1.446) & (zz < 1.4925)
cols = {'F1': (200, 120, 60), 'F2': (255, 90, 60), 'F3': (90, 230, 140)}
for tag in ('F2', 'F3'):
    V, F = load(tag); T = ml.tri_fan(F); out = []
    for z in zs:
        pl = sl.chain(sl.slice_axis(V, T, 2, float(z))); out.append(max(np.abs(p[:, 0]).max() for p in pl))
    cur.append((np.stack([np.array(out) * 1000, zs * 1000], 1), cols[tag], 2, f'{tag} mesh (front-view jaw contour)'))
marks = [(float(h) * 1000, float(z) * 1000, (255, 255, 120)) for z, h in zip(zz[m], hw[m])]
plot2d(cur, (45, 95, 1444, 1496), 14.0, str(fl.W / 'proof/F3_jaw_contour_vs_plate.png'), grid=2.0, title='jaw contour: half width (mm) vs height (mm); yellow circles = raw plate rows', marks=marks, label_every=10)
# ---------------------------------------------------------------- wall normal elevation along the visible jaw wall (analytic surfaces of F2 and F3)
def eps_curve(H, yc):
    V, F = grid(H, nth=361, nph=240, th=(0, 100), ph=(-62, 10)); N = surf_normals(H, V)
    eps = np.degrees(np.arcsin(np.clip(N[:, 2], -1, 1)))
    sel = np.abs(V[:, 1] - yc) < 0.0015; z = V[sel, 2]; e = eps[sel]; x = V[sel, 0]; out = []
    for zb in np.arange(1.440, 1.520, 0.002):
        mm = (z >= zb) & (z < zb + 0.002)
        if mm.sum() == 0: continue
        i = np.argmax(x[mm]); out.append((e[mm][i], (zb + 0.001) * 1000))
    return np.array(out)
H2, _ = trial.make_H(); H3, _ = trial.make_H(**make_f3.KW)
cur = []
for yc, shade in ((-0.030, 1.0), (0.0, 0.6)):
    for tag, H in (('F2', H2), ('F3', H3)):
        c = eps_curve(H, yc); col = tuple(int(v * shade) for v in cols[tag])
        cur.append((c, col, 2, f'{tag} analytic surface, y = {yc*1000:.0f} mm'))
plot2d(cur, (-60, 5, 1440, 1520), 12.0, str(fl.W / 'proof/F3_jaw_wall_normal_elevation.png'), grid=5.0, title='visible jaw wall: normal elevation (deg, u) vs height (mm, v)', label_every=10)
print('plots done')
