"""Close-up renders of a kit blend on a body.  blender -b --factory-startup --python view_blend.py -- <kit.blend> <male|female> <White|Black> <out_prefix> <preset> [--body body.blend:Obj] [--parts shoes,socks] [--lift-from shoe]
Presets: feetR / feetL = side, front, heel(back), q3 (low 3/4) of ONE foot; feetBoth = front/back/side of both feet; ankle = a taller crop."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector
from kitlib import *
import render_setup as rs
from preview_common import material

args = sys.argv[sys.argv.index('--') + 1:]
kit, gender, cw, prefix, preset = args[:5]
opts = args[5:]
body_spec = None
if '--body' in opts:
    body_spec = opts[opts.index('--body') + 1]
only = None
if '--parts' in opts:
    only = opts[opts.index('--parts') + 1].split(',')
hide_kit_other = True
bpy.ops.wm.open_mainfile(filepath=kit)
sc = bpy.context.scene
other = 'Black' if cw == 'White' else 'White'
for c in list(bpy.data.collections):
    if c.name.endswith(other) or 'FitArmsCand' in c.name or c.name == 'FitRef':
        for o in c.objects:
            o.hide_render = True
            o.hide_viewport = True
for o in bpy.data.objects:
    if o.name.startswith('FitRef'):
        o.hide_render = True
if body_spec:
    path, obj = body_spec.split(':')
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [obj]
    b = dst.objects[0]
    sc.collection.objects.link(b)
    b.data.materials.clear()
    b.data.materials.append(material('Body_skin', (0.80, 0.60, 0.46), .55, .3))
    b.name = 'Body_view'
    b.hide_render = False
else:
    b = [o for o in bpy.data.objects if o.name.startswith('FitRef_Body') and not o.name.endswith('ArmsCandidate')][0]
    b.hide_render = False
    b.data.materials.clear()
    b.data.materials.append(material('Body_skin', (0.80, 0.60, 0.46), .55, .3))
# keep only the requested part kinds in view (shoes / socks); polo + bottom hidden for foot close-ups
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('Kit_'):
        kind = 'shoes' if '_Shoe_' in o.name else 'socks' if '_Sock_' in o.name else 'other'
        if only is not None and kind not in only:
            o.hide_render = True
# lowest point of the shoes in the shown colourway
zmin = 0.0
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('Kit_Shoe_') and o.name.endswith(cw) and not o.hide_render:
        V, F = mesh_arrays(o)
        zmin = min(zmin, float(V[:, 2].min()))
rs.setup(samples=48)
rs.set_floor_z(zmin)
print('floor z', zmin)
VB, FB = mesh_arrays(b)

def foot_center(side):
    m = (VB[:, 0] * side > 0.02) & (VB[:, 2] < 0.035)
    P = VB[m]
    return np.array([P[:, 0].mean(), 0.5 * (P[:, 1].min() + P[:, 1].max()), 0.07])

PRESETS = {
    'feetR': (+1, [('side', 90, 6), ('front', 0, 8), ('heel', 180, 8), ('q3', 38, 14)]),
    'feetL': (-1, [('side', -90, 6), ('front', 0, 8), ('heel', 180, 8), ('q3', -38, 14)]),
    'full': (+1, [('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)]),
}
side, views = PRESETS[preset]
c = foot_center(side)
if preset == 'full':
    c = np.array([0.0, -0.05, 0.86])
dist = float(os.environ.get('VDIST', 0.95))
lens = float(os.environ.get('VLENS', 85))
res = tuple(int(x) for x in os.environ.get('VRES', '640,640').split(','))
tz = float(os.environ.get('VTZ', 0.095)) if preset != 'full' else 0.86
for nm, az, el in views:
    rs.shot(f'{prefix}_{nm}.png', (c[0], c[1], tz), az, el, dist=dist, lens=lens, res=res)
print('done', prefix)
