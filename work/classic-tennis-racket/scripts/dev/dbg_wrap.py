import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import male_hand as MH
from handpose import apply_chain
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
chains = MH.build_chains(Q)
phi, U_g, V_g = 28, 0.0, 0.0
a = WR.axis_dir(phi)
W_g = WR.lift_for_clearance(Qs, (U_g, V_g), a, margin=0.0005)
O = np.array([U_g, V_g, W_g])
ch = chains['middle']
W = ch.bone_weights(Q)
idx = np.where(ch.member > 0.02)[0]
Qi = Q[idx]; Wi = W[idx]
print('middle finger joints', [j.round(4).tolist() for j in ch.J], 'axis', ch.axis_dir.round(3), 'cyl O', O.round(4), 'a', a.round(3))
for ang1 in (0, 20, 30, 40, 44, 50):
    P1 = apply_chain(Qi, ch, [np.radians(ang1), 0, 0], W=Wi)
    d = WR.cyl_dist(P1, O, a)
    t_rest = (Qi - ch.J[1]) @ ch.axis_dir
    print(f'MCP={ang1:3d}: dmin all={d.min()*1000:.2f}mm  at t_rest(PIP-rel)={t_rest[d.argmin()]:.3f}  bone w={Wi[d.argmin()].round(2)}  P={P1[d.argmin()].round(3)}')
    # min per bone
    for k in (1, 2, 3):
        m = Wi[:, k] > 0.6
        if m.any():
            print(f'    bone{k}: n={m.sum()} dmin={d[m].min()*1000:.2f}mm  dmax={d[m].max()*1000:.1f}mm')
