import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
import postcard_props_lib as PL
hole=os.environ["HOLE"]; seed=int(os.environ.get("SEED","1"))
keys=os.environ["KEYS"].split(",")
outd=os.environ["OUT"]; tag=os.environ.get("TAG","r"); os.makedirs(outd,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=f"{R}/work/postcard-look/baseline/blender/hole_{hole}.blend")
out=PL.swap_legacy_rocks(None,basalt=(hole=="10"),seed=seed)
bpy.context.view_layer.update()
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'
sc.render.resolution_x=520; sc.render.resolution_y=640
sc.world=bpy.data.worlds.new("w"); sc.world.color=(0.62,0.72,0.86)
sel=[]
for o in bpy.data.objects:
    if o.type!='MESH': continue
    p=o.matrix_world.translation
    if o in out and o.get('lk_swap') in keys: sel.append(o); o.hide_render=False
    else: o.hide_render=True
pts=np.concatenate([np.array([list(o.matrix_world@v.co) for v in o.data.vertices]) for o in sel])
c=(pts.min(0)+pts.max(0))/2; span=max(pts.max(0)-pts.min(0))*1.1
print("sel",len(sel),"bbox",pts.min(0),pts.max(0))
cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=span
for az in (0,90,180,270):
    a=math.radians(az)
    cam.location=Vector((c[0]+math.sin(a)*200,c[1]-math.cos(a)*200,c[2])); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{outd}/{tag}_{az}.png"; bpy.ops.render.render(write_still=True)
