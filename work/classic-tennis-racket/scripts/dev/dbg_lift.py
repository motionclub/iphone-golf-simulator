import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import male_hand as MH
import wrap as WR
reset_scene()
body = load_body_copy('male')
co = mesh_co(body); T = mesh_tris(body)
sel, c, u, v, p = MH.frame_from_body(co)
Q = MH.to_hand(co[sel], c, u, v, p)
idxmap = -np.ones(len(co), int); idxmap[sel] = np.arange(len(sel))
Ts = idxmap[T]; Ts = Ts[np.all(Ts >= 0, axis=1)]
a_, b_, c_ = Q[Ts[:, 0]], Q[Ts[:, 1]], Q[Ts[:, 2]]
Qs = np.concatenate([Q, (a_ + b_) / 2, (b_ + c_) / 2, (c_ + a_) / 2, (a_ + b_ + c_) / 3])
print('Wp stats: palm-side max by (U,V) cell (2cm cells): printing the top surface height map Wp_max')
us = np.arange(-0.12, 0.10, 0.02); vs = np.arange(-0.08, 0.08, 0.02)
print('        V:' + ' '.join(f'{x:+.2f}' for x in vs))
for u0 in us:
    row = []
    for v0 in vs:
        m = (Qs[:, 0] >= u0) & (Qs[:, 0] < u0 + 0.02) & (Qs[:, 1] >= v0) & (Qs[:, 1] < v0 + 0.02)
        row.append(f'{Qs[m, 2].max():+.3f}' if m.any() else '  .  ')
    print(f'U={u0:+.2f}  ' + ' '.join(row))
for phi in (28,):
    a = WR.axis_dir(phi)
    for U_g in (0.0,):
        d = Qs[:, :2] - np.array([U_g, 0.0])[None, :]
        perp = np.abs(d[:, 0] * a[1] - d[:, 1] * a[0])
        need = WR.R_GRIP + 0.0005
        s = perp < need
        val = Qs[:, 2] + np.sqrt(np.maximum(need ** 2 - perp ** 2, 0))
        val[~s] = -1
        order = np.argsort(-val)[:8]
        print('limiting points for phi', phi, 'U_g', U_g)
        for i in order: print('   Q', Qs[i].round(4), 'perp', round(float(perp[i]), 4), 'val', round(float(val[i]), 4))
