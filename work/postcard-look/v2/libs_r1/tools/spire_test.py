"""Spire report + render sheet (scratch). usage: Blender -b --factory-startup --python spire_test.py -- OUT_PREFIX [old]
'old' = import the backup lib (before this round) instead of the live one."""
import sys, os, math, importlib.util
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; use_old = len(a) > 1 and a[1] == "old"
if use_old:
    spec = importlib.util.spec_from_file_location("postcard_props_lib", REPO + "/work/postcard-look/v2/libs_r1/backup/postcard_props_lib.py")
    PL = importlib.util.module_from_spec(spec); sys.modules["postcard_props_lib"] = PL; spec.loader.exec_module(PL)
else:
    import postcard_props_lib as PL
import previews_lib as PV
LOOK = REPO + "/Unity/Assets/Resources/Course/Look/"
kinds = list(PL.SEASTACK_KINDS) + ["ROCK_SPIRE_A"]
PL.ensure_library(kinds)
for im in bpy.data.images:
    if im.name.endswith(".png") and os.path.isfile(LOOK + im.name):
        im.filepath = LOOK + im.name; im.reload()
for k in kinds:
    me = PL.library_object(k).data
    r = PL.seastack_report(me)
    sh = PL.rock_shape_report(me)
    pa = np.array([p.area for p in me.polygons]); mi = np.array([p.material_index for p in me.polygons])
    grass = float(pa[mi == 1].sum() / pa.sum())
    print(f"SPIRE {k}: faces {len(me.polygons)} welded {sh['verts']} taper {r['taper']:.2f} rise {r['band_rise']:.2f} cap {r['cap_share']:.2f} facets {r['facets']} fills {[round(f,2) for f in r['fills']]} slices {r['slices']} distinct {r['distinct']} ok {r['ok']} {r['why']} | shape ok {sh['ok']} {sh['why']} | grass {grass*100:.0f}%")
sc = bpy.context.scene
PV.setup_scene(sky=(190, 205, 225))
ld = bpy.data.lights.new("sun", 'SUN'); ld.energy = 3.0
lo = bpy.data.objects.new("sun", ld); sc.collection.objects.link(lo); lo.rotation_euler = (math.radians(55), 0, math.radians(30))
# sea plane
bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, 0)); g = bpy.context.active_object
gm = bpy.data.materials.new("sea"); gm.diffuse_color = (0.05, 0.25, 0.45, 1); g.data.materials.append(gm)
x = -34.0
for k in kinds:
    PL.place(None, k, (x, 0, 0), 0.3, 1.0, allow_low=True)
    x += 13.0
res = (1600, 560)
for az, loc in ((0, (0, -90, 9)), (60, (78, -45, 9))):
    c = PV.cam("C%d" % az, loc, (0, 0, 8), 30)
    PV.render(c, f"{out}_{az}.png", res, 24)
# a Game-like tee view of one stack (distance ~ 55 m, 13-18 m tall, 60 deg vertical fov, portrait)
bpy.ops.object.select_all(action='DESELECT')
for o in [o for o in bpy.data.objects if o.name.startswith("ROCK_") and "." in o.name]:
    bpy.data.objects.remove(o, do_unlink=True)
PL.place(None, "ROCK_SEASTACK_B", (-3, 0, 0), 0.3, 1.0, allow_low=True)
PL.place(None, "ROCK_SEASTACK_A", (9, 6, 0), 1.2, 0.9, allow_low=True)
c = PV.cam("CG", (0, -52, 7.0), (2, 0, 9.0), 40)
PV.render(c, f"{out}_game.png", (900, 1100), 24)
c = PV.cam("CG2", (14, -20, 6.0), (-3, 0, 9.0), 45)
PV.render(c, f"{out}_close.png", (1000, 1000), 24)
