"""blender -b file --python rsil.py -- out_prefix : flat silhouette front/back at plate framing."""
import bpy, sys
from mathutils import Vector
pre=sys.argv[sys.argv.index('--')+1]
S=0.0025954198473282443
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading; sh.light='FLAT'; sh.color_type='SINGLE'; sh.single_color=(1,1,1)
sc.display.render_aa='OFF'
sc.render.film_transparent=True
sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=1280*S
zc=(679-360)*S
def shot(name,x,d):
    d=Vector(d); cam.location=Vector((x,0,zc))-d*3
    cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
shot('front',(640-440)*S,(0,1,0))
shot('back',(847-640)*S,(0,-1,0))
