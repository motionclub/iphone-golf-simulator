"""Plate-aligned render set (RGBA, transparent bg) for the head: front, left, q3L, q3R, top.  Runs inside Blender.
render_set(tag, objs=None) renders whatever is in the scene (all visible mesh objects)."""
import math
import numpy as np
import bpy
import h1lib as H
from h1lib import K, TOP, zrow, ycol

# panel -> (box in plate px, az, target)
Q3_APEX_ROW = 397.0
SETS = {
    'front': dict(box=(5, 62, 433, 352), az=0.0, kind='front'),
    'left': dict(box=(433, 62, 834, 352), az=90.0, kind='side'),
    'q3L': dict(box=(5, 390, 433, 668), az=32.5, kind='q3'),
    'q3R': dict(box=(433, 390, 834, 668), az=30.0, kind='q3'),
}


def cam_for(name, up=2):
    p = SETS[name]; x0, y0, x1, y1 = p['box']; w, h = x1 - x0, y1 - y0
    cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
    if p['kind'] == 'front':
        target = (float(H.xcol(cxp)), -0.04, float(zrow(cyp)))
    elif p['kind'] == 'side':
        target = (0.0, float(ycol(cxp)), float(zrow(cyp)))
    else:
        zc = TOP - (cyp - Q3_APEX_ROW) * K
        target = (0.0, -0.040, zc)
    return dict(target=target, az=p['az'], el=0.0, scale=w * K, res=(w * up, h * up))


def setup(transparent=True, skin=(0.80, 0.56, 0.42), cavity=True):
    H.setup_render(skin=skin, cavity=cavity)
    s = bpy.context.scene
    s.render.film_transparent = transparent
    s.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'


def render_set(tag, names=('front', 'left', 'q3L', 'q3R'), up=2, extra=None):
    out = H.W / 'r' / tag; out.mkdir(parents=True, exist_ok=True)
    for n in names:
        c = cam_for(n, up)
        H.shot(out / f'{n}.png', c['target'], c['az'], c['el'], c['scale'], c['res'])
    if extra:
        for n, (target, az, el, scale, res) in extra.items():
            H.shot(out / f'{n}.png', target, az, el, scale, res)
    return out
