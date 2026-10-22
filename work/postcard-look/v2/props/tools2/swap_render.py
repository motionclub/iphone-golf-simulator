"""Workbench previews (NOT Game-view proof) of swapped legacy stacks. HOLE=09 KEYS=ROCK_STACK_01,ROCK_STACK_04 OUT=dir"""
import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
import postcard_props_lib as PL
hole = os.environ.get("HOLE", "09"); keys = os.environ["KEYS"].split(","); outd = os.environ["OUT"]; seed = int(os.environ.get("SEED", "1"))
os.makedirs(outd, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=f"{R}/work/postcard-look/baseline/blender/hole_{hole}.blend")
out = PL.swap_legacy_rocks(None, basalt=False, seed=seed)
bpy.context.view_layer.update()
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = 560; sc.render.resolution_y = 560
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.62, 0.72, 0.86)
for o in list(bpy.data.objects):
    if o.type == 'MESH': o.hide_render = True
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
# a sea plane for context
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0)); sea = bpy.context.active_object
for key in keys:
    ks = key.split("+")
    grp = [o for o in out if o.get("lk_swap") in ks]
    if not grp: print("no group", key); continue
    pts = np.concatenate([np.array([list(o.matrix_world @ v.co) for v in o.data.vertices]) for o in grp])
    c = (pts.min(0) + pts.max(0)) / 2
    span = max(pts.max(0) - pts.min(0)) * 1.15
    sea.location = (c[0], c[1], 0.0); sea.hide_render = False
    sea.data.materials.clear()
    for o in bpy.data.objects:
        if o.type == 'MESH' and o is not sea: o.hide_render = o.get("lk_swap") not in ks
    for az in (0, 70):
        a = math.radians(az)
        cam.data.ortho_scale = span
        cam.location = Vector((c[0] + math.sin(a) * 120, c[1] - math.cos(a) * 120, c[2] + 8)); cam.rotation_euler = (math.radians(86), 0, a)
        sc.render.filepath = f"{outd}/{hole}_{key.replace('+', '_')}_{az}.png"
        bpy.ops.render.render(write_still=True)
    print("rendered", key, len(grp), "pieces", [o.data.name for o in grp])
