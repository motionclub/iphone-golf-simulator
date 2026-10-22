"""Scan the grip placement (U_g, phi) for the male hand: analytic lift + sequential-contact wrap; report contacts / penetration."""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import male_hand as MH
from handpose import apply_chain
import wrap as WR

reset_scene()
body = load_body_copy('male')
co = mesh_co(body)
T = mesh_tris(body)
sel, c, u, v, p = MH.frame_from_body(co)
Q = MH.to_hand(co[sel], c, u, v, p)
# denser surface samples (vertices + edge midpoints) of the hand subset for the clearance lift
idxmap = -np.ones(len(co), int); idxmap[sel] = np.arange(len(sel))
Ts = idxmap[T]; Ts = Ts[np.all(Ts >= 0, axis=1)]
a_, b_, c_ = Q[Ts[:, 0]], Q[Ts[:, 1]], Q[Ts[:, 2]]
Qs = np.concatenate([Q, (a_ + b_) / 2, (b_ + c_) / 2, (c_ + a_) / 2, (a_ + b_ + c_) / 3])
chains = MH.build_chains(Q)
thumb = MH.build_thumb(Q)
amax = [np.radians(90), np.radians(105), np.radians(80)]
print('phi U_g V_g | lift | per finger: angles(deg) contacts')
for phi in (28, 36, 44):
    for U_g in (-0.03, -0.015, 0.0):
        for V_g in (-0.045, -0.03, -0.015):
            a = WR.axis_dir(phi)
            W_g = WR.lift_for_clearance(Qs, (U_g, V_g), a, margin=0.0005)
            O = np.array([U_g, V_g, W_g])
            row = []
            tot = 0
            for name in ('index', 'middle', 'ring', 'pinky'):
                ang, idx, Pn, cont = WR.wrap_digit(Q, chains[name], O, a, amax)
                dmin = WR.cyl_dist(Pn, O, a).min()
                row.append(f"{name[:3]}:{np.degrees(ang[0]):.0f}/{np.degrees(ang[1]):.0f}/{np.degrees(ang[2]):.0f}{''.join('Y' if x else 'n' for x in cont)} d={dmin*1000:+.1f}")
                tot += sum(np.degrees(ang))
            print(f"phi={phi:2d} U_g={U_g:+.3f} V_g={V_g:+.3f} | W_g={W_g:.4f} | " + ' | '.join(row) + f' | sum={tot:.0f}')
