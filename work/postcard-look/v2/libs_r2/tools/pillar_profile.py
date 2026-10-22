"""Radial profile of the hole 10 pillar: ray casts outward from the pillar axis at several heights. usage: Blender -b --factory-startup --python pillar_profile.py -- BLEND"""
import sys, math, collections
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
pin = bpy.data.objects["MARKER_PIN"].matrix_world.translation if "MARKER_PIN" in bpy.data.objects else None
print("PIN", tuple(pin) if pin else None)
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
# find the green outline centre: GREEN object bbox
g = bpy.data.objects.get("GREEN")
ws = [g.matrix_world @ Vector(c) for c in g.bound_box]
cx = sum(w.x for w in ws) / 8; cy = sum(w.y for w in ws) / 8
print("GREEN bbox", min(w.x for w in ws), max(w.x for w in ws), min(w.y for w in ws), max(w.y for w in ws), "centre", cx, cy)
for z in (5.9, 5.5, 4.5, 3.0, 1.5, 0.3, -1.0, -3.0, -5.5):
    row = []
    for az in range(0, 360, 45):
        d = Vector((math.cos(math.radians(az)), math.sin(math.radians(az)), 0))
        o = Vector((cx, cy, z)) + d * 60.0
        ok, loc, nrm, idx, ob, m = sc.ray_cast(dg, o, -d, distance=70.0)
        row.append((round((loc - Vector((cx, cy, z))).length, 1) if ok else None, ob.name[:14] if ok else None))
    print("Z %5.1f" % z, " ".join("%s:%s" % (r[0], r[1]) for r in row))
# objects near the pillar by prefix
cnt = collections.Counter()
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    c = ob.matrix_world @ Vector(ob.bound_box[0])
    if math.hypot(c.x - cx, c.y - cy) < 60:
        cnt[ob.name.rsplit("_", 1)[0]] += 1
print("NEAR", dict(cnt))
