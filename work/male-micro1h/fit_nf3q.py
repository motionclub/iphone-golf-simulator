"""Fit the loft front-section exponents nf(z) to the 3/4 plate contours (corrected yaws).  Pure numpy (no Blender)."""
import sys, time, math, json
sys.path.insert(0, '.')
import numpy as np
from PIL import Image
import h1lib as H, loft as L, sculpt as S
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
K = H.K; TOP = H.TOP
plate = Image.open(R + 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
V = np.load('data/proxy_L3.npz', allow_pickle=True)['V']
PANELS = {'q3L': dict(box=(5, 390, 433, 668), az=41.0, pm=176.5), 'q3R': dict(box=(433, 390, 834, 668), az=36.0, pm=589.5)}
ROWS_L = [r for r in range(430, 586, 6) if not (466 <= r <= 474)]
ROWS_R = list(range(430, 466, 6))


def plate_contours(box):
    p = np.asarray(plate.crop(box)).astype(float)
    sk = (p[..., 0] - p[..., 2] > 35) & (p[..., 0] > 100)
    out = {}
    for r in set(ROWS_L + ROWS_R):
        cs = np.where(sk[int(r - box[1])])[0]
        if len(cs): out[r] = (box[0] + cs.min(), box[0] + cs.max())
    return out


PC = {n: plate_contours(p['box']) for n, p in PANELS.items()}


def stage1(P, nf=None):
    loft = L.Loft(nf=nf) if nf is not None else L.Loft()
    P0, _, _ = L.remap(P, loft)
    P1, _ = S.apply(P0, np.zeros_like(P0), S.PRM, ('nose', 'orbit', 'brow', 'cheek', 'eye', 'mouth', 'ear'), F=None)
    keep = P[:, 2] < 1.462; P1[keep] = P[keep]
    return P1


def mesh_contours(P1, name):
    p = PANELS[name]; a = math.radians(p['az'])
    u = P1[:, 0] * math.cos(a) + (P1[:, 1] + 0.1254) * math.sin(a)          # relative to the pupil mid (0,-0.1254)
    col = p['pm'] + u / K
    out = {}
    for r in set(ROWS_L + ROWS_R):
        z = TOP - (r - 397) * K
        sel = np.abs(P1[:, 2] - z) < 0.0008
        if sel.sum() < 5: continue
        out[r] = (col[sel].min(), col[sel].max())
    return out


def residuals(nf=None, P1=None, detail=False):
    if P1 is None: P1 = stage1(V, nf)
    res = []; info = {}
    for n in PANELS:
        mc = mesh_contours(P1, n); pc = PC[n]
        for r in ROWS_L:
            if r in mc and r in pc:
                d = (mc[r][0] - pc[r][0]) * K * 1000; res.append(d); info[(n, 'L', r)] = d
        for r in ROWS_R:
            if r in mc and r in pc:
                d = (mc[r][1] - pc[r][1]) * K * 1000; res.append(d * 0.5); info[(n, 'R', r)] = d
    res = np.array(res)
    return (res, info) if detail else res


if __name__ == '__main__':
    base = [2.3, 2.4, 2.3, 2.15, 2.12, 2.3, 2.7, 2.5, 2.2]
    r0 = residuals(base); print('baseline rms %.2f mm' % np.sqrt((r0 ** 2).mean()))
    nf = list(base)
    for sweep in range(3):
        for i in range(len(nf)):
            best = (np.sqrt((residuals(nf) ** 2).mean()), nf[i])
            for dv in (-0.3, -0.2, -0.1, 0.1, 0.2, 0.3):
                t = list(nf); t[i] = float(np.clip(nf[i] + dv, 1.7, 3.4))
                e = np.sqrt((residuals(t) ** 2).mean())
                if e < best[0] - 1e-4: best = (e, t[i])
            nf[i] = best[1]
        print('sweep', sweep, 'rms %.3f' % np.sqrt((residuals(nf) ** 2).mean()), [round(x, 2) for x in nf])
    res, info = residuals(nf, detail=True)
    for k, v in sorted(info.items()): print(k, '%.1f' % v)
    json.dump(nf, open('data/nf_fit_3q.json', 'w'))
