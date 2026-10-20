"""usage: blender -b file.blend --python rend.py -- out_prefix  ; renders arm views with Workbench."""
import bpy, sys, math, numpy as np
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:]; pre=argv[0]
sc=bpy.context.scene
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name not in('Body_M',): o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='SINGLE'; sh.single_color=(0.62,0.62,0.64); sh.show_cavity=False
sh.studio_light='rim.sl' if False else sh.studio_light
sc.render.resolution_x=900; sc.render.resolution_y=900; sc.render.film_transparent=False
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.2,0.2,0.22)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
def shot(name,center,dirv,scale,up=(0,0,1)):
    d=Vector(dirv).normalized(); cam.location=Vector(center)+d*3
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
    # make up = z
    q=(-d).to_track_quat('-Z','Y'); cam.rotation_euler=q.to_euler()
    cam.data.ortho_scale=scale
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
V={
 'front':(0,-1,0),'back':(0,1,0),'side':(1,0,0),
}
# full arm views, right arm (x>0): centre ~ (0.42,-0.05,1.0)
for k,d in V.items():
    shot('arm_'+k,(0.42,-0.05,1.0),d,0.9)
# hand closeups, hand ~ x 0.6-0.67, z 0.8-0.9
for k,d in {'front':(0,-1,0),'back':(0,1,0),'palm':(0,0,1),'top':(0,0,-1)}.items():
    shot('hand_'+k,(0.63,-0.11,0.84),d,0.26)
