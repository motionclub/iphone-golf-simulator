#!/usr/bin/env python3
"""Add a tight alpha-bounded rect to every cloud in clouds.json (less transparent overdraw on the phone).
   tools/tighten_clouds.py blender/clouds"""
import sys, json, os
import numpy as np
from PIL import Image
d = sys.argv[1]
J = json.load(open(os.path.join(d, 'clouds.json')))
A = np.asarray(Image.open(os.path.join(d, 'CloudSixWay_A.png')))[..., 3].astype(float) / 255
H, W = A.shape
A = A[::-1]  # rows from the bottom, like uv
for c in J['clouds']:
    u0, v0, du, dv = c['uv_rect']
    x0, y0, x1, y1 = int(u0 * W), int(v0 * H), int((u0 + du) * W), int((v0 + dv) * H)
    cell = A[y0:y1, x0:x1]
    ys, xs = np.nonzero(cell > 2 / 255)
    pad = 3
    tx0, tx1 = max(0, xs.min() - pad), min(cell.shape[1], xs.max() + 1 + pad)
    ty0, ty1 = max(0, ys.min() - pad), min(cell.shape[0], ys.max() + 1 + pad)
    cw, ch = cell.shape[1], cell.shape[0]
    c['tight_uv'] = [u0 + tx0 / cw * du, v0 + ty0 / ch * dv, (tx1 - tx0) / cw * du, (ty1 - ty0) / ch * dv]
    c['tight_width_m'] = c['width_m'] * (tx1 - tx0) / cw
    c['tight_height_m'] = c['height_m'] * (ty1 - ty0) / ch
    c['tight_base_from_bottom'] = (c['base_from_bottom'] * ch - ty0) / (ty1 - ty0)
    c['tight_centre_x'] = ((tx0 + tx1) / 2 / cw - .5)   # horizontal offset of the tight rect, in cell widths
    c['area_saved'] = 1 - (tx1 - tx0) * (ty1 - ty0) / (cw * ch)
    print(c['index'], c['kind'], 'saved %.0f%%' % (100 * c['area_saved']))
json.dump(J, open(os.path.join(d, 'clouds.json'), 'w'), indent=1)
