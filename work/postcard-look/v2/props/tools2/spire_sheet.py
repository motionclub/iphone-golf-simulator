"""Workbench contact sheet of the spire kinds from 3 azimuths (scratch preview, NOT Game-view proof). OUT=png"""
import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
import postcard_props_lib as PL
out = os.environ["OUT"]
kinds = list(PL.SEASTACK_KINDS) + ["ROCK_SPIRE_A"]
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = 1500; sc.render.resolution_y = 520
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.62, 0.72, 0.86)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 78
imgs = []
for az in (0, 60, 120):
    for o in [o for o in bpy.data.objects if o.name.startswith("ROCK_") and o is not None and o.parent is None and "." in o.name]:
        bpy.data.objects.remove(o, do_unlink=True)
    x = -34.0
    for k in kinds:
        PL.place(None, k, (x, 0, 0), math.radians(az) + 0.3)
        x += 13.0
    cam.location = (0, -120, 10); cam.rotation_euler = (math.radians(90), 0, 0)
    p = f"{out}_{az}.png"; sc.render.filepath = p
    bpy.ops.render.render(write_still=True); imgs.append(p)
