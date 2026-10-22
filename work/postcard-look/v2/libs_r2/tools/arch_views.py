"""EEVEE views of the lib's arch from the front-left, the back-right and above (scratch preview, NOT Game-view proof). usage: Blender -b --factory-startup --python arch_views.py -- OUTPREFIX [broken]"""
import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
import postcard_props_lib as PL
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; broken = len(a) > 1 and a[1] == "broken"
r = PL.build_masonry_arch(None, (0, 0, 0.0), 0.0, span_m=9.144 if not broken else 6.0, height_m=12.166 if not broken else 9.0, seed=8 if not broken else 12, base_rock=False, vines=True, broken=broken, name="DRESS_ARCH_00")
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
try: sc.view_settings.view_transform = 'AgX'
except Exception: pass
sc.render.resolution_x = 800; sc.render.resolution_y = 1000
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.70, 0.90, 1)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(55), 0, math.radians(30))
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 40
for name, pos in (("front", (-12, -30, 9)), ("back", (13, 30, 8)), ("top", (4, -14, 30))):
    cam.location = pos
    cam.rotation_euler = (Vector((0, 0, 6.0)) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{out}_{name}.png"
    bpy.ops.render.render(write_still=True)
print("DONE")
