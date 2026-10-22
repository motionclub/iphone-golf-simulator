import sys, os, math, collections
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
import postcard_props_lib as PL
bpy.ops.wm.open_mainfile(filepath=R + "/work/postcard-look/baseline/blender/hole_09.blend")
legs={}
for o in PL.legacy_rocks():
    if o.name.startswith("ROCK_STACK"):
        me=o.data; co=np.array([list(o.matrix_world@v.co) for v in me.vertices]); legs[o.name]=(co.min(0),co.max(0))
for k,(a,b) in sorted(legs.items()): print("LEGACY",k,"size",np.round(b-a,1),"z",round(a[2],1),round(b[2],1))
out=PL.swap_legacy_rocks(None, basalt=False, seed=5)
bpy.context.view_layer.update()
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='SINGLE'; sc.display.shading.single_color=(0.55,0.55,0.5)
sc.render.resolution_x=500; sc.render.resolution_y=500
sc.world=bpy.data.worlds.new("w"); sc.world.color=(0.6,0.7,0.85)
for o in list(bpy.data.objects):
    if o.type=='MESH' and not o.get("lk_swap"): o.hide_render=True
cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
for key in ("ROCK_STACK_02","ROCK_STACK_04","ROCK_STACK_01"):
    grp=[o for o in out if o["lk_swap"]==key]
    c=np.mean([list(o.matrix_world.translation) for o in grp],0)
    for o in out: o.hide_render = o["lk_swap"]!=key
    for az in (0,90):
        a=math.radians(az)
        cam.data.ortho_scale=34
        cam.location=Vector((c[0]+math.sin(a)*80,c[1]-math.cos(a)*80,c[2]+6)); cam.rotation_euler=(math.radians(90),0,a)
        sc.render.filepath=f"{R}/work/postcard-look/v2/review_P/s9_{key}_{az}.png"; bpy.ops.render.render(write_still=True)
