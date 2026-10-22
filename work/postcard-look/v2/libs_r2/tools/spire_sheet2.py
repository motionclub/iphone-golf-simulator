"""EEVEE contact sheet of the spire kinds from 3 azimuths with the real Look textures (scratch preview, NOT Game-view proof). usage: Blender -b --factory-startup --python spire_sheet2.py -- OUTPREFIX [LIB.py]"""
import sys, os, math, importlib.util
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]
libpath = a[1] if len(a) > 1 else R + "/blender/scripts/postcard_props_lib.py"
spec = importlib.util.spec_from_file_location("pl_under_test", libpath)
PL = importlib.util.module_from_spec(spec); sys.modules["pl_under_test"] = PL; spec.loader.exec_module(PL)
kinds = list(PL.SEASTACK_KINDS) + ["ROCK_SPIRE_A"]
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.view_settings.view_transform = 'AgX'
except Exception:
    pass
sc.render.resolution_x = 1500; sc.render.resolution_y = 560
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.70, 0.90, 1)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(50), 0, math.radians(35))
water = bpy.data.objects.new("water", bpy.data.meshes.new("water"))
me = water.data; me.from_pydata([(-80, -80, 0), (80, -80, 0), (80, 80, 0), (-80, 80, 0)], [], [(0, 1, 2, 3)]); sc.collection.objects.link(water)
mat = bpy.data.materials.new("wm"); mat.use_nodes = True; mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.2, 0.45, 1); water.data.materials.append(mat)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 78
for az in (0, 60, 120):
    for o in [o for o in bpy.data.objects if o.name.startswith("ROCK_") and o.parent is None and "." in o.name]:
        bpy.data.objects.remove(o, do_unlink=True)
    x = -34.0
    for k in kinds:
        PL.place(None, k, (x, 0, 0), math.radians(az) + 0.3)
        x += 13.0
    cam.location = (0, -120, 10); cam.rotation_euler = (math.radians(90), 0, 0)
    sc.render.filepath = f"{out}_{az}.png"
    bpy.ops.render.render(write_still=True)
print("DONE")
