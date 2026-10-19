import sys, json; sys.path.insert(0, __file__.rsplit('/',1)[0]); import numpy as np, off
from collections import Counter
h = off.Head(); R = off.ref_tables()
def boundary(h):
    e = np.vstack([h.tri[:, [0, 1]], h.tri[:, [1, 2]], h.tri[:, [2, 0]]]); e.sort(1)
    u, c = np.unique(e, axis=0, return_counts=True); return u[c == 1]
B = boundary(h)
def report(P, label):
    G = h.U(h.warp(h.base, P)) * 1000
    ys = np.array([86, 46, 14, 6, -10, -22, -34, -50, -58, -66, -74, -82, -90, -98, -106, -114, -122, -130])
    half, front = off.slices(G, h.tri, ys)
    hf, _ = off.slices(G, h.tri, ys, zmin=-45)
    print(label)
    for y, a, b in zip(ys, half, hf):
        i = np.argmin(abs(R['y'] - y)); print(f'  y {y:5d} full {a:6.1f} ref {R["half"][i]:6.1f}  front-face(z>-45) {b:6.1f}')
    # eye apertures: boundary vertices with 20<|x|<60, -25<y<15, z>-40
    v = np.unique(B.ravel()); g = G[v]; m = (np.abs(g[:, 0]) > 15) & (np.abs(g[:, 0]) < 62) & (g[:, 1] > -30) & (g[:, 1] < 15) & (g[:, 2] > -45)
    g = g[m & (g[:, 0] > 0)]
    print(f'  eye hole (one side): x {g[:,0].min():.1f}..{g[:,0].max():.1f} (w {np.ptp(g[:,0]):.1f})  y {g[:,1].min():.1f}..{g[:,1].max():.1f} (h {np.ptp(g[:,1]):.1f})')
    # ears: rows where the full silhouette exceeds the face-wall silhouette by > 6 mm
    yy = np.arange(20, -80, -1.0); a, _ = off.slices(G, h.tri, yy); b, _ = off.slices(G, h.tri, yy, zmin=-75)
    S = h.U(h.to_face(h.base)) * 1000
    return G
if __name__ == '__main__':
    P = dict(off.DEFAULT); P.update(json.loads(sys.argv[1]) if len(sys.argv) > 1 else {})
    report(P, json.dumps({k: v for k, v in P.items() if off.DEFAULT[k] != v}))
