"""collar_lie_check.py - what LIE do the VISIBLE parts of FAIRWAY_FIRSTCUT have? (repair round 1: the collar was recoloured to LK_ROUGH because it is the rough lie round the fairway.)
Samples a 1 m grid over the FIRSTCUT top faces; a point is VISIBLE when no higher play surface (FAIRWAY / GREEN / GREEN_APRON / TEE_BOX / BUNKER*) lies over it. Prints the lie shares of the visible points and of the hidden ones.
  Blender -b --factory-startup --python collar_lie_check.py -- --blend stage/hole_09.blend"""
import sys, math, numpy as np, bpy
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import postcard_lib as P
A = sys.argv[sys.argv.index("--") + 1:]
BLEND = A[A.index("--blend") + 1]
D = P.start("hole09_design", out_dir="/tmp/collar_scratch")
bpy.ops.wm.open_mainfile(filepath=BLEND)
def bvh_of(names):
    V, F = [], []
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name in names:
            o.data.calc_loop_triangles(); b = len(V)
            V += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            F += [tuple(b + i for i in t.vertices) for t in o.data.loop_triangles if t.normal.z > 0.3]
    return BVHTree.FromPolygons(V, F)
fc = bvh_of({"FAIRWAY_FIRSTCUT"})
over = bvh_of({"FAIRWAY", "GREEN", "GREEN_APRON", "TEE_BOX", "BUNKER_01", "BUNKER_02", "BUNKER_03", "BUNKER_01_LIP", "BUNKER_02_LIP", "BUNKER_03_LIP"})
o = bpy.data.objects["FAIRWAY_FIRSTCUT"]
co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
xs = np.arange(co[:, 0].min(), co[:, 0].max(), 1.0); ys = np.arange(co[:, 1].min(), co[:, 1].max(), 1.0)
vis, hid = [], []
for y in ys:
    for x in xs:
        h = fc.ray_cast(Vector((x, y, 20.0)), Vector((0, 0, -1)), 40.0)
        if h[0] is None:
            continue
        top = over.ray_cast(Vector((x, y, 20.0)), Vector((0, 0, -1)), 40.0)
        (hid if (top[0] is not None and top[0].z > h[0].z + 0.01) else vis).append((x, y))
names = {v: k for k, v in vars(P).items() if k.startswith("LIE_") and isinstance(v, int)}
def share(pts):
    if not pts: return {}
    X = np.array([p[0] for p in pts]); Y = np.array([p[1] for p in pts])
    c = P.lie_codes_m(D, X, Y)
    out = {}
    for k in np.unique(c): out[names.get(int(k), int(k))] = round(float((c == k).mean()), 3)
    return out
print("COLLAR visible points", len(vis), "lies", share(vis))
print("COLLAR hidden (under a higher play surface) points", len(hid), "lies", share(hid))
