"""Profile silhouette error (mm, mesh - plate) at the lip rows for variants: python3.13 lipprofile_err.py <tag> ... (data/V_<tag>.npy; 'start' = current blend start)"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from l_edit import *
ctx = LCtx(with_dist=False); V0 = ctx.V0; E = ctx.E
vs = {'start': V0}; vs.update({t: np.load(W / f'data/V_{t}.npy') for t in sys.argv[1:]})
head = (V0[:, 2] > 1.40) & (np.abs(V0[:, 0]) < 0.12) & (ctx.M.deg > 0)
zs = np.arange(1.480, 1.526, 0.002); rows = []
for z in zs:
    r = rowz(z); k = int(r); pL = plate_sil_rows('left', [r]); pR = plate_sil_rows('right', [r])
    yl = prof_y(pL[k][0], 'left') * 1000; yr = prof_y(pR[k][0], 'right') * 1000
    rows.append([z * 1000, yl, yr] + [plane_section(V, E, 2, z, head)[:, 1].min() * 1000 for V in vs.values()])
R = np.array(rows); names = list(vs)
print('mean abs err vs L / R plate (z 1480-1524), and upper-lip rows 1514-1520 / lower-lip rows 1496-1506 mean signed error (L,R):')
for i, n in enumerate(names):
    y = R[:, 3 + i]; e = np.abs(np.stack([y - R[:, 1], y - R[:, 2]], 1))
    up = (R[:, 0] >= 1514) & (R[:, 0] <= 1520); lw = (R[:, 0] >= 1496) & (R[:, 0] <= 1506)
    print(f'  {n:6s} mean|err| {e[:, 0].mean():.2f} / {e[:, 1].mean():.2f} max {e[:, 0].max():.2f} / {e[:, 1].max():.2f} | upper {np.mean(y[up] - R[up, 1]):+.2f},{np.mean(y[up] - R[up, 2]):+.2f} | lower {np.mean(y[lw] - R[lw, 1]):+.2f},{np.mean(y[lw] - R[lw, 2]):+.2f}')
