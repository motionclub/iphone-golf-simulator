"""EEVEE sheet of the shrub kinds (3 azimuths, perspective, real Look textures; scratch preview, NOT Game-view proof). usage: Blender -b --factory-startup --python shrub_sheet.py -- OUT.png [LIB.py]"""
import sys, os, math, importlib.util
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]
libpath = a[1] if len(a) > 1 else R + "/blender/scripts/postcard_props_lib.py"
spec = importlib.util.spec_from_file_location("pl_under_test", libpath)
PL = importlib.util.module_from_spec(spec); sys.modules["pl_under_test"] = PL; spec.loader.exec_module(PL)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
try: sc.view_settings.view_transform = 'Standard'
except Exception: pass
sc.render.resolution_x = 1500; sc.render.resolution_y = 700
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.82, 0.95, 1)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(35))
g = bpy.data.objects.new("g", bpy.data.meshes.new("g"))
g.data.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)], [], [(0, 1, 2, 3)]); sc.collection.objects.link(g)
mat = bpy.data.materials.new("gm"); mat.use_nodes = True; mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.33, 0.33, 0.12, 1); g.data.materials.append(mat)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
kinds = ["PLANT_SHRUB_A", "PLANT_SHRUB_B", "PLANT_SHRUB_C"]
x = -4.0
for k in kinds:
    for j, az in enumerate((0.3, 1.6)):
        PL.place(None, k, (x + 0.0, 0.0 + j * 1.9, 0.0), az, 1.0, allow_low=True) if "allow_low" in PL.place.__code__.co_varnames else PL.place(None, k, (x, j * 1.9, 0.0), az, 1.0)
    x += 2.4
cam.location = (-0.5, -9.0, 2.6); cam.rotation_euler = (math.radians(78), 0, 0)
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
rep = PL.library_report()
for k in kinds: print("REPORT", k, rep[k])
print("DONE")
