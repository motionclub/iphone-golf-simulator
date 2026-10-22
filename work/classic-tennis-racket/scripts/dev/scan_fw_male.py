import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import male_hand as MH
import wrap as WR
import fingerwrap as FW
reset_scene()
body = load_body_copy('male')
co = mesh_co(body); T = mesh_tris(body)
sel, c, u, v, p = MH.frame_from_body(co)
Q = MH.to_hand(co[sel], c, u, v, p)
idxmap = -np.ones(len(co), int); idxmap[sel] = np.arange(len(sel))
Ts = idxmap[T]; Ts = Ts[np.all(Ts >= 0, axis=1)]
qa, qb, qc = Q[Ts[:, 0]], Q[Ts[:, 1]], Q[Ts[:, 2]]
Qs = np.concatenate([Q, (qa + qb) / 2, (qb + qc) / 2, (qc + qa) / 2, (qa + qb + qc) / 3])
chains = MH.build_chains(Q)
print('phi  U_g    V_g   | W_g   | finger: disp(mm)/mind(mm)  ...')
for phi in (48, 52, 56):
    for U_g in (-0.04, -0.03, -0.02, -0.01):
        for V_g in (-0.03, -0.015, 0.0):
            a = WR.axis_dir(phi)
            W_g = WR.lift_for_clearance(Qs, (U_g, V_g), a, margin=0.0005)
            O = np.array([U_g, V_g, W_g])
            Qn = Q.copy(); row = []; ok = True; worst = 9
            for name in ('index', 'middle', 'ring', 'pinky'):
                ch = chains[name]
                out, info = FW.wrap_finger(Q, ch.member, ch.J[0], ch.axis_dir, None, O, a, length=MH.FINGERS[name]['tip'] - MH.U_MCP)
                ok &= info['ok']
                Qn += (out - Q)
                m = ch.member > 0.5
                d = WR.cyl_dist(Qn[m], O, a)
                disp = np.linalg.norm((Qn - Q)[m], axis=1).max() * 1000
                row.append(f'{name[:3]} {disp:3.0f}/{d.min()*1000:+4.1f}')
                worst = min(worst, d.min() * 1000)
            print(f'{phi}  {U_g:+.3f} {V_g:+.3f} | {W_g:.4f} | ' + ' | '.join(row) + f' | ok={ok} worst={worst:+.1f}')
