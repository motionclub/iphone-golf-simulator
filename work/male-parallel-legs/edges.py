"""Silhouette edge tables: plate (frozen target masks) vs mesh vertices, per world height z (row), in metres.
Views: bald_front bald_back sheet_front sheet_back (horizontal axis = world x; back views are mirrored), left/right (horizontal = world y; left: image-left = front)."""
import json
import numpy as np
from PIL import Image
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
CAMS = {v['name']: v for v in json.load(open(R + '/work/male-silhouette/reference-cameras.json'))['views']}
VIEWS = ['bald_front', 'bald_back', 'sheet_front', 'sheet_back', 'left', 'right']
_masks = {}


def target_mask(v):
    if v not in _masks:
        a = np.array(Image.open(R + f'/work/male-silhouette/{v}_target.png').convert('L'))
        _masks[v] = a > 127
    return _masks[v]


def cam(v):
    c = CAMS[v]; return c['metres_per_pixel'], c['sole_y'], c['centre_x']


def h_sign(v):
    """horizontal image axis -> world coordinate: u = sign*(px-cx)*mpp ; front/sheet_front/left: u = x (or y) , back: u=x with sign -1, right: u = y with sign -1"""
    return {'bald_front': +1, 'sheet_front': +1, 'bald_back': -1, 'sheet_back': -1, 'left': +1, 'right': -1}[v]


def row_to_z(v, row):
    mpp, sole, cx = cam(v); return (sole - (row + 0.5)) * mpp


def z_to_row(v, z):
    mpp, sole, cx = cam(v); return sole - z / mpp - 0.5


def spans(v, z, xlim=None):
    """foreground runs on the image row at height z -> list of (u0,u1) in metres (u = h_sign*(px-cx)*mpp), sorted ascending u; sub-pixel is not attempted"""
    m = target_mask(v); mpp, sole, cx = cam(v)
    r = int(round(z_to_row(v, z)))
    if r < 0 or r >= m.shape[0]: return []
    row = m[r]
    xs = np.nonzero(np.diff(np.r_[0, row.astype(np.int8), 0]))[0]
    runs = [(xs[i], xs[i + 1]) for i in range(0, len(xs), 2)]
    s = h_sign(v)
    out = []
    for a, b in runs:
        u0 = s * (a - cx) * mpp; u1 = s * (b - cx) * mpp      # b is exclusive edge
        out.append((min(u0, u1), max(u0, u1)))
    return sorted(out)
