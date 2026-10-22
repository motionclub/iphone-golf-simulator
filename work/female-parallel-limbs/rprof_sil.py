"""blender -b file --python rprof_sil.py -- out.png : flat alpha silhouette of the left profile at the same 3x crop framing as rprof.py"""
import bpy, sys
from mathutils import Vector
import numpy as np
out=sys.argv[sys.argv.index('--')+1]
S=0.005916/3
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading; sh.light='FLAT'; sh.color_type='SINGLE'; sh.single_color=(1,1,1)
sc.display.render_aa='OFF'; sc.render.film_transparent=True; sc.view_settings.view_transform='Standard'
sc.render.resolution_x=390; sc.render.resolution_y=900
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=900*S
me=bpy.data.objects['Body_F'].data
v=np.array([tuple(x.co) for x in me.vertices]); h=v[v[:,2]>1.45]; yc=(h[:,1].min()+h[:,1].max())/2
d=Vector((-1,0,0)); cam.location=Vector((3,yc-75*S,0.8468)); cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sc.render.filepath=out; bpy.ops.render.render(write_still=True)
