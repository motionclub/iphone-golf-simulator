"""Arch preview + numbers (scratch). usage: Blender -b --factory-startup --python arch_test.py -- OUT_PREFIX [span height broken]"""
import sys, os, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
import postcard_lib as P
import postcard_props_lib as PL
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]
span = float(a[1]) if len(a) > 1 else 7.5
height = float(a[2]) if len(a) > 2 else 11.0
broken = (a[3] == "1") if len(a) > 3 else False
PL.ensure_library(["ROCK_OUTCROP_A"])
LOOK = REPO + "/Unity/Assets/Resources/Course/Look/"
for im in bpy.data.images:
    if im.name.endswith(".png") and os.path.isfile(LOOK + im.name):
        im.filepath = LOOK + im.name; im.reload()
r = PL.build_masonry_arch(None, (0, 0, 5.0), 0.0, span_m=span, height_m=height, seed=8, base_rock=False, vines=False, broken=broken)
ob = r["arch"]
me = ob.data
print("ARCH faces", len(me.polygons), "verts", len(me.vertices), "dims", r["dims"])
# ground plate
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 5.0))
g = bpy.context.active_object; g.name = "G"
gm = bpy.data.materials.new("gm"); gm.diffuse_color = (0.3, 0.45, 0.2, 1); g.data.materials.append(gm)
PV.setup_scene()
sc = bpy.context.scene
if not any(o.type == 'LIGHT' for o in bpy.data.objects):
    ld = bpy.data.lights.new("sun", 'SUN'); ld.energy = 3.5
    lo = bpy.data.objects.new("sun", ld); sc.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(52), 0, math.radians(35))
views = {"front": ((0, -24, 9.5), (0, 0, 10.0), 40, (900, 1100)), "q3": ((-14, -18, 8.0), (0, 0, 10.5), 40, (900, 1100)),
         "back": ((9, 20, 9.0), (0, 0, 10.0), 40, (900, 1100)), "closeR": ((6, -9, 11.0), (4, 0, 10.5), 36, (1000, 1000)),
         "game": ((-1, -23, 8.5), (0, 0, 11.0), 60, (900, 1600))}
for n, (loc, look, fov, res) in views.items():
    c = PV.cam("C_" + n, loc, look, fov)
    PV.render(c, f"{out}_{n}.png", res, 24)
