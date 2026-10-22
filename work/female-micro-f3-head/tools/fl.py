"""Female HeroBase head lock (MicroF1) core library.  Runs in Blender's python 3.13 (numpy) or `python3.13` of Blender for pure-numpy tools.
Conventions (mesh): x = left/right (symmetric), y negative = front of the face, z up, metres.  Front of the character looks toward -Y.

Plate calibration (female_head_detail.jpg, 1280x720, same camera scale in front/profile panels):
  K    = 1.537 mm/px   (cranium width 129.5 px <-> 198.6 mm of female_body_bald.jpg front; ear-to-ear 155 px <-> 238 mm)
  z(row)  = ZTOP - (row - ROW_TOP)*K            top of skull row 69.5 <-> z 1.7039 (body plate calibrated height)
  x(col)  = (col - CXF)*K                       front panel, CXF = face centre column
  y(col)  = Y0 + (col - COL0)*K                 left-profile panel (face looks to image-left), neck centre column COL0 <-> neck ring centre y Y0
  right profile (face looks to image-right): y(col) = Y0 - (col - COL0R)*K
"""
import math, json, sys
from pathlib import Path
import numpy as np

ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W = ROOT / 'work/female-micro-f3-head'
PLATES = ROOT / 'ArtDir/hero/base_lock'
K = 0.001537
ZTOP = 1.7039
ROW_TOP = 69.5
CXF = 259.0
Y0 = 0.006
COL0 = 653.0
COL0R = 993.0
MM = 0.001


def zrow(r): return ZTOP - (np.asarray(r, float) - ROW_TOP) * K
def rowz(z): return ROW_TOP + (ZTOP - np.asarray(z, float)) / K
def xcol(c): return (np.asarray(c, float) - CXF) * K
def ycolL(c): return Y0 + (np.asarray(c, float) - COL0) * K
def ycolR(c): return Y0 - (np.asarray(c, float) - COL0R) * K


def sstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def sstep5(a, b, x):
    """quintic smootherstep: C2 (zero first AND second derivative at both ends), so a zone weight multiplied into a displacement adds no curvature jump"""
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * t * (t * (6 * t - 15) + 10)


# ------------------------------------------------------------------------------------------------ plate foreground masks (PIL via male pylib)
def load_plate(name='female_head_detail.jpg'):
    sys.path.insert(0, str(ROOT / 'work/male-micro1i/pylib'))
    from PIL import Image
    return np.asarray(Image.open(PLATES / name).convert('RGB')).astype(float)


def fg_mask(a):
    sat = a.max(axis=2) - a.min(axis=2); V = a.mean(axis=2)
    return ~((sat < 16) & (V > 150))


# ------------------------------------------------------------------------------------------------ panels (plate crop boxes) and their orthographic cameras
PANELS = {
    'front': dict(box=(85, 55, 430, 342)),
    'left':  dict(box=(440, 55, 800, 342)),
    'right': dict(box=(830, 55, 1195, 342)),
    'q3L':   dict(box=(85, 385, 430, 656)),
    'q3R':   dict(box=(440, 385, 800, 656)),
    'top':   dict(box=(830, 385, 1195, 656)),
}
Q3 = {'q3L': dict(yaw=36.0, scale=1.0, tx=0.0, tz=0.0), 'q3R': dict(yaw=-36.0, scale=1.0, tx=0.0, tz=0.0)}   # refined by calib34.py -> data/q3.json


def panel_cam(name, up=3):
    """target (x,y,z), azimuth deg (0: camera at -Y; 90: camera at +X; -90: camera at -X), ortho scale (m, width), resolution"""
    x0, y0, x1, y1 = PANELS[name]['box']; w, h = x1 - x0, y1 - y0
    cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
    zc = float(zrow(cyp))
    if name == 'front':
        return dict(target=(float(xcol(cxp)), 0.0, zc), az=0.0, scale=w * K, res=(w * up, h * up))
    if name == 'left':
        return dict(target=(0.0, float(ycolL(cxp)), zc), az=90.0, scale=w * K, res=(w * up, h * up))
    if name == 'right':
        return dict(target=(0.0, float(ycolR(cxp)), zc), az=-90.0, scale=w * K, res=(w * up, h * up))
    raise KeyError(name)


# ------------------------------------------------------------------------------------------------ mesh helpers
def mesh_arrays(me):
    n = len(me.vertices)
    V = np.empty(n * 3, np.float64); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    nl = len(me.loops)
    cv = np.empty(nl, np.int64); me.loops.foreach_get('vertex_index', cv)
    ls = np.empty(len(me.polygons), np.int64); me.polygons.foreach_get('loop_start', ls)
    lt = np.empty(len(me.polygons), np.int64); me.polygons.foreach_get('loop_total', lt)
    F = [cv[a:a + b] for a, b in zip(ls, lt)]
    return V, F


def make_mesh_object(name, V, F, link=True, smooth=True):
    import bpy
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', np.asarray(V, np.float32).ravel())
    lens = np.array([len(f) for f in F], np.int64)
    me.loops.add(int(lens.sum())); me.polygons.add(len(F))
    me.loops.foreach_set('vertex_index', np.concatenate([np.asarray(f, np.int64) for f in F]))
    me.polygons.foreach_set('loop_start', np.concatenate([[0], np.cumsum(lens)[:-1]]))
    me.polygons.foreach_set('loop_total', lens)
    me.update(calc_edges=True)
    if smooth:
        me.polygons.foreach_set('use_smooth', [True] * len(F))
    o = bpy.data.objects.new(name, me)
    if link:
        bpy.context.scene.collection.objects.link(o)
    return o
