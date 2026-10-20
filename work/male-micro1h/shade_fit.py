"""Analysis-by-synthesis helper: fit a Lambert light to the plate dome, then compare predicted shading of the sculpted head to the plate face.
Pure numpy (no Blender): proxy points -> stage1 -> normals -> orthographic splat at plate scale."""
import sys, math
sys.path.insert(0, '.')
import numpy as np
from PIL import Image
import h1lib as H, loft as L, sculpt as S, proxy as PX
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
K = H.K; TOP = H.TOP
plate = Image.open(R + 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('L')
D = np.load('data/proxy_L3.npz', allow_pickle=True); V0 = D['V']; F0 = D['F']


def stage1(P, prm=None, nf=None):
    loft = L.Loft(nf=nf) if nf is not None else L.Loft()
    P0, _, _ = L.remap(P, loft)
    P1, _ = S.apply(P0, np.zeros_like(P0), prm or S.PRM, ('nose', 'orbit', 'brow', 'cheek', 'eye', 'mouth', 'ear'), F=None)
    keep = P[:, 2] < 1.462; P1[keep] = P[keep]
    return P1


FRONT = dict(box=(5, 62, 433, 352))


def splat_front(P, N, box=FRONT['box'], scale=1):
    """returns (Nimg (h,w,3), depth (h,w)) nearest-surface normals seen from the front (camera at -y)"""
    x0, y0, x1, y1 = box; w = (x1 - x0) * scale; h = (y1 - y0) * scale
    col = (227.6 + P[:, 0] / K - x0) * scale; row = (76 + (TOP - P[:, 2]) / K - y0) * scale
    ci = np.round(col).astype(int); ri = np.round(row).astype(int)
    ok = (ci >= 0) & (ci < w) & (ri >= 0) & (ri < h) & (N[:, 1] < 0.2)
    depth = np.full((h, w), np.inf); idx = -np.ones((h, w), int)
    flat = ri[ok] * w + ci[ok]; vi = np.where(ok)[0]
    order = np.argsort(-P[vi, 1])        # farthest first, nearest (most negative y) written last
    d = depth.ravel(); ix = idx.ravel()
    ix[flat[order]] = vi[order]
    d[flat[order]] = P[vi[order], 1]
    Nimg = np.zeros((h, w, 3)); m = idx >= 0
    Nimg[m] = N[idx[m]]
    # fill isolated holes: uncovered pixels with >=3 covered 8-neighbours take the mean neighbour normal
    for _ in range(2):
        pad = np.pad(m, 1); cnt = sum(pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + w].astype(int) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
        hole = (~m) & (cnt >= 3)
        if not hole.any(): break
        acc = np.zeros_like(Nimg); padN = np.pad(Nimg, ((1, 1), (1, 1), (0, 0))); padm = np.pad(m, 1)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if (dy, dx) == (0, 0): continue
                acc += padN[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] * padm[1 + dy:1 + dy + h, 1 + dx:1 + dx + w][..., None]
        nn = np.linalg.norm(acc, axis=2, keepdims=True) + 1e-12
        Nimg[hole] = (acc / nn)[hole]; m = m | hole
    return Nimg, depth, m


def lambert(Nimg, l, a, b):
    return a + b * np.clip(Nimg @ l, 0, None)


def fit_light(Nimg, mask, lum, region):
    """grid search of the light direction on the dome region; returns (l, a, b, rms)"""
    r0, r1, c0, c1 = region
    m = mask[r0:r1, c0:c1]; Ns = Nimg[r0:r1, c0:c1][m]; Ls = lum[r0:r1, c0:c1][m]
    best = None
    for az in np.arange(-80, 81, 4):
        for el in np.arange(-20, 81, 4):
            a_ = math.radians(az); e_ = math.radians(el)
            l = np.array([math.sin(a_) * math.cos(e_), -math.cos(a_) * math.cos(e_), math.sin(e_)])   # towards the light (camera side = -y)
            s = np.clip(Ns @ l, 0, None)
            A = np.stack([np.ones_like(s), s], axis=1)
            sol, res, _, _ = np.linalg.lstsq(A, Ls, rcond=None)
            rms = np.sqrt(np.mean((A @ sol - Ls) ** 2))
            if best is None or rms < best[3]: best = (l, sol[0], sol[1], rms, az, el)
    return best


if __name__ == '__main__':
    P1 = stage1(V0); N1 = PX.vertex_normals(P1, F0)
    Nimg, depth, mask = splat_front(P1, N1)
    lum = np.asarray(plate.crop(FRONT['box'])).astype(float)
    # dome: plate rows 80..135 -> panel rows 18..73 ; columns 190..265 -> panel cols 185..260
    best = fit_light(Nimg, mask, lum, (18, 73, 150, 280))
    print('light az %d el %d  a %.1f b %.1f  rms %.2f' % (best[4], best[5], best[1], best[2], best[3]))
