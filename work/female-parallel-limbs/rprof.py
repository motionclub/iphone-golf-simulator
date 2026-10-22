"""blender -b file --python rprof.py -- out.png : left profile (camera +x looking -x) at multiangle-plate scale, 3x crop."""
import bpy, sys
from mathutils import Vector
out=sys.argv[sys.argv.index('--')+1]
S=0.005916*1.0/3
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='MATERIAL'
sc.render.resolution_x=390; sc.render.resolution_y=900
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.85,0.85,0.86)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=900*S
# head centre in y (model) -> image x of plate head centre (790-700)*3 = 270 px
import numpy as np
me=bpy.data.objects['Body_F'].data
v=np.array([tuple(x.co) for x in me.vertices]); h=v[v[:,2]>1.45]
yc=(h[:,1].min()+h[:,1].max())/2
d=Vector((-1,0,0)); zc=0.8468
# image x = (140?)... camera right vector = -y direction? camera at +x looking -x: right = +y? determine empirically: place so head centre at px 270
# right vector for looking -x with up +z is (0,1,0)*(-1)? compute: right = dir x up
right=d.cross(Vector((0,0,1))); print('right',right)
# desired: head centre at 270px from left => offset from image centre (195px) = +75px to the right
off=75*S
cam_y=yc - (right.y)*off
cam.location=Vector((3,cam_y,zc)); cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sc.render.filepath=out; bpy.ops.render.render(write_still=True)
