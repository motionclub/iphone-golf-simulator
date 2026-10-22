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
chains = MH.build_chains(Q)
idxmap = -np.ones(len(co), int); idxmap[sel] = np.arange(len(sel))
Ts = idxmap[T]; Ts = Ts[np.all(Ts >= 0, axis=1)]
qa, qb, qc = Q[Ts[:, 0]], Q[Ts[:, 1]], Q[Ts[:, 2]]
Qs = np.concatenate([Q, (qa + qb) / 2, (qb + qc) / 2, (qc + qa) / 2, (qa + qb + qc) / 3])
phi, U_g, V_g = 28, -0.015, -0.03
a = WR.axis_dir(phi)
W_g = WR.lift_for_clearance(Qs, (U_g, V_g), a, margin=0.0005)
O = np.array([U_g, V_g, W_g])
for name, ch in chains.items():
    M = ch.J[0]
    x_f, y_f, z_f = FW.finger_local_frame(M, ch.axis_dir)
    loc = np.stack([(Q - M) @ x_f, (Q - M) @ y_f, (Q - M) @ z_f], 1)
    core = ch.member > 0.5
    zin = loc[core & (loc[:, 0] > 0.005), 2]
    t_off = float(np.percentile(zin, 99)) + 0.0004
    Cc3 = FW.axis_plane_centre(O, a, M, y_f)
    B, th, Cc2 = FW.offset_curve_2d(Cc3, M, x_f, z_f, a, WR.R_GRIP, t_off)
    inside = None
    # is M (origin) inside the offset curve? polar test
    ang = np.arctan2(-Cc2[1], -Cc2[0]) % (2 * np.pi)
    k = int(ang / (2 * np.pi) * len(B)) % len(B)
    r_curve = np.linalg.norm(B[k] - Cc2)
    d_M = np.linalg.norm(Cc2)
    print(f'{name}: M={M.round(4)}  t_off={t_off*1000:.1f}mm  Cc2={Cc2.round(4)}  |Cc2|={d_M*1000:.1f}mm  curve radius toward M={r_curve*1000:.1f}mm  -> M {"INSIDE" if d_M < r_curve else "outside"}  zrange core [{zin.min()*1000:.1f},{zin.max()*1000:.1f}]')
