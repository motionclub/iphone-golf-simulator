import sys
sys.path.insert(0, '.')
import numpy as np
from PIL import Image
import shade_fit as SF
from shade_fit import *

def make(P1, F0, tag, light=None):
    N1 = PX.vertex_normals(P1, F0)
    Nimg, depth, mask = splat_front(P1, N1)
    lum = np.asarray(plate.crop(FRONT['box'])).astype(float)
    if light is None:
        best = fit_light(Nimg, mask, lum, (18, 73, 150, 280)); light = (best[0], best[1], best[2])
    l, a, b = light
    pred = lambert(Nimg, l, a, b)
    res = lum - pred
    # face crop: plate cols 150..310, rows 120..300 -> panel coords (-5,-62)
    c0, c1, r0, r1 = 145, 305, 58, 238
    def to_img(arr, lo=0, hi=255):
        return Image.fromarray(np.clip((arr - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)).convert('RGB')
    A = to_img(lum); B = to_img(np.where(mask, pred, 40))
    # residual diverging
    rr = np.clip(res / 60.0, -1, 1)
    rgb = np.zeros(res.shape + (3,))
    rgb[..., 0] = np.where(rr > 0, 255, 255 * (1 + rr)); rgb[..., 1] = 255 * (1 - np.abs(rr)); rgb[..., 2] = np.where(rr < 0, 255, 255 * (1 - rr))
    rgb[~mask] = 40
    C = Image.fromarray(rgb.astype(np.uint8))
    box = (c0 - 0, r0, c1 - 0, r1)
    crops = [im.crop((c0 - 5 + 5, r0, c1, r1)) for im in (A, B, C)]
    W = crops[0].width; Hh = crops[0].height
    sheet = Image.new('RGB', (W * 3 + 20, Hh))
    for i, c in enumerate(crops): sheet.paste(c, (i * (W + 10), 0))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.LANCZOS)
    sheet.save('r/shade_%s.png' % tag); return res, mask

if __name__ == '__main__':
    P1 = stage1(V0)
    make(P1, F0, 'base')
    print('ok')
