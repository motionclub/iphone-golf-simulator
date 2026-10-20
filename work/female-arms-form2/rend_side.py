"""blender -b file --python rend_side.py -- out.png : left-profile ortho at the plate side-panel framing (crop x 750..850,y 95..250 @ S2)"""
import bpy, sys
from mathutils import Vector
out=sys.argv[sys.argv.index('--')+1]
S2=1.7039/288.5
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
    if o.type=='EMPTY': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='SINGLE'; sh.single_color=(0.78,0.78,0.80); sh.show_cavity=False; sh.show_shadows=False
sc.render.film_transparent=True
K=8; sc.render.resolution_x=100*K; sc.render.resolution_y=155*K
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=155*S2
yc=(800-791.5)*S2; zc=(338.5-172.5)*S2
cam.location=Vector((5,yc,zc)); d=Vector((-1,0,0)); cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sc.render.filepath=out; bpy.ops.render.render(write_still=True)
