import sys
sys.path.insert(0, '.')
from plateview import *
from zone import zone_mask
V = np.load('data/V_base.npy'); N = vertex_normals(V); Z = zone_mask(V)
def poly3(N):
    x, y, z = N[:, 0], N[:, 1], N[:, 2]
    terms = [np.ones_like(x), x, y, z, x * x, y * y, z * z, x * y, y * z, x * z, x ** 3, y ** 3, z ** 3, x * x * y, x * x * z, y * y * x, y * y * z, z * z * x, z * z * y, x * y * z]
    return np.stack(terms, 1)
def sh2s(N):   # x-symmetric SH2 (drop terms odd in x)
    x, y, z = N[:, 0], N[:, 1], N[:, 2]; return np.stack([np.ones_like(x), y, z, y * z, 3 * z * z - 1, x * x - y * y], 1)
for name in ('front', 'back'):
    vw = View(name); body = (V[:, 2] < 1.40) & (np.abs(V[:, 0]) < 0.40); vis = visible(vw, V, N, sel=V[:, 2] < 1.40) & body
    col, row = vw.project(V)
    for sig in (2.5, 4.0):
        I = bilinear(gblur(PLATE, sig), col, row)
        fit = vis & ~Z; test = vis & Z & (np.abs(V[:, 0]) < 0.15) & (V[:, 2] > 0.80) & (V[:, 2] < 1.36)
        for bname, B in (('SH2', sh2), ('SH2-xsym', sh2s), ('poly3', poly3)):
            A = B(N); c, *_ = np.linalg.lstsq(A[fit], I[fit], rcond=None); p = A @ c
            r2f = 1 - ((I[fit] - p[fit]) ** 2).sum() / ((I[fit] - I[fit].mean()) ** 2).sum()
            r2t = 1 - ((I[test] - p[test]) ** 2).sum() / ((I[test] - I[test].mean()) ** 2).sum()
            rms = np.sqrt(((I[test] - p[test]) ** 2).mean()); cor = np.corrcoef(I[test], p[test])[0, 1]
            print(f'{name} blur {sig}: {bname:9s} fit-set R2 {r2f:.3f} ({fit.sum()} verts) | TORSO held-out R2 {r2t:.3f} corr {cor:.3f} rms {rms:.1f} (std {I[test].std():.1f}, n {test.sum()})')
