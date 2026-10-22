"""Fast orthographic silhouette rasteriser + XOR metrics vs the frozen plate masks (same cameras as the locked Blender ones)."""
import numpy as np
from PIL import Image, ImageDraw
from edges import CAMS, target_mask, cam, h_sign, VIEWS
from leglib import F, N, V0, ZT
W_, H_ = 1280, 720
_quads = [p for p in F]


def project(V, v):
    mpp, sole, cx = cam(v)
    u = V[:, 1] if v in ('left', 'right') else V[:, 0]
    px = cx + h_sign(v) * u / mpp
    py = sole - V[:, 2] / mpp
    return px, py


def mask(V, v, faces=None):
    px, py = project(V, v)
    img = Image.new('L', (W_, H_), 0); d = ImageDraw.Draw(img)
    for p in (faces if faces is not None else _quads):
        d.polygon([(px[i], py[i]) for i in p], fill=1)
    return np.array(img, bool)


def xor_pct(m, t, rows=None):
    if rows is not None: m = m[rows]; t = t[rows]
    return 100.0 * (m != t).sum() / max(1, (m | t).sum())


def metrics(V, views=VIEWS, verbose=False):
    out = {}
    for v in views:
        m = mask(V, v); t = target_mask(v)
        mpp, sole, cx = cam(v)
        r_leg = slice(int(sole - ZT / mpp), H_)
        r_foot = slice(int(sole - 0.16 / mpp), H_)
        out[v] = dict(total=xor_pct(m, t), leg=xor_pct(m, t, r_leg), foot=xor_pct(m, t, r_foot))
    return out


def fmt(res):
    return ' | '.join('%s tot %.2f leg %.2f foot %.2f' % (v[:6], r['total'], r['leg'], r['foot']) for v, r in res.items())
