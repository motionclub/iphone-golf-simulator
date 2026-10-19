"""GARMENT PIPELINE: shaded proof images with the stress-test pixels painted red (worst view of a frame)."""
import numpy as np
import render as RD

COL = {'body': (.86, .66, .52), 'Kit_Top': (.30, .48, .78), 'Kit_Bottom': (.20, .24, .40), 'Kit_Sock_L': (.95, .95, .95), 'Kit_Sock_R': (.95, .95, .95),
       'Kit_Shoe_L': (.98, .98, .98), 'Kit_Shoe_R': (.98, .98, .98), 'Kit_Belt': (.40, .25, .15), 'Acc_Cap': (.85, .85, .85), 'Acc_GloveL': (.97, .97, .97)}


_HI = {}


def hi_renderer(W=1080, H=1350):
    if (W, H) not in _HI: _HI[(W, H)] = RD.Renderer(W, H, 1.0)
    return _HI[(W, H)]


def shot(S, Ps, view, mask=None, size=None, crop=None, R=None, centre=None):
    """shaded image of the posed set from view (az, el), 1080x1350 by default (proof >= 1080p); mask (h,w) at the metric
    resolution, painted red (nearest upsample). crop = (cx, cy, half) in output pixels."""
    R = R or hi_renderer()
    centre = Ps[0].mean(0) if centre is None else centre
    V = RD.view_matrix(centre, *view)
    bs = []
    for it, P in zip(S.items, Ps):
        sel = np.nonzero(it.drawn)[0] if it.kind == 'body' else np.arange(len(it.tri))
        bs.append(RD.look_batch(R, P, it.tri[sel], COL.get(it.tag, (.6, .7, .6))))
    img = RD.look_draw(R, bs, V).astype(np.float64)
    if mask is not None and mask.any():
        yy = (np.arange(R.H) * mask.shape[0] / R.H).astype(int); xx = (np.arange(R.W) * mask.shape[1] / R.W).astype(int)
        mask = mask[yy][:, xx]
        img[mask] = img[mask] * .25 + np.array([255, 20, 20]) * .75
    img = img.astype(np.uint8)
    if crop is not None:
        cx, cy, hf = crop; H, W = img.shape[:2]
        x0, y0 = int(np.clip(cx - hf, 0, W - 2 * hf)), int(np.clip(cy - hf, 0, H - 2 * hf))
        img = img[y0:y0 + 2 * hf, x0:x0 + 2 * hf]
    return img


def worst(S, Ps, res):
    """(view index, mask) of the view with the most flagged pixels (res from S.frame(..., keep_masks=True))."""
    vi = int(np.argmax(res['views']))
    return vi, res['masks'][vi][0]
