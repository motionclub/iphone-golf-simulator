"""nxchg5.py: how much the thigh/fold stripe pattern (vertex-normal x component) changed vs FORM4 in the leg-top band: rms and p95 of |dn_x| per z-band"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import photo3 as ph
Z = np.load(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/data/zone5.npz'); EXT = Z['ext']; T5 = Z['torso']
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C4 = np.load(HERE + '/data/co_FORM4_final.npy').astype(np.float64)
N4 = ph.vertex_normals(C4, ph.TRI)

def nxchg(co, zr=(0.62, 0.80), xr=(0.03, 0.17)):
    N = ph.vertex_normals(co, ph.TRI)
    m = EXT & (co[:, 1] > 0.0) & (co[:, 2] >= zr[0]) & (co[:, 2] < zr[1]) & (np.abs(co[:, 0]) >= xr[0]) & (np.abs(co[:, 0]) <= xr[1])
    d = (N - N4)[m]
    return float(np.sqrt((d[:, 0] ** 2).mean())), float(np.percentile(np.abs(d[:, 0]), 95)), float(np.sqrt((d[:, 1] ** 2).mean()))

if __name__ == '__main__':
    for p in sys.argv[1:]:
        a = nxchg(np.load(p).astype(np.float64)); print(os.path.basename(p), 'rms dn_x %.4f p95 %.4f | rms dn_y %.4f' % a)
