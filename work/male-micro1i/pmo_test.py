"""Synthetic validation of PMO: displace the mesh by a known smooth field, synthesise plate images from it, recover the field."""
import sys, time
sys.path.insert(0, '.')
from pmo import *

NOISE = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
LAP = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
MAG = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
V0, F, loops = load('h0')
Msh = Mesh(V0, F)
views = make_views(('front', 'q3L', 'q3R', 'left'))
# free zone
x = np.abs(V0[:, 0]); y = V0[:, 1]; z = V0[:, 2]
zone = (z > 1.47) & (z < 1.64) & (x < 0.075) & (y < -0.06)
free = zone
# directions: smoothed base normals
N0 = vertex_normals(V0, F)
pb = Problem(V0, F, views, free, N0, wmask=np.where(zone, 1.0, 0.0), ring=(np.abs(V0[:, 2] - 1.43) < 0.0015))
N_base = pb.normals(V0)
pb.d = N_base
pb.setup_visibility(V0, N_base)
print('free verts', len(pb.idx), 'visible per view', {k: int(v[free].sum()) for k, v in pb.vis.items()})
# ground truth displacement: 3 Gaussian bumps along normals
def bump(cx, cz, rx, rz, amp):
    return amp * np.exp(-0.5 * (((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2))
h_true_full = bump(0.050, 1.545, 0.018, 0.014, 0.004) + bump(0.0, 1.62, 0.03, 0.012, -0.003) + bump(0.0, 1.50, 0.02, 0.012, 0.003) * (x < 0.09)
h_true = np.where(free, h_true_full, 0.0) * 1000.0           # millimetres
# mirror the malar bump to -x side as bump uses |x| already (x=abs)
P_true = V0.copy(); P_true += pb.d * (h_true[:, None] * 1e-3)
N_true = pb.normals(P_true)
# synthetic plate images
def synth(view, P, N):
    Q, Nq = fold_pts(P, N, view.fold)
    col, row = view.project(Q)
    s = view.a + view.b * np.clip(Nq @ view.l, 0, None)
    ok = pb.vis[view.name]          # visible vertices only (depth-tested)
    img = np.zeros((720, 1280)); wgt = np.zeros((720, 1280))
    c0 = np.floor(col[ok]).astype(int); r0 = np.floor(row[ok]).astype(int); fc = col[ok] - c0; fr = row[ok] - r0
    for dc, dr, w in ((0, 0, (1 - fc) * (1 - fr)), (1, 0, fc * (1 - fr)), (0, 1, (1 - fc) * fr), (1, 1, fc * fr)):
        cc = np.clip(c0 + dc, 0, 1279); rr_ = np.clip(r0 + dr, 0, 719)
        np.add.at(img, (rr_, cc), w * s[ok]); np.add.at(wgt, (rr_, cc), w)
    sig = 1.6
    num = gauss_blur(img, sig); den = gauss_blur(wgt, sig)
    out = np.where(den > 1e-3, num / np.maximum(den, 1e-9), 100.0)
    return out
rng = np.random.default_rng(1)
for v in views:
    v.img = synth(v, P_true, N_true) + rng.normal(0, NOISE, (720, 1280))
    v.img = gauss_blur(v.img, 1.0)
# starting residual at h=0
r0 = pb.residuals(np.zeros(len(pb.idx)))
print('rms residual at h=0: %.3f over %d rows' % (np.sqrt((r0 ** 2).mean()), len(r0)))
r_true = pb.residuals(h_true[pb.idx])
print('rms residual at h_true: %.3f' % np.sqrt((r_true ** 2).mean()))
t0 = time.time()
h = solve_gn(pb, np.zeros(len(pb.idx)), lam_lap=LAP, lam_mag=MAG, iters=5, verbose=True)
print('solve %.1fs' % (time.time() - t0))
ht = h_true[pb.idx]
print('recovered: corr %.3f, rms err %.3f mm (rms true %.3f mm), max |h| %.2f mm' % (np.corrcoef(h, ht)[0, 1], np.sqrt(((h - ht) ** 2).mean()), np.sqrt((ht ** 2).mean()), np.abs(h).max()))
np.save('data/pmo_test_h.npy', h)
