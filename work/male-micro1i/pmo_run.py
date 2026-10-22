"""Run PMO on real plates.  python3.13 pmo_run.py <src_tag> <out_tag> <lam_lap> <lam_mag> <hmax_mm> [iters] [views]"""
import sys, time, json
sys.path.insert(0, '.')
from pmo_setup import *

src, out_tag = sys.argv[1], sys.argv[2]
LAP = float(sys.argv[3]); MAG = float(sys.argv[4]); HMAX = float(sys.argv[5])
ITERS = int(sys.argv[6]) if len(sys.argv) > 6 else 6
VNAMES = sys.argv[7].split(',') if len(sys.argv) > 7 else ['front', 'q3L', 'q3R', 'left']
RHO_CLEAN, RHO_STUB = 0.955, 0.88

V0, F, loops = load(src)
views = make_views(tuple(VNAMES))
zone = build_zone(V0)
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
print('free', len(pb.idx), 'data-weighted', int((pb.wmask > 0.05).sum()), 'frozen-at-contour verts', int((fz[pb.idx] > 20).sum()))
# mirror map within the free set
fi = pb.idx; Pm = V0[fi].copy(); Pm[:, 0] *= -1
mir = np.arange(len(fi))
for s in range(0, len(fi), 400):
    d2 = ((Pm[s:s + 400, None, :] - V0[fi][None, :, :]) ** 2).sum(axis=2)
    j = d2.argmin(axis=1); ok = np.sqrt(d2[np.arange(len(j)), j]) < 0.0015
    mir[s:s + 400] = np.where(ok, j, np.arange(s, s + len(j)))
sym = lambda hh: 0.5 * (hh + hh[mir])
t0 = time.time()
h = solve_gn(pb, np.zeros(len(fi)), lam_lap=LAP, lam_mag=MAG, freeze_w=fz, iters=ITERS, hmax=HMAX, verbose=True, symmetrize=sym)
print('solve %.0fs' % (time.time() - t0))
hfull = np.zeros(len(V0)); hfull[fi] = h
V1 = V0 + Nb * (hfull[:, None] * 1e-3)
np.save(f'data/V_{out_tag}.npy', V1); np.save(f'data/h_{out_tag}.npy', hfull)
print('h stats mm: rms %.2f  max %.2f  min %.2f' % (np.sqrt((h ** 2).mean()), h.max(), h.min()))
