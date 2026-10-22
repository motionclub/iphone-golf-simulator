"""Cross-sections perpendicular to the forearm axis (arms3.AX) near the wrist, current mesh. py.sh wrist_probe.py"""
import sys, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
from hlib import *
M = Mesh.from_npz(W / 'data/mesh_cur.npz'); V = M.V.astype(np.float64)
AX = np.array([0.678, -0.178, -0.713]); AX /= np.linalg.norm(AX); C0 = np.array([0.437, -0.061, 1.064])
side = +1
Q = V.copy(); Q[:, 0] *= side
gx = Q[:, 0]
sel = (gx > 0.30) & (Q[:, 2] < 1.10)
t = (Q - C0) @ AX
# local hand axes expressed via the same frame: use a' (A) and n (N) projected to the plane perpendicular to AX
a_dir = A - A.dot(AX) * AX; a_dir /= np.linalg.norm(a_dir); n_dir = np.cross(AX, a_dir)
print('hand frame D.AX = %.3f' % D.dot(AX), ' w=0 (O2) at t=%.4f' % ((O2 - C0) @ AX))
print('  t(mm)  w_of_centroid  width_a  depth_n  [mm]  (slab 8 mm, arm+hand verts only; thumb included above w>0)')
for t0 in np.arange(0.00, 0.34, 0.01):
    m = sel & (t >= t0) & (t < t0 + 0.01)
    if m.sum() < 6: continue
    P = Q[m]; pa = (P - C0) @ a_dir; pn = (P - C0) @ n_dir
    w = ((P - O2) @ D).mean()
    print('  %5.0f  %8.1f   %6.1f  %6.1f' % ((t0 + 0.005) * 1000, w * 1000, (pa.max() - pa.min()) * 1000, (pn.max() - pn.min()) * 1000))
