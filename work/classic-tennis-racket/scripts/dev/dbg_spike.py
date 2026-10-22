import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import male_hand as MH
import wrap as WR
import fingerwrap as FW
from armpose import ArmRig
reset_scene()
body = load_body_copy('male')
co = mesh_co(body); T = mesh_tris(body)
sel, c, u, v, p = MH.frame_from_body(co)
Q = MH.to_hand(co[sel], c, u, v, p)
chains = MH.build_chains(Q)
phi, U_g, V_g = 40, -0.02, -0.015
a = WR.axis_dir(phi)
idxmap = -np.ones(len(co), int); idxmap[sel] = np.arange(len(sel))
Ts = idxmap[T]; Ts = Ts[np.all(Ts >= 0, axis=1)]
qa, qb, qc = Q[Ts[:, 0]], Q[Ts[:, 1]], Q[Ts[:, 2]]
Qs = np.concatenate([Q, (qa + qb) / 2, (qb + qc) / 2, (qc + qa) / 2, (qa + qb + qc) / 3])
W_g = WR.lift_for_clearance(Qs, (U_g, V_g), a, margin=0.0005)
O = np.array([U_g, V_g, W_g])
Qn = Q.copy()
for name, ch in chains.items():
    out, info = FW.wrap_finger(Q, ch.member, ch.J[0], ch.axis_dir, None, O, a, length=MH.FINGERS[name]['tip'] - MH.U_MCP)
    Qn += (out - Q)
def stretch(P, label):
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    L0 = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
    L1 = np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1)
    r = L1 / np.maximum(L0, 1e-6)
    i = np.argsort(-L1)[:5]
    print(label, 'max edge', L1.max().round(3), 'rest', L0[np.argmax(L1)].round(4), ' worst ratio', r.max().round(1))
    return e[np.argmax(L1)], P
co2 = co.copy(); co2[sel] = MH.from_hand(Qn, c, u, v, p)
e, _ = stretch(co2, 'after wrap')
S = np.array([-0.2102, -0.0291, 1.3896]); E = np.array([-0.3345, -0.0380, 1.1535]); Wr = np.array([-0.529, -0.081, 0.967])
rig = ArmRig(S, E, Wr)
force = np.zeros(len(co)); force[sel] = 1.0
rig.force = force
co3 = rig.skin(co2, 16, 95, P_rest=co)
e, _ = stretch(co3, 'after arm')
print('worst edge verts rest', co[e[0]].round(3), co[e[1]].round(3), 'wrapped', co2[e[0]].round(3), co2[e[1]].round(3), 'posed', co3[e[0]].round(3), co3[e[1]].round(3))
m = rig.member(co2)
print('member of the two verts (from wrapped pos):', m[e[0]].round(3), m[e[1]].round(3), ' from rest pos:', rig.member(co)[e[0]].round(3), rig.member(co)[e[1]].round(3))

e_all = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
L1 = np.linalg.norm(co3[e_all[:, 0]] - co3[e_all[:, 1]], axis=1)
order = np.argsort(-L1)[:6]
mm = rig.member(co)
for i in order:
    a_, b_ = e_all[i]
    print('edge len %.3f rest %s %s  posed %s %s member %.2f %.2f' % (L1[i], co[a_].round(3), co[b_].round(3), co3[a_].round(3), co3[b_].round(3), mm[a_], mm[b_]))
