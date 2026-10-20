"""Plate-aligned head renders + overlays for Micro1g (runs inside Blender; composition in plain python3 w/ PIL).

Framing reproduces the male_head_detail.jpg panels exactly (k = 1.3043874 mm/px, top row 76 -> z 1.70466) and the
multi-angle plate heads approximately (orthographic, same ortho scale per crop box).
"""
import math, json
from pathlib import Path
import numpy as np

K = 0.0013043874429196725
TOP = 1.7046599388122559
ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
FL = ROOT / 'ArtDir/hero/base_lock/face_lock'
# head-detail panels: (box, azimuth, elevation, target)  azimuth 0 = front camera at -Y ; 90 = camera at +X (left profile shows nose at left)
PANELS = {
    '01_front': ((5, 62, 433, 352), 0, 0),
    '02_left': ((433, 62, 834, 352), 90, 0),
    '03_right': ((834, 62, 1271, 352), -90, 0),
    '04_q3L': ((5, 390, 433, 668), 40, 0),
    '05_q3R': ((433, 390, 834, 668), -40, 0),
    '06_top': ((834, 390, 1272, 668), 0, 89),
}
PANEL_ROW0 = {'01_front': 62, '02_left': 62, '03_right': 62, '04_q3L': 390, '05_q3R': 390, '06_top': 390}
# centre of each panel in metres: x-centre of face is plate col 227.5 (front panel) ; profile anchor y=0.065 at col 712
CENTRES = {
    '01_front': (0.0, 0.0, None), '02_left': (None, 0.065 + ((433 + 834) / 2 - 712) * K, None), '03_right': (None, 0.065 + (((834 + 1271) / 2) - 1051.5) * K + 0.0, None),
}


def panel_shot(lib, name, path, res_scale=2):
    """render the mesh at the exact framing of a head-detail panel"""
    box, az, el = PANELS[name]
    w = box[2] - box[0]; h = box[3] - box[1]
    zc = TOP - ((box[1] + box[3]) / 2 - 76) * K
    if name in ('01_front', '04_q3L', '05_q3R', '06_top'):
        # face centre at col 227.5 in the 01 panel; 04/05 panels are the same width family -> assume centred the same way
        xc = (227.5 - (box[0] + box[2]) / 2) * K if name == '01_front' else 0.0
        target = (xc, -0.04, zc) if name != '06_top' else (0.0, -0.02, 1.60)
        if name == '06_top':
            zc_scale = w * K
            lib.shot(path, target, 0, 89, zc_scale, (w * res_scale, h * res_scale)); return
        if name in ('04_q3L', '05_q3R'):
            target = (0.0, -0.04, TOP - ((390 + 668) / 2 - 404) * K)   # 3/4 panels: top of head at ~row 404
    else:
        yc = 0.065 + ((box[0] + box[2]) / 2 - 712) * K if name == '02_left' else 0.065 - (((box[0] + box[2]) / 2) - 1051.5) * K
        target = (0.0, yc, zc)
    lib.shot(path, target, az, el, w * K, (w * res_scale, h * res_scale))
