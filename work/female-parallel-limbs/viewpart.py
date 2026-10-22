"""blender -b --python viewpart.py -- which(foot|hand) npz out_prefix : orthographic views of a raw part at plate pixel scale."""
import bpy, sys, numpy as np
from mathutils import Vector
which,npz,pre=sys.argv[sys.argv.index('--')+1:][:3]
S=0.0025954198473282443
d=np.load(npz); V=d['V']; F=d['F']
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('p'); me.from_pydata(V.tolist(),[],F.tolist()); me.update()
ob=bpy.data.objects.new('p',me); bpy.context.scene.collection.objects.link(ob)
for p in me.polygons: p.use_smooth=True
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='SINGLE'
sh.single_color=(0.93,0.74,0.60) if which=='foot' else (0.72,0.72,0.74)
sc.render.resolution_x=600; sc.render.resolution_y=600
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.85,0.85,0.86)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
def shot(name,center,dirv,upv,scale):
    dv=Vector(dirv).normalized(); cam.location=Vector(center)-dv*2
    q=dv.to_track_quat('-Z','Y'); cam.rotation_euler=q.to_euler(); cam.data.ortho_scale=scale
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
if which=='foot':
    c=(0.1103,-0.07,0.08)
    shot('front',(0.1103,0,0.09),(0,1,0),None,0.30)
    shot('side',(0.1103,-0.07,0.09),(-1,0,0),None,0.30)
    shot('top',(0.1103,-0.07,0.0),(0,0,-1),None,0.30)
    shot('q',(0.1103,-0.07,0.07),(-0.6,0.7,-0.35),None,0.30)
else:
    shot('front',(0.235,0,0.78),(0,1,0),None,0.30)
    shot('side',(0.235,0,0.78),(-1,0,0),None,0.30)
    shot('back',(0.235,0,0.78),(0,-1,0),None,0.30)
    shot('q',(0.235,0,0.78),(-0.6,-0.7,-0.2),None,0.30)
