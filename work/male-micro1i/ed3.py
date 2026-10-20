"""Edit e3: fair the lower face (remove lumps) while restoring the plate-matched centre-line profile."""
import sys; sys.path.insert(0, '.')
from edlib import *


def centerline(V, zs, xw=0.004, front=True):
    """front-most y at |x|<xw for the z levels (median of the 3 nearest-in-z vertices of the front shell)"""
    out = []
    for z in zs:
        sel = np.where((np.abs(V[:, 0]) < xw) & (np.abs(V[:, 2] - z) < 0.0025) & (V[:, 1] < -0.06))[0]
        out.append(V[sel, 1].min() if len(sel) else np.nan)
    return np.array(out)


def lower_mask(V, z0=1.456, z1=1.532, xmax=0.078, ymax=-0.045):
    ax = np.abs(V[:, 0]); z = V[:, 2]; y = V[:, 1]
    w = sstep(z0 - 0.004, z0 + 0.006, z) * (1 - sstep(z1 - 0.006, z1 + 0.004, z))
    w = w * (1 - sstep(xmax - 0.010, xmax, ax)) * (1 - sstep(ymax + 0.0, ymax + 0.020, y))
    # keep the nose block untouched
    w = w * (1 - (1 - sstep(0.026, 0.034, ax)) * sstep(1.524, 1.532, z))
    return w


def e3_clean(V, M, iters=14, strength=1.0, restore_profile=True):
    V0 = V.copy()
    w = lower_mask(V) * strength
    P = M.taubin(V, w, iters=iters)
    if restore_profile:
        zs = np.arange(1.452, 1.532, 0.002)
        c0 = centerline(V0, zs); c1 = centerline(P, zs)
        ok = ~(np.isnan(c0) | np.isnan(c1))
        dy = np.interp(P[:, 2], zs[ok], (c0 - c1)[ok])
        dy = poly_smooth(zs[ok] * 1000, (c0 - c1)[ok], 2.0) if False else dy
        gx = np.exp(-0.5 * (P[:, 0] / 0.020) ** 2)
        P[:, 1] += dy * gx * (w > 0.02) * np.clip(w * 2, 0, 1)
    return P


if __name__ == '__main__':
    tag_in = sys.argv[1] if len(sys.argv) > 1 else 'p9'; tag_out = sys.argv[2] if len(sys.argv) > 2 else 'e3'
    iters = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    V0, F, loops = load(tag_in); M = Mesh(V0, F)
    V1 = e3_clean(V0, M, iters=iters)
    d = np.linalg.norm(V1 - V0, axis=1)
    print('moved verts', int((d > 1e-6).sum()), 'max mm %.2f  mean(moved) mm %.2f' % (d.max() * 1000, d[d > 1e-6].mean() * 1000))
    np.save(f'data/V_{tag_out}.npy', V1)


def e3b_chinband(V, M, iters=25):
    """smooth the chin-band / under-chin / jaw-underside zigzag (coarse-to-dense boundary) -- keeps the centre-line profile"""
    V0 = V.copy()
    ax = np.abs(V[:, 0]); z = V[:, 2]; y = V[:, 1]
    w = sstep(1.447, 1.455, z) * (1 - sstep(1.468, 1.478, z)) * (1 - sstep(0.082, 0.092, ax)) * (1 - sstep(-0.01, 0.02, y))
    P = M.taubin(V, w, iters=iters)
    zs = np.arange(1.448, 1.478, 0.002)
    c0 = centerline(V0, zs); c1 = centerline(P, zs)
    ok = ~(np.isnan(c0) | np.isnan(c1))
    if ok.sum() > 3:
        dy = np.interp(P[:, 2], zs[ok], (c0 - c1)[ok])
        P[:, 1] += dy * np.exp(-0.5 * (P[:, 0] / 0.025) ** 2) * np.clip(w * 2, 0, 1)
    return P
