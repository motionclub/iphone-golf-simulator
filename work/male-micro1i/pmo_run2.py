"""PMO with smooth symmetric RBF basis.  python3.13 pmo_run2.py <src> <out> <sigma_mm> <spacing_mm> <lam_c> <hmax_mm> [iters] [views]"""
import sys, time
sys.path.insert(0, '.')
from pmo_setup import *

src, out_tag = sys.argv[1], sys.argv[2]
SIG = float(sys.argv[3]) * 1e-3; SPC = float(sys.argv[4]) * 1e-3; LAMC = float(sys.argv[5]); HMAX = float(sys.argv[6])
ITERS = int(sys.argv[7]) if len(sys.argv) > 7 else 5
VNAMES = sys.argv[8].split(',') if len(sys.argv) > 8 else ['front', 'q3L', 'q3R', 'left']
RHO_CLEAN, RHO_STUB = 0.955, 0.88
V0, F, loops = load(src)
views = make_views(tuple(VNAMES))
ZLO = float(sys.argv[10]) if len(sys.argv) > 10 else 1.452
zone = build_zone(V0, margin_z=(ZLO, 1.625))
N0 = vertex_normals(V0, F)
ring = (np.abs(V0[:, 2] - 1.43) < 0.0015)
pb = Problem(V0, F, views, zone, N0, wmask=np.zeros(len(V0)), ring=ring)
Nb = pb.normals(V0); pb.d = Nb
pb.setup_visibility(V0, Nb)
m = feature_masks(V0); Sf = stubble_field(V0, m)
feat = np.maximum.reduce(list(m.values()))
pb.wmask = np.where(zone, 1.0 - feat, 0.0)
pb.rho = RHO_CLEAN * (1.0 - (1.0 - RHO_STUB) * Sf)
fz = contour_freeze(pb, Nb, views)
CW = float(sys.argv[9]) if len(sys.argv) > 9 else 6.0
if CW > 0: add_contour_constraints(pb, V0, w_s=CW, names=tuple(n for n in ('q3L', 'q3R', 'left', 'front') if n in VNAMES))
Phi, C = make_basis(V0[pb.idx], SPC, SIG)
print('free', len(pb.idx), 'basis', Phi.shape[1], 'data-weighted', int((pb.wmask > 0.05).sum()))
t0 = time.time()
c = solve_gn_rbf(pb, Phi, np.zeros(Phi.shape[1]), lam_c=LAMC, fz=fz, iters=ITERS, hmax=HMAX)
h = Phi @ c
print('solve %.0fs; h stats mm: rms %.2f max %.2f min %.2f' % (time.time() - t0, np.sqrt((h ** 2).mean()), h.max(), h.min()))
hfull = np.zeros(len(V0)); hfull[pb.idx] = h
np.save(f'data/V_{out_tag}.npy', V0 + Nb * (hfull[:, None] * 1e-3)); np.save(f'data/h_{out_tag}.npy', hfull)
