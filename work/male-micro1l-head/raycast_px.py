"""Cast the clay jaw_q camera ray through a pixel (640 space) and report the Body_M hit.  blender -b --python raycast_px.py -- <blend> <px> <py>"""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head/pylib')
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); px, py = float(argv[1]), float(argv[2])
body = bpy.data.objects['Body_M']; me = body.data
V = [tuple(v.co) for v in me.vertices]; T = []
for p in me.polygons:
    vs = list(p.vertices); T.append((vs[0], vs[1], vs[2]))
    if len(vs) > 3: T.append((vs[0], vs[2], vs[3]))
bvh = BVHTree.FromPolygons(V, T)
az, el, tgt, sc = math.radians(55), math.radians(-8), Vector((0.03, -0.06, 1.48)), 0.17
camdir = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
d = -camdir; right = d.cross(Vector((0, 0, 1))); right.normalize(); up = right.cross(d); up.normalize(); up = -up if up.z < 0 else up
u = (px - 320) / 640 * sc; v = (320 - py) / 640 * sc
origin = tgt + u * right + v * up + camdir * 2.0
hit = bvh.ray_cast(origin, d, 5.0)
print('HIT', [round(c * 1000, 1) for c in hit[0]] if hit[0] else None, 'normal', [round(c, 2) for c in hit[1]] if hit[1] else None, 'face', hit[2])
