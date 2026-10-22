import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy
from mathutils import Vector
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='SINGLE'; sc.display.shading.single_color=(0.55,0.55,0.5)
sc.display.shading.show_cavity=False
sc.render.resolution_x=360; sc.render.resolution_y=520
sc.view_settings.view_transform='Standard'
sc.world=bpy.data.worlds.new("w"); sc.world.color=(0.6,0.7,0.85)
kinds=["ROCK_SEASTACK_A","ROCK_SEASTACK_B","ROCK_SEASTACK_C"]
cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
import numpy as np
for k in kinds:
    ob=PL.library_object(k)
    inst=bpy.data.objects.new("i",ob.data); sc.collection.objects.link(inst)
    H=max(v.co.z for v in ob.data.vertices)
    cam.data.ortho_scale=H*1.35
    for az in (0,90,180,270):
        a=math.radians(az)
        cam.location=Vector((math.sin(a)*60,-math.cos(a)*60,H*0.45))
        cam.rotation_euler=(math.radians(90),0,a)
        sc.render.filepath=f"/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/review_P/r_{k}_{az}.png"
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(inst)
