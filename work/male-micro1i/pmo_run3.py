"""PMO, broad-relief variant.  python3.13 pmo_run3.py <src> <out> <sigma_mm> <spacing_mm> <lam_c> <hmax_mm> <contour_w> [iters]"""
import sys, time
sys.path.insert(0, '.')
from pmo_setup import *
src, out_tag = sys.argv[1], sys.argv[2]
SIG = float(sys.argv[3]) * 1e-3; SPC = float(sys.argv[4]) * 1e-3; LAMC = float(sys.argv[5]); HMAX = float(sys.argv[6]); CW = float(sys.argv[7])
ITERS = int(sys.argv[8]) if len(sys.argv) > 8 else 8
V0, F, loops = load(src)
views = make_views(('front', 'q3L', 'q3R', 'left'))
zone = build_zone(V0, margin_z=(1.452, 1.625))
N0 = vertex_normals(V0, F); ring = (np.abs(V0[:, 2] - 1.43) < 0.0015)
pb = Problem(V0, F, views, zone, N0, wmask=np.zeros(len(V0)), ring=ring)
Nb = pb.normals(V0); pb.d = Nb; pb.setup_visibility(V0, Nb)
m = feature_masks(V0); Sf = stubble_field(V0, m)
feat = np.maximum.reduce(list(m.values()))
x = np.abs(V0[:, 0]); z = V0[:, 2]
# registration-sensitive regions: nose block, eye surround, mouth/lips + corners, brows
nose = (1 - sstep(0.030, 0.038, x)) * sstep(1.521, 1.530, z) * (1 - sstep(1.590, 1.602, z))
eye_dil = 1.0 - sstep(0.010, 0.020, S.poly_dist(x, z, S.smooth_poly(S.eye_poly())))
mouth = (1 - sstep(0.046, 0.054, x)) * sstep(1.488, 1.496, z) * (1 - sstep(1.522, 1.530, z))
brow = 1.0 - sstep(0.008, 0.016, np.minimum.reduce([seg_dist_pts(x, z, [((227.6 - c) * K, float(H.zrow(r))) for c, r in BROW_CL])]))
excl = np.maximum.reduce([nose, eye_dil, mouth, brow, feat])
pb.wmask = np.where(zone, 1.0 - excl, 0.0)
pb.rho = 0.955 * (1.0 - 0.12 * Sf)
fz = contour_freeze(pb, Nb, views)
add_contour_constraints(pb, V0, w_s=CW, names=('q3L', 'q3R', 'left', 'front'))
Phi, C = make_basis(V0[pb.idx], SPC, SIG)
print('free', len(pb.idx), 'basis', Phi.shape[1], 'data-weighted verts', int((pb.wmask > 0.05).sum()))
t0 = time.time()
c = solve_gn_rbf(pb, Phi, np.zeros(Phi.shape[1]), lam_c=LAMC, fz=fz, iters=ITERS, hmax=HMAX)
h = Phi @ c
print('solve %.0fs; h stats mm: rms %.2f max %.2f min %.2f' % (time.time() - t0, np.sqrt((h ** 2).mean()), h.max(), h.min()))
hfull = np.zeros(len(V0)); hfull[pb.idx] = h
np.save(f'data/V_{out_tag}.npy', V0 + Nb * (hfull[:, None] * 1e-3)); np.save(f'data/h_{out_tag}.npy', hfull)
